# src/game/game.py
"""
Game — loop principal do jogo.

Responsabilidades:
    - Inicializar Pygame e criar a janela (1280x720).
    - Gerar/regenerar o dungeon via DungeonGenerator.
    - Processar input:
        · WASD    → movimento do jogador / ataque adjacente.
        · Setas   → panning manual da câmera.
        · C       → centraliza câmera no jogador.
        · TAB     → toggle do overlay de debug A*.
        · R       → regenerar dungeon.
        · .       → esperar turno.
    - Executar turno dos monstros após cada ação do jogador.
    - Resolver combate básico (jogador ↔ monstro).
    - Verificar pisada em armadilha e aplicar dano.
    - Delegar renderização ao Renderer.
    - Manter log de mensagens de eventos.
"""

from __future__ import annotations

import sys
import random

import pygame

from src.dungeon.generator import DungeonGenerator, DungeonData
from src.entities.player import Player
from src.entities.monster import Monster, create_random_monster
from src.entities.item import Item
from src.game.renderer import Renderer
from src.game.constants import (
    WINDOW_TITLE, SCREEN_W, SCREEN_H, FPS,
    NUM_MONSTERS,
    TRAP_DAMAGE_MIN, TRAP_DAMAGE_MAX,
    CAM_PAN_SPEED, CAM_MAX_OFFSET,
    KEY_MOVE_UP, KEY_MOVE_DOWN, KEY_MOVE_LEFT, KEY_MOVE_RIGHT, KEY_WAIT,
    KEY_CAM_UP, KEY_CAM_DOWN, KEY_CAM_LEFT, KEY_CAM_RIGHT, KEY_CAM_RESET,
    KEY_DEBUG, KEY_REGEN,
    REGEN_HOLD_MS,
)

Coord = tuple[int, int]

# Mapeamento tecla → delta (col, row) para movimento do jogador (WASD)
_MOVE_DELTA: dict[int, Coord] = {
    KEY_MOVE_UP:    ( 0, -1),
    KEY_MOVE_DOWN:  ( 0,  1),
    KEY_MOVE_LEFT:  (-1,  0),
    KEY_MOVE_RIGHT: ( 1,  0),
}

# Mapeamento tecla → delta (col, row) para panning da câmera (setas)
_CAM_DELTA: dict[int, Coord] = {
    KEY_CAM_UP:    ( 0, -CAM_PAN_SPEED),
    KEY_CAM_DOWN:  ( 0,  CAM_PAN_SPEED),
    KEY_CAM_LEFT:  (-CAM_PAN_SPEED, 0),
    KEY_CAM_RIGHT: ( CAM_PAN_SPEED, 0),
}

STATE_PLAYING   = 0
STATE_GAME_OVER = 1
STATE_VICTORY   = 2


class Game:
    """
    Classe principal que integra todos os subsistemas.

    Usage:
        game = Game()
        game.run()
    """

    def __init__(self, seed: int | None = None) -> None:
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)

        self._screen   = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        # Update SCREEN_W and SCREEN_H constants effectively in this module if needed, or rely on info
        info = pygame.display.Info()
        self.screen_w = info.current_w
        self.screen_h = info.current_h
        
        self._clock    = pygame.time.Clock()
        self._renderer = Renderer(self._screen, self.screen_w, self.screen_h)

        self._seed       = seed
        self._debug_mode = False
        self._running    = True
        self._state      = STATE_PLAYING
        self._total_victory = False
        self._rng        = random.Random(seed)

        # Estado do mundo (inicializado em _new_dungeon)
        self._dungeon:  DungeonData | None = None
        self._player:   Player      | None = None
        self._monsters: list[Monster]      = []
        self._msg_log:  list[str]          = []
        self._regen_started_at: int | None = None

        self._new_dungeon()

    # ── Geração ───────────────────────────────────────────────────────────────

    def _new_dungeon(self) -> None:
        """
        Gera um novo dungeon, posiciona jogador e monstros.
        Chamado na inicialização e ao pressionar R.
        """
        dungeon_seed = self._rng.randint(0, 2**31)
        gen = DungeonGenerator(seed=dungeon_seed)
        self._dungeon = gen.generate()

        rooms = self._dungeon.rooms
        if not rooms:
            self._log("ERRO: Nenhuma sala gerada!")
            return

        # Posição inicial do jogador (centro da sala 0)
        ps = self._dungeon.player_start
        self._player = Player(
            col=ps[0], row=ps[1],
            hp=30, max_hp=30,
            name="Herói",
        )

        # Centraliza câmera no jogador ao (re)gerar o dungeon
        self._renderer.camera.reset()

        # Monstros distribuídos nas salas 1..N
        self._monsters = []
        monster_rooms = rooms[1:] if len(rooms) > 1 else rooms
        for i in range(min(NUM_MONSTERS, len(monster_rooms) * 3)):
            room = self._rng.choice(monster_rooms)
            mc = self._rng.randint(room.col + 1, room.col + room.width  - 2)
            mr = self._rng.randint(room.row + 1, room.row + room.height - 2)
            m = create_random_monster(mc, mr, self._rng)
            self._monsters.append(m)

        self._state = STATE_PLAYING
        self._total_victory = False

        self._log(
            f"Dungeon: {len(rooms)} salas | "
            f"{len(self._dungeon.mst_edges)} corredores (MST) | "
            f"{len(self._dungeon.trap_cells)} armadilhas | "
            f"{len(self._monsters)} monstros"
        )

    # ── Loop principal ────────────────────────────────────────────────────────

    def run(self) -> None:
        """Loop principal do jogo. Bloqueia até fechar a janela."""
        while self._running:
            self._clock.tick(FPS)
            player_acted = self._handle_events()
            if self._state == STATE_PLAYING and player_acted:
                self._check_trap()
                self._check_weapon_pickup()
                self._check_victory()
                if self._state == STATE_PLAYING:
                    self._process_monster_turns()
            self._render()

        pygame.quit()
        sys.exit()

    # ── Input ─────────────────────────────────────────────────────────────────

    def _handle_events(self) -> bool:
        """
        Processa eventos Pygame.

        Returns:
            True se o jogador realizou uma ação de turno (move ou esperar).
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
                return False

            if event.type == pygame.KEYDOWN:
                # ── Ações sem turno ───────────────────────────────────────────

                if event.key == KEY_DEBUG:
                    self._debug_mode = not self._debug_mode
                    self._log(f"Debug A* {'ATIVADO' if self._debug_mode else 'desativado'}")
                    return False

                if event.key == KEY_REGEN and self._regen_started_at is None:
                    self._regen_started_at = pygame.time.get_ticks()
                    self._log("Segure R por 1 segundo para reiniciar a run.")
                    return False

                if self._state in (STATE_GAME_OVER, STATE_VICTORY):
                    continue  # Só aceita R ou sair

                if event.key == KEY_CAM_RESET:
                    self._renderer.camera.reset()
                    return False

                # ── Panning da câmera (setas) ─────────────────────────────────
                if event.key in _CAM_DELTA:
                    dc, dr = _CAM_DELTA[event.key]
                    self._renderer.camera.pan(dc, dr, CAM_MAX_OFFSET)
                    return False

                # ── Ações de turno ────────────────────────────────────────────

                if event.key == KEY_WAIT:
                    self._player.end_turn()
                    return True

                if event.key in _MOVE_DELTA and self._player and self._dungeon:
                    dc, dr = _MOVE_DELTA[event.key]
                    target = (self._player.col + dc, self._player.row + dr)

                    # Verifica ataque a monstro adjacente
                    if self._player_attack_if_monster_at(target):
                        self._player.end_turn()
                        return True

                    # Movimento normal
                    monster_positions = {m.pos for m in self._monsters if m.is_alive}
                    if self._player.try_move(
                        dc, dr,
                        self._dungeon.tilemap.is_walkable,
                        monster_positions,
                    ):
                        self._player.end_turn()
                        return True

            if event.type == pygame.KEYUP and event.key == KEY_REGEN:
                if self._regen_started_at is not None:
                    held_ms = pygame.time.get_ticks() - self._regen_started_at
                    self._regen_started_at = None
                    if held_ms >= REGEN_HOLD_MS:
                        self._new_dungeon()
                    else:
                        self._log("R soltado cedo demais. Segure por 1 segundo.")
                return False

        return False

    # ── Armadilhas ────────────────────────────────────────────────────────────

    def _check_trap(self) -> None:
        """
        Verifica se o jogador pisou em uma armadilha.
        Se sim, aplica dano aleatório e desativa a armadilha (converte para FLOOR).
        """
        if not self._player or not self._dungeon:
            return

        tilemap = self._dungeon.tilemap
        pc, pr = self._player.pos

        if tilemap.is_trap(pc, pr):
            damage = self._rng.randint(TRAP_DAMAGE_MIN, TRAP_DAMAGE_MAX)
            effective = self._player.take_damage(damage)
            tilemap.disarm_trap(pc, pr)
            self._log(
                f"Armadilha! Voce tomou {effective} de dano! "
                f"HP: {self._player.hp}/{self._player.max_hp}"
            )
            if not self._player.is_alive:
                self._state = STATE_GAME_OVER
                self._log("Voce foi derrotado! Pressione R para regenerar.")

    def _check_weapon_pickup(self) -> None:
        """Verifica se o jogador pisou em uma arma."""
        if not self._player or not self._dungeon:
            return
        
        pos = self._player.pos
        if pos in self._dungeon.weapons:
            weapon = self._dungeon.weapons[pos]
            current_weapon = self._player.weapon
            if (weapon.max_damage, weapon.min_damage) > (current_weapon.max_damage, current_weapon.min_damage):
                self._dungeon.weapons.pop(pos)
                self._player.weapon = weapon
                self._player.add_score(weapon.score_bonus)
                self._log(f"Voce pegou: {weapon.name} ({weapon.min_damage}-{weapon.max_damage} dmg)!")
            else:
                self._log(f"{weapon.name} e inferior a arma atual. Item ignorado.")
            
        if pos in self._dungeon.items:
            item = self._dungeon.items[pos]
            if item.is_armor:
                current_bonus = self._player.armor.hp_bonus if self._player.armor else 0
                if item.hp_bonus > current_bonus:
                    self._dungeon.items.pop(pos)
                    self._player.armor = item
                    self._player.add_score(item.score_bonus)
                    self._player.increase_max_hp(item.hp_bonus)
                    self._log(f"Armadura! Max HP +{item.hp_bonus}. HP: {self._player.hp}/{self._player.max_hp}")
                else:
                    self._log(f"{item.name} e inferior a armadura atual. Item ignorado.")
            else:
                self._dungeon.items.pop(pos)
                self._player.add_score(item.score_bonus)
                healed = self._player.heal(item.heal_amount)
                self._log(f"Pocao! Curou {healed} HP. HP: {self._player.hp}/{self._player.max_hp}")

    def _check_victory(self) -> None:
        """Verifica se o jogador alcançou a saída."""
        if not self._player or not self._dungeon:
            return
        if self._player.pos == self._dungeon.exit_pos:
            self._total_victory = bool(self._monsters) and all(
                not monster.is_alive for monster in self._monsters
            )
            self._state = STATE_VICTORY
            if self._total_victory:
                self._log("VITORIA TOTAL! Voce derrotou todos os inimigos e escapou da masmorra!")
            else:
                self._log("VITORIA! Voce escapou da masmorra!")

    # ── Combate ───────────────────────────────────────────────────────────────

    def _player_attack_if_monster_at(self, target: Coord) -> bool:
        """
        Se há um monstro em *target*, ataca-o e retorna True.
        """
        for m in self._monsters:
            if m.is_alive and m.pos == target:
                dmg = self._player.weapon.roll_damage(self._rng)
                effective = m.take_damage(dmg)
                self._log(
                    f"Voce atacou {m.name} por {effective} de dano! "
                    f"HP: {m.hp}/{m.max_hp}"
                )
                if not m.is_alive:
                    self._log(f"{m.name} foi derrotado!")
                    self._player.add_score(10)
                return True
        return False

    def _monster_attack_player(self, monster: Monster) -> None:
        """Monstro ataca o jogador."""
        if not self._player:
            return
        dmg = monster.attack_power
        effective = self._player.take_damage(dmg)
        self._log(
            f"{monster.name} atacou voce por {effective} de dano! "
            f"HP: {self._player.hp}/{self._player.max_hp}"
        )
        if not self._player.is_alive:
            self._state = STATE_GAME_OVER
            self._log("Voce foi derrotado! Pressione R para regenerar.")

    # ── Turno dos monstros ────────────────────────────────────────────────────

    def _process_monster_turns(self) -> None:
        """
        Executa o turno de cada monstro vivo.

        Para cada monstro:
            1. Chama decide_action() → MonsterAction (move/attack/wait).
            2. Resolve a ação:
               - move   : verifica walkable + sem colisão.
               - attack : aplica dano ao jogador.
               - wait   : não faz nada.
        """
        if not self._player or not self._dungeon or not self._player.is_alive:
            return

        alive_monsters = [m for m in self._monsters if m.is_alive]
        all_positions  = {m.pos for m in alive_monsters}

        for monster in alive_monsters:
            action = monster.decide_action(
                player_pos=self._player.pos,
                graph=self._dungeon.graph,
                all_monster_positions=all_positions,
            )

            if action.kind == "attack":
                self._monster_attack_player(monster)

            elif action.kind == "move" and action.target is not None:
                new_pos = action.target
                others  = all_positions - {monster.pos}
                if (
                    self._dungeon.tilemap.is_walkable(*new_pos)
                    and new_pos not in others
                    and new_pos != self._player.pos
                ):
                    all_positions.discard(monster.pos)
                    monster.move_to(*new_pos)
                    all_positions.add(new_pos)

    # ── Renderização ──────────────────────────────────────────────────────────

    def _render(self) -> None:
        if not self._dungeon or not self._player:
            return
        self._renderer.render_all(
            tilemap=self._dungeon.tilemap,
            player=self._player,
            monsters=self._monsters,
            weapons=self._dungeon.weapons,
            items=self._dungeon.items,
            debug_mode=self._debug_mode,
            message_log=self._msg_log,
            is_game_over=(self._state == STATE_GAME_OVER),
            is_victory=(self._state == STATE_VICTORY),
            is_total_victory=self._total_victory,
        )

    # ── Utilitários ───────────────────────────────────────────────────────────

    def _log(self, message: str) -> None:
        """Adiciona uma mensagem ao log de eventos (máx. 50 entradas)."""
        print(f"[LOG] {message}")
        self._msg_log.append(message)
        if len(self._msg_log) > 50:
            self._msg_log.pop(0)
