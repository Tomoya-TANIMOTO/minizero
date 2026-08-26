#!/usr/bin/env python3
"""(I-b) 初期局面（着手0手）の root 直下 4手のフル桁ダンプ。

初手の合法手 E3 / F4 / C5 / D6 は初期配置の安定化群（id, diag, antidiag, rot180）
で1軌道になる。P・Q・N・gaz_decision_score をフル桁で並べ、max-min を出す。
判定・解釈は書かない。

使い方: python3 xrl_viz/analyze_initial.py
"""
import json
import os

B = 8
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "data/sym/initial_n128.json")
FIELDS = ("N", "P", "Q", "v", "p_logit", "gaz_decision_score", "gaz_eliminated_round")


def cell(r, c):
    return f"{chr(ord('A') + c)}{r + 1}"


def fmt(x):
    return "None" if x is None else (repr(x) if isinstance(x, float) else str(x))


d = json.load(open(SRC))
mv = d["moves"][0]
root = mv["root"]
kids = root["children"]

print("=" * 92)
print("(I-b) 初期局面（着手0手・黒番）の root 直下")
print("=" * 92)
print(f"  ファイル: xrl_viz/data/sym/initial_n128.json")
print(f"  n = 128, root N = {root['N']}, 選ばれた手 = {mv['played']}")
print(f"  root の gaz_decision_score = {fmt(root.get('gaz_decision_score'))}"
      f" / gaz_eliminated_round = {fmt(root.get('gaz_eliminated_round'))}")
print(f"  root 直下（訪問順） = {' '.join(cell(c['row'], c['col']) for c in kids)}")
print(f"  子ノード数 = {len(kids)}")
print()

hdr = f"  {'cell':<6}" + "".join(f"{f:<24}" for f in FIELDS)
print(hdr)
print("  " + "-" * (len(hdr) - 2))
for c in sorted(kids, key=lambda x: cell(x["row"], x["col"])):
    print(f"  {cell(c['row'], c['col']):<6}" + "".join(fmt(c.get(f)).ljust(24) for f in FIELDS))

print()
print("  4手の max-min（フル桁）")
for f in FIELDS:
    vals = [c.get(f) for c in kids]
    if any(v is None for v in vals):
        print(f"    {f:<22} 値に None を含む: {[fmt(v) for v in vals]}")
        continue
    print(f"    {f:<22} max {fmt(max(vals)):<24} min {fmt(min(vals)):<24} "
          f"max-min {fmt(max(vals) - min(vals))}")

print()
print("  変換ごとに対応づけたペアの差")
print("  （4手まとめた max-min は 2+2 の割れ方を隠すので、変換ごとに分けて出す。")
print("    厳密には点対称は rot180 のみ。diag / antidiag は対角線に関する鏡映で、")
print("    3つとも初期配置を保つ安定化群の元。utils/rotation.h の enum 名を併記する。）")
by_cell = {cell(c["row"], c["col"]): c for c in kids}
TF = [
    ("diag     (r,c)->(c,r)      = kHorizontalRotation270", lambda r, c: (c, r)),
    ("antidiag (r,c)->(7-c,7-r)  = kHorizontalRotation90", lambda r, c: (B - 1 - c, B - 1 - r)),
    ("rot180   (r,c)->(7-r,7-c)  = kRotation180", lambda r, c: (B - 1 - r, B - 1 - c)),
]
for name, f in TF:
    print(f"\n    [{name}]")
    seen = set()
    for k in sorted(by_cell):
        r, c = int(k[1:]) - 1, ord(k[0]) - ord("A")
        m = cell(*f(r, c))
        if (m, k) in seen:
            continue
        seen.add((k, m))
        a, b = by_cell[k], by_cell[m]
        print(f"      {k} <-> {m}")
        for fl in FIELDS:
            x, y = a.get(fl), b.get(fl)
            print(f"        {fl:<22} {fmt(x):<16} {fmt(y):<16} |Δ| {fmt(abs(x - y))}")

print()
print("  各子の1手先（孫）ノード数")
for c in sorted(kids, key=lambda x: cell(x["row"], x["col"])):
    gk = c.get("children", [])
    print(f"    {cell(c['row'], c['col']):<6} 孫 {len(gk):2d} 件: "
          + " ".join(f"{cell(g['row'], g['col'])}(N={g['N']})" for g in gk))
