# src/entities/item.py
"""
Sistema de itens consumíveis (Armaduras e Poções).

- Armaduras: Representadas por números (1, 2, 3). Aumentam o max_hp.
- Poções: Representadas por um coração ('♥') ou um símbolo '+'. Curam o jogador.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

@dataclass(frozen=True)
class Item:
    name: str
    symbol: str
    color: tuple[int, int, int]
    spawn_weight: int
    is_armor: bool = False
    hp_bonus: int = 0      # Quanto aumenta no max_hp (se armadura)
    heal_amount: int = 0   # Quanto cura (se poção)
    score_bonus: int = 5

_ITEM_TABLE: list[Item] = [
    # -- Poções --
    Item("Pocao Pequena", "+", (255, 100, 100), spawn_weight=35, heal_amount=10),
    Item("Pocao Grande", "+", (255, 30, 30), spawn_weight=15, heal_amount=25),
    
    # -- Armaduras (aumentam max HP e curam o equivalente) --
    Item("Trapos", "1", (200, 200, 200), spawn_weight=25, is_armor=True, hp_bonus=5),
    Item("Cota de Malha", "2", (50, 200, 50), spawn_weight=15, is_armor=True, hp_bonus=10),
    Item("Placas de Aco", "3", (50, 100, 255), spawn_weight=8, is_armor=True, hp_bonus=20),
    Item("Armadura Lendaria", "4", (255, 150, 0), spawn_weight=2, is_armor=True, hp_bonus=35),
]

_ITEM_NAMES = _ITEM_TABLE
_ITEM_WEIGHTS = [i.spawn_weight for i in _ITEM_TABLE]

def random_item(rng: random.Random) -> Item:
    """Sorteia um item (armadura ou poção) baseado nos pesos."""
    return rng.choices(_ITEM_NAMES, weights=_ITEM_WEIGHTS, k=1)[0]
