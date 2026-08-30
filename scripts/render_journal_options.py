"""Markdown -> LaTeX (xelatex) converter for draft/journal-options.md.

Handles the subset of Markdown that file uses: ATX headings, `---` rules,
`>` blockquotes, pipe tables, `-`/`1.` lists (with soft-wrapped items),
**bold**, *italic*, `code`, and a handful of unicode glyphs.

Usage:
    python scripts/render_journal_options.py draft/journal-options.md out.tex
    cd <dir of out.tex> && xelatex out.tex && xelatex out.tex
    # then copy the resulting PDF to draft/journal-options.pdf
"""
import re
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
raw = open(SRC, encoding="utf-8").read().splitlines()

PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage{fontspec}
\usepackage[a4paper,margin=1.9cm]{geometry}
\usepackage{longtable}
\usepackage{array}
\usepackage{booktabs}
\usepackage{enumitem}
\usepackage{pifont}
\usepackage[hidelinks]{hyperref}
\setmainfont{Latin Modern Roman}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt plus 1.5pt minus 1pt}
\newcommand{\rulesep}{\par\vspace{2pt}\noindent\hrulefill\par\vspace{4pt}}
\setlist{nosep,leftmargin=1.3em,topsep=2pt,parsep=2pt,itemsep=2pt}
\renewcommand{\arraystretch}{1.2}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\raggedbottom
\begin{document}
\sloppy
"""
POST = "\\end{document}\n"

GLYPHS = [("\u2605", r"\ding{72}"), ("\u00bd", r"\textonehalf "),
          ("\u2192", r"$\rightarrow$"), ("\u2194", r"$\leftrightarrow$"),
          ("\u2248", r"$\approx$"), ("\u2264", r"$\leq$"),
          ("\u2265", r"$\geq$"), ("\u00d7", r"$\times$"),
          ("\u2014", "---"), ("\u2013", "--"), ("\u2026", r"\ldots "),
          ("\u201c", "``"), ("\u201d", "''"), ("\u2018", "`"),
          ("\u2019", "'"), ("\u00a0", "\\,")]


def esc(s):
    raw_tokens = []

    def stash(text):
        raw_tokens.append(text)
        return f"\x00{len(raw_tokens)-1}\x00"

    s = re.sub(r"`([^`]+)`", lambda m: stash(
        r"\texttt{" + m.group(1).replace("\\", r"\textbackslash{}")
        .replace("_", r"\_").replace("&", r"\&").replace("%", r"\%")
        .replace("$", r"\$").replace("#", r"\#").replace("{", r"\{")
        .replace("}", r"\}") + "}"), s)
    s = s.replace("~", stash(r"\textasciitilde{}"))
    s = s.replace("^", stash(r"\textasciicircum{}"))
    # escape remaining LaTeX specials
    s = (s.replace("\\", r"\textbackslash{}").replace("{", r"\{")
         .replace("}", r"\}").replace("&", r"\&").replace("%", r"\%")
         .replace("$", r"\$").replace("#", r"\#").replace("_", r"\_"))
    for a, b in GLYPHS:
        s = s.replace(a, b)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"\*([^*]+)\*", r"\\emph{\1}", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: raw_tokens[int(m.group(1))], s)


def is_block_start(ln):
    st = ln.lstrip()
    return (st.startswith(("#", "|", ">"))
            or re.match(r"^(-|\*|\d+\.)\s", st)
            or re.match(r"^-{3,}\s*$", st))


# --- pass 1: unwrap soft line breaks (join wrapped paragraph/list lines) ---
lines = []
for ln in raw:
    if (lines and ln.strip() and lines[-1].strip()
            and not is_block_start(ln)
            and not is_block_start(lines[-1])
            and not lines[-1].lstrip().startswith("|")):
        lines[-1] = lines[-1].rstrip() + " " + ln.strip()
    elif (lines and ln.strip() and lines[-1].strip()
          and re.match(r"^(-|\*|\d+\.)\s", lines[-1].lstrip())
          and ln.startswith("  ") and not is_block_start(ln)):
        lines[-1] = lines[-1].rstrip() + " " + ln.strip()
    else:
        lines.append(ln)

# --- pass 2: emit LaTeX ---
out = [PREAMBLE]
i, n = 0, len(lines)
in_list = None


def close_list():
    global in_list
    if in_list:
        out.append(r"\end{itemize}" if in_list == "ul" else r"\end{enumerate}")
        in_list = None


while i < n:
    ln = lines[i]

    if (ln.lstrip().startswith("|") and i + 1 < n
            and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1])
            and "-" in lines[i + 1]):
        close_list()
        header = [c.strip() for c in ln.strip().strip("|").split("|")]
        ncol = len(header)
        body = []
        i += 2
        while i < n and lines[i].lstrip().startswith("|"):
            body.append([c.strip() for c in
                         lines[i].strip().strip("|").split("|")])
            i += 1
        if ncol <= 3:
            w = [r"L{0.28\textwidth}"] + \
                [f"L{{{0.64/(ncol-1):.3f}\\textwidth}}"] * (ncol - 1)
            size = r"\footnotesize"
        elif ncol <= 5:
            w = [f"L{{{0.92/ncol:.3f}\\textwidth}}"] * ncol
            size = r"\footnotesize"
        else:
            first = 0.135
            rest = (0.86 - first) / (ncol - 1)
            w = [f"L{{{first:.3f}\\textwidth}}"] + \
                [f"L{{{rest:.3f}\\textwidth}}"] * (ncol - 1)
            size = r"\scriptsize"
        out.append(r"\begingroup" + size)
        out.append(r"\begin{longtable}{" + "".join(w) + "}")
        out.append(r"\toprule")
        out.append(" & ".join(r"\textbf{" + esc(h) + "}" for h in header)
                   + r" \\")
        out.append(r"\midrule\endhead")
        for r_ in body:
            r_ = (r_ + [""] * ncol)[:ncol]
            out.append(" & ".join(esc(c) for c in r_) + r" \\[2pt]")
        out.append(r"\bottomrule")
        out.append(r"\end{longtable}\endgroup")
        continue

    m = re.match(r"^(#{1,4})\s+(.*)$", ln)
    if m:
        close_list()
        cmd = {1: r"\section*", 2: r"\subsection*",
               3: r"\subsubsection*", 4: r"\paragraph*"}[len(m.group(1))]
        out.append(cmd + "{" + esc(m.group(2)) + "}")
        i += 1
        continue

    if re.match(r"^\s*-{3,}\s*$", ln):
        close_list()
        out.append(r"\rulesep")
        i += 1
        continue

    if ln.startswith(">"):
        close_list()
        buf = []
        while i < n and lines[i].startswith(">"):
            buf.append(lines[i].lstrip(">").strip())
            i += 1
        out.append(r"\begin{quote}\itshape " +
                   esc(" ".join(x for x in buf if x)) + r"\end{quote}")
        continue

    m = re.match(r"^\s*[-*]\s+(.*)$", ln)
    if m:
        if in_list != "ul":
            close_list()
            out.append(r"\begin{itemize}")
            in_list = "ul"
        out.append(r"\item " + esc(m.group(1)))
        i += 1
        continue

    m = re.match(r"^\s*\d+\.\s+(.*)$", ln)
    if m:
        if in_list != "ol":
            close_list()
            out.append(r"\begin{enumerate}")
            in_list = "ol"
        out.append(r"\item " + esc(m.group(1)))
        i += 1
        continue

    if ln.strip() == "":
        close_list()
        out.append("")
        i += 1
        continue

    close_list()
    out.append(esc(ln))
    i += 1

close_list()
out.append(POST)
open(OUT, "w", encoding="utf-8").write("\n".join(out))
print("wrote", OUT)
