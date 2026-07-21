# 序盤固定コーパス（教授指示② 複数対局）

生成日: 2026-07-21
生成スクリプト: `xrl_viz/gen_corpus.sh`（コンテナ内で実行）
監査スクリプト: `xrl_viz/audit_corpus.py`

## 設計

- **3手固定**。2手固定は3系統で対局数に届かず、4手固定は 60〜61 系統で選定基準が別途必要になる。
  14 系統（`tools/opening_branches.py` で列挙）は選定理由を明示できる規模。
- **4系統**。①②③で2手目の3系統をすべて覆い、①④で同一2手からの3手目分岐を含める。
- **n 水準 16 / 32 / 128**。

| 記号 | 着手列 | 位置づけ |
|---|---|---|
| S1 | E3 D3 C4 | 系統1（対角） |
| S2 | E3 F3 F4 | 系統2 |
| S3 | E3 F5 D6 | 系統3 |
| S4 | E3 D3 C6 | 系統1 の別分岐（S1 と2手目まで同一） |

固定手は先手(黒)から交互。B=1手目, W=2手目, B=3手目で、ply 3（白番）からエンジンが指す。
4系統とも全手合法であり、意図した局面に到達することを盤面図で確認済み。

## 生成方式

- **主軸（方式2・打ち直し）**: 各系統を n=128 で最後まで対局させ（`src_S*_n128.json`）、
  その着手列を `replay_line.py` で n=16/32/128 に打ち直す（`replay_S*_n*.json`、12記録）。
  全 ply で3水準を直接比較できるため、これを説明の主材料とする。
- **補助（方式1・独立対局）**: S1 のみ、3水準それぞれに固定手の続きを自分で打たせる
  （`indep_S1_n*.json`、3記録）。「n を変えると対局そのものが変わる」ことを示す。

## 使用エンジン

コミット `fd5d477116b0850aca61fb067869a1009a536dea`
（virtual loss 修正 `c8117dc` と tree_json のフィルタ修正 `cf20e4c` を含む）

```
生成に使ったエンジンのコミット: fd5d477116b0850aca61fb067869a1009a536dea

=== (4)(5) 健全性・決定論条件 ===
  indep_S1_n128.json         ply  61  不整合 0  終局後 4  p_noise {0}
  indep_S1_n16.json          ply  61  不整合 0  終局後 4  p_noise {0}
  indep_S1_n32.json          ply  61  不整合 0  終局後 4  p_noise {0}
  replay_S1_n128.json        ply  63  不整合 0  終局後 3  p_noise {0}
  replay_S1_n16.json         ply  63  不整合 0  終局後 3  p_noise {0}
  replay_S1_n32.json         ply  63  不整合 0  終局後 3  p_noise {0}
  replay_S2_n128.json        ply  63  不整合 0  終局後 3  p_noise {0}
  replay_S2_n16.json         ply  63  不整合 0  終局後 3  p_noise {0}
  replay_S2_n32.json         ply  63  不整合 0  終局後 3  p_noise {0}
  replay_S3_n128.json        ply  63  不整合 0  終局後 3  p_noise {0}
  replay_S3_n16.json         ply  63  不整合 0  終局後 3  p_noise {0}
  replay_S3_n32.json         ply  63  不整合 0  終局後 3  p_noise {0}
  replay_S4_n128.json        ply  63  不整合 0  終局後 3  p_noise {0}
  replay_S4_n16.json         ply  63  不整合 0  終局後 3  p_noise {0}
  replay_S4_n32.json         ply  63  不整合 0  終局後 3  p_noise {0}
  src_S1_n128.json           ply  61  不整合 0  終局後 4  p_noise {0}
  src_S2_n128.json           ply  61  不整合 0  終局後 4  p_noise {0}
  src_S3_n128.json           ply  61  不整合 0  終局後 4  p_noise {0}
  src_S4_n128.json           ply  61  不整合 0  終局後 4  p_noise {0}

  全記録の p_noise の値集合: {0}  -> 決定論条件 成立

=== (6) 記録の一覧 ===
記録                         系統   着手列(固定3手)           n    手数    黒    白     勝敗
replay_S1_n16              S1   E3 D3 C4           16    60   31   33    白勝ち
replay_S1_n32              S1   E3 D3 C4           32    60   31   33    白勝ち
replay_S1_n128             S1   E3 D3 C4          128    60   31   33    白勝ち
replay_S2_n16              S2   E3 F3 F4           16    60   41   23    黒勝ち
replay_S2_n32              S2   E3 F3 F4           32    60   41   23    黒勝ち
replay_S2_n128             S2   E3 F3 F4          128    60   41   23    黒勝ち
replay_S3_n16              S3   E3 F5 D6           16    60   34   30    黒勝ち
replay_S3_n32              S3   E3 F5 D6           32    60   34   30    黒勝ち
replay_S3_n128             S3   E3 F5 D6          128    60   34   30    黒勝ち
replay_S4_n16              S4   E3 D3 C6           16    60   32   32     引分
replay_S4_n32              S4   E3 D3 C6           32    60   32   32     引分
replay_S4_n128             S4   E3 D3 C6          128    60   32   32     引分
indep_S1_n16               S1   E3 D3 C4           16    60   22   42    白勝ち
indep_S1_n32               S1   E3 D3 C4           32    60   17   47    白勝ち
indep_S1_n128              S1   E3 D3 C4          128    60   31   33    白勝ち

=== 到達盤面図 ===

[主軸] 系統 S1 (E3 D3 C4) の最終盤面（3水準で共通の着手列）
    8  X X X X X X X O
    7  O O X X X X O O
    6  O O X X X O X O
    5  O O X X X X O O
    4  O X X O X X O O
    3  O O X O X O O O
    2  O O O O O O O O
    1  X X X O X X X O
       A B C D E F G H

[主軸] 系統 S2 (E3 F3 F4) の最終盤面（3水準で共通の着手列）
    8  X X X X X X X X
    7  X O X X O O O O
    6  X X X X X X O O
    5  X O X X X O O O
    4  X O X X X O X O
    3  X X X O X X X O
    2  X X X X X X X O
    1  X O O O O O X O
       A B C D E F G H

[主軸] 系統 S3 (E3 F5 D6) の最終盤面（3水準で共通の着手列）
    8  X X X X X X X O
    7  X X O O O X X X
    6  X O X O O O X X
    5  X X O O O X O O
    4  X X O O X X O O
    3  X O O X O O O X
    2  X O O O O O O X
    1  X X X X X X O O
       A B C D E F G H

[主軸] 系統 S4 (E3 D3 C6) の最終盤面（3水準で共通の着手列）
    8  X X X X X X X O
    7  O X X X O X O O
    6  O X X X X O O O
    5  O X O X O X O O
    4  O X O O X X O O
    3  O O X X O X O O
    2  O O O O O O O O
    1  X X X X X X X X
       A B C D E F G H

[補助] indep_S1_n16 の最終盤面
    8  O X X X O O O O
    7  O O O O O X O O
    6  O O O X X O X O
    5  O O O X O X X O
    4  O X X O O X X O
    3  X X O O X X X O
    2  X O O O O O X O
    1  O O O O O O O X
       A B C D E F G H

[補助] indep_S1_n32 の最終盤面
    8  O O O O O O O X
    7  X O O X X O X O
    6  X O O O O X O O
    5  O O X O X O O O
    4  X O X X O O O O
    3  X X X X O O O O
    2  X O O O O O O O
    1  O O O O O O O O
       A B C D E F G H

[補助] indep_S1_n128 の最終盤面
    8  X X X X X X X O
    7  O O X X X X O O
    6  O O X X X O X O
    5  O O X X X X O O
    4  O X X O X X O O
    3  O O X O X O O O
    2  O O O O O O O O
    1  X X X O X X X O
       A B C D E F G H

=== (7) 同一系統で n によって着手が分岐した最初の ply（主軸12記録）===
  S1: 最初の分岐 ply 4  n=16:F4 / n=32:C5 / n=128:C5   （分岐した ply は全 29 件）
  S2: 最初の分岐 ply 4  n=16:C4 / n=32:E2 / n=128:E2   （分岐した ply は全 28 件）
  S3: 最初の分岐 ply 9  n=16:C5 / n=32:G3 / n=128:G3   （分岐した ply は全 31 件）
  S4: 最初の分岐 ply 11  n=16:E2 / n=32:B5 / n=128:B5   （分岐した ply は全 22 件）
```
