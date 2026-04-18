# ESORICS 2026 LNCS LaTeX Package

This directory contains a Springer `LNCS` LaTeX draft for the current manuscript.

## Official format basis

- ESORICS 2026 official CFP: `https://sites.google.com/di.uniroma1.it/esorics2026/call-for/papers`
- Springer proceedings author page: `https://www.springer.com/gp/computer-science/lncs/conference-proceedings-guidelines`

Key constraints confirmed from the official pages on `2026-04-18`:

- use the official `LNCS` template;
- do not modify the original template margins;
- submitted papers must be at most `16` pages, excluding bibliography and well-marked appendices;
- total submission length must be at most `20` pages;
- submission format is PDF;
- review is single-blind.

## Files

- `main.tex`: LNCS manuscript source derived from `paper/main.md`
- `main.pdf`: compiled PDF
- `template/`: official Springer download bundle
- `springer_computer_proceedings_author_instructions.pdf`: official author instructions PDF
- `figures/`: local copies of figure assets used by the LaTeX build

## Build

```bash
cd paper/latex
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

## Notes

- The current draft author block is `Wenzhang Du, Independent Researcher`.
- Add a corresponding contact email if the submission venue requires one.
