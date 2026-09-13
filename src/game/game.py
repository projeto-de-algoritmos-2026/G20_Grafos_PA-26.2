# src/game/game.py
"""
Game — loop principal do jogo.

Responsabilidades:
    - Inicializar Pygame e criar a janela.
    - Gerar/regenerar o dungeon via DungeonGenerator.
    - Processar input do jogador (movimento, debug, regenerar).
    - Executar turno dos monstros (chamada à MonsterAI via Monster.decide_action).
    - Resolver combate básico.
    - Delegar renderização ao Renderer.
    - Manter log de mensagens de eventos.
"""

from __future__ import annotations

import sys
import random

import pygame

from src.dungeon.generator import DungeonGenerator, DungeonData
from src.entities.player import Player
from src.entities.monster import Monster
from src.game.renderer import Renderer
from src.game.constants import (
    WINDOW_TITLE, SCREEN_W, SCREEN_H, FPS, TILE_SIZE,
    NUM_MONSTERS,
    KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_WAIT, KEY_DEBUG, KEY_REGEN,
)

Coord = tuple[int, int]

# Deltas de movimento para as teclas
_MOVE_DELTA: dict[int, Coord] = {
    KEY_UP:    ( 0, -1),
    KEY_DOWN:  ( 0,  1),
    KEY_LEFT:  (-1,  0),
    KEY_RIGHT: ( 1,  0),
}


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

        self._screen   = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self._clock    = pygame.time.Clock()
        self._renderer = Renderer(self._screen)

        self._seed       = seed
        self._debug_mode = False
        self._running    = True
        self._rng        = random.Random(seed)

        # Estado do mundo (inicializado em _new_dungeon)
        self._dungeon:  DungeonData | None = None
        self._player:   Player      | None = None
        self._monsters: list[Monster]      = []
        self._msg_log:  list[str]          = []

        self._new_dungeon()

    # ── Geração ───────────────────────────────────────────────────────────────

    def _new_dungeon(self) -> None:
        """
        Gera um novo dungeon, posiciona jogador e monstros.
        Chamado na inicialização e ao pressionar R.
        """
        # Semente aleatória ou a partir do estado atual do RNG
        dungeon_seed = self._rng.randint(0, 2**31)
        gen = DungeonGenerator(seed=dungeon_seed)
        self._dungeon = gen.generate()

        rooms = self._dungeon.rooms
        if not rooms:
            self._log("ERRO: Nenhuma sala gerada!")
            return

        # Jogador na primeira sala
        ps = self._dungeon.player_start
        self._player = Player(
            col=ps[0], row=ps[1],
            hp=30, max_hp=30,
            name="Herói",
        )

        # Monstros em salas aleatórias (evita sala do jogador se possível)
        self._monsters = []
        monster_rooms = rooms[1:] if len(rooms) > 1 else rooms
        for i in range(min(NUM_MONSTERS, len(monster_rooms) * 2)):
            room = self._rng.choice(monster_rooms)
            # Gera posição aleatória dentro da sala
            mc = self._rng.randint(room.col + 1, room.col + room.width  - 2)
            mr = self._rng.randint(room.row + 1, room.row + room.height - 2)
            m = Monster(
                col=mc, row=mr,
                hp=10, max_hp=10,
                name=f"Goblin {i+1}",
                attack_power=3,
                vision_range=15,
            )
            self._monsters.append(m)

        self._log(
            f"Dungeon gerado: {len(rooms)} salas, "
            f"{len(self._dungeon.mst_edges)} corredores MST, "
            f"{len(self._monsters)} monstros."
        )

    # ── Loop principal ────────────────────────────────────────────────────────

    def run(self) -> None:
        """Loop principal do jogo. Bloqueia até fechar a janela."""
        while self._running:
            self._clock.tick(FPS)
            player_acted = self._handle_events()
            if player_acted:
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
                # Toggle debug
                if event.key == KEY_DEBUG:
                    self._debug_mode = not self._debug_mode
                    self._log(f"Debug {'ON' if self._debug_mode else 'OFF'} — overlay A*")
                    return False

                # Regenerar dungeon
                if event.key == KEY_REGEN:
                    self._new_dungeon()
                    self._log("Novo dungeon gerado!")
                    return False

                # Esperar um turno
                if event.key == KEY_WAIT:
                    self._player.end_turn()
                    return True

                # Movimento
                if event.key in _MOVE_DELTA and self._player and self._dungeon:
                    dc, dr = _MOVE_DELTA[event.key]
                    target = (self._player.col + dc, self._player.row + dr)

                    # Verifica se ataca monstro adjacente
                    attacked = self._player_attack_if_monster_at(target)
                    if attacked:
                        self._player.end_turn()
                        return True

                    # Movimento normal
                    monster_positions = {m.pos for m in self._monsters if m.is_alive}
                    moved = self._player.try_move(
                        dc, dr,
                        self._dungeon.tilemap.is_walkable,
                        monster_positions,
                    )
                    if moved:
                        self._player.end_turn()
                        return True

        return False

    # ── Combate ───────────────────────────────────────────────────────────────

    def _player_attack_if_monster_at(self, target: Coord) -> bool:
        """
        Se há um monstro em *target*, ataca e retorna True.
        TODO: adicionar dados de dano, críticos, resistências etc.
        """
        for m in self._monsters:
            if m.is_alive and m.pos == target:
                dmg = self._player.attack_power
                effective = m.take_damage(dmg)
                self._log(f"Você atacou {m.name} por {effective} de dano! HP: {m.hp}/{m.max_hp}")
                if not m.is_alive:
                    self._log(f"{m.name} foi derrotado!")
                    self._player.add_score(10)
                return True
        return False

    def _monster_attack_player(self, monster: Monster) -> None:
        """Monstro ataca o jogador."""
        dmg = monster.attack_power
        effective = self._player.take_damage(dmg)
        self._log(f"{monster.name} atacou você por {effective} de dano! HP: {self._player.hp}/{self._player.max_hp}")
        if not self._player.is_alive:
            self._log("Você foi derrotado! Pressione R para regenerar.")

    # ── Turno dos monstros ────────────────────────────────────────────────────

    def _process_monster_turns(self) -> None:
        """
        Executa o turno de cada monstro vivo.

        Para cada monstro:
            1. Chama decide_action() → MonsterAction (move/attack/wait).
            2. Resolve a ação:
               - move   : verifica walkable + não colide com outros monstros.
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
                # Verifica colisão com outros monstros (exceto self)
                others = all_positions - {monster.pos}
                if (
                    self._dungeon.tilemap.is_walkable(*new_pos)
                    and new_pos not in others
                    and new_pos != self._player.pos
                ):
                    all_positions.discard(monster.pos)
                    monster.move_to(*new_pos)
                    all_positions.add(new_pos)

        # Remove monstros mortos da lista principal
        self._monsters = [m for m in self._monsters if m.is_alive]

    # ── Renderização ──────────────────────────────────────────────────────────

    def _render(self) -> None:
        if not self._dungeon or not self._player:
            return
        self._renderer.render_all(
            tilemap=self._dungeon.tilemap,
            player=self._player,
            monsters=[m for m in self._monsters if m.is_alive],
            debug_mode=self._debug_mode,
            message_log=self._msg_log,
        )

    # ── Utilitários ───────────────────────────────────────────────────────────

    def _log(self, message: str) -> None:
        """Adiciona uma mensagem ao log de eventos (máx. 50 entradas)."""
        print(f"[LOG] {message}")
        self._msg_log.append(message)
        if len(self._msg_log) > 50:
            self._msg_log.pop(0)
