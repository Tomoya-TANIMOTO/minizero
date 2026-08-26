#!/usr/bin/env bash
# sweep_n.sh — n スイープ用の eval 記録を取得する。
# 出典: halving 発火条件 n >= log2(m) * m/2 = 32  [gumbel_zero.cpp L109-110]
set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="othello_8x8_gaz_n16/model/weight_iter_150000.pt"
BASE_CFG="xrl_viz/othello_8x8_gaz_eval.cfg"
OUTDIR="xrl_viz/data/sweep"
DATE="$(date +%Y%m%d)"
MAX_MOVES=64
LEVELS=(16 24 32 64 128 256)

mkdir -p "$OUTDIR" xrl_viz/cfg

for n in "${LEVELS[@]}"; do
  CFG="xrl_viz/cfg/othello_8x8_gaz_eval_n${n}.cfg"
  sed -E "s|^actor_num_simulation=[0-9]+|actor_num_simulation=${n}|" "$BASE_CFG" > "$CFG"

  for kv in "actor_use_gumbel_noise=false" \
            "actor_use_dirichlet_noise=false" \
            "actor_use_random_rotation_features=false" \
            "actor_select_action_by_count=true" \
            "actor_select_action_by_softmax_count=false" \
            "actor_gumbel_sample_size=16"; do
    grep -qE "^${kv}( |$|#)" "$CFG" || { echo "NG $CFG: $kv が満たされていない"; exit 1; }
  done
  grep -qE "^actor_num_simulation=${n}( |$|#)" "$CFG" || { echo "NG $CFG: n=${n} 書き換え失敗"; exit 1; }

  OUT="${OUTDIR}/n${n}_eval_${DATE}_game01.json"
  echo "==> n=${n} -> ${OUT}"
  xrl_viz/Capture_game.sh "$MODEL" "$CFG" "$MAX_MOVES" > "$OUT"
  echo "    完了 ($(python3 -c "import json;print(len(json.load(open('$OUT'))['moves']))") ply)"
done

echo
echo "全水準の取得が完了。次: python3 analyze_sweep.py ${OUTDIR}"
