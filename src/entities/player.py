# src/entities/player.py
"""
Classe Player — jogador controlado pelo usuário.
"""

from __future__ import annotations
from dataclasses import dataclass, field

from src.entities.entity import Entity
from src.entities.item import Item
from src.entities.weapon import Weapon, FISTS

Coord = tuple[int, int]


@dataclass
class Player(Entity):
    """
    Jogador controlado pelo usuário via teclado.

    Herda de Entity toda a lógica de HP e posição.
    Adiciona atributos de combate básico (ataque) e contagem de turnos.

    Attributes:
        weapon       : arma equipada.
        armor        : armadura equipada, se houver.
        level        : nível atual do personagem.
        turns        : número de turnos jogados.
        score        : pontuação acumulada.
    """
    weapon:       Weapon = FISTS
    armor:        Item | None = None
    level:        int = 1
    turns:        int = field(default=0, init=False)
    score:        int = field(default=0, init=False)

    # ── Ações ─────────────────────────────────────────────────────────────────

    def try_move(
        self,
        dc: int,
        dr: int,
        is_walkable_fn,
        occupied_positions: set[Coord],
    ) -> bool:
        """
        Tenta mover o jogador em (dc, dr).

        Args:
            dc, dr             : delta de coluna e linha.
            is_walkable_fn     : callable(col, row) → bool do TileMap.
            occupied_positions : conjunto de posições ocupadas por monstros.

        Returns:
            True se o movimento foi realizado.
        """
        nc, nr = self.col + dc, self.row + dr
        if is_walkable_fn(nc, nr) and (nc, nr) not in occupied_positions:
            self.move_to(nc, nr)
            return True
        return False

    def end_turn(self) -> None:
        """Incrementa o contador de turnos."""
        self.turns += 1

    def add_score(self, points: int) -> None:
        self.score += points

    def increase_max_hp(self, amount: int) -> None:
        """
        Aumenta o HP máximo do jogador e soma ao HP atual proporcionalmente,
        sem resetar a vida.
        """
        self.max_hp += amount
        self.hp += amount
