# Multidimensional racial residential segregation across Brazilian cities (2022 Census)

Reproducible pipeline for the nationwide segregation analysis: the `segbr/` Python
package does data loading, city assembly and the computation of nine PySAL
`segregation` indices; the `scripts/` drivers build the city universe, run the
nationwide computation and regenerate every figure and table in the manuscript
(`draft/draft_v5.tex`, and the REBEP version `draft/rebep/manuscript.tex`).

## Reproducing the analysis

1. **Get the IBGE source data.** Download the files listed in
   [`MANIFEST.md`](MANIFEST.md) and place them at the paths given there
   (`Agregados_por_setores_cor_ou_raca_BR_csv/` and `shapefiles_2022/<UF>_setores_CD2022/`
   for all 27 UFs). They are ~2.3 GB total and are not stored in this repository.

2. **Create the environment.** The geospatial stack (geopandas, libpysal,
   pyogrio, ...) is only available in the conda env, not in a plain `pip` install:

   ```
   conda env create -f environment.yml
   conda activate segbr
   ```

   `requirements-lock.txt` is a machine `pip freeze` record kept only as an exact
   version reference; it is **not** directly installable (see its header).

3. **Run the pipeline** (use the interpreter from the `segbr` env; on the
   development machine that is `C:/Users/renan/anaconda3/python.exe`):

   ```
   python scripts/build_universe.py            # -> outputs/city_universe_2022.csv
   python scripts/build_municipio_names.py     # -> outputs/municipio_names.csv (one-off)
   python scripts/run_nationwide.py            # -> outputs/segregation_profiles_2022.parquet
   python scripts/build_municipio_polygons.py  # -> outputs/{municipio,uf}_polygons.gpkg
   python scripts/figures.py all               # -> figures/*.png, outputs/tables/*.tex
   ```

4. **Build the manuscript:**

   ```
   cd draft && pdflatex -interaction=nonstopmode draft_v5.tex \
     && bibtex draft_v5 \
     && pdflatex -interaction=nonstopmode draft_v5.tex \
     && pdflatex -interaction=nonstopmode draft_v5.tex   # -> draft_v5.pdf
   ```

   The REBEP package builds the same way from `draft/rebep/` (`manuscript.tex`).

Every figure and table regenerates from the committed
`outputs/segregation_profiles_2022.parquet` and `outputs/city_universe_2022.csv`,
so steps 1–3 can be skipped if you only want to rebuild the paper.

## Tests

```
C:/Users/renan/anaconda3/python.exe -m pytest tests/ -q
```
