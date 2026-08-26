#!/usr/bin/env python3
"""plot_visits_bar.py — ポスター用「root 直下の訪問数」棒グラフをベクタ PDF で書き出す．

出すのは訪問数 N だけ（Q・v・勝率など強さに関する量は一切描かない）．
単色・全バー同色（特定の手を「正解」に見せない）．

使い方:
  python3 xrl_viz/plot_visits_bar.py [出力.pdf] [--png 確認用.png]

既定の対象局面（オープンキャンパス用に選定）:
  xrl_viz/data/corpus/replay_S2_n128.json の ply 17（白番, 空マス 43）
  着手列 BE3 WF3 BF4 WD3 BE2 WG4 BC4 WC3 BE6 WF6 BD2 WC2 BF2 WC6 BB4 WD6 BG3
"""
import json
import math
import os
import sys

import cairo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_alignment import aid_to_coord  # noqa: E402

SRC = "xrl_viz/data/corpus/replay_S2_n128.json"
PLY = 17
TOP = 6                      # 上位何手まで描くか
OUT_DEFAULT = "xrl_viz/figs/visits_n128_S2_ply17.pdf"

# --- 見た目（単位は pt = 1/72 inch。ベクタなので拡大しても劣化しない）--------
W, H = 800.0, 533.0                # ≒ 282mm × 188mm
M_L, M_R, M_T, M_B = 67.0, 53.0, 100.0, 110.0
BAR_FILL = (0.227, 0.416, 0.659)   # 単色．全バー同色
INK = (0.102, 0.125, 0.157)        # 見出し
INK_2 = (0.290, 0.329, 0.376)      # 数値・軸ラベル
INK_MUTED = (0.549, 0.588, 0.635)  # 補助線・脚注
BG = (1.0, 1.0, 1.0)
RADIUS = 4.0                       # データ端の角丸
FONT = "Noto Sans CJK JP"


def set_font(cr, size, bold=False):
    cr.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,
                        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(size)


def text(cr, x, y, s, size, color, bold=False, anchor="l"):
    """y はベースライン．anchor: l=左寄せ / m=中央 / r=右寄せ．"""
    set_font(cr, size, bold)
    cr.set_source_rgb(*color)
    xb, _, w, _, _, _ = cr.text_extents(s)
    dx = {"l": 0.0, "m": -w / 2 - xb, "r": -w - xb}[anchor]
    cr.move_to(x + dx, y)
    cr.show_text(s)


def bar_path(cr, x0, x1, ytop, ybase, r):
    """上端だけ角丸の棒．"""
    r = min(r, (x1 - x0) / 2, max(ybase - ytop, 0.01))
    cr.new_path()
    cr.move_to(x0, ybase)
    cr.line_to(x0, ytop + r)
    cr.arc(x0 + r, ytop + r, r, math.pi, 1.5 * math.pi)
    cr.line_to(x1 - r, ytop)
    cr.arc(x1 - r, ytop + r, r, 1.5 * math.pi, 2 * math.pi)
    cr.line_to(x1, ybase)
    cr.close_path()


def load_moves(src, ply, top):
    """指定 ply の root 直下の子を訪問数降順で返す． [(座標, N), ...]"""
    rec = json.load(open(src))
    e = next(x for x in rec if x["ply"] == ply)
    t = e["tree"]
    kids = sorted(t["root"]["children"], key=lambda c: -c["N"])
    b = t["board_size"]
    return [(aid_to_coord(c["action_id"], b) or "PASS", c["N"]) for c in kids[:top]], t


def draw(cr, moves):
    vmax = moves[0][1]
    ytop_val = vmax * 1.08                   # バー頭上に数値を置く余白

    cr.set_source_rgb(*BG)
    cr.paint()

    # --- 見出し -------------------------------------------------------------
    text(cr, M_L, 36, "AI が読んだ回数（訪問数）", 31, INK, bold=True)
    text(cr, M_L, 62, "上位2手はぴったり同じ回数。「一番読んだ手」が決まらない。",
         19, INK_2)

    # --- 描画領域 -----------------------------------------------------------
    x0, x1 = M_L, W - M_R
    y0, y1 = M_T, H - M_B                    # y1 が基線
    plot_h = y1 - y0

    def ypix(v):
        return y1 - plot_h * v / ytop_val

    # 同じ高さであることを示す水平ガイド（灰色・全バー共通、特定の手を強調しない）
    gy = ypix(vmax)
    cr.set_source_rgb(*INK_MUTED)
    cr.set_line_width(1.2)
    cr.set_dash([6, 5])
    cr.move_to(x0, gy)
    cr.line_to(x1, gy)
    cr.stroke()
    cr.set_dash([])
    text(cr, x1, gy - 9, "同じ高さ＝同じ回数", 14.5, INK_MUTED, anchor="r")

    # --- 棒 -----------------------------------------------------------------
    n = len(moves)
    slot = (x1 - x0) / n
    bw = slot * 0.60
    for i, (mv, v) in enumerate(moves):
        cx = x0 + slot * (i + 0.5)
        bx0, bx1 = cx - bw / 2, cx + bw / 2
        by = ypix(v)
        cr.set_source_rgb(*BAR_FILL)
        bar_path(cr, bx0, bx1, by, y1, RADIUS)
        cr.fill()
        text(cr, cx, by - 9, str(v), 19.5, INK_2, bold=True, anchor="m")
        text(cr, cx, y1 + 32, mv, 25, INK, bold=True, anchor="m")

    # --- 軸 -----------------------------------------------------------------
    cr.set_source_rgb(*INK_2)
    cr.set_line_width(1.6)
    cr.move_to(x0, y1)
    cr.line_to(x1, y1)
    cr.stroke()
    text(cr, x0, y0 - 11, "回数", 15.5, INK_2)
    text(cr, x1, y1 + 66, "打てる場所（盤の座標）", 15.5, INK_2, anchor="r")

    # --- 脚注（局面の同定用） ------------------------------------------------
    text(cr, M_L, H - 22,
         "オセロ 8×8 ／ 探索回数 n=128 ／ 白番 ／ 着手列 "
         "E3 F3 F4 D3 E2 G4 C4 C3 E6 F6 D2 C2 F2 C6 B4 D6 G3 の局面",
         11.5, INK_MUTED)


def main():
    args = [a for a in sys.argv[1:]]
    png = None
    if "--png" in args:
        i = args.index("--png")
        png = args[i + 1]
        del args[i:i + 2]
    out = args[0] if args else OUT_DEFAULT

    moves, tree = load_moves(SRC, PLY, TOP)

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    surf = cairo.PDFSurface(out, W, H)
    draw(cairo.Context(surf), moves)
    surf.finish()
    print(f"書き出し: {out}  ({W:.0f}x{H:.0f}pt = {W/72:.1f}x{H/72:.1f} inch, ベクタ)")

    if png:                                   # ラスタ版（300dpi 相当）
        s = 300 / 72
        isurf = cairo.ImageSurface(cairo.FORMAT_RGB24, int(W * s), int(H * s))
        icr = cairo.Context(isurf)
        icr.scale(s, s)
        draw(icr, moves)
        isurf.write_to_png(png)
        try:                                  # 300dpi を PNG に書き込む（配置時の実寸が合う）
            from PIL import Image
            Image.open(png).save(png, dpi=(300, 300))
        except ImportError:
            pass
        print(f"確認用: {png}（{int(W * s)}x{int(H * s)}px, 300dpi）")

    print("描いた手:", " ".join(f"{m}:{v}" for m, v in moves))
    print("手番:", tree["to_play"], "／ 空マス:",
          sum(1 for r in tree["board"] for x in r if x is None))


if __name__ == "__main__":
    main()
