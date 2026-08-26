#!/usr/bin/env bash
# capture_initial.sh — 着手0手の初期局面で1回だけ探索させ、その tree_json を出す。
#
# なぜ capture_opening.sh で足りないか:
#   (1) 固定手を1手以上要求する（OPENING は必須引数）。
#   (2) 仮に呼べても取れない。console.cpp の cmdTreeJson は actor_->getMCTSRootNode()
#       を出すだけなので、探索を1回も走らせる前の root には子が無い。
#       capture_opening.sh の [T0] がまさにそれで、board しか保存していない。
# よって初期局面の探索木には genmove を1回挟む別口が要る。
#
# バイナリ直接起動（tools/quick-run.sh 非経由）は capture_opening.sh と同じ理由（研究メモ §2.1b）。
#
# 使い方（コンテナ内で実行）:
#   xrl_viz/capture_initial.sh MODEL CFG > out.json
set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${1:?model folder or .pt path required}"
CONF="${2:?cfg required}"
GAME_TYPE="othello"

MODEL_PT="$MODEL"
[ -d "$MODEL" ] && MODEL_PT=$(ls -t "$MODEL"/model/*.pt "$MODEL"/*.pt 2>/dev/null | head -n1)

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
echo "[capture_initial] 初期局面(黒番)で1回探索..." 1>&2

# [T0] 探索前（root に子は無いが board が着手前の初期配置）→ genmove → [T1] 探索木
printf 'tree_json\ngenmove b\ntree_json\nquit\n' | "build/${GAME_TYPE}/minizero_${GAME_TYPE}" \
    -mode console -conf_file "$CONF" -conf_str "nn_file_name=${MODEL_PT}" > "$TMP" 2>/dev/null

python3 - "$TMP" <<'PY'
import sys, json

with open(sys.argv[1]) as f:
    bodies = [ln[2:].strip() for ln in f if ln.startswith("= ")]

# 応答は tree_json / genmove / tree_json の3件。ずれていたら黙って進めずに落とす。
if len(bodies) != 3:
    sys.exit(f"[capture_initial] 致命的: 応答が {len(bodies)} 件、期待 3 件")
for i, what in ((0, "探索前の tree_json"), (2, "探索後の tree_json")):
    if not bodies[i].startswith("{"):
        sys.exit(f"[capture_initial] 致命的: {what} が JSON でない: {bodies[i][:120]!r}")
t0 = json.loads(bodies[0])
played = bodies[1]
tj = json.loads(bodies[2])

# tj の board は着手「後」なので、board には t0（着手前）のものを充てる。
# これは capture_opening.sh が prev["board"] を使うのと同じ理由。
out = {"game": tj.get("game"), "board_size": tj.get("board_size"),
       "opening": [], "initial_board": t0["board"],
       "moves": [{"ply": 0, "played": played, "to_play": "B",
                  "board": t0["board"], "root": tj["root"]}]}
print(json.dumps(out))
sys.stderr.write(f"[capture_initial] played={played}, "
                 f"root children={len(tj['root'].get('children', []))}\n")
PY
