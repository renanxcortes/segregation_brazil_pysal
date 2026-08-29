# Data manifest — IBGE 2022 source files

The pipeline needs the following IBGE Censo Demográfico 2022 source files. They are
**not stored in this repository** because of their size (~2.3 GB total); download
them from IBGE and place them at the paths below before running the pipeline.

IBGE periodically re-releases these files, so exact byte sizes and checksums are
not pinned here. Whoever downloads the data should record the size and a checksum
(e.g. `sha256sum`) of each file for their own run.

## 1. Census race aggregates by tract

- **Path:** `Agregados_por_setores_cor_ou_raca_BR_csv/Agregados_por_setores_cor_ou_raca_BR.csv`
- **What:** Censo Demográfico 2022, "Agregados por setores censitários — Cor ou raça"
  (tract-level counts by colour/race category).
- **Source:**
  https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-2022-agregados-por-setores-censitarios.html
  (FTP mirror: https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/)
- **Size / format:** ~193 MB, `;`-separated, latin-1 / UTF-8 encoding.

## 2. Census-tract boundaries (malha de setores censitários 2022)

- **Path:** `shapefiles_2022/<UF>_setores_CD2022/` for all 27 federative units
  (e.g. `shapefiles_2022/SP_setores_CD2022/SP_setores_CD2022.shp` plus its
  `.dbf`, `.prj`, `.shx` siblings).
- **What:** IBGE malha de setores censitários 2022, tract polygons, native
  SIRGAS 2000 (EPSG:4674).
- **Source:**
  https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/26565-malhas-de-setores-censitarios-divisoes-intramunicipais.html
- **Size:** ~2.1 GB total across the 27 UFs.

## Not needed for the core analysis

Other archives present in a working checkout (`microdados_censo_superior_2019/`,
`Agregados_por_bairros_demografia_BR.zip`, `RS_20241211/`, etc.) are exploratory
material and are not read by `scripts/build_universe.py`,
`scripts/run_nationwide.py`, `scripts/build_municipio_polygons.py` or
`scripts/figures.py`.
