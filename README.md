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
    │   ├── generator.py           ← DungeonGenerator (pipeline completo + armadilhas)
    │   └── tilemap.py             ← TileMap (WALL / FLOOR / CORRIDOR / TRAP)
    ├── entities/
    │   ├── entity.py              ← Classe base Entity
    │   ├── player.py              ← Player
    │   └── monster.py             ← Monster + MonsterAI
    └── game/
        ├── constants.py           ← Constantes globais (teclas, cores, câmera)
        ├── renderer.py            ← Renderer Pygame com câmera / viewport
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

## 🎮 Controles

| Tecla | Ação |
|-------|------|
| **W A S D** | Mover o jogador (↑ ← ↓ →) |
| **W/A/S/D** sobre monstro adjacente | Atacar o monstro |
| **. (ponto)** | Esperar um turno (passa o turno sem mover) |
| **↑ ↓ ← →** (setas) | Mover a câmera manualmente (panning) |
| **C** | Centralizar a câmera no jogador |
| **TAB** | Toggle do overlay de debug A\* |
| **R** | Regenerar dungeon com nova semente |

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
| **Armadilhas** | Tiles TRAP têm peso 8 no grafo — monstros preferem contorná-las |
| **Complexidade** | O(V log V) no pior caso; muito mais rápido na prática |

---

## ☠️ Armadilhas

- Geradas aleatoriamente em tiles de FLOOR e CORRIDOR após a construção do dungeon.
- Visualmente indicadas por um glifo **X** vermelho no tile.
- **Zona segura**: raio de 4 tiles ao redor do ponto de início do jogador nunca contém armadilhas.
- Ao pisá-las, o jogador recebe dano aleatório (3–8 HP) e a armadilha é **desarmada** (vira FLOOR).
- Monstros evitam armadilhas graças ao peso alto na aresta do GridGraph (A* as contorna).

---

## 📷 Sistema de Câmera

- A janela exibe uma **viewport de 1280×720 px** (≈ 40×22 tiles visíveis).
- O dungeon é maior (60×45 tiles) — use as setas para explorar.
- A câmera **segue automaticamente o jogador** (sempre centralizado por padrão).
- **Setas** deslocam a câmera até 8 tiles em qualquer direção, permitindo "olhar ao redor".
- **C** recentra a câmera no jogador instantaneamente.

---

## 🐛 Modo Debug (tecla TAB)

Ao pressionar **TAB**, um overlay semi-transparente aparece sobre as células
do caminho calculado pelo A\* entre o monstro mais próximo e o jogador:

| Cor | Significado |
|-----|-------------|
| 🟡 Amarelo (fundo) | Células intermediárias do caminho A\* |
| 🟢 Verde (borda) | Posição do monstro (origem do caminho) |
| 🔵 Azul (borda) | Posição do jogador (destino do caminho) |

---

## 💖 Barra de HP do Jogador

- Exibida no canto superior esquerdo, sempre visível.
- Muda de cor conforme o HP restante:
  - **Verde** → HP > 60 %
  - **Amarelo** → HP entre 30 % e 60 %
  - **Vermelho** → HP < 30 % (situação crítica)

---

## ⚙️ Configurações (`src/game/constants.py`)

```python
SCREEN_W       = 1280   # Largura da janela em pixels
SCREEN_H       = 720    # Altura da janela em pixels
TILE_SIZE      = 32     # Pixels por tile
GRID_W         = 60     # Largura do dungeon em tiles
GRID_H         = 45     # Altura do dungeon em tiles
NUM_ROOMS      = 12     # Número de salas
ROOM_MIN_SIZE  = 5      # Tamanho mínimo de sala
ROOM_MAX_SIZE  = 11     # Tamanho máximo de sala
NUM_MONSTERS   = 8      # Monstros por dungeon
NUM_TRAPS      = 18     # Armadilhas por dungeon
CAM_MAX_OFFSET = 8      # Deslocamento máximo da câmera em tiles
TRAP_DAMAGE_MIN = 3     # Dano mínimo por armadilha
TRAP_DAMAGE_MAX = 8     # Dano máximo por armadilha
```

---

## 📐 Arquitetura — Fluxo de Dados

```
main.py
  └── Game.__init__()
        └── DungeonGenerator.generate()
              ├── _place_rooms()              → list[Room]
              ├── kruskal_mst(rooms)          ← ALGORITMO 1 (MST)
              │     └── UnionFind
              ├── TileMap.carve_*()           → grade de tiles
              ├── _place_traps()              → TRAP tiles no mapa
              └── GridGraph(tilemap)          → grafo com pesos (TRAP=8)

Game.run()
  └── [turno do jogador]
        ├── _check_trap()                     → dano se pisar armadilha
        └── _process_monster_turns()
              └── Monster.decide_action()
                    └── MonsterAI.calculate_next_step()
                          └── astar.find_path()   ← ALGORITMO 2 (A*)
                                └── GridGraph.neighbors()
                                      └── peso alto nas armadilhas
```

---

## 👥 Grupo 20 — PA 26.2

> Disciplina: Projeto de Algoritmos · UnB · 2026/2