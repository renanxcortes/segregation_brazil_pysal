"""Build manuscript.docx for REBEP submission from manuscript.tex.

REBEP accepts Word files only. This script:
  1. Inlines every \\input{...} table (pandoc does not expand \\input),
     stripping \\resizebox wrappers that pandoc cannot parse.
  2. Runs pandoc with citeproc + the ABNT CSL style so in-text citations
     and the reference list follow ABNT NBR 10520 / NBR 6023.
  3. Applies the REBEP formatting (double spacing, Times New Roman 12pt)
     via a reference .docx template.
  4. Strips identifying document metadata (author, etc.) for blind review.

Usage (from draft/rebep/):
    python build_docx.py
"""
import io
import re
import subprocess
import sys
import zipfile
import shutil
from pathlib import Path

HERE = Path(__file__).parent
MANUSCRIPT = HERE / "manuscript.tex"
FLAT = HERE / "_manuscript_flat.tex"
TABLES_DIR = HERE / ".." / ".." / "outputs" / "tables"
OUT_DOCX = HERE / "manuscript.docx"
REF_DOCX = HERE / "_reference.docx"
CSL = HERE / "abnt.csl"
BIB = HERE / "references.bib"

INPUT_RE = re.compile(r"\\input\{([^}]+)\}")


def strip_resizebox(tex: str) -> str:
    """Remove \\resizebox{\\textwidth}{!}{ ... } wrappers pandoc cannot parse,
    keeping the wrapped tabular content."""
    tex = tex.replace("\\resizebox{\\textwidth}{!}{%\n", "")
    tex = tex.replace("\\resizebox{\\textwidth}{!}{%", "")
    # remove the matching lone closing brace line and the stray '%' left
    # before \end{tabular}
    tex = tex.replace("\\end{tabular}%\n}\n", "\\end{tabular}\n")
    tex = tex.replace("\\end{tabular}%\n}", "\\end{tabular}")
    return tex


def flatten(tex_path: Path) -> str:
    text = tex_path.read_text(encoding="utf-8")

    def repl(m):
        rel = m.group(1)
        candidate = (HERE / rel).resolve()
        content = candidate.read_text(encoding="utf-8")
        return strip_resizebox(content)

    return INPUT_RE.sub(repl, text)


def make_reference_docx():
    """Reference docx pandoc uses for base styles: Times New Roman 12pt,
    double spacing. Pandoc's default docDefaults already sets 12pt
    (w:sz 24 half-points); we only need to swap the theme font for an
    explicit Times New Roman and add double line spacing."""
    tmp = HERE / "_refdocx_extract"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    base = subprocess.run(
        ["pandoc", "--print-default-data-file=reference.docx"],
        check=True, capture_output=True,
    ).stdout
    with zipfile.ZipFile(io.BytesIO(base)) as z:
        z.extractall(tmp)

    styles_path = tmp / "word" / "styles.xml"
    styles = styles_path.read_text(encoding="utf-8")

    times_roman = (
        '<w:rFonts w:ascii="Times New Roman" w:eastAsia="Times New Roman" '
        'w:hAnsi="Times New Roman" w:cs="Times New Roman" />'
    )
    styles = re.sub(
        r'<w:rFonts w:asciiTheme="minorHAnsi"[^/]*/>',
        times_roman,
        styles,
    )
    styles = styles.replace(
        '<w:pPrDefault>\n      <w:pPr>\n        <w:spacing w:after="200" />\n      </w:pPr>\n    </w:pPrDefault>',
        '<w:pPrDefault>\n      <w:pPr>\n        <w:spacing w:after="200" w:line="480" w:lineRule="auto" />\n      </w:pPr>\n    </w:pPrDefault>',
    )
    styles_path.write_text(styles, encoding="utf-8")

    if REF_DOCX.exists():
        REF_DOCX.unlink()
    with zipfile.ZipFile(REF_DOCX, "w", zipfile.ZIP_DEFLATED) as z:
        for f in tmp.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(tmp))
    shutil.rmtree(tmp)


def strip_docx_metadata(docx_path: Path):
    tmp = HERE / "_out_extract"
    if tmp.exists():
        shutil.rmtree(tmp)
    with zipfile.ZipFile(docx_path) as z:
        z.extractall(tmp)
    core = tmp / "docProps" / "core.xml"
    if core.exists():
        text = core.read_text(encoding="utf-8")
        for tag in ["dc:creator", "cp:lastModifiedBy", "dc:description", "dc:subject"]:
            text = re.sub(rf"<{tag}>.*?</{tag}>", f"<{tag}></{tag}>", text, flags=re.S)
        core.write_text(text, encoding="utf-8")
    app = tmp / "docProps" / "app.xml"
    if app.exists():
        text = app.read_text(encoding="utf-8")
        text = re.sub(r"<Company>.*?</Company>", "<Company></Company>", text, flags=re.S)
        app.write_text(text, encoding="utf-8")
    if docx_path.exists():
        docx_path.unlink()
    with zipfile.ZipFile(docx_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in tmp.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(tmp))
    shutil.rmtree(tmp)


def main():
    FLAT.write_text(flatten(MANUSCRIPT), encoding="utf-8")
    make_reference_docx()
    subprocess.run(
        [
            "pandoc",
            str(FLAT),
            "-f", "latex",
            "-t", "docx",
            "--citeproc",
            f"--bibliography={BIB}",
            f"--csl={CSL}",
            f"--reference-doc={REF_DOCX}",
            "--resource-path", f".:{HERE / '..' / '..' / 'figures'}",
            "-o", str(OUT_DOCX),
        ],
        check=True,
        cwd=HERE,
    )
    strip_docx_metadata(OUT_DOCX)
    FLAT.unlink()
    print(f"Wrote {OUT_DOCX}")


if __name__ == "__main__":
    sys.exit(main())
