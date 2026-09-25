# SDD ledger — plan: network_segregation/docs/plan.md
Setup: Ruling: no worktree, no commits, ledger here (not .superpowers/) — author forbade commits and touching anything outside network_segregation/ — cost if wrong: none; task ranges not tied to git commits.
Pre-flight: T2 GROUPS→T5/T7 ok; T3 prepare_graph/snap_points→T4/T7 ok (node object array); T4 Pairs/graph_to_csr→T5/T6/T7 ok; T6 fragmentation(Gc, **frag_kwargs)→T7/T8 ok; T7 indices_long/cities.parquet→T10/T11/T12 ok; T10 analysis_frame.parquet→T12 ok; T11 numbers.tex→T14 ok.
Task 1: complete (tests: pytest tests/test_env.py → 10 passed)
Task 2: Ruling: added CD_MUN to read_file columns (then dropped) — pyogrio where-clause returns empty when its field is not selected — cost if wrong: none (behaviour verified on real Porto Alegre: 2695 tracts).
Task 2: complete (tests: pytest tests/test_cities.py → 5 passed)
Task 3: Ruling: snap test asserts list(ids)==[(0,0),(2,2)] only (dropped the redundant map(tuple) branch) — equivalent assertion — cost: none.
Task 3: complete (tests: pytest tests/test_network.py → 4 passed; live smoke 342 nodes/456 edges)
Task 4: complete (tests: pytest tests/test_distances.py → 6 passed)
Task 5: complete (tests: pytest tests/test_measures.py → 5 passed; exact match vs segregation w= path)
Task 6: Ruling: netseg env switched to OpenBLAS (libblas=*=*openblas, pinned in environment.yml) — conda-forge MKL 2026 crashed on any matmul (0xc06d007f) — cost if wrong: none; numerics identical up to BLAS rounding.
Task 6: Ruling: plan said 6 tests, file has 5 — plan miscount — cost: none.
Task 6: complete (tests: pytest tests/test_topology.py → 5 passed; full suite green)
Task 7: Ruling: pipeline test fixture uses integer node ids — osmnx.project_graph cannot handle tuple node ids (real OSM ids are ints) — cost: none.
Task 7: Ruling: compute_indices drops groups with zero citywide count before MultiInfoTheory (new test test_group_absent_citywide_is_ignored_not_nan RED→GREEN) — PySAL returns NaN (0·log0); H convention treats it as 0 — cost if wrong: none for 91 large cities, all groups present.
Task 7: Ruling: topology computed on ALL nodes inside the urban footprint (clip_graph(largest=False)); meshedness numerator e−v+p; fragmentation routes on the full buffered connected graph with origins/targets sampled only from urban nodes (tests test_clip_graph_can_keep_all_components, test_meshedness_uses_all_components, test_fragmentation_samples_only_from_given_nodes RED→GREEN) — Palmas: footprint (populated urban tracts) has holes where zero-pop tracts are dropped and superblocks connect through outside streets; LCC kept only 4457/14002 urban nodes — cost if wrong: metrics differ from a strict LCC definition; documented in paper methods.
Task 11: Ruling: write_macros writes with newline="\n" and test compares bytes — Windows write_text emits CRLF; the bash heredoc also stripped escapes in the test literal (restored from plan) — cost: none.
Tasks 10/11/12 code: models.py, report.py, vignette.py written TDD (tests RED at collection → GREEN); suite 51 passed. Script parts pending full run.
Author request (2026-09-24): added population-matched robustness (Saporito 2026, Urban Science 10(9):506). weights.matched_kernel_matrix (row-adaptive linear kernel; bisection per tract so Euclidean env population = 2-km network env population); pipeline spec "popmatch" (euc = matched Euclidean, net = main network) + city fields env_pop_*; tests test_matched_kernel_* (3) and test_run_city_population_matched_spec RED→GREEN; suite 55 passed. Palmas: env pop euc 9209 vs net 4333; popmatch H_euc 0.0306 > H_net 0.0299.
Author request: run order smallest→largest (São Paulo last). São Paulo graph already cached (complete GraphML, 345 MB).
Task 13: complete (34 verified entries incl. saporito2026; knaap key renamed knaap2024segregated — published EPB 51(7) 2024; cortes2020open is J. Comput. Soc. Sci. 3:135–166 not JGS — plan's hint was wrong)
Run: Ruling: download_walk_graph retries up to 6x with growing waits (tests test_download_retries_transient_errors / _gives_up RED→GREEN, suite 57) — 11 cities failed on overpass-api.de connect timeouts; run restarted (resumes from cache) — cost: slower run when Overpass is flaky.
Author decision (2026-09-24): street networks from one Geofabrik extract (brazil-latest.osm.pbf, replication 2026-09-23T20:22:04Z, md5 9d51956c…) instead of Overpass (throttled/blocked after ~5 cities). New module netseg/osm_extract.py: osmium tags-filter (w/highway, once) + osmium extract per city (complete_ways) + OSMnx walk filter parsed from osmnx (Overpass semantics) + truncate_by_edge + simplify. Tests tests/test_osm_extract.py (15) RED→GREEN; suite 72. osmium-tool added to env.
Validation: Palmas extract vs Overpass — identical tract-pair network distances (35,330 pairs, max diff 0) and urban node count; only the 2-km buffer periphery differs (fragmentation 0.7765 vs 0.7781).
Overpass caches moved to data/osm_overpass and data/stale_overpass (not used).
Task 7: complete (91/91 cities, 0 failures; 1820 index rows; suite 72 passed)
Task 8: complete (STABLE: max |ΔF| 0.0147 < 0.02 when S,N doubled; outputs/tables/fragmentation_stability.csv)
Task 10: Ruling: kept K&R specification although VIF(meshedness)=12.7, VIF(dead-end)=9.4 — collinearity stated in Results; flagged to author — cost if wrong: individual coefficients of those two unstable.
Task 10: complete (models.tex; F coefficient n.s.)
Task 11: complete (+ extra macros: popmatch, env-pop ratio and its Spearman correlations with topology — supports the scale-mechanism interpretation)
Task 12: complete (6 figures rendered and visually checked; fixed extent, label collisions, colorbar overlap)
Task 9: complete (pandana cross-check: |H_net ours − pandana| ≤ 0.0009 for Porto Alegre, Curitiba, Salvador; pyarrow + openblas added to environment-crosscheck.yml)
Task 14: complete (manuscript.pdf 18 pp, latexmk 0 warnings/overfull; all numbers via numbers.tex macros or \input tables; microtype dropped — not in TinyTeX)
Final review: self-review (no subagent — none requested by author). Checked: d_net ≥ d_euc (so popmatch bisection bounded by 2 km); Review Focus items all have tests; spec updated for data-source change and popmatch; suite 72 passed; git status shows only untracked network_segregation/.
Final: minor (deferred): VIF values (12.7, 9.4) typed in results.tex rather than macros.
Final: minor (deferred): popmatch "Mean gap" shows -0.000 at 3 decimals in robustness table.
