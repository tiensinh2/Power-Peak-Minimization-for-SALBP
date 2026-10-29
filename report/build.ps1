$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
    if ($LASTEXITCODE -ne 0) { throw "pdflatex failed with exit code $LASTEXITCODE" }
    bibtex manuscript
    if ($LASTEXITCODE -ne 0) { throw "bibtex failed with exit code $LASTEXITCODE" }
    pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
    if ($LASTEXITCODE -ne 0) { throw "pdflatex (bibliography pass) failed with exit code $LASTEXITCODE" }
    pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
    if ($LASTEXITCODE -ne 0) { throw "pdflatex (final pass) failed with exit code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
