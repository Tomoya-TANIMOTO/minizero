#!/usr/bin/env python3
"""盤面の読み方と各記録の開始局面を1枚のテキストにまとめる。

数値は一切ここで計算せず、生成済み JSON の board をそのまま描く。
出力: xrl_viz/data/BOARD_REFERENCE.txt

参照する記録が data/sym・data/corpus14・data/corpus の3つにまたがるため、
どれかの下ではなく共通の親 data/ 直下に置く。

使い方: python3 xrl_viz/make_board_reference.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_alignment import legal_moves  # noqa: E402

B = 8
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "xrl_viz/data/BOARD_REFERENCE.txt")

SYM4 = [
    ("E3 D3 C4", "id       (r,c)->(r,c)      ", "xrl_viz/data/corpus/src_S1_n128.json"),
    ("F4 F5 E6", "antidiag (r,c)->(7-c,7-r)  ", "xrl_viz/data/sym/state_antidiag_n128.json"),
    ("C5 C4 D3", "diag     (r,c)->(c,r)      ", "xrl_viz/data/sym/state_diag_n128.json"),
    ("D6 E6 F5", "rot180   (r,c)->(7-r,7-c)  ", "xrl_viz/data/sym/state_rot180_n128.json"),
]

LINES14 = [
    ("E3 D3 C2", "xrl_viz/data/corpus14/line_E3D3C2_n128.json"),
    ("E3 D3 C3", "xrl_viz/data/corpus14/line_E3D3C3_n128.json"),
    ("E3 D3 C4", "xrl_viz/data/corpus/src_S1_n128.json"),
    ("E3 D3 C5", "xrl_viz/data/corpus14/line_E3D3C5_n128.json"),
    ("E3 D3 C6", "xrl_viz/data/corpus/src_S4_n128.json"),
    ("E3 F3 G3", "xrl_viz/data/corpus14/line_E3F3G3_n128.json"),
    ("E3 F3 F4", "xrl_viz/data/corpus/src_S2_n128.json"),
    ("E3 F3 C5", "xrl_viz/data/corpus14/line_E3F3C5_n128.json"),
    ("E3 F3 D6", "xrl_viz/data/corpus14/line_E3F3D6_n128.json"),
    ("E3 F5 C6", "xrl_viz/data/corpus14/line_E3F5C6_n128.json"),
    ("E3 F5 D6", "xrl_viz/data/corpus/src_S3_n128.json"),
    ("E3 F5 E6", "xrl_viz/data/corpus14/line_E3F5E6_n128.json"),
    ("E3 F5 F6", "xrl_viz/data/corpus14/line_E3F5F6_n128.json"),
    ("E3 F5 G6", "xrl_viz/data/corpus14/line_E3F5G6_n128.json"),
]

GLYPH = {"B": "X", "W": "O", None: "."}


def cell(r, c):
    return f"{chr(ord('A') + c)}{r + 1}"


def draw(board, marks=(), rank1_at_top=True):
    """marks に入れた (r,c) は '*' で上書きする。返り値は行のリスト。"""
    mk = set(marks)
    rows = range(B) if rank1_at_top else range(B - 1, -1, -1)
    out = ["   A B C D E F G H"]
    for r in rows:
        cells = ["*" if (r, c) in mk else GLYPH[board[r][c]] for c in range(B)]
        out.append(f" {r + 1} " + " ".join(cells))
    return out


def side_by_side(blocks, gap="    "):
    h = max(len(b) for b in blocks)
    w = [max(len(l) for l in b) for b in blocks]
    lines = []
    for i in range(h):
        lines.append(gap.join((b[i] if i < len(b) else "").ljust(w[j])
                              for j, b in enumerate(blocks)).rstrip())
    return lines


def load_board(rel, which):
    d = json.load(open(os.path.join(ROOT, rel)))
    return d["initial_board"] if which == "init" else d["moves"][0]["board"]


L = []
w = L.append

w("=" * 78)
w("盤面の読み方と、各記録の開始局面")
w("=" * 78)
w("生成: xrl_viz/make_board_reference.py（生成済み JSON の board をそのまま描画）")
w("記号: X = 黒(B)   O = 白(W)   . = 空   * = その手番の合法手")
w("")

w("-" * 78)
w("0. 記録の置き場所（本ファイルが参照する JSON は3ディレクトリに分かれている）")
w("-" * 78)
w("  xrl_viz/data/sym/       初期局面と (I) の点対称3状態")
w("      initial_n128.json            初期局面（0手）で1回だけ探索したもの")
w("      state_antidiag_n128.json     F4 F5 E6")
w("      state_diag_n128.json         C5 C4 D3")
w("      state_rot180_n128.json       D6 E6 F5")
w("      repro_S1_ply3.json           E3 D3 C4 の撮り直し（既存との一致確認用）")
w("")
w("  xrl_viz/data/corpus14/  (II) 14軌道のうち新規に撮った10本")
w("      line_<着手列>_n128.json      例 line_E3D3C2_n128.json")
w("")
w("  xrl_viz/data/corpus/    (II) 14軌道のうち既存の4本（2026-07-21 生成・同一バイナリ）")
w("      src_S1_n128.json = E3 D3 C4     src_S2_n128.json = E3 F3 F4")
w("      src_S3_n128.json = E3 F5 D6     src_S4_n128.json = E3 D3 C6")
w("")
w("  本ファイルは3つにまたがるので、どれかの下ではなく data/ 直下に置いてある。")
w("  各セクションの盤面には出典ファイルを併記した。")
w("")

w("-" * 78)
w("1. 座標とインデックスの対応")
w("-" * 78)
w("  tree_json のノードは row / col を 0 起点で持つ。cell 名との対応は")
w("")
w("      cell 名 = chr('A' + col) + str(row + 1)")
w("      col: A=0 B=1 C=2 D=3 E=4 F=5 G=6 H=7")
w("      row: 0 が rank 1、7 が rank 8")
w("      action_id = row * 8 + col        （例 F3 -> row 2, col 5, id 21）")
w("")
w("  board は board[row][col] の入れ子配列。console.cpp の boardToJson が")
w("  row を 0 から回して出しているので、JSON の先頭の行が rank 1。")
w("")

w("-" * 78)
w("2. 描く向きが repo 内で2通りある（表示だけの違い・データは同一）")
w("-" * 78)
w("  同じ board を2通りに描いたもの。中身は同じで、上下が逆なだけ。")
w("  cell 名の対応（E3 がどこか）は変わらないので、必ず行番号のラベルを見ること。")
w("")
init = load_board("xrl_viz/data/sym/initial_n128.json", "init")
a = ["  [向き A] rank 1 が上（オセロの通常図・本ファイルはこちらで統一）"] + \
    ["  " + l for l in draw(init, rank1_at_top=True)]
b = ["  [向き B] rank 1 が下（xrl_viz/audit_corpus.py の board_str がこちら）"] + \
    ["  " + l for l in draw(init, rank1_at_top=False)]
L.extend(side_by_side([a, b], gap="   "))
w("")
w("  向き A = xrl_viz/verify_openings.py / 本ファイル")
w("  向き B = xrl_viz/audit_corpus.py の board_str（= audit_report.txt の盤面図）")
w("  console.cpp:323 のコメントは row 0 を「下段」と呼んでおり、向き B の見方に相当する。")
w("")

w("-" * 78)
w("3. 初期局面（着手 0 手・黒番）")
w("-" * 78)
w("  一次データ: xrl_viz/data/sym/initial_n128.json の initial_board")
w("")
lm0 = sorted(legal_moves(init, "B", B))
blocks = [
    ["  [配置]"] + ["  " + l for l in draw(init)],
    ["  [合法手 * を重ねたもの]"] + ["  " + l for l in draw(init, lm0)],
]
L.extend(side_by_side(blocks))
w("")
w("  中央4マス: D4 = X(黒)   E4 = O(白)   D5 = O(白)   E5 = X(黒)")
w("  → 通常のオセロ図（D4 白 / E4 黒 / D5 黒 / E5 白）とは対角が逆。")
w("     tools/opening_branches.py の冒頭にも同じ注記がある。")
w("")
w("  黒番の合法手 4 手: " + " ".join(cell(r, c) for r, c in lm0))
w("  この 4 手は初期配置を保つ対称変換（下記 4 つ）で互いに移り合う 1 軌道。")
w("    id       (r,c)->(r,c)          E3 -> E3")
w("    diag     (r,c)->(c,r)          E3 -> C5")
w("    antidiag (r,c)->(7-c,7-r)      E3 -> F4")
w("    rot180   (r,c)->(7-r,7-c)      E3 -> D6")
w("  （盤面全体の二面体群 D4 は 8 個あるが、初期配置を色ごと保つのはこの 4 個だけ。）")
w("  各手の N / P / Q / gaz_decision_score は xrl_viz/data/sym/initial_report.txt を見ること。")
w("")

w("-" * 78)
w("4. (I) 点対称 4 状態の開始局面（3 手を打った後・ply 3・白番）")
w("-" * 78)
w("  4 つとも、指定の変換で写すと E3 D3 C4 の盤面に重なる（着手列・手番も一致）。")
w("")
for i in range(0, 4, 2):
    blocks = []
    for line, tname, rel in SYM4[i:i + 2]:
        bd = load_board(rel, "ply3")
        lm = sorted(legal_moves(bd, "W", B))
        blocks.append([f"  [{line}]  変換 {tname.strip()}"]
                      + ["  " + l for l in draw(bd, lm)]
                      + [f"  合法手: {' '.join(cell(r, c) for r, c in lm)}",
                         f"  出典: {rel}"])
    L.extend(side_by_side(blocks))
    w("")
w("  基準 E3 D3 C4 の合法手 B3 F3 B5 F5 が、各状態では別の cell 名で現れる。")
w("  差分の数値は xrl_viz/data/sym/symmetry_report.txt を見ること。")
w("")

w("-" * 78)
w("5. (II) 14 軌道の開始局面（3 手を打った後・ply 3・白番）")
w("-" * 78)
w("  14 軌道はすべて初手 E3。対称正規化した 3 手開きの全系統。")
w("")
for i in range(0, len(LINES14), 2):
    blocks = []
    for line, rel in LINES14[i:i + 2]:
        bd = load_board(rel, "ply3")
        lm = sorted(legal_moves(bd, "W", B))
        tag = "（既存）" if "/corpus/" in rel else "（新規）"
        blocks.append([f"  [{line}] {tag}"]
                      + ["  " + l for l in draw(bd, lm)]
                      + [f"  合法手 {len(lm)}: {' '.join(cell(r, c) for r, c in lm)}",
                         f"  出典: {rel}"])
    L.extend(side_by_side(blocks))
    w("")
w("  最終盤面は xrl_viz/data/corpus14/audit_report.txt の (d) 節（向き B で描かれている）。")
w("")

with open(OUT, "w") as f:
    f.write("\n".join(L) + "\n")
print(f"書き出し: {OUT}  ({len(L)} 行)")
