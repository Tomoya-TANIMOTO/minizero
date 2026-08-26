#!/usr/bin/env python3
"""生成前チェック：開き手列の合法性・到達局面・点対称変換の対応を確認する．

エンジンを起動しない純 Python の検査．GPU も不要．
  (I)   点対称4状態 E3 D3 C4 / F4 F5 E6 / C5 C4 D3 / D6 E6 F5
        指定の3変換で E3 フレームへ写したとき着手列と盤面が一致するか
  (II)  14 開きが全手合法で意図した局面に到達するか
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_alignment import legal_moves          # noqa: E402
from analyze_taskB_detail import apply_move      # noqa: E402

B = 8


def start():
    b = [[None] * B for _ in range(B)]
    b[3][3] = "B"   # D4
    b[3][4] = "W"   # E4
    b[4][3] = "W"   # D5
    b[4][4] = "B"   # E5
    return b


def cell_to_rc(s):
    return int(s[1:]) - 1, ord(s[0].upper()) - ord("A")


def rc_to_cell(rc):
    r, c = rc
    return f"{chr(ord('A') + c)}{r + 1}"


TF = {
    "id":       lambda r, c: (r, c),
    "antidiag": lambda r, c: (B - 1 - c, B - 1 - r),
    "diag":     lambda r, c: (c, r),
    "rot180":   lambda r, c: (B - 1 - r, B - 1 - c),
}


def transform_board(b, f):
    nb = [[None] * B for _ in range(B)]
    for r in range(B):
        for c in range(B):
            rr, cc = f(r, c)
            nb[rr][cc] = b[r][c]
    return nb


def play_line(moves):
    """着手列を打つ．全手合法なら (board, to_play, None)．違法なら (None, None, 理由)．"""
    b, p = start(), "B"
    for i, mv in enumerate(moves):
        r, c = cell_to_rc(mv)
        lm = sorted(legal_moves(b, p, B))
        if (r, c) not in lm:
            return None, None, (f"ply {i} の {mv}({p}) が違法．合法手 = "
                                + " ".join(rc_to_cell(x) for x in lm))
        b = apply_move(b, p, r * B + c, B)
        p = "W" if p == "B" else "B"
    return b, p, None


def board_str(b):
    out = ["  " + " ".join(chr(ord('A') + c) for c in range(B))]
    for r in range(B):
        out.append(f"{r + 1} " + " ".join({None: ".", "B": "X", "W": "O"}[b[r][c]]
                                          for c in range(B)))
    return "\n".join(out)


LINES14 = [
    "E3 D3 C2", "E3 D3 C3", "E3 D3 C4", "E3 D3 C5", "E3 D3 C6",
    "E3 F3 G3", "E3 F3 F4", "E3 F3 C5", "E3 F3 D6",
    "E3 F5 C6", "E3 F5 D6", "E3 F5 E6", "E3 F5 F6", "E3 F5 G6",
]

SYM = [
    ("E3 D3 C4", "id"),
    ("F4 F5 E6", "antidiag"),
    ("C5 C4 D3", "diag"),
    ("D6 E6 F5", "rot180"),
]

fail = 0

print("=" * 78)
print("(0) 初期配置を保つ変換（安定化群）の確認")
print("=" * 78)
s0 = start()
for name, f in TF.items():
    ok = transform_board(s0, f) == s0
    print(f"  {name:9s} 初期配置を保つ: {'Y' if ok else 'N'}")
    if not ok:
        fail += 1

print()
print("=" * 78)
print("(I) 点対称4状態：変換後に E3 D3 C4 と一致するか")
print("=" * 78)
ref_board, ref_play, err = play_line("E3 D3 C4".split())
assert err is None, err
for line, tname in SYM:
    mv = line.split()
    b, p, err = play_line(mv)
    if err:
        print(f"  {line:10s} [{tname:8s}] 違法: {err}")
        fail += 1
        continue
    f = TF[tname]
    mapped = [rc_to_cell(f(*cell_to_rc(m))) for m in mv]
    seq_ok = mapped == "E3 D3 C4".split()
    brd_ok = transform_board(b, f) == ref_board
    ply_ok = p == ref_play
    print(f"  {line:10s} [{tname:8s}] 全手合法 Y / 写像後の着手列 = {' '.join(mapped)} "
          f"（E3 D3 C4 と一致: {'Y' if seq_ok else 'N'}） / "
          f"写像後の盤面一致: {'Y' if brd_ok else 'N'} / 手番一致: {'Y' if ply_ok else 'N'}")
    if not (seq_ok and brd_ok and ply_ok):
        fail += 1

print()
print(f"  基準 E3 D3 C4 到達局面（ply3, 手番 {ref_play}）:")
print("\n".join("    " + l for l in board_str(ref_board).split("\n")))
print("    合法手: " + " ".join(rc_to_cell(x) for x in sorted(legal_moves(ref_board, ref_play, B))))

print()
print("=" * 78)
print("(II) 14 開き：全手合法か・到達局面")
print("=" * 78)
seen = {}
for line in LINES14:
    mv = line.split()
    b, p, err = play_line(mv)
    if err:
        print(f"  {line:10s} 違法: {err}")
        fail += 1
        continue
    key = tuple(tuple(row) for row in b) + (p,)
    dup = seen.get(key)
    seen[key] = line
    nlegal = len(legal_moves(b, p, B))
    print(f"  {line:10s} 全手合法 Y / ply3 手番 {p} / 次の合法手数 {nlegal:2d}"
          + (f" / 局面重複: {dup}" if dup else ""))

print()
print("=" * 78)
print(f"NG 件数: {fail}")
print("=" * 78)
sys.exit(1 if fail else 0)
