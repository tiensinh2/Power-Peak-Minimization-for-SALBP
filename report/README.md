# Report workspace

The report uses the same Elsevier CAS single-column format as the N-Queens project and the course requirement: `\documentclass[a4paper,fleqn]{cas-sc}`. The project includes the CAS class, shared style file, numbered-author bibliography style, and front-matter thumbnail assets needed to build the manuscript. `manuscript.tex` is a clean SALB3PM outline; replace the marked author and content placeholders as the project develops.

## Build on Windows

Install a LaTeX distribution such as MiKTeX and ensure `pdflatex` and `bibtex` are available in `PATH`. From this `report/` directory:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
bibtex manuscript
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
```

Or from the project root, run `./report/build.ps1`. The final PDF is `report/manuscript.pdf`. LaTeX auxiliary files and the generated PDF are ignored by Git; commit the `.tex`, `.bib`, required style files and any final figures the group wants to preserve.

## Layout and working notes

The starter follows the existing project report's article flow: title/authors/affiliation, abstract, keywords, introduction, problem definition, related work, proposed SAT/MaxSAT models, exact baselines, experimental setup, results, discussion/conclusion, declarations, and references. Author names, emails, institution, and repository URL are explicit placeholders; replace them before submission. The manuscript makes no experimental claims. Fill results sections only when implementation and measurements support them.

Put report figures in `report/figures/` and keep the source data/scripts under `results/` and `src/`. Use PDF or PNG figures with `pdflatex`; do not point the manuscript at untracked machine-local paths. Add the repository URL to the Data Availability statement before submission.

`cas-sc.cls`, `cas-common.sty`, `cas-model2-names.bst`, and the required CAS thumbnail assets were copied from the Elsevier CAS bundle already used by the N-Queens project. The class files retain their upstream license notices. They are included as build dependencies; no N-Queens manuscript text, data, or figures were copied.
