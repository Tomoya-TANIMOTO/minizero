#!/usr/bin/env python3
"""(I) 点対称4状態の探索木を E3 フレームへ写して突き合わせる。

各木の全ノードの (row, col) に変換をかけて E3 フレームの cell 名に直し、
root からの cell 列（パス）でノードを対応付けて生の差分だけを出す。
判定・解釈は書かない。

P・Q・gumbel score は盤の向きに依存しないスカラーなので、変換は cell の
対応付けにのみ使う（値そのものは変換しない）。3変換とも自己逆。

使い方: python3 xrl_viz/analyze_symmetry.py
"""
import json
import os
import sys

B = 8
HERE = os.path.dirname(os.path.abspath(__file__))

REF = os.path.join(HERE, "data/corpus/src_S1_n128.json")
STATES = [
    ("F4 F5 E6", "antidiag", "(r,c)->(7-c,7-r)", lambda r, c: (B - 1 - c, B - 1 - r),
     os.path.join(HERE, "data/sym/state_antidiag_n128.json")),
    ("C5 C4 D3", "diag", "(r,c)->(c,r)", lambda r, c: (c, r),
     os.path.join(HERE, "data/sym/state_diag_n128.json")),
    ("D6 E6 F5", "rot180", "(r,c)->(7-r,7-c)", lambda r, c: (B - 1 - r, B - 1 - c),
     os.path.join(HERE, "data/sym/state_rot180_n128.json")),
]
FIELDS = ("N", "Q", "P", "v", "p_logit", "gaz_decision_score", "gaz_eliminated_round")


def cell(r, c):
    return f"{chr(ord('A') + c)}{r + 1}"


def cell_to_rc(s):
    return int(s[1:]) - 1, ord(s[0].upper()) - ord("A")


def flatten(node, f, path=()):
    """(mapped-path -> node) の辞書。root は path=() で、変換は子の cell にのみ効く。"""
    out = {path: node}
    for ch in node.get("children", []):
        out.update(flatten(ch, f, path + (cell(*f(ch["row"], ch["col"])),)))
    return out


def fmt(x):
    return "None" if x is None else (repr(x) if isinstance(x, float) else str(x))


def pathstr(p):
    return "/".join(p) if p else "(root)"


def main():
    ref = json.load(open(REF))["moves"][0]
    ident = flatten(ref["root"], lambda r, c: (r, c))
    ref_kids = [cell(ch["row"], ch["col"]) for ch in ref["root"]["children"]]

    print("=" * 92)
    print("(I) 点対称4状態の探索木を E3 フレームへ写して突き合わせる")
    print("=" * 92)
    print(f"基準: E3 D3 C4 (src_S1_n128.json moves[0], ply 3, 白番)")
    print(f"  root N = {ref['root']['N']}, 選ばれた手 = {ref['played']}")
    print(f"  root 直下 = {' '.join(ref_kids)}   ノード総数 = {len(ident)}")

    for line, tname, tdesc, f, path in STATES:
        st = json.load(open(path))
        mv = st["moves"][0]
        mapped = flatten(mv["root"], f)
        kids_raw = [cell(ch["row"], ch["col"]) for ch in mv["root"]["children"]]
        kids_map = [cell(*f(ch["row"], ch["col"])) for ch in mv["root"]["children"]]

        print()
        print("-" * 92)
        print(f"■ {line}  変換 {tname} {tdesc}")
        print("-" * 92)
        print(f"  root N = {mv['root']['N']}   ノード総数 = {len(mapped)}（基準 {len(ident)}）")
        print(f"  root 直下（元フレーム） = {' '.join(kids_raw)}")
        print(f"  root 直下（E3 フレーム） = {' '.join(kids_map)}")

        # 1) root 直下の子集合
        a, b = set(ref_kids), set(kids_map)
        print()
        print(f"  1) root 直下の子集合が変換後に一致するか: {'Y' if a == b else 'N'}")
        if a != b:
            print(f"     基準にのみ: {' '.join(sorted(a - b)) or '(なし)'}")
            print(f"     こちらにのみ: {' '.join(sorted(b - a)) or '(なし)'}")
        # console.cpp の appendNodeJson は node->getChild(i) の順にそのまま出す。
        # 行動 ID 順でも訪問数順でもなく、木の内部の子配列の順（展開順）。
        print(f"     出力順（内部の子配列の順）: 基準 {ref_kids} / こちら {kids_map}"
              f"  一致: {'Y' if ref_kids == kids_map else 'N'}")

        common = sorted(set(ident) & set(mapped), key=lambda p: (len(p), p))
        only_ref = sorted(set(ident) - set(mapped), key=lambda p: (len(p), p))
        only_st = sorted(set(mapped) - set(ident), key=lambda p: (len(p), p))
        print(f"     対応が付いたノード {len(common)} / 基準のみ {len(only_ref)} / こちらのみ {len(only_st)}")
        if only_ref:
            print(f"       基準のみ: {', '.join(pathstr(p) for p in only_ref[:12])}")
        if only_st:
            print(f"       こちらのみ: {', '.join(pathstr(p) for p in only_st[:12])}")

        # 各フィールドの差
        deltas = {k: [] for k in FIELDS}
        for p in common:
            x, y = ident[p], mapped[p]
            for k in FIELDS:
                u, v = x.get(k), y.get(k)
                if u is None or v is None:
                    continue
                deltas[k].append((abs(u - v), p, u, v))
        for k in FIELDS:
            deltas[k].sort(key=lambda t: -t[0])

        def report(k, label, topn):
            d = deltas[k]
            if not d:
                print(f"     （{label} は比較対象ノードなし）")
                return
            nz = [t for t in d if t[0] != 0]
            print(f"     最大 |Δ{label}| = {fmt(d[0][0])}  at {pathstr(d[0][1])}"
                  f"   （基準 {fmt(d[0][2])} / こちら {fmt(d[0][3])}）")
            print(f"     Δ{label} ≠ 0 のノード数 = {len(nz)} / {len(d)}")
            for dd, p, u, v in nz[:topn]:
                print(f"       {pathstr(p):<28} 基準 {fmt(u):<14} こちら {fmt(v):<14} Δ {fmt(dd)}")

        # 2) P
        print()
        print("  2) 対応ノード間の ΔP")
        report("P", "P", 15)

        # 3) gumbel score
        print()
        print("  3) 対応ノード間の Δgaz_decision_score")
        report("gaz_decision_score", "gaz_decision_score", 15)
        print("     root 直下の gaz_decision_score（E3 フレームの cell で並べる）")
        ref_top = {cell(ch["row"], ch["col"]): ch for ch in ref["root"]["children"]}
        st_top = {cell(*f(ch["row"], ch["col"])): ch for ch in mv["root"]["children"]}
        print(f"       {'cell':<6}{'基準 score':<22}{'こちら score':<22}{'Δ':<22}"
              f"{'基準 N':<9}{'こちら N':<9}{'基準 elim':<11}{'こちら elim'}")
        for cl in sorted(set(ref_top) | set(st_top)):
            u, v = ref_top.get(cl), st_top.get(cl)
            us = u["gaz_decision_score"] if u else None
            vs = v["gaz_decision_score"] if v else None
            dd = abs(us - vs) if (us is not None and vs is not None) else None
            print(f"       {cl:<6}{fmt(us):<22}{fmt(vs):<22}{fmt(dd):<22}"
                  f"{fmt(u['N'] if u else None):<9}{fmt(v['N'] if v else None):<9}"
                  f"{fmt(u['gaz_eliminated_round'] if u else None):<11}"
                  f"{fmt(v['gaz_eliminated_round'] if v else None)}")

        # 4) 選ばれた手
        pr, pc = cell_to_rc(mv["played"])
        played_mapped = cell(*f(pr, pc))
        print()
        print(f"  4) 選ばれた手: 基準 {ref['played']} / こちら {mv['played']} "
              f"→ E3 フレームで {played_mapped}   一致: "
              f"{'Y' if played_mapped == ref['played'] else 'N'}")

        # 5) N, Q
        print()
        print("  5) 対応ノード間の ΔN, ΔQ")
        report("N", "N", 15)
        report("Q", "Q", 15)

        print()
        print("  （参考）その他のフィールド")
        for k in ("v", "p_logit", "gaz_eliminated_round"):
            d = deltas[k]
            if d:
                nz = sum(1 for t in d if t[0] != 0)
                print(f"     最大 |Δ{k}| = {fmt(d[0][0])} at {pathstr(d[0][1])}"
                      f"   ≠0 のノード数 = {nz} / {len(d)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
