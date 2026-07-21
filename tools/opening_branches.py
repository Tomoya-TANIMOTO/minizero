#!/usr/bin/env python3
"""8x8 Othello の序盤分岐数を数える（合法手の列挙のみ．対局は生成しない）．

初期配置は MiniZero の clear_board 直後の実配置に合わせる：
  D4=X(黒), E4=O(白), D5=O(白), E5=X(黒)   ※通常図と対角が逆
  先手は黒（記録の ply0 が to_play=B）

対称性は「初期配置を色ごと保つ盤面変換」だけを使う．
盤面全体の二面体群 D4（8個）のうち，初期配置を保つものを実際に判定して求める．
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "xrl_viz"))
from check_alignment import legal_moves  # noqa: E402
from analyze_taskB_detail import apply_move  # noqa: E402

B = 8


def start():
    b = [[None] * B for _ in range(B)]
    b[3][3] = "B"   # D4
    b[3][4] = "W"   # E4
    b[4][3] = "W"   # D5
    b[4][4] = "B"   # E5
    return b


def coord(r, c):
    return f"{chr(ord('A') + c + (1 if c >= 8 else 0))}{r + 1}"


# --- 二面体群 D4 の 8 変換（(r,c) -> (r,c)） ---
TRANSFORMS = {
    "id":        lambda r, c: (r, c),
    "rot90":     lambda r, c: (c, B - 1 - r),
    "rot180":    lambda r, c: (B - 1 - r, B - 1 - c),
    "rot270":    lambda r, c: (B - 1 - c, r),
    "flip_h":    lambda r, c: (r, B - 1 - c),
    "flip_v":    lambda r, c: (B - 1 - r, c),
    "diag":      lambda r, c: (c, r),
    "antidiag":  lambda r, c: (B - 1 - c, B - 1 - r),
}


def transform_board(b, f):
    nb = [[None] * B for _ in range(B)]
    for r in range(B):
        for c in range(B):
            rr, cc = f(r, c)
            nb[rr][cc] = b[r][c]
    return nb


def stabilizer():
    """初期配置を色ごと保つ変換の名前一覧を返す．"""
    s0 = start()
    return [n for n, f in TRANSFORMS.items() if transform_board(s0, f) == s0]


STAB = stabilizer()


def canon_seq(seq):
    """着手列を対称性で正規化する（安定化群の像のうち辞書順最小）．"""
    best = None
    for n in STAB:
        f = TRANSFORMS[n]
        t = tuple(f(r, c) for (r, c) in seq)
        if best is None or t < best:
            best = t
    return best


CELL = {None: 0, "B": 1, "W": 2}


def canon_board(b, to_play):
    best = None
    for n in STAB:
        tb = transform_board(b, TRANSFORMS[n])
        key = (to_play, tuple(CELL[x] for row in tb for x in row))
        if best is None or key < best:
            best = key
    return best


def expand(nodes):
    """(board, to_play, seq) の集合を1手進める．"""
    out = []
    for b, p, seq in nodes:
        mv = sorted(legal_moves(b, p, B))
        opp = "W" if p == "B" else "B"
        for (r, c) in mv:
            out.append((apply_move(b, p, r * B + c, B), opp, seq + [(r, c)]))
    return out


def main():
    print(f"初期配置を保つ対称変換（安定化群）: {STAB}  → 位数 {len(STAB)}")
    print(f"（盤面全体の二面体群は 8 個．初期配置が対角非対称なので半分に落ちる）\n")

    s0 = start()
    print("初期局面の合法手（黒番）:",
          " ".join(coord(r, c) for r, c in sorted(legal_moves(s0, "B", B))))
    print()

    nodes = [(s0, "B", [])]
    print(f"{'手数':>4} | {'手番':^4} | {'着手列の総数':>12} | {'各局面の合法手数':>16} | "
          f"{'系統(着手列)':>12} | {'系統(局面)':>10}")
    print("-" * 88)
    for depth in range(1, 5):
        # この手数を指す直前の局面ごとの合法手数
        counts = sorted({len(legal_moves(b, p, B)) for b, p, _ in nodes})
        mover = nodes[0][1]
        nodes = expand(nodes)
        seq_sys = len({canon_seq(s) for _, _, s in nodes})
        pos_sys = len({canon_board(b, p) for b, p, _ in nodes})
        rng = str(counts[0]) if len(counts) == 1 else f"{counts[0]}〜{counts[-1]} {counts}"
        print(f"{depth:>4} | {mover:^4} | {len(nodes):>12} | {rng:>16} | "
              f"{seq_sys:>12} | {pos_sys:>10}")

    print()
    print("固定手数ごとの系統数（= その手数まで打ち切ったときに残る系統）")
    nodes = [(s0, "B", [])]
    for depth in range(1, 5):
        nodes = expand(nodes)
        seq_sys = len({canon_seq(s) for _, _, s in nodes})
        pos_sys = len({canon_board(b, p) for b, p, _ in nodes})
        if depth >= 2:
            print(f"  {depth}手固定: 着手列ベース {seq_sys} 系統 / 局面ベース {pos_sys} 系統")


if __name__ == "__main__":
    main()
