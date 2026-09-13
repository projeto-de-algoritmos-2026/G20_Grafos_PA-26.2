# src/entities/monster.py
"""
Classe Monster e MonsterAI — monstros controlados pelo algoritmo A*.

MonsterAI encapsula toda a lógica de pathfinding:
    - Chama astar.next_step() com a posição do jogador como destino.
    - Passa as posições dos outros monstros como bloqueios dinâmicos.
    - Armazena o caminho completo para visualização de debug.

Monster herda Entity e delega a tomada de decisão de movimento à MonsterAI.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.entities.entity import Entity
from src.algorithms import astar

if TYPE_CHECKING:
    from src.graph.grid_graph import GridGraph

Coord = tuple[int, int]


class MonsterAI:
    """
    Inteligência Artificial do monstro baseada no algoritmo A*.

    Responsabilidades:
        - Calcular o próximo passo do monstro em direção ao jogador.
        - Manter o caminho completo para overlay de debug.
        - Respeitar bloqueios dinâmicos (outros monstros).

    A lógica de combate (atacar o jogador se adjacente) fica em Monster.decide_action().
    """

    def __init__(self) -> None:
        # Caminho completo mais recente calculado pelo A* (para debug overlay)
        self.last_path: list[Coord] = []

    def calculate_next_step(
        self,
        origin: Coord,
        destination: Coord,
        graph: "GridGraph",
        blocked: set[Coord] | None = None,
    ) -> Coord | None:
        """
        Calcula e armazena o caminho até *destination* usando A*.

        Args:
            origin      : posição atual do monstro.
            destination : posição do jogador.
            graph       : GridGraph do dungeon (caminháveis + pesos).
            blocked     : posições de outros monstros (bloqueios extras).

        Returns:
            Próximo passo (Coord), ou None se não há caminho.
        """
        path = astar.find_path(origin, destination, graph, blocked=blocked)
        self.last_path = path

        if len(path) >= 2:
            return path[1]   # índice 0 = origem, índice 1 = próximo passo
        return None


@dataclass
class Monster(Entity):
    """
    Monstro inimigo controlado por IA.

    Attributes:
        attack_power : dano base por ataque ao jogador.
        color        : cor do monstro.
        ai           : instância de MonsterAI para pathfinding.
        vision_range : alcance de visão em tiles (só persegue se dentro do range).
    """
    attack_power: int      = 3
    color:        tuple[int, int, int] = (220, 70, 70)
    vision_range: int      = 15   # tiles — define quando o monstro "acorda"
    ai:           MonsterAI = field(default_factory=MonsterAI, init=False)

    # ── Lógica de turno ───────────────────────────────────────────────────────

    def decide_action(
        self,
        player_pos: Coord,
        graph: "GridGraph",
        all_monster_positions: set[Coord],
    ) -> "MonsterAction":
        """
        Decide a ação do monstro para o turno atual.

        Prioridades:
            1. Se adjacente ao jogador → ATTACK.
            2. Se dentro de vision_range e há caminho → MOVE (próximo passo A*).
            3. Caso contrário → WAIT.

        Args:
            player_pos            : posição atual do jogador.
            graph                 : GridGraph do dungeon.
            all_monster_positions : posições de TODOS os monstros (incluindo self)
                                    — o método exclui a própria posição antes
                                    de passar como bloqueio ao A*.

        Returns:
            MonsterAction descrevendo o que o monstro vai fazer.
        """
        pc, pr = player_pos
        mc, mr = self.pos

        # Distância de Manhattan ao jogador
        dist = abs(pc - mc) + abs(pr - mr)

        # 1. Ataque adjacente (dist == 1 em movimento cardinal)
        if dist == 1:
            return MonsterAction(kind="attack", target=player_pos)

        # Fora do alcance de visão → aguarda
        if dist > self.vision_range:
            return MonsterAction(kind="wait")

        # 2. Pathfinding A*
        # Remove a própria posição do conjunto de bloqueios
        blocked = all_monster_positions - {self.pos}

        next_pos = self.ai.calculate_next_step(
            origin=self.pos,
            destination=player_pos,
            graph=graph,
            blocked=blocked,
        )

        if next_pos is not None:
            return MonsterAction(kind="move", target=next_pos)

        # 3. Sem caminho → aguarda
        return MonsterAction(kind="wait")

    def execute_action(self, action: "MonsterAction") -> None:
        """
        Executa um MOVE action (atualiza posição).
        Ataques são resolvidos pelo Game.
        """
        if action.kind == "move" and action.target is not None:
            self.move_to(*action.target)

    # ── Debug ─────────────────────────────────────────────────────────────────

    @property
    def debug_path(self) -> list[Coord]:
        """Caminho A* mais recente para overlay de debug."""
        return self.ai.last_path


@dataclass
class MonsterAction:
    """
    Resultado de Monster.decide_action().

    Attributes:
        kind   : "move" | "attack" | "wait"
        target : coordenada de destino (move → próximo tile; attack → posição do jogador).
    """
    kind:   str
    target: Coord | None = None

def create_random_monster(col: int, row: int, rng: random.Random) -> Monster:
    """Cria um monstro aleatório de 4 tipos possíveis."""
    types = [
        {"name": "Goblin", "hp": 10, "dmg": 3, "color": (100, 200, 100), "weight": 40},
        {"name": "Orc", "hp": 20, "dmg": 5, "color": (50, 150, 50), "weight": 30},
        {"name": "Troll", "hp": 35, "dmg": 8, "color": (150, 100, 100), "weight": 20},
        {"name": "Cavaleiro Sombrio", "hp": 50, "dmg": 12, "color": (100, 50, 150), "weight": 10},
    ]
    choice = rng.choices(types, weights=[t["weight"] for t in types], k=1)[0]
    return Monster(
        col=col, row=row,
        hp=choice["hp"], max_hp=choice["hp"],
        name=choice["name"],
        attack_power=choice["dmg"],
        color=choice["color"],
        vision_range=18
    )
