#!/usr/bin/env bash
# gen_corpus.sh — 序盤3手を固定した複数対局コーパスを生成する。
#
# 主軸(方式2・打ち直し):
#   各系統を n=128 で最後まで対局させて着手列を得て、その着手列を
#   n=16/32/128 の各エンジンに打ち直す。全 ply で3水準を直接比較できる。
#   4系統 × 3水準 = 12記録。
#
# 補助(方式1・独立対局):
#   系統① だけ、3水準それぞれに固定手の続きを自分で打たせる。
#   「n を変えると対局そのものが変わる」ことを示すため。3記録。
#
# 使い方（コンテナ内で実行）: xrl_viz/gen_corpus.sh [OUTDIR]
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="${1:-xrl_viz/data/corpus}"
MODEL="othello_8x8_gaz_n16/model/weight_iter_150000.pt"
LEVELS=(16 32 128)
MAXPLY=63

# 系統の代表着手列。tools/opening_branches.py の 14 系統から選定。
# S1 と S4 は 2手目まで同一(系統1)で、3手目で分岐する。
declare -A LINE=( [S1]="E3 D3 C4" [S2]="E3 F3 F4" [S3]="E3 F5 D6" [S4]="E3 D3 C6" )
ORDER=(S1 S2 S3 S4)

mkdir -p "$OUT"
git log -1 --format='%H' > "$OUT/ENGINE_COMMIT.txt"
echo "エンジンのコミット: $(cat "$OUT/ENGINE_COMMIT.txt")" 1>&2

echo "=== 主軸: n=128 で対局させて着手列を得る ===" 1>&2
for s in "${ORDER[@]}"; do
  xrl_viz/capture_opening.sh "$MODEL" "xrl_viz/cfg/othello_8x8_gaz_eval_n128.cfg" \
      "${LINE[$s]}" 61 > "$OUT/src_${s}_n128.json"
done

echo "=== 主軸: その着手列を各水準に打ち直す ===" 1>&2
for s in "${ORDER[@]}"; do
  for n in "${LEVELS[@]}"; do
    python3 xrl_viz/replay_line.py "$OUT/src_${s}_n128.json" "$MAXPLY" "$n" \
        "$OUT/replay_${s}_n${n}.json"
  done
done

echo "=== 補助: 系統① を各水準に独立に対局させる ===" 1>&2
for n in "${LEVELS[@]}"; do
  xrl_viz/capture_opening.sh "$MODEL" "xrl_viz/cfg/othello_8x8_gaz_eval_n${n}.cfg" \
      "${LINE[S1]}" 61 > "$OUT/indep_S1_n${n}.json"
done

echo "=== 完了 ===" 1>&2
ls -1 "$OUT" 1>&2
