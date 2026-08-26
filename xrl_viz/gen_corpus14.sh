#!/usr/bin/env bash
# gen_corpus14.sh — 初手 E3 の対称正規化3手開き 14 軌道を n=128 で生成する。
#
# 既存の xrl_viz/data/corpus/src_S{1..4}_n128.json（S1=E3 D3 C4, S2=E3 F3 F4,
# S3=E3 F5 D6, S4=E3 D3 C6）は同一エンジンで生成済みなので再利用し、
# 残り 10 軌道だけを新規に撮る。gen_corpus.sh と違い n 水準の打ち直しはしない。
#
# 使い方（コンテナ内で実行）: xrl_viz/gen_corpus14.sh [OUTDIR]
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="${1:-xrl_viz/data/corpus14}"
MODEL="othello_8x8_gaz_n16/model/weight_iter_150000.pt"
CFG="xrl_viz/cfg/othello_8x8_gaz_eval_n128.cfg"

# 既存 4 軌道を除いた 10 本。順序は 2手目→3手目の辞書順。
NEW=(
  "E3 D3 C2" "E3 D3 C3" "E3 D3 C5"
  "E3 F3 G3" "E3 F3 C5" "E3 F3 D6"
  "E3 F5 C6" "E3 F5 E6" "E3 F5 F6" "E3 F5 G6"
)

mkdir -p "$OUT"
git log -1 --format='%H' > "$OUT/ENGINE_COMMIT.txt"
echo "エンジンのコミット: $(cat "$OUT/ENGINE_COMMIT.txt")" 1>&2

for line in "${NEW[@]}"; do
  tag="${line// /}"                     # "E3 D3 C2" -> "E3D3C2"
  echo "=== $line ===" 1>&2
  xrl_viz/capture_opening.sh "$MODEL" "$CFG" "$line" 61 \
      > "$OUT/line_${tag}_n128.json" 2> "$OUT/line_${tag}_n128.log"
done

echo "=== 完了 ===" 1>&2
ls -1 "$OUT" 1>&2
