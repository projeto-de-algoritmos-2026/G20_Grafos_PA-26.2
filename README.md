# 🎮 Rogue-like PA-26.2 — G20 · Projeto de Algoritmos

Jogo rogue-like 2D em Python + Pygame com geração procedural de dungeon via **MST (Kruskal)** e IA de perseguição dos monstros via **A\***.

---

## 🗂️ Estrutura do Projeto

```
G20_Grafos_PA-26.2/
├── main.py                        ← Ponto de entrada
├── requirements.txt
└── src/
    ├── graph/
    │   ├── grid_graph.py          ← GridGraph (vértices/arestas do dungeon)
    │   └── union_find.py          ← Union-Find (usado pelo Kruskal)
    ├── algorithms/
    │   ├── kruskal.py             ← ★ MST via Kruskal (geração de corredores)
    │   └── astar.py               ← ★ A* com heurística Manhattan (IA)
    ├── dungeon/
    │   ├── generator.py           ← DungeonGenerator (pipeline completo)
    │   └── tilemap.py             ← TileMap (WALL / FLOOR / CORRIDOR)
    ├── entities/
    │   ├── entity.py              ← Classe base Entity
    │   ├── player.py              ← Player
    │   └── monster.py             ← Monster + MonsterAI
    └── game/
        ├── constants.py           ← Constantes globais
        ├── renderer.py            ← Renderer Pygame
        └── game.py                ← Game (loop principal)
```

---

## 🚀 Como Rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Rodar com dungeon aleatório
python main.py

# 3. Rodar com semente reproduzível (mesmo dungeon toda vez)
python main.py --seed 42
```

---

## 🧩 Algoritmos de Grafos Implementados

### 1 — Árvore Geradora Mínima · Kruskal (`src/algorithms/kruskal.py`)

| Item | Detalhe |
|------|---------|
| **Aplicação** | Seleciona o conjunto mínimo de corredores para conectar todas as salas |
| **Vértices** | Salas geradas aleatoriamente no grid |
| **Arestas** | Todas as combinações de pares de salas (grafo completo); peso = distância euclidiana entre centros |
| **Complexidade** | O(N² log N) para N salas |
| **Estrutura auxiliar** | Union-Find com compressão de caminho e união por rank → O(α(N)) por operação |

**Pipeline:**
```
Salas → Grafo completo → Sort por peso → Kruskal + Union-Find → MST de corredores → TileMap
```

### 2 — A\* Pathfinding (`src/algorithms/astar.py`)

| Item | Detalhe |
|------|---------|
| **Aplicação** | Cada monstro calcula o menor caminho até o jogador a cada turno |
| **Heurística** | Distância de Manhattan `h(n) = |Δcol| + |Δrow|` — admissível para movimentos cardinais |
| **Grafo** | GridGraph implícito sobre células caminháveis do TileMap |
| **Bloqueios dinâmicos** | Posições de outros monstros aumentam o custo da aresta (desvio suave) |
| **Complexidade** | O(V log V) no pior caso; muito mais rápido na prática |
| **Otimizações** | Closed set, detecção de entradas duplicadas no heap, limite de iterações |

---

## 🎮 Controles

| Tecla | Ação |
|-------|------|
| ↑ ↓ ← → | Mover / Atacar monstro adjacente |
| `.` | Esperar um turno |
| `D` | **Toggle debug** — visualiza caminho A* do monstro mais próximo |
| `R` | Regenerar dungeon |

---

## 🐛 Modo Debug (tecla D)

Ao pressionar **D**, um overlay semi-transparente aparece sobre as células
do caminho calculado pelo A\* entre o monstro mais próximo e o jogador:

- 🟡 **Amarelo** — células intermediárias do caminho
- 🟢 **Verde** (borda) — posição do monstro (origem)
- 🔴 **Vermelho** (borda) — posição do jogador (destino)

Isso permite demonstrar visualmente o algoritmo durante a defesa do projeto.

---

## ⚙️ Configurações (`src/game/constants.py`)

```python
GRID_W         = 50    # Largura do dungeon em tiles
GRID_H         = 35    # Altura do dungeon em tiles
TILE_SIZE      = 32    # Pixels por tile
NUM_ROOMS      = 10    # Número de salas
ROOM_MIN_SIZE  = 4     # Tamanho mínimo de sala
ROOM_MAX_SIZE  = 10    # Tamanho máximo de sala
NUM_MONSTERS   = 6     # Monstros por dungeon
```

---

## 📐 Arquitetura — Fluxo de Dados

```
main.py
  └── Game.__init__()
        └── DungeonGenerator.generate()
              ├── _place_rooms()            → list[Room]
              ├── kruskal_mst(rooms)        ← ALGORITMO 1
              │     └── UnionFind
              ├── TileMap.carve_*()         → grade de tiles
              └── GridGraph(tilemap)        → grafo de células

Game.run()
  └── [turno do jogador]
        └── _process_monster_turns()
              └── Monster.decide_action()
                    └── MonsterAI.calculate_next_step()
                          └── astar.find_path()     ← ALGORITMO 2
                                └── GridGraph.neighbors()
```

---

## 👥 Grupo 20 — PA 26.2

> Disciplina: Projeto de Algoritmos · UnB · 2026/2