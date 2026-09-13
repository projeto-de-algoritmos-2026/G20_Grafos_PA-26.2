# src/entities/entity.py
"""
Classe base para todas as entidades do jogo (jogador e monstros).
"""

from __future__ import annotations
from dataclasses import dataclass, field

Coord = tuple[int, int]


@dataclass
class Entity:
    """
    Entidade genérica posicionada no grid.

    Attributes:
        col, row : posição atual no grid.
        hp       : pontos de vida atuais.
        max_hp   : pontos de vida máximos.
        name     : nome da entidade (para logs/HUD).
    """
    col:    int
    row:    int
    hp:     int
    max_hp: int
    name:   str = "Entity"

    # ── Posição ───────────────────────────────────────────────────────────────

    @property
    def pos(self) -> Coord:
        """Posição atual como tupla (col, row)."""
        return (self.col, self.row)

    def move_to(self, col: int, row: int) -> None:
        """Move a entidade para (col, row)."""
        self.col = col
        self.row = row

    # ── Combate básico ────────────────────────────────────────────────────────

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        """
        Aplica dano. Retorna o dano efetivo aplicado.
        HP não cai abaixo de 0.
        """
        effective = min(self.hp, max(0, amount))
        self.hp -= effective
        return effective

    def heal(self, amount: int) -> int:
        """
        Cura a entidade. Retorna a cura efetiva aplicada.
        HP não ultrapassa max_hp.
        """
        effective = min(self.max_hp - self.hp, max(0, amount))
        self.hp += effective
        return effective

    def __repr__(self) -> str:
        return f"{self.name}(pos={self.pos}, hp={self.hp}/{self.max_hp})"
