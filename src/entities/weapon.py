# src/entities/weapon.py
"""
Sistema de armas do jogo.

Armas são itens espalhados no chão do dungeon.
O jogador as pega automaticamente ao caminhar sobre elas.
Cada arma tem dano mínimo/máximo e uma chance de aparecer (peso).

Tabela de loot (ponderada):
    Adaga          40 %   → dano  4–7   (arma comum, upgrade rápido)
    Espada Curta   25 %   → dano  7–11  (dano médio)
    Maça           18 %   → dano  9–14  (lenta mas pesada)
    Machado        12 %   → dano 12–17  (rara, alto dano)
    Espada Flamejante  5 %→ dano 16–22  (épica)

O jogador começa com Punhos (sem arma no chão) — dano 3–5.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Weapon:
    """
    Arma equipável.

    Attributes:
        name       : nome de exibição.
        min_damage : dano mínimo por ataque.
        max_damage : dano máximo por ataque.
        color      : cor RGB para ícone no HUD.
        symbol     : símbolo de 1 char exibido no tile do item.
        spawn_weight: peso na tabela de loot (maior → mais comum).
        score_bonus: pontos bônus ao pegar a arma.
    """
    name:         str
    min_damage:   int
    max_damage:   int
    color:        tuple[int, int, int]
    symbol:       str
    spawn_weight: int
    score_bonus:  int = 0

    def roll_damage(self, rng: random.Random | None = None) -> int:
        """Sorteia um valor de dano entre min e max."""
        r = rng or random
        return r.randint(self.min_damage, self.max_damage)

    def __str__(self) -> str:
        return f"{self.name} ({self.min_damage}–{self.max_damage})"


# ─── Definições de armas ──────────────────────────────────────────────────────

FISTS = Weapon(
    name="Punhos",
    min_damage=3, max_damage=5,
    color=(180, 140, 100),
    symbol="·",
    spawn_weight=0,    # nunca gerada no chão
    score_bonus=0,
)

_WEAPON_TABLE: list[Weapon] = [
    Weapon(
        name="Adaga",
        min_damage=4, max_damage=7,
        color=(200, 200, 200),  # Comum (Cinza)
        symbol="D",
        spawn_weight=40,
        score_bonus=5,
    ),
    Weapon(
        name="Espada Curta",
        min_damage=7, max_damage=11,
        color=(50, 200, 50),    # Incomum (Verde)
        symbol="E",
        spawn_weight=25,
        score_bonus=10,
    ),
    Weapon(
        name="Maca",
        min_damage=9, max_damage=14,
        color=(50, 100, 255),   # Raro (Azul)
        symbol="M",
        spawn_weight=18,
        score_bonus=15,
    ),
    Weapon(
        name="Machado",
        min_damage=12, max_damage=17,
        color=(180, 50, 200),   # Épico (Roxo)
        symbol="A",             # 'A' para Axe (Machado) para não conflitar muito
        spawn_weight=12,
        score_bonus=25,
    ),
    Weapon(
        name="Espada Flamejante",
        min_damage=16, max_damage=22,
        color=(255, 150, 0),    # Lendário (Laranja)
        symbol="F",
        spawn_weight=5,
        score_bonus=50,
    ),
]

# Pré-calcula a lista ponderada para random.choices
_WEAPON_NAMES:   list[Weapon] = _WEAPON_TABLE
_WEAPON_WEIGHTS: list[int]    = [w.spawn_weight for w in _WEAPON_TABLE]


def random_weapon(rng: random.Random) -> Weapon:
    """
    Sorteia uma arma da tabela de loot usando os pesos definidos.

    Args:
        rng: instância de random.Random para reprodutibilidade.

    Returns:
        Uma Weapon sorteada.
    """
    return rng.choices(_WEAPON_NAMES, weights=_WEAPON_WEIGHTS, k=1)[0]
