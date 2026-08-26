#!/usr/bin/env python3
"""dump_position.py — 指定局面を機械可読（全64マス）で書き出し、独立再現で検証する．

検証は2系統:
  (a) tree JSON の board（エンジンが吐いた局面）
  (b) clear_board 相当の初期配置から着手列を打ち直した局面（本スクリプト内のオセロ実装）
両者が全64マス一致することを確認する．

初期配置は frozen_positions.md の記述に従う: D4=X, E4=O, D5=O, E5=X（通常図と対角が逆）．

使い方: python3 xrl_viz/dump_position.py [出力.json]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_alignment import DIRS, aid_to_coord, coord_to_rc, legal_moves  # noqa: E402

SRC = "xrl_viz/data/corpus/replay_S2_n128.json"
PLY = 17
TOP = 6
OUT_DEFAULT = "xrl_viz/figs/board_S2_ply17.json"
ENGINE_COMMIT = "fd5d477116b0850aca61fb067869a1009a536dea"
INITIAL = {"D4": "X", "E4": "O", "D5": "O", "E5": "X"}   # frozen_positions.md
B = 8


def coord(r, c):
    """(row, col) -> 'A1' 形式．row 0 が 1 段目、col 0 が A 列．"""
    return f"{chr(ord('A') + c + (1 if c >= 8 else 0))}{r + 1}"


def board_to_cells(board):
    """tree JSON の board（'B'/'W'/None）を {'A1': 'X', ...} に変換．"""
    return {coord(r, c): {"B": "X", "W": "O", None: "."}[board[r][c]]
            for r in range(B) for c in range(B)}


def cells_to_ascii(cells):
    """8段目から1段目へ、'X'/'O'/'.' の行リスト．"""
    return [" ".join(cells[coord(r, c)] for c in range(B)) for r in range(B - 1, -1, -1)]


def cells_to_board(cells):
    """{'A1': 'X', ...} を tree JSON と同じ board 形式に戻す．"""
    inv = {"X": "B", "O": "W", ".": None}
    return [[inv[cells[coord(r, c)]] for c in range(B)] for r in range(B)]


def replay(moves):
    """初期配置から着手列を打つ．戻り値: (cells, 手番)．非合法手があれば例外．"""
    cells = {coord(r, c): "." for r in range(B) for c in range(B)}
    cells.update(INITIAL)
    stone = {"B": "X", "W": "O"}
    turn = "B"
    for i, mv in enumerate(moves):
        board = cells_to_board(cells)
        if (r_c := coord_to_rc(mv, B)) not in legal_moves(board, turn, B):
            raise ValueError(f"{i + 1}手目 {turn}{mv} が非合法（パスの可能性）")
        r, c = r_c
        me, opp = stone[turn], stone["W" if turn == "B" else "B"]
        cells[mv] = me
        for dr, dc in DIRS:                       # 挟んだ石を返す
            line, rr, cc = [], r + dr, c + dc
            while 0 <= rr < B and 0 <= cc < B and cells[coord(rr, cc)] == opp:
                line.append(coord(rr, cc))
                rr, cc = rr + dr, cc + dc
            if line and 0 <= rr < B and 0 <= cc < B and cells[coord(rr, cc)] == me:
                for p in line:
                    cells[p] = me
        turn = "W" if turn == "B" else "B"
    return cells, turn


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else OUT_DEFAULT
    rec = json.load(open(SRC))
    e = next(x for x in rec if x["ply"] == PLY)
    t = e["tree"]

    # (a) エンジンが吐いた局面
    cells = board_to_cells(t["board"])
    to_play = t["to_play"]

    # (b) 着手列からの独立再現
    line = [x["line_move"] for x in rec if x["ply"] < PLY]
    cells_replay, turn_replay = replay(line)
    diff = sorted(k for k in cells if cells[k] != cells_replay[k])
    ok = not diff and turn_replay == to_play

    # 合法手と訪問数
    legal = sorted((coord(r, c) for r, c in legal_moves(t["board"], to_play, B)),
                   key=lambda s: (s[0], int(s[1:])))
    kids = sorted(t["root"]["children"], key=lambda c: -c["N"])
    visits = [{"move": aid_to_coord(c["action_id"], B), "N": c["N"],
               "rank": i + 1, "in_figure": i < TOP}
              for i, c in enumerate(kids)]

    data = {
        "id": "S2_ply17",
        "source": {"file": SRC, "ply": PLY, "engine_commit": ENGINE_COMMIT,
                   "n_simulations": 128, "game": t["game"], "board_size": B},
        "initial_placement": INITIAL,
        "move_sequence": [f"{'BW'[i % 2]}{m}" for i, m in enumerate(line)],
        "to_play": to_play,
        "to_play_label": {"B": "黒(X)", "W": "白(O)"}[to_play],
        "legend": {"X": "黒", "O": "白", ".": "空"},
        "cells": {k: cells[k] for k in sorted(cells, key=lambda s: (s[0], int(s[1:])))},
        "ascii_rank8_to_rank1": cells_to_ascii(cells),
        "empties": sum(1 for v in cells.values() if v == "."),
        "legal_moves": legal,
        "root_visits": visits,
        "played": e["line_move"],
        "verification": {
            "replay_matches_tree_json": ok,
            "mismatched_cells": diff,
            "replayed_to_play": turn_replay,
        },
    }
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"書き出し: {out}")
    print(f"再現一致: {ok}（不一致マス {len(diff)} / 手番 再現={turn_replay} JSON={to_play}）")
    for row in data["ascii_rank8_to_rank1"]:
        print("   ", row)
    print("    A B C D E F G H")
    print(f"空マス {data['empties']} / 合法手 {len(legal)}: {' '.join(legal)}")
    print("上位6手:", " ".join(f"{v['move']}:{v['N']}" for v in visits[:TOP]))
    print("実際に打たれた手:", data["played"])


if __name__ == "__main__":
    main()
