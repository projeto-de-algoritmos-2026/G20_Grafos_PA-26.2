# src/game/renderer.py
"""
Renderer — responsável por todo o desenho Pygame.

Separação de responsabilidades:
    Game     → lógica de turno, estado do mundo.
    Renderer → traduz o estado em pixels.

Funcionalidades:
    - Desenha TileMap (WALL / FLOOR / CORRIDOR).
    - Desenha entidades (Jogador, Monstros).
    - Overlay de debug (tecla D):
        · Caminho A* do monstro mais próximo ao jogador (células coloridas).
        · Indicador de origem e destino do caminho.
    - HUD básico (HP, turno, modo debug).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.dungeon.tilemap import TileType
from src.game.constants import (
    TILE_SIZE,
    C_WALL, C_FLOOR, C_CORRIDOR, C_GRID_LINE,
    C_PLAYER, C_MONSTER,
    C_PATH_FILL, C_START_NODE, C_GOAL_NODE,
    C_TEXT, C_TEXT_ACCENT, C_HUD_BG,
    SCREEN_W, SCREEN_H,
)

if TYPE_CHECKING:
    from src.dungeon.tilemap import TileMap
    from src.entities.player import Player
    from src.entities.monster import Monster

Coord = tuple[int, int]

# Cores sólidas dos tiles
_TILE_COLOR = {
    TileType.WALL:     C_WALL,
    TileType.FLOOR:    C_FLOOR,
    TileType.CORRIDOR: C_CORRIDOR,
}


class Renderer:
    """Encapsula toda a lógica de renderização Pygame."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self._font_sm = pygame.font.SysFont("monospace", 14, bold=False)
        self._font_md = pygame.font.SysFont("monospace", 18, bold=True)

        # Surface auxiliar para overlays transparentes
        self._overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

    # ── API pública ───────────────────────────────────────────────────────────

    def render_all(
        self,
        tilemap: "TileMap",
        player: "Player",
        monsters: list["Monster"],
        debug_mode: bool,
        message_log: list[str],
    ) -> None:
        """
        Renderiza um frame completo.

        Args:
            tilemap     : mapa de tiles atual.
            player      : entidade do jogador.
            monsters    : lista de monstros vivos.
            debug_mode  : se True, desenha overlay do caminho A*.
            message_log : últimas mensagens para o log de eventos.
        """
        self.screen.fill(C_WALL)

        self._draw_tilemap(tilemap)

        if debug_mode:
            self._draw_debug_paths(monsters, player)

        self._draw_entities(player, monsters)
        self._draw_hud(player, debug_mode, message_log)

        pygame.display.flip()

    # ── Camadas de desenho ────────────────────────────────────────────────────

    def _draw_tilemap(self, tilemap: "TileMap") -> None:
        """Desenha cada tile do mapa."""
        for row in range(tilemap.height):
            for col in range(tilemap.width):
                tile = tilemap.get(col, row)
                color = _TILE_COLOR.get(tile, C_WALL)
                rect  = self._cell_rect(col, row)
                pygame.draw.rect(self.screen, color, rect)

    def _draw_debug_paths(
        self,
        monsters: list["Monster"],
        player: "Player",
    ) -> None:
        """
        Overlay de debug: pinta o caminho A* do monstro mais próximo ao jogador.

        Células do caminho recebem uma sobreposição semi-transparente amarela.
        Origem e destino são marcados com cores distintas.
        """
        if not monsters:
            return

        # Monstro mais próximo (distância de Manhattan)
        pc, pr = player.pos
        closest = min(
            monsters,
            key=lambda m: abs(m.col - pc) + abs(m.row - pr),
        )

        path = closest.debug_path
        if not path:
            return

        self._overlay.fill((0, 0, 0, 0))   # limpa overlay

        # Desenha células intermediárias do caminho
        for coord in path[1:-1]:
            r = self._cell_rect(*coord)
            pygame.draw.rect(self._overlay, C_PATH_FILL, r)

        # Origem (monstro)
        if path:
            pygame.draw.rect(self.screen, C_START_NODE, self._cell_rect(*path[0]), 3)

        # Destino (jogador)
        if len(path) > 1:
            pygame.draw.rect(self.screen, C_GOAL_NODE, self._cell_rect(*path[-1]), 3)

        self.screen.blit(self._overlay, (0, 0))

        # Label no centro da tela
        lbl = self._font_sm.render(
            f"DEBUG — A* path len={len(path)}  monstro=({closest.col},{closest.row})",
            True, C_TEXT_ACCENT,
        )
        self.screen.blit(lbl, (8, SCREEN_H - 24))

    def _draw_entities(self, player: "Player", monsters: list["Monster"]) -> None:
        """Desenha jogador e monstros como círculos coloridos."""
        # Monstros
        for m in monsters:
            if m.is_alive:
                cx, cy = self._cell_center(m.col, m.row)
                radius = TILE_SIZE // 2 - 3
                pygame.draw.circle(self.screen, C_MONSTER, (cx, cy), radius)
                # Barra de HP mini
                self._draw_mini_hp_bar(m.col, m.row, m.hp, m.max_hp)

        # Jogador (por cima dos monstros)
        px, py = self._cell_center(player.col, player.row)
        radius = TILE_SIZE // 2 - 2
        pygame.draw.circle(self.screen, C_PLAYER, (px, py), radius)

    def _draw_mini_hp_bar(
        self, col: int, row: int, hp: int, max_hp: int
    ) -> None:
        """Barra de HP de 1 tile de largura sobre a entidade."""
        x = col * TILE_SIZE
        y = row * TILE_SIZE - 5
        w = TILE_SIZE
        h = 3
        pygame.draw.rect(self.screen, (80, 0, 0), (x, y, w, h))
        filled = int(w * hp / max_hp) if max_hp > 0 else 0
        pygame.draw.rect(self.screen, (180, 30, 30), (x, y, filled, h))

    def _draw_hud(
        self,
        player: "Player",
        debug_mode: bool,
        message_log: list[str],
    ) -> None:
        """HUD superior com HP, turno e modo ativo."""
        lines = [
            f"HP: {player.hp}/{player.max_hp}   Turno: {player.turns}   Pontos: {player.score}",
            f"[Setas] Mover  [.] Esperar  [D] Debug={'ON' if debug_mode else 'OFF'}  [R] Regenerar",
        ]
        y = 4
        for line in lines:
            surf = self._font_sm.render(line, True, C_TEXT)
            self.screen.blit(surf, (6, y))
            y += 18

        # Log de mensagens (canto inferior esquerdo)
        log_y = SCREEN_H - 20 - 16 * min(len(message_log), 3)
        for msg in message_log[-3:]:
            surf = self._font_sm.render(msg, True, C_TEXT)
            self.screen.blit(surf, (6, log_y))
            log_y += 16

    # ── Helpers de geometria ──────────────────────────────────────────────────

    @staticmethod
    def _cell_rect(col: int, row: int) -> pygame.Rect:
        return pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    @staticmethod
    def _cell_center(col: int, row: int) -> tuple[int, int]:
        return (
            col * TILE_SIZE + TILE_SIZE // 2,
            row * TILE_SIZE + TILE_SIZE // 2,
        )
