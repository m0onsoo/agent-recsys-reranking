# Offline Analysis Scripts

These scripts are copied unchanged from the local experiment archive. They read
local raw run directories, profiles, and the derived MovieLens bundle, which are
not included in this repository. No API calls are made by these scripts.

For `analyze_full.py` and `bias_eval.py`, use the copies in the archive's original
`n1000_v2/analysis_full/` and `n1000_v2/analysis_bias/` directories; their relative
paths depend on that layout. For `v3_vs_reference.py` and `fusion_split_half.py`,
run the archived scripts from the archive's `jinyi_results/` directory, with the
local source repository and derived bundle alongside it. The fusion script also
reads the adjacent `v3_vs_reference.py`.

Published aggregate CSVs are in `../summary_csv/`. Raw artifacts remain off GitHub.