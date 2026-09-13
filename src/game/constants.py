# src/game/constants.py
"""
Constantes globais do jogo.
Ajuste TILE_SIZE, GRID_W, GRID_H e NUM_ROOMS para calibrar o dungeon.
"""

# ─── Janela ───────────────────────────────────────────────────────────────────
WINDOW_TITLE   = "Rogue-like PA-26.2 — G20"
TILE_SIZE      = 32          # pixels por célula do grid
GRID_W         = 50          # largura do dungeon em tiles
GRID_H         = 35          # altura do dungeon em tiles
SCREEN_W       = TILE_SIZE * GRID_W
SCREEN_H       = TILE_SIZE * GRID_H
FPS            = 60

# ─── Geração ──────────────────────────────────────────────────────────────────
NUM_ROOMS      = 10          # número de salas geradas
ROOM_MIN_SIZE  = 4           # dimensão mínima de uma sala (tiles)
ROOM_MAX_SIZE  = 10          # dimensão máxima de uma sala (tiles)
MAX_PLACE_TRIES = 200        # tentativas de posicionar sala sem sobreposição
NUM_MONSTERS   = 6           # monstros gerados por dungeon

# ─── Pesos de grafo ───────────────────────────────────────────────────────────
WEIGHT_FLOOR    = 1          # custo padrão de andar num tile de piso
WEIGHT_MONSTER  = 5          # custo aumentado de passar por tile com monstro
                             # (usado pelo A* para desviar de aliados)

# ─── Cores (R, G, B) ──────────────────────────────────────────────────────────
C_BLACK        = (  0,   0,   0)
C_WALL         = ( 30,  30,  45)   # azul-escuro para paredes
C_FLOOR        = ( 60,  60,  80)   # cinza-médio para piso de sala
C_CORRIDOR     = ( 50,  50,  65)   # cinza mais escuro para corredor
C_GRID_LINE    = ( 20,  20,  30)   # linhas de grade (debug)

C_PLAYER       = ( 80, 200, 255)   # azul claro — jogador
C_MONSTER      = (220,  70,  70)   # vermelho — monstros

# Debug overlay
C_PATH_FILL    = (255, 220,   0, 110)   # amarelo semi-transparente — caminho A*
C_MST_LINE     = (  0, 255, 150,  90)   # verde-água — corredores MST (debug)
C_START_NODE   = (  0, 255,   0)        # origem do caminho
C_GOAL_NODE    = (255,   0,   0)        # destino do caminho

# HUD
C_HUD_BG       = ( 10,  10,  20, 180)
C_TEXT         = (220, 220, 240)
C_TEXT_ACCENT  = ( 80, 200, 255)

# ─── Teclas de ação ───────────────────────────────────────────────────────────
import pygame
KEY_UP     = pygame.K_UP
KEY_DOWN   = pygame.K_DOWN
KEY_LEFT   = pygame.K_LEFT
KEY_RIGHT  = pygame.K_RIGHT
KEY_WAIT   = pygame.K_PERIOD   # '.' para esperar um turno
KEY_DEBUG  = pygame.K_d        # 'D' para toggle do overlay de debug
KEY_REGEN  = pygame.K_r        # 'R' para regenerar dungeon
