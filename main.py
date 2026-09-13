# main.py
"""
Ponto de entrada do jogo.

Uso:
    python main.py
    python main.py --seed 42     # dungeon reproduzível
"""

from __future__ import annotations

import argparse
import sys


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rogue-like PA-26.2 — Grafos (MST + A*)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Semente aleatória para geração reproduzível do dungeon.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # Importação local para que erros de import (ex: pygame ausente) sejam
    # exibidos com mensagem amigável.
    try:
        from src.game.game import Game
    except ImportError as exc:
        print(f"[ERRO] Falha ao importar módulos do jogo: {exc}")
        print("Execute:  pip install -r requirements.txt")
        sys.exit(1)

    game = Game(seed=args.seed)
    game.run()


if __name__ == "__main__":
    main()
