# Journal options for the nationwide multidimensional segregation paper

**Paper in one line.** A nationwide, multidimensional, point-estimation description of
racial residential segregation across 319 Brazilian cities (2022 Census, nine PySAL
indices spanning the five Massey–Denton dimensions), with a fully reproducible pipeline.
Its headline results: the evenness indices are near-redundant and South/Southeast lead
on them (updating Sousa Filho et al. 2023 to 2022), but the exposure dimension inverts
the regional ranking and "the most segregated city" has no dimension-independent answer.

**What a reviewer will weigh.** Strengths: newest census, genuinely multidimensional,
open/reproducible, a clean conceptual point (one index is not enough). Weaknesses a
reviewer may press on: it is descriptive (no inference, deferred), no temporal or
individual-level data, the "contribution beyond Sousa Filho 2023" is incremental, and
Relative Concentration is unreliable for majority-minority cities.

> Metrics (impact factor, quartile, review time, APC) are approximate, as of early 2026.
> Verify current figures on each journal's site before submitting.

---

## Recommendation summary

| Rank | Journal | Why |
|---|---|---|
| **1 (primary)** | **Revista Brasileira de Estudos de População (REBEP)** | The exact scholarly conversation this paper joins; the two papers it builds on are here; no fee; strong Qualis; the "update to Sousa Filho 2023" framing lands perfectly. Formatting overhead (Word, ABNT, trilingual, ≤5 illustrations) is the price. |
| **2 (English, methods-forward)** | **Applied Spatial Analysis and Policy** | Best international home for a "nationwide spatially-explicit multi-city analysis" that isn't a new method; established, indexed, no reformat cost from the current LaTeX. |
| **3 (English, demography-forward)** | **Demographic Research** | Free, fast, prestigious in demography, wide readership — but selective, and it will want a sharper demographic (not just spatial) contribution. |
| Situational | Spatial Demography; Journal of Computational Social Science; Cadernos Metrópole; Caderno CRH; EURE | Good fits for specific framings — see profiles. |

**If your priority is** … the Brazilian debate and your Brazilian CV → **REBEP**. International
visibility with least friction → **Applied Spatial Analysis and Policy**. Speed + open
access + reach, and you're willing to sharpen the demographic angle → **Demographic
Research**.

---

## Decision matrix

| Journal | Scope fit | Open access | APC | Typical 1st decision | Language | Reformat cost from current LaTeX | Audience |
|---|---|---|---|---|---|---|---|
| REBEP | ★★★★★ | Yes (diamond) | None | 6–12 mo | PT/EN/ES | High (Word, ABNT, trilingual, ≤5 figs) | Brazilian demography/urban |
| Applied Spatial Analysis and Policy | ★★★★ | Hybrid | ~US$3,700 if OA; free if not | 3–5 mo | EN | Low (Springer LaTeX) | Applied spatial analysts, planners |
| Demographic Research | ★★★½ | Yes (diamond) | None | 4–7 mo | EN | Medium (their template) | International demographers |
| Spatial Demography | ★★★★½ | Hybrid | ~US$3,000 if OA; free if not | 4–8 mo (variable) | EN | Low | Spatial demographers (small) |
| Journal of Computational Social Science | ★★★ | Hybrid | ~US$3,300 if OA; free if not | 3–5 mo | EN | Low | Computational social scientists |
| Environment and Planning B: UACS | ★★★ | Hybrid | ~US$3,200 if OA; free if not | 3–6 mo | EN | Low–medium (SAGE) | Urban analytics / big-data urban |
| Population, Space and Place | ★★★ | Hybrid | ~US$4,000 if OA; free if not | 4–7 mo | EN | Low (Wiley) | Population geographers |
| Cadernos Metrópole | ★★★ | Yes (diamond) | None | 4–9 mo | PT (EN/ES accepted) | Medium | Brazilian urban studies |
| Caderno CRH | ★★½ | Yes (diamond) | None | 4–9 mo | PT | Medium | Brazilian sociology (race, work, city) |
| EURE | ★★★ | Yes (diamond) | None | 6–12 mo | ES (EN/PT accepted) | Medium | Latin American urban/regional studies |

"Diamond" = open access with no author fee.

---

## Detailed profiles

### 1. Revista Brasileira de Estudos de População (REBEP)

- **Publisher / indexing.** ABEP (Associação Brasileira de Estudos Populacionais). SciELO,
  Scopus, Redalyc, DOAJ. Qualis CAPES A1 (Demografia / Planejamento Urbano). No JCR
  impact factor (SciELO metrics instead).
- **Scope fit.** Direct. Both predecessor papers are here: Sousa Filho et al. (2023, the
  nationwide D-only 2010 study you extend) and Barros & Feitosa (2024, São Paulo–London).
- **Format.** Word only; ABNT (NBR 6023/10520) author–date references; abstract ~200
  words in **Portuguese, English and Spanish**; up to **5 illustrations**; 8,000-word cap;
  blind review with full anonymisation. A REBEP submission package (`draft/rebep/`) is
  already prepared, with the trilingual front matter drafted and a `SUBMISSION.md`
  checklist.

**Pros**
- Speaks to exactly the audience that will cite it; the incremental-over-Sousa-Filho
  framing is a feature here, not a weakness.
- Diamond open access — no fee, permanent free access, high SciELO visibility in Brazil
  and Latin America.
- A1 Qualis is valuable for a Brazilian author's evaluation (Lattes/CAPES).
- Bilingual/trilingual publication broadens reach without you translating the body
  (REBEP arranges it post-acceptance).
- Accepts descriptive demographic analysis; inference is not expected.

**Cons**
- Low international citation impact and reach relative to Springer/Wiley/SAGE titles.
- Real formatting labour: convert to Word + ABNT, cut 8 figures to 5, re-export figures
  as EPS/editable at 300 dpi, produce ES front matter, complete two REBEP forms.
- Review can be slow (6–12 months is common for SciELO journals).
- Portuguese-dominant editorial process; responses and proofs often in Portuguese
  (not a problem for you, but worth noting for co-authors).

**Verdict.** The natural home. Choose it if you want the paper embedded in the Brazilian
literature and counted well on your Brazilian CV, and you accept the formatting overhead.

---

### 2. Applied Spatial Analysis and Policy (Springer)

- **Indexing / metrics.** SSCI; JCR impact factor ≈ 2.5–3; Scopus Q1 (Geography, Planning
  & Development). Established (since 2008).
- **Scope fit.** "Development and application of spatial analysis to social, economic and
  environmental problems, with a policy dimension." A nationwide, spatially explicit,
  multi-city segregation analysis is squarely in scope.
- **Format.** Springer LaTeX template — minimal reformat from your current `draft_v5.tex`.
  No hard figure cap. Author–year references.

**Pros**
- Best international fit for a paper that is an *application* of spatial methods at
  national scale rather than a new method — reviewers there expect exactly this shape.
- Lowest friction: your LaTeX, your figures, your English text mostly carry over.
- The reproducible pipeline is a recognised plus in this venue.
- Free to publish (subscription route); OA optional.
- Decent, stable impact and a readership of people who use these indices.

**Cons**
- Expects a discernible **policy** hook — you would need a paragraph or two making the
  "what should planners/policymakers do with a multidimensional reading" argument
  explicit (currently only implicit).
- Not a demography journal; the racial-inequality and Brazilian-formation framing has to
  be pitched as spatial-policy relevance, which slightly flattens it.
- OA APC (~US$3,700) is steep if you need gold OA; the free route is subscription-only.
- Mid-tier impact — respectable, not prestige.

**Verdict.** The safest international target. Recommended fallback / co-primary with REBEP.

---

### 3. Demographic Research (Max Planck Institute for Demographic Research)

- **Indexing / metrics.** SSCI; JCR impact factor ≈ 2–2.5; Scopus Q1 (Demography).
  Fully open access, **no APC**, MPIDR-funded.
- **Scope fit.** All of formal, empirical and applied demography. Residential segregation
  and its measurement appear regularly. Has short formats ("Descriptive Finding",
  "Research Material") as well as full "Research Articles".
- **Format.** Their own template (LaTeX or Word). Reasonably light. Fast production.

**Pros**
- Free, open, and genuinely fast for the field (often a first decision in 4–7 months, and
  quick to appear online after acceptance).
- Prestigious and widely read across international demography — good citation potential.
- Would take a nationwide descriptive study; "Descriptive Finding" is a legitimate route
  if you keep it tight.
- No fee at all.

**Cons**
- Selective, with a meaningful desk-reject rate; the editors want a clear demographic
  contribution, not "we computed nine indices for Brazil."
- Will likely push you to foreground the **demographic** story (composition ↔ exposure,
  the North/Northeast majority-minority structure, what this implies for contact and
  cumulative disadvantage) over the methods-comparison story.
- Spatially explicit methods are welcome but not the journal's centre of gravity; a
  reviewer may want more on mechanisms and less on index taxonomy.
- Cross-sectional, no individual data — some reviewers there prefer more analytical leverage.

**Verdict.** High-value if you're willing to re-angle the framing toward demography.
Worth a pre-submission enquiry to the editors.

---

### 4. Spatial Demography (Springer)

- **Indexing / metrics.** Scopus; ESCI (not core SSCI); low/again-building impact.
  Publishes the spatial-analysis-of-population niche.
- **Scope fit.** Excellent on paper — Rey, Cortes & Knaap (2021), "Comparative Spatial
  Segregation Analytics," is in this journal, and the editorial board knows the PySAL
  `segregation` framework you use.
- **Format.** Springer LaTeX — minimal reformat.

**Pros**
- Tightest topical fit of any English journal; the reviewers will not need the PySAL
  framework explained.
- Your prior work and network are here.
- Free to publish (subscription route).

**Cons**
- Small circulation and low visibility; a paper here is read by a narrow group.
- The journal has had **irregular publication cadence** (a multi-year gap around
  2018–2021); confirm it is actively publishing and on schedule before committing.
- ESCI-only indexing means it counts less in some evaluation systems than SSCI titles.
- Little "prestige" return relative to the effort.

**Verdict.** Reasonable if topical fit and a friendly review matter more than reach.
Check the journal's current activity first.

---

### 5. Journal of Computational Social Science (Springer)

- **Indexing / metrics.** SSCI/ESCI; JCR impact factor ≈ 2–3 (young journal, rising).
  Scopus Q1/Q2.
- **Scope fit.** Computational methods and large-scale data for social science. Your
  `cortes2020` (the PySAL segregation module paper) is here.
- **Format.** Springer LaTeX — minimal reformat.

**Pros**
- The open, reproducible pipeline (package + scripts + pinned environment + one-command
  regeneration) is genuinely central to this journal's values.
- Author familiarity; the module paper's readership overlaps.
- Reasonably fast.

**Cons**
- The journal rewards **methodological or computational novelty**. This paper applies an
  existing module to a new dataset; a reviewer may judge the computational contribution
  thin, especially with inference deferred.
- The substantive racial-segregation contribution is not what this readership optimises for.
- Would likely require reframing around "a reproducible computational workflow for
  nationwide multidimensional segregation measurement," which stretches the paper.

**Verdict.** Only if you substantially expand the methods/workflow contribution.

---

### 6. Environment and Planning B: Urban Analytics and City Science (SAGE)

- **Indexing / metrics.** SSCI; JCR impact factor ≈ 3.5–4.5; Scopus Q1 (Urban Studies,
  Geography). High visibility.
- **Scope fit.** Urban analytics, spatial data science, quantitative urban research.
  Barros & Feitosa (2018), "Uneven geographies," is in EPB.
- **Format.** SAGE template; author–year. Moderate reformat.

**Pros**
- The strongest impact/visibility of the realistic options.
- "Spatial data science applied to cities" is exactly the journal's brand; the
  reproducibility angle fits.
- Urban segregation is an established EPB topic.

**Cons**
- Competitive; a high share of desk rejects. Reviewers expect novelty in *urban-analytics*
  terms — a new method, a new data source, a scale or resolution not seen before. A
  descriptive multi-city index comparison on public census aggregates may be judged
  "not novel enough for EPB."
- Leans toward big-data / computational / network-based urban work.
- OA APC is high; free route is subscription.

**Verdict.** Aim here only if you can sharpen a methodological or data novelty claim.
Higher risk, higher reward.

---

### 7. Population, Space and Place (Wiley)

- **Indexing / metrics.** SSCI; JCR impact factor ≈ 3–4; Scopus Q1 (Demography, Geography).
- **Scope fit.** Population geography — migration, mobility, life course, residential
  patterns, inequality in space.
- **Format.** Wiley template; light reformat.

**Pros**
- Demography + geography readership; segregation and residential sorting are in scope.
- Good international visibility.

**Cons**
- The journal's centre of gravity is migration / mobility / life-course, often with
  individual-level or longitudinal data. A cross-sectional, area-level, descriptive index
  study is a weaker fit than at ASAP or Demographic Research.
- Competitive; OA APC ~US$4,000.
- A reviewer may ask for analytical leverage the data cannot provide.

**Verdict.** Possible but not a natural fit; lower on the list.

---

### 8. Cadernos Metrópole (PUC-SP)

- **Indexing / metrics.** SciELO, Scopus, Redalyc, DOAJ. Qualis A1. Diamond open access.
- **Scope fit.** Urban and metropolitan studies in Brazil and Latin America. Gonçalves &
  Strauch (2026), "Segregação racial em Belo Horizonte," is here.
- **Format.** Word; Portuguese preferred (English/Spanish accepted). ABNT.

**Pros**
- Brazilian urban-studies audience, strong Qualis, no fee.
- The racialised-space and center–periphery framing is native to this journal.
- An alternative to REBEP if you want an urban-studies rather than demography home.

**Cons**
- More sociological / planning-oriented; heavy quantitative-index detail may not suit the
  readership. Reviewers will want more urban-process interpretation and historical framing,
  less methods taxonomy.
- Portuguese-dominant; similar formatting overhead to REBEP.
- Lower quantitative-methods credibility signal than a demography or spatial-analysis title.

**Verdict.** A solid Brazilian alternative if the paper leans more "urban inequality" than
"segregation measurement." Otherwise REBEP is the better Brazilian choice.

---

### 9. Caderno CRH (UFBA)

- **Indexing / metrics.** SciELO, Scopus, Redalyc. Qualis A1. Diamond open access.
- **Scope fit.** Sociology of work, urban sociology, race and inequality in Brazil. França
  (2022), "Segregação residencial por raça e classe em Fortaleza, Salvador e São Paulo,"
  is here.
- **Format.** Word; Portuguese; ABNT.

**Pros**
- Race and urban inequality are central to this journal; the political/structural framing
  is welcome.
- No fee, A1 Qualis, open access.

**Cons**
- A sociology journal — a nine-index spatial-measurement paper is methodologically
  heavier than its usual content, and reviewers will want a stronger sociological/
  theoretical contribution.
- Portuguese only; formatting overhead.
- Least methods-friendly of the Brazilian options.

**Verdict.** Only if you substantially rewrite toward a sociological argument about
racial inequality, with the indices in a supporting role.

---

### 10. EURE (Pontificia Universidad Católica de Chile)

- **Indexing / metrics.** SSCI; JCR impact factor ≈ 1–1.5; Scopus Q2 (Urban Studies).
  Diamond open access. The leading Latin American urban/regional studies journal.
- **Scope fit.** Urban and regional studies across Latin America; comparative and
  single-country. Accepts Spanish, Portuguese and English.
- **Format.** Their template; Spanish-dominant process. ABNT-like.

**Pros**
- SSCI-indexed regional journal — more international credit than a SciELO-only title.
- Latin American comparative urban framing would be welcomed if foregrounded.
- No fee, open access.

**Cons**
- Broad urban-studies readership, not a segregation-methods audience.
- Spanish-dominant editorial process; you'd likely submit and revise in Spanish or
  accept a translation step.
- Review times can be long.
- Would want the "Latin American city" narrative pushed to the front, changing the paper's
  emphasis.

**Verdict.** A regional option with SSCI indexing; middling fit for the paper as written.

---

## Also considered (briefly)

- **SN Social Sciences (Springer).** Broad social-science journal; deSousaFilho et al.
  (2022, income segregation in Brazilian cities) is here. Fast, less selective, but
  APC-funded (~US$1,700), lower prestige, "megajournal" perception. A backstop, not a
  target.
- **Regional Studies, Regional Science (Taylor & Francis).** Open, short-format, quick.
  Possible for a condensed version, but limited depth and reach.
- **Journal of Maps.** Only if reframed around the cartography, which this paper is not.

---

## Practical notes

1. **One journal at a time.** Do not submit in parallel; it is grounds for rejection at
   all of them.
2. **Two ready tracks.** The paper is already in submittable shape for the Springer
   LaTeX journals (ASAP, Spatial Demography, JCSS) with near-zero reformat. The REBEP
   track needs the `SUBMISSION.md` checklist worked through.
3. **Figure count.** REBEP and Cadernos Metrópole cap illustrations at 5; the current 8
   figures must be merged/cut for those. The Springer/SAGE/Wiley journals have no hard cap.
4. **Policy paragraph.** For ASAP (and to strengthen any submission), add an explicit
   paragraph on what a multidimensional reading implies for housing and urban policy.
5. **Pre-submission enquiry.** For Demographic Research and EPB:UACS, a short email to
   the editor with the abstract is worth the day it costs — both have high desk-reject
   rates and the reply tells you whether to invest in the reformat.
6. **If REBEP is the choice:** confirm with the IntechOpen book editors (the original
   chapter venue) that publishing this as a REBEP article is acceptable and that the
   chapter, if still going ahead, will be sufficiently different.
