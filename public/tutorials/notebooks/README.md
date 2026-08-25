# ELVES tutorial notebooks

Small, self-contained examples for working with public ELVES data products.

## Notebooks

- `01_quenched_fraction.ipynb` — select confirmed ELVES-Dwarf satellites,
  classify them with the color--magnitude quenching cut, and calculate binned
  quenched fractions with Jeffreys binomial intervals. The rendered tutorial is
  published at `/tutorials/quenched-fraction/`.

## Refreshing the website view

The website uses a checked-in, executed HTML fragment so an ordinary Astro build
does not require a Python or Jupyter environment. After editing a notebook, run:

```bash
npm run render:notebooks
```

This requires Jupyter, NumPy, Astropy, and Matplotlib. The command executes the
notebook and replaces its fragment under `public/tutorials/rendered/`; a failed
cell stops the render instead of publishing stale output.

Each notebook should:

- use only public data products;
- run without project-specific modules or private filesystem paths;
- state its sample definition and assumptions explicitly;
- keep dependencies and runtime modest;
- use a numbered filename so future tutorials have a stable order.
