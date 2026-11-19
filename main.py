#!/usr/bin/env python3
"""Entry point do Organizador de Arquivos."""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from organizer.config import load_config, save_config
from organizer.classifier import plan_moves
from organizer.mover import execute_moves


def run_cli(args):
    cfg = load_config()
    if args.source:
        cfg["source_dirs"] = [args.source]
    if args.dest:
        cfg["destination_base"] = args.dest
    if args.recursive:
        cfg["recursive"] = True
    moves = plan_moves(cfg)
    print(f"Preview: {len(moves)} arquivo(s) seriam movidos.")
    for m in moves[:50]:
        print(f"  {m['src']}  ->  {m['dst']}  [{m['category']}]")
    if len(moves) > 50:
        print(f"  ... e mais {len(moves)-50}")
    if args.apply:
        res = execute_moves(moves, cfg)
        print(f"Concluído: {res['moved']} movidos, {res['skipped']} pulados, {len(res['errors'])} erros.")
    else:
        print("Use --apply para executar de fato.")


def main():
    parser = argparse.ArgumentParser(description="Organizador de Arquivos")
    parser.add_argument("--cli", action="store_true", help="Modo linha de comando")
    parser.add_argument("--source", help="Pasta de origem")
    parser.add_argument("--dest", help="Pasta de destino base")
    parser.add_argument("--recursive", action="store_true", help="Recursivo")
    parser.add_argument("--apply", action="store_true", help="Executar movimentos")
    args = parser.parse_args()

    if args.cli:
        run_cli(args)
        return

    # GUI
    from organizer.gui import main as gui_main
    gui_main()


if __name__ == "__main__":
    main()
