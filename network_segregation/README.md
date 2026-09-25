# Segregated by design in Brazil?

Self-contained companion code for the paper *Segregated by Design in Brazil? Street-Network Topology and the
Measurement of Racial Segregation*. It reads the repository's 2022 census inputs read-only and writes only inside
this folder.

    conda env create -f environment.yml          # env "netseg" (OpenBLAS, osmium-tool, osmnx, segregation 2.5.3)
    conda activate netseg
    pytest                                        # unit tests

    # OpenStreetMap snapshot used in the paper (Geofabrik, replication 2026-09-23T20:22:04Z; see outputs/osm_snapshot.txt)
    curl -L -o data/osm_source/brazil-latest.osm.pbf https://download.geofabrik.de/south-america/brazil-latest.osm.pbf

    python scripts/run_all.py                     # 91 cities -> outputs/ (resumable; smallest first, Sao Paulo last)
    python scripts/check_fragmentation_stability.py
    python scripts/fit_models.py
    python scripts/make_tables.py
    python scripts/make_figures.py

    # optional cross-check against segregation's native pandana route (separate env)
    conda env create -f environment-crosscheck.yml
    conda run -n netseg-pandana python scripts/run_crosscheck_pandana.py
    python scripts/make_tables.py

    python scripts/sync_manuscript_assets.py
    cd manuscript && latexmk -pdf manuscript.tex

Caches: clipped city graphs in `data/osm/`, tract-pair distances in `data/pairs/`, per-city results in
`data/results/` (delete a city's JSON to recompute it). `docs/spec.md` is the design, `docs/plan.md` the
implementation plan and `docs/progress.md` the execution log with every deviation from the plan.
