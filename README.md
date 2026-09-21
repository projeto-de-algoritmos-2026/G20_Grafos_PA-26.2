# 🎮 Rogue-like PA-26.2 — G20 · Projeto de Algoritmos

Jogo rogue-like 2D em Python + Pygame com geração procedural de dungeon via **MST (Kruskal)**, posicionamento topológico da saída via **Dijkstra**, IA de perseguição dos monstros via **A\*** e modo comparativo/benchmark em tempo real entre **Dijkstra e A\***.

---

## 🗂️ Estrutura do Projeto

```
G20_Grafos_PA-26.2/
├── main.py                        ← Ponto de entrada
├── requirements.txt
├── tests/
│   ├── test_kruskal.py            ← Testes de MST (Kruskal) e Union-Find
│   ├── test_astar.py              ← Testes de Pathfinding A* e GridGraph
│   └── test_dijkstra.py           ← Testes de Dijkstra e Comparador de Grafos
└── src/
    ├── graph/
    │   ├── grid_graph.py          ← GridGraph (vértices/arestas do dungeon)
    │   └── union_find.py          ← Union-Find (usado pelo Kruskal)
    ├── algorithms/
    │   ├── kruskal.py             ← ★ MST via Kruskal (geração de corredores)
    │   ├── astar.py               ← ★ A* com heurística Manhattan (IA monstros)
    │   └── dijkstra.py            ← ★ Dijkstra (saída ótima + benchmark vs A*)
    ├── dungeon/
    │   ├── generator.py           ← DungeonGenerator (pipeline completo + Dijkstra exit)
    │   └── tilemap.py             ← TileMap (WALL / FLOOR / CORRIDOR / TRAP / EXIT)
    ├── entities/
    │   ├── entity.py              ← Classe base Entity
    │   ├── player.py              ← Player
    │   ├── monster.py             ← Monster + MonsterAI
    │   ├── weapon.py              ← Armas com atributos
    │   └── item.py                ← Itens e armaduras
    └── game/
        ├── constants.py           ← Constantes globais (teclas, cores, câmera)
        ├── renderer.py            ← Renderer Pygame com câmera / HUD / overlay comparativo
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

# 4. Executar toda a suíte de testes automatizados de grafos
python -m unittest discover tests/
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
| **TAB** | Toggle do overlay de debug comparativo (**Dijkstra vs A\***) |
| **R** (segurar 1s) | Regenerar dungeon com nova semente |

---

## 🧩 Algoritmos de Grafos Implementados

### 1 — Árvore Geradora Mínima · Kruskal (`src/algorithms/kruskal.py`)

| Item | Detalhe |
|------|---------|
| **Aplicação** | Seleciona o conjunto mínimo de corredores para conectar todas as salas sem ciclos |
| **Vértices** | Salas geradas aleatoriamente no grid |
| **Arestas** | Todas as combinações de pares de salas (grafo completo); peso = distância euclidiana entre centros |
| **Complexidade** | O(E log E) com E = N*(N-1)/2 → O(N² log N) para N salas |
| **Estrutura auxiliar** | Union-Find com compressão de caminho e união por rank → O(α(N)) por operação |

**Pipeline:**
```
Salas → Grafo completo → Sort por peso → Kruskal + Union-Find → MST de corredores → TileMap
```

---

### 2 — Dijkstra de Fonte Única & Ponto a Ponto (`src/algorithms/dijkstra.py`)

| Item | Detalhe |
|------|---------|
| **Aplicação 1 (Geração)** | **Posicionamento da Saída (EXIT)**: busca de fonte única a partir do jogador no labirinto real de corredores e paredes para achar a sala topologicamente mais distante |
| **Aplicação 2 (Benchmark)** | **Comparação com A\***: calcula o caminho do monstro até o jogador expandindo em ondas concêntricas (sem heurística) para contrastar métricas de busca |
| **Grafo** | `GridGraph` ponderado (piso = 1, armadilha = 8, outros monstros = penalidade) |
| **Complexidade** | O((V + E) log V) utilizando fila de prioridade Min-Heap (`heapq`) |

---

### 3 — A\* Pathfinding com Heurística de Manhattan (`src/algorithms/astar.py`)

| Item | Detalhe |
|------|---------|
| **Aplicação** | Cada monstro persegue o jogador a cada turno com cálculo em tempo real |
| **Heurística** | Distância de Manhattan `h(n) = |Δcol| + |Δrow|` — admissível e consistente para grid cardinal |
| **Grafo** | `GridGraph` implícito sobre células caminháveis do TileMap |
| **Bloqueios dinâmicos** | Posições de outros monstros aumentam o custo da aresta (desvio suave) |
| **Complexidade** | O(V log V) no pior caso; na prática explora uma fração mínima dos nós |

---

## 📊 Comparativo Empírico: Dijkstra vs A\* (Modo Debug - Tecla TAB)

Ao pressionar **TAB**, o jogo entra em modo comparativo executando ambos os algoritmos em tempo real para a rota do monstro mais próximo até o jogador:

| Camada Visual | Cor no Mapa | Significado Teórico |
|---|---|---|
| **Dijkstra** | 🔵 Azul Translúcido | Nós avaliados na expansão omnidirecional ($h = 0$) |
| **A\*** | 🟠 Âmbar Translúcido | Nós avaliados na expansão guiada pela heurística de Manhattan |
| **Caminho Ótimo** | 🟡 Amarelo Brilhante | Trajeto de menor custo encontrado (idêntico em ambos) |
| **Origem / Destino** | 🟢 Verde / 🔵 Azul | Posicionamento do monstro e do jogador |

### Painel de Benchmark no HUD
O HUD exibe em tempo real:
- **Nós explorados** pelo Dijkstra vs A*
- **Tempo de execução** em microssegundos ($\mu s$)
- **Custo do caminho acumulado** (comprovando otimalidade idêntica)
- **Percentual de redução de busca do A\*** (comprovando empiricamente a eficácia da heurística admissível)

---

## ☠️ Armadilhas

- Geradas aleatoriamente em tiles de FLOOR após a construção do dungeon.
- Visualmente indicadas por um glifo **X** vermelho no tile.
- **Zona segura**: raio de 4 tiles ao redor do ponto de início do jogador nunca contém armadilhas.
- Ao pisá-las, o jogador recebe dano aleatório (3–8 HP) e a armadilha é desarmada.
- Monstros evitam armadilhas graças ao peso elevado na aresta do GridGraph (peso 8).

---

## 📷 Sistema de Câmera

- A janela exibe uma **viewport com câmera móvel centralizada no jogador**.
- O dungeon é maior (60×45 tiles) — use as setas para deslocar a visualização.
- **C** recentra a câmera no jogador instantaneamente.

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
              ├── _place_traps()              → TRAP tiles (peso 8)
              ├── GridGraph(tilemap)          → grafo com pesos reais
              └── dijkstra_all_distances()    ← ALGORITMO 2 (Dijkstra - Saída)
                    └── posiciona EXIT na sala de maior distância real

Game.run()
  └── [turno do jogador]
        ├── _check_trap()                     → dano se pisar armadilha
        └── _process_monster_turns()
              └── Monster.decide_action()
                    └── MonsterAI.calculate_next_step()
                          └── astar.find_path()   ← ALGORITMO 3 (A*)
                                └── GridGraph.neighbors()
```

---

## 👥 Grupo 20 — PA 26.2

> Disciplina: Projeto de Algoritmos · UnB · 2026/2