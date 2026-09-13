# src/game/constants.py
"""
Constantes globais do jogo.
Ajuste TILE_SIZE, GRID_W, GRID_H e NUM_ROOMS para calibrar o dungeon.
"""

import pygame

# ─── Janela ───────────────────────────────────────────────────────────────────
WINDOW_TITLE   = "Rogue-like PA-26.2 — G20"
TILE_SIZE      = 32          # pixels por célula do grid
GRID_W         = 60          # largura do dungeon em tiles (maior que a tela)
GRID_H         = 45          # altura do dungeon em tiles (maior que a tela)
SCREEN_W       = 1920        # largura da janela em pixels
SCREEN_H       = 1080        # altura da janela em pixels

# Quantos tiles cabem na viewport (arredondado para cima + margem de 1)
VIEWPORT_COLS  = SCREEN_W // TILE_SIZE + 2
VIEWPORT_ROWS  = SCREEN_H // TILE_SIZE + 2

FPS            = 60

# ─── Geração ──────────────────────────────────────────────────────────────────
NUM_ROOMS       = 12         # número de salas geradas
ROOM_MIN_SIZE   = 5          # dimensão mínima de uma sala (tiles)
ROOM_MAX_SIZE   = 11         # dimensão máxima de uma sala (tiles)
MAX_PLACE_TRIES = 300        # tentativas de posicionar sala sem sobreposição
NUM_MONSTERS    = 8          # monstros gerados por dungeon
NUM_TRAPS       = 18         # armadilhas geradas por dungeon

# ─── Pesos de grafo ───────────────────────────────────────────────────────────
WEIGHT_FLOOR    = 1          # custo padrão de andar num tile de piso
WEIGHT_TRAP     = 8          # monstros preferem não pisar em armadilhas
WEIGHT_MONSTER  = 5          # custo aumentado de passar por tile com monstro

# ─── Armadilhas ───────────────────────────────────────────────────────────────
TRAP_DAMAGE_MIN = 3          # dano mínimo por armadilha
TRAP_DAMAGE_MAX = 8          # dano máximo por armadilha

# ─── Câmera ───────────────────────────────────────────────────────────────────
CAM_PAN_SPEED   = 1          # tiles por tecla de seta (panning manual)
CAM_MAX_OFFSET  = 8          # offset máximo da câmera em relação ao jogador (tiles)

# ─── Cores (R, G, B) ──────────────────────────────────────────────────────────
C_BLACK        = (  0,   0,   0)
C_WALL         = ( 25,  25,  40)   # azul-escuro para paredes
C_FLOOR        = ( 55,  55,  75)   # cinza-médio para piso de sala
C_CORRIDOR     = ( 45,  45,  60)   # cinza mais escuro para corredor
C_TRAP         = (120,  30,  30)   # vermelho escuro — armadilha oculta
C_TRAP_GLYPH   = (220,  60,  60)   # vermelho vivo — glifo da armadilha (X)
C_EXIT         = (255, 215,   0)   # Dourado — glifo de saída

# Entidades
C_PLAYER       = ( 80, 200, 255)   # azul claro — jogador
C_MONSTER      = (220,  70,  70)   # vermelho — monstros

# HP Bar
C_HP_BG        = ( 60,  10,  10)
C_HP_FILL      = (200,  40,  40)
C_HP_FILL_HIGH = ( 50, 180,  80)
C_HP_FILL_MID  = (210, 160,  30)

# Debug overlay
C_PATH_FILL    = (255, 220,   0, 110)   # amarelo semi-transparente — caminho A*
C_MST_LINE     = (  0, 255, 150,  90)   # verde-água — corredores MST (debug)
C_START_NODE   = (  0, 220,  80)        # origem do caminho (monstro)
C_GOAL_NODE    = ( 80, 180, 255)        # destino do caminho (jogador)

# HUD
C_TEXT         = (210, 210, 230)
C_TEXT_ACCENT  = ( 80, 200, 255)
C_TEXT_WARN    = (230, 100,  60)
C_HUD_PANEL    = ( 12,  12,  22, 200)

# ─── Teclas — Movimento do Jogador (WASD) ─────────────────────────────────────
KEY_MOVE_UP    = pygame.K_w
KEY_MOVE_DOWN  = pygame.K_s
KEY_MOVE_LEFT  = pygame.K_a
KEY_MOVE_RIGHT = pygame.K_d
KEY_WAIT       = pygame.K_PERIOD   # '.' para esperar um turno

# ─── Teclas — Câmera (Setas) ──────────────────────────────────────────────────
KEY_CAM_UP     = pygame.K_UP
KEY_CAM_DOWN   = pygame.K_DOWN
KEY_CAM_LEFT   = pygame.K_LEFT
KEY_CAM_RIGHT  = pygame.K_RIGHT
KEY_CAM_RESET  = pygame.K_c       # 'C' centraliza a câmera no jogador

# ─── Teclas — Ações ───────────────────────────────────────────────────────────
KEY_DEBUG      = pygame.K_TAB     # TAB para toggle do overlay de debug
KEY_REGEN      = pygame.K_r       # 'R' para regenerar dungeon
