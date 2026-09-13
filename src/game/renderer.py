# src/game/renderer.py
"""
Renderer — responsável por todo o desenho Pygame.

Separação de responsabilidades:
    Game     → lógica de turno, estado do mundo.
    Renderer → traduz o estado em pixels na viewport com câmera.

Sistema de Câmera:
    A câmera é definida pela posição (cam_col, cam_row) em tiles — o canto
    superior esquerdo do que está sendo exibido. Todas as coordenadas de
    tile são convertidas para coordenadas de tela subtraindo esse offset.

Funcionalidades:
    - Viewport com câmera scrollável (só renderiza tiles visíveis).
    - Desenha TileMap (WALL / FLOOR / CORRIDOR / TRAP).
    - Glifo 'X' nas armadilhas visíveis.
    - Barra de HP do jogador proeminente no HUD.
    - Overlay de debug (tecla TAB):
        · Caminho A* do monstro mais próximo ao jogador (células coloridas).
    - HUD com controles, HP, turno.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from src.dungeon.tilemap import TileType
from src.game.constants import (
    TILE_SIZE, SCREEN_W, SCREEN_H, VIEWPORT_COLS, VIEWPORT_ROWS,
    C_WALL, C_FLOOR, C_CORRIDOR, C_TRAP, C_TRAP_GLYPH,
    C_PLAYER, C_MONSTER,
    C_PATH_FILL, C_START_NODE, C_GOAL_NODE,
    C_TEXT, C_TEXT_ACCENT, C_TEXT_WARN,
    C_HP_BG, C_HP_FILL, C_HP_FILL_HIGH, C_HP_FILL_MID,
)

if TYPE_CHECKING:
    from src.dungeon.tilemap import TileMap
    from src.entities.player import Player
    from src.entities.monster import Monster
    from src.entities.weapon import Weapon
    from src.entities.item import Item

Coord = tuple[int, int]

# Mapeamento tile → cor base
_TILE_COLOR = {
    TileType.WALL:     C_WALL,
    TileType.FLOOR:    C_FLOOR,
    TileType.CORRIDOR: C_CORRIDOR,
    TileType.TRAP:     C_TRAP,
    TileType.EXIT:     C_FLOOR, # Fundo igual ao piso, vamos desenhar algo por cima
}


class Camera:
    """
    Gerencia a posição da câmera (offset em tiles, canto superior esquerdo).

    O jogador é mantido no centro por padrão; setas aplicam um offset manual
    limitado por CAM_MAX_OFFSET tiles em qualquer direção.
    """

    def __init__(self) -> None:
        # Offset manual em tiles (deslocamento em relação ao centro no jogador)
        self.offset_col: int = 0
        self.offset_row: int = 0

    def reset(self) -> None:
        self.offset_col = 0
        self.offset_row = 0

    def pan(self, dc: int, dr: int, max_offset: int) -> None:
        """Desloca a câmera em (dc, dr) tiles, respeitando o limite."""
        self.offset_col = max(-max_offset, min(max_offset, self.offset_col + dc))
        self.offset_row = max(-max_offset, min(max_offset, self.offset_row + dr))

    def top_left(self, player_col: int, player_row: int) -> tuple[int, int]:
        """
        Retorna (cam_col, cam_row) — tile do canto superior esquerdo da viewport.

        Centraliza o jogador + offset manual.
        """
        viewport_half_w = SCREEN_W // (2 * TILE_SIZE)
        viewport_half_h = SCREEN_H // (2 * TILE_SIZE)
        cam_col = player_col + self.offset_col - viewport_half_w
        cam_row = player_row + self.offset_row - viewport_half_h
        return cam_col, cam_row


class Renderer:
    """Encapsula toda a lógica de renderização Pygame com suporte à câmera."""

    def __init__(self, screen: pygame.Surface, screen_w: int, screen_h: int) -> None:
        self.screen = screen
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.camera = Camera()
        self._font_sm  = pygame.font.SysFont("monospace", 13, bold=False)
        self._font_md  = pygame.font.SysFont("monospace", 16, bold=True)
        self._font_hud = pygame.font.SysFont("monospace", 15, bold=True)
        self._font_huge = pygame.font.SysFont("monospace", 48, bold=True)

        # Surface auxiliar para overlays semi-transparentes
        self._overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)

    # ── API pública ───────────────────────────────────────────────────────────

    def render_all(
        self,
        tilemap: "TileMap",
        player: "Player",
        monsters: list["Monster"],
        weapons: dict[Coord, "Weapon"],
        items: dict[Coord, "Item"],
        debug_mode: bool,
        message_log: list[str],
        is_game_over: bool,
        is_victory: bool,
    ) -> None:
        """
        Renderiza um frame completo usando o sistema de câmera.
        """
        self.screen.fill(C_WALL)

        cam_col, cam_row = self.camera.top_left(player.col, player.row)

        self._draw_tilemap(tilemap, cam_col, cam_row)
        self._draw_weapons(weapons, cam_col, cam_row)
        self._draw_items(items, cam_col, cam_row)

        if debug_mode:
            self._draw_debug_paths(monsters, player, cam_col, cam_row)

        self._draw_entities(player, monsters, cam_col, cam_row)
        self._draw_hud(player, monsters, debug_mode, message_log)

        if is_game_over:
            self._draw_game_over()
        elif is_victory:
            self._draw_victory()

        pygame.display.flip()

    # ── Câmera ────────────────────────────────────────────────────────────────

    def _world_to_screen(self, col: int, row: int, cam_col: int, cam_row: int) -> tuple[int, int]:
        """Converte coordenada de tile para pixel na tela."""
        sx = (col - cam_col) * TILE_SIZE
        sy = (row - cam_row) * TILE_SIZE
        return sx, sy

    def _screen_rect(self, col: int, row: int, cam_col: int, cam_row: int) -> pygame.Rect:
        sx, sy = self._world_to_screen(col, row, cam_col, cam_row)
        return pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE)

    def _screen_center(self, col: int, row: int, cam_col: int, cam_row: int) -> tuple[int, int]:
        sx, sy = self._world_to_screen(col, row, cam_col, cam_row)
        return sx + TILE_SIZE // 2, sy + TILE_SIZE // 2

    # ── Camadas de desenho ────────────────────────────────────────────────────

    def _draw_tilemap(self, tilemap: "TileMap", cam_col: int, cam_row: int) -> None:
        """Desenha apenas os tiles visíveis na viewport atual."""
        v_cols = self.screen_w // TILE_SIZE + 2
        v_rows = self.screen_h // TILE_SIZE + 2
        for dr in range(v_rows + 1):
            for dc in range(v_cols + 1):
                world_col = cam_col + dc
                world_row = cam_row + dr

                if not tilemap.in_bounds(world_col, world_row):
                    # Fora do mapa → cor de parede padrão (já foi fill)
                    continue

                tile  = tilemap.get(world_col, world_row)
                color = _TILE_COLOR.get(tile, C_WALL)
                rect  = self._screen_rect(world_col, world_row, cam_col, cam_row)
                pygame.draw.rect(self.screen, color, rect)

                # Glifo 'X' nas armadilhas
                if tile == TileType.TRAP:
                    self._draw_trap_glyph(rect)
                elif tile == TileType.EXIT:
                    self._draw_exit_glyph(rect)

    def _draw_weapons(self, weapons: dict[Coord, "Weapon"], cam_col: int, cam_row: int) -> None:
        """Desenha as armas espalhadas pelo chão."""
        for (col, row), weapon in weapons.items():
            rect = self._screen_rect(col, row, cam_col, cam_row)
            if -TILE_SIZE <= rect.x <= self.screen_w and -TILE_SIZE <= rect.y <= self.screen_h:
                lbl = self._font_md.render(weapon.symbol, True, weapon.color)
                self.screen.blit(lbl, (rect.x + 8, rect.y + 4))

    def _draw_trap_glyph(self, rect: pygame.Rect) -> None:
        """Desenha um 'X' estilizado no centro do tile de armadilha."""
        margin = 6
        x1, y1 = rect.left + margin, rect.top + margin
        x2, y2 = rect.right - margin, rect.bottom - margin
        pygame.draw.line(self.screen, C_TRAP_GLYPH, (x1, y1), (x2, y2), 2)
        pygame.draw.line(self.screen, C_TRAP_GLYPH, (x2, y1), (x1, y2), 2)

    def _draw_exit_glyph(self, rect: pygame.Rect) -> None:
        """Desenha um portão estilizado para a saída."""
        from src.game.constants import C_EXIT
        lbl = self._font_sm.render("EXIT", True, C_EXIT)
        self.screen.blit(lbl, (rect.x, rect.y + 10))

    def _draw_items(self, items: dict[Coord, "Item"], cam_col: int, cam_row: int) -> None:
        """Desenha armaduras e poções."""
        for (col, row), item in items.items():
            rect = self._screen_rect(col, row, cam_col, cam_row)
            if -TILE_SIZE <= rect.x <= self.screen_w and -TILE_SIZE <= rect.y <= self.screen_h:
                lbl = self._font_md.render(item.symbol, True, item.color)
                self.screen.blit(lbl, (rect.x + 8, rect.y + 4))

    def _draw_debug_paths(
        self,
        monsters: list["Monster"],
        player: "Player",
        cam_col: int,
        cam_row: int,
    ) -> None:
        """
        Overlay de debug: pinta o caminho A* do monstro mais próximo ao jogador.
        Células do caminho recebem sobreposição semi-transparente amarela.
        """
        if not monsters:
            return

        pc, pr = player.pos
        closest = min(
            monsters,
            key=lambda m: abs(m.col - pc) + abs(m.row - pr),
        )

        path = closest.debug_path
        if not path:
            return

        self._overlay.fill((0, 0, 0, 0))

        for coord in path[1:-1]:
            r = self._screen_rect(*coord, cam_col, cam_row)
            pygame.draw.rect(self._overlay, C_PATH_FILL, r)

        self.screen.blit(self._overlay, (0, 0))

        # Bordas de origem e destino
        if path:
            pygame.draw.rect(
                self.screen, C_START_NODE,
                self._screen_rect(*path[0], cam_col, cam_row), 3
            )
        if len(path) > 1:
            pygame.draw.rect(
                self.screen, C_GOAL_NODE,
                self._screen_rect(*path[-1], cam_col, cam_row), 3
            )

        lbl = self._font_sm.render(
            f"DEBUG A*: caminho={len(path)} tiles | monstro=({closest.col},{closest.row})",
            True, C_TEXT_ACCENT,
        )
        self.screen.blit(lbl, (8, SCREEN_H - 22))

    def _draw_entities(
        self,
        player: "Player",
        monsters: list["Monster"],
        cam_col: int,
        cam_row: int,
    ) -> None:
        """Desenha jogador e monstros como círculos coloridos."""
        radius = TILE_SIZE // 2 - 3

        for m in monsters:
            if not m.is_alive:
                continue
            cx, cy = self._screen_center(m.col, m.row, cam_col, cam_row)
            if -TILE_SIZE <= cx <= self.screen_w + TILE_SIZE and -TILE_SIZE <= cy <= self.screen_h + TILE_SIZE:
                pygame.draw.circle(self.screen, m.color, (cx, cy), radius)
                self._draw_mini_hp_bar(m.col, m.row, m.hp, m.max_hp, cam_col, cam_row)

        # Jogador (por cima dos monstros)
        px, py = self._screen_center(player.col, player.row, cam_col, cam_row)
        pygame.draw.circle(self.screen, C_PLAYER, (px, py), radius + 1)

    def _draw_mini_hp_bar(
        self,
        col: int, row: int,
        hp: int, max_hp: int,
        cam_col: int, cam_row: int,
    ) -> None:
        """Barra de HP minúscula sobre o monstro."""
        sx, sy = self._world_to_screen(col, row, cam_col, cam_row)
        w, h = TILE_SIZE, 3
        pygame.draw.rect(self.screen, (70, 10, 10), (sx, sy - 5, w, h))
        if max_hp > 0:
            filled = max(1, int(w * hp / max_hp))
            pygame.draw.rect(self.screen, (180, 30, 30), (sx, sy - 5, filled, h))

    # ── HUD ───────────────────────────────────────────────────────────────────

    def _draw_hud(
        self,
        player: "Player",
        monsters: list["Monster"],
        debug_mode: bool,
        message_log: list[str],
    ) -> None:
        """HUD superior com barra de HP destacada e controles."""
        self._draw_player_hp_bar(player)
        self._draw_info_line(player, monsters, debug_mode)
        self._draw_controls_hint()
        self._draw_message_log(message_log)

    def _draw_game_over(self) -> None:
        """Desenha a tela de Game Over semi-transparente no centro."""
        self._overlay.fill((0, 0, 0, 180))
        self.screen.blit(self._overlay, (0, 0))

        lbl = self._font_huge.render("GAME OVER", True, C_HP_FILL)
        rect = lbl.get_rect(center=(self.screen_w // 2, self.screen_h // 2 - 40))
        self.screen.blit(lbl, rect)

        lbl2 = self._font_md.render("Pressione R para tentar novamente", True, C_TEXT)
        rect2 = lbl2.get_rect(center=(self.screen_w // 2, self.screen_h // 2 + 20))
        self.screen.blit(lbl2, rect2)

    def _draw_victory(self) -> None:
        """Desenha a tela de Vitória semi-transparente no centro."""
        from src.game.constants import C_EXIT
        self._overlay.fill((0, 0, 0, 180))
        self.screen.blit(self._overlay, (0, 0))

        lbl = self._font_huge.render("VITORIA TOTAL!", True, C_EXIT)
        rect = lbl.get_rect(center=(self.screen_w // 2, self.screen_h // 2 - 40))
        self.screen.blit(lbl, rect)

        lbl2 = self._font_md.render("Todos os inimigos derrotados! Segure R por 1 segundo para nova run", True, C_TEXT)
        rect2 = lbl2.get_rect(center=(self.screen_w // 2, self.screen_h // 2 + 20))
        self.screen.blit(lbl2, rect2)

    def _draw_player_hp_bar(self, player: "Player") -> None:
        """
        Barra de HP do jogador — proeminente no canto superior esquerdo.
        Muda de cor conforme o HP: verde (alto) → amarelo (médio) → vermelho (baixo).
        """
        bar_x, bar_y = 8, 8
        bar_w, bar_h = 200, 18
        ratio = player.hp / player.max_hp if player.max_hp > 0 else 0

        # Fundo
        pygame.draw.rect(self.screen, C_HP_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4)

        # Preenchimento com cor gradativa
        if ratio > 0.6:
            fill_color = C_HP_FILL_HIGH
        elif ratio > 0.3:
            fill_color = C_HP_FILL_MID
        else:
            fill_color = C_HP_FILL

        filled_w = max(0, int(bar_w * ratio))
        if filled_w > 0:
            pygame.draw.rect(
                self.screen, fill_color,
                (bar_x, bar_y, filled_w, bar_h),
                border_radius=4,
            )

        # Borda
        pygame.draw.rect(self.screen, (100, 100, 130), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

        # Texto HP
        hp_txt = self._font_hud.render(
            f"HP  {player.hp} / {player.max_hp}", True, C_TEXT
        )
        self.screen.blit(hp_txt, (bar_x + 6, bar_y + 1))

    def _draw_info_line(self, player: "Player", monsters: list["Monster"], debug_mode: bool) -> None:
        """Linha com turno, pontuação, progresso e equipamentos."""
        debug_str = "  [TAB] DEBUG ON " if debug_mode else ""
        defeated = sum(not monster.is_alive for monster in monsters)
        armor_str = (
            f"{player.armor.name} (+{player.armor.hp_bonus} HP)"
            if player.armor is not None else "Nenhuma"
        )
        line = (
            f"Jogadas: {player.turns}   Pontos: {player.score}   "
            f"Inimigos: {defeated}/{len(monsters)}   "
            f"Arma: {player.weapon.name} ({player.weapon.min_damage}-{player.weapon.max_damage})"
            f"   Armadura: {armor_str}"
            f"{debug_str}"
        )
        surf = self._font_sm.render(line, True,
                                    C_TEXT_ACCENT if debug_mode else C_TEXT)
        self.screen.blit(surf, (8, 32))

    def _draw_controls_hint(self) -> None:
        """Dica de controles no canto inferior direito."""
        hints = [
            "WASD: Mover   .: Esperar   Segure R: Nova run",
            "Setas: Camara  C: Centralizar  TAB: Debug A*",
        ]
        y = self.screen_h - 12 - len(hints) * 15
        for hint in hints:
            surf = self._font_sm.render(hint, True, (130, 130, 155))
            self.screen.blit(surf, (self.screen_w - surf.get_width() - 8, y))
            y += 15

    def _draw_message_log(self, message_log: list[str]) -> None:
        """Log de mensagens no canto inferior esquerdo."""
        lines = message_log[-4:]
        y = self.screen_h - 8 - len(lines) * 16
        for i, msg in enumerate(lines):
            alpha = 180 + int(75 * (i / max(len(lines) - 1, 1)))
            # Mensagens de dano em vermelho-alaranja
            color = C_TEXT_WARN if any(
                kw in msg.lower() for kw in ("dano", "armadilha", "atacou", "derrotado")
            ) else C_TEXT
            surf = self._font_sm.render(msg, True, color)
            self.screen.blit(surf, (8, y))
            y += 16
