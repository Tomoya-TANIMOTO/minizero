#!/usr/bin/env python3
"""audit_corpus.py — 序盤固定コーパスの健全性検査と一覧化．

検査:
  (4) 全記録の board/root 対応（capture 形式は check_alignment、replay 形式は個別）
  (5) 決定論条件（p_noise が全ノードで 0）
  (6) 系統・着手列・n・勝敗・手数・到達盤面図の一覧
  (7) 同一系統で n によって着手が分岐した最初の ply（主軸12記録）
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_alignment import legal_moves  # noqa: E402
from analyze_taskB_detail import apply_move  # noqa: E402

B = 8
D = "xrl_viz/data/corpus"
SYS = {"S1": "E3 D3 C4", "S2": "E3 F3 F4", "S3": "E3 F5 D6", "S4": "E3 D3 C6"}
LEVELS = (16, 32, 128)


def coord(aid):
    if aid == B * B:
        return "PASS"
    x, y = aid % B, aid // B
    return f"{chr(ord('A') + x + (1 if x >= 8 else 0))}{y + 1}"


def rc(mv):
    x = ord(mv[0]) - ord("A")
    x -= 1 if mv[0] > "I" else 0
    return int(mv[1:]) - 1, x


def walk_nodes(node):
    yield node
    for c in node.get("children", []):
        yield from walk_nodes(c)


def check_noise(path, roots):
    vals = {n.get("p_noise") for r in roots for n in walk_nodes(r)}
    return vals


def final_board(init, line):
    """初期盤面に着手列を適用して最終盤面を返す．"""
    b = [row[:] for row in init]
    for color, mv in line:
        if mv == "PASS":
            continue
        r, c = rc(mv)
        b = apply_move(b, color, r * B + c, B)
    return b


def board_str(b):
    out = []
    for r in range(7, -1, -1):
        out.append(f"    {r+1}  " + " ".join({"B": "X", "W": "O", None: "."}[b[r][c]] for c in range(B)))
    out.append("       A B C D E F G H")
    return "\n".join(out)


def line_from_capture(d):
    """capture_opening.sh の記録から (color, move) の全着手列を復元する．
    played が Resign の ply でも着手は盤面に反映されているので盤面差分を使う．"""
    line = [(o["color"], o["move"]) for o in d["opening"]]
    ms = d["moves"]
    for i in range(len(ms) - 1):
        cur, nxt = ms[i]["board"], ms[i + 1]["board"]
        newly = [(r, c) for r in range(B) for c in range(B)
                 if cur[r][c] is None and nxt[r][c] is not None]
        if len(newly) == 1:
            line.append((ms[i]["to_play"], f"{chr(ord('A')+newly[0][1])}{newly[0][0]+1}"))
        elif len(newly) == 0:
            line.append((ms[i]["to_play"], "PASS"))
        else:
            raise SystemExit(f"着手を特定できない ply {ms[i]['ply']}")
    return line


def main():
    commit = open(f"{D}/ENGINE_COMMIT.txt").read().strip()
    print(f"生成に使ったエンジンのコミット: {commit}\n")

    # ---- (4)(5) 健全性と決定論条件 ----
    print("=== (4)(5) 健全性・決定論条件 ===")
    noise_all = set()
    for p in sorted(glob.glob(f"{D}/*.json")):
        d = json.load(open(p))
        name = os.path.basename(p)
        if isinstance(d, list):        # replay 形式
            roots = [r["tree"]["root"] for r in d if r["tree"]]
            bad = term = 0
            for r in d:
                t = r["tree"]
                if t is None:
                    bad += 1
                    continue
                # 終局後の ply は console.cpp L167 が isEnvTerminal() で早期 return し
                # 次行の setTurn を通らないため to_play が更新されない。探索も走らない。
                # データの破損ではないので別枠で数える。
                if len(legal_moves(t["board"], t["to_play"], B)) == 0:
                    term += 1
                    continue
                kids = {coord(c["action_id"]) for c in t["root"].get("children", [])}
                em = r["engine_move"].upper()
                if em not in ("RESIGN",) and em not in kids:
                    bad += 1
                if t["to_play"] != r["color"]:
                    bad += 1
            n = len(d)
            extra = f" 終局後 {term}"
        else:                          # capture 形式
            roots = [m["root"] for m in d["moves"]]
            nfix = len(d.get("opening", []))
            bad = 0 if len(d["moves"]) == 64 - nfix else 1
            term = 0
            for m in d["moves"]:
                if len(legal_moves(m["board"], m["to_play"], B)) == 0:
                    term += 1
                    continue
                if m["played"] in ("Resign", "PASS"):
                    continue
                kids = {coord(c["action_id"]) for c in m["root"].get("children", [])}
                r_, c_ = rc(m["played"])
                if m["played"] not in kids or m["board"][r_][c_] is not None:
                    bad += 1
            n = len(d["moves"])
            extra = f" 終局後 {term}"
        vals = check_noise(p, roots)
        noise_all |= vals
        print(f"  {name:26s} ply {n:3d}  不整合 {bad} {extra}  p_noise {vals}")
    print(f"\n  全記録の p_noise の値集合: {noise_all}"
          f"  -> 決定論条件 {'成立' if noise_all == {0} else '**不成立**'}\n")

    # ---- (6) 一覧 ----
    print("=== (6) 記録の一覧 ===")
    print(f"{'記録':26s} {'系統':4s} {'着手列(固定3手)':16s} {'n':>4s} "
          f"{'手数':>5s} {'黒':>4s} {'白':>4s} {'勝敗':>6s}")
    finals = {}
    for s in SYS:
        for tag, pat in (("src", f"{D}/src_{s}_n128.json"),):
            d = json.load(open(pat))
            line = line_from_capture(d)
            fb = final_board(d["initial_board"], line)
            nb = sum(r.count("B") for r in fb)
            nw = sum(r.count("W") for r in fb)
            nmoves = sum(1 for _, m in line if m != "PASS")
            finals[("replay", s)] = (fb, nb, nw, nmoves)
    for s in SYS:
        fb, nb, nw, nm = finals[("replay", s)]
        res = "黒勝ち" if nb > nw else ("白勝ち" if nw > nb else "引分")
        for n in LEVELS:
            print(f"{'replay_'+s+'_n'+str(n):26s} {s:4s} {SYS[s]:16s} {n:4d} "
                  f"{nm:5d} {nb:4d} {nw:4d} {res:>6s}")
    for n in LEVELS:
        d = json.load(open(f"{D}/indep_S1_n{n}.json"))
        line = line_from_capture(d)
        fb = final_board(d["initial_board"], line)
        nb = sum(r.count("B") for r in fb)
        nw = sum(r.count("W") for r in fb)
        nm = sum(1 for _, m in line if m != "PASS")
        res = "黒勝ち" if nb > nw else ("白勝ち" if nw > nb else "引分")
        finals[("indep", n)] = (fb, nb, nw, nm)
        print(f"{'indep_S1_n'+str(n):26s} {'S1':4s} {SYS['S1']:16s} {n:4d} "
              f"{nm:5d} {nb:4d} {nw:4d} {res:>6s}")

    print("\n=== 到達盤面図 ===")
    for s in SYS:
        print(f"\n[主軸] 系統 {s} ({SYS[s]}) の最終盤面（3水準で共通の着手列）")
        print(board_str(finals[("replay", s)][0]))
    for n in LEVELS:
        print(f"\n[補助] indep_S1_n{n} の最終盤面")
        print(board_str(finals[("indep", n)][0]))

    # ---- (7) n による着手の分岐 ----
    print("\n=== (7) 同一系統で n によって着手が分岐した最初の ply（主軸12記録）===")
    for s in SYS:
        recs = {n: {r["ply"]: r["engine_move"].upper()
                    for r in json.load(open(f"{D}/replay_{s}_n{n}.json"))} for n in LEVELS}
        plies = sorted(set.intersection(*(set(v) for v in recs.values())))
        first = None
        for p in plies:
            if p < 3:
                continue          # 固定手はエンジンの選択ではない
            vals = {n: recs[n][p] for n in LEVELS}
            if len({v for v in vals.values()}) > 1:
                first = (p, vals)
                break
        diffs = sum(1 for p in plies if p >= 3 and len({recs[n][p] for n in LEVELS}) > 1)
        if first:
            print(f"  {s}: 最初の分岐 ply {first[0]}  " +
                  " / ".join(f"n={n}:{v}" for n, v in first[1].items()) +
                  f"   （分岐した ply は全 {diffs} 件）")
        else:
            print(f"  {s}: 3水準とも全 ply で一致")


if __name__ == "__main__":
    main()
