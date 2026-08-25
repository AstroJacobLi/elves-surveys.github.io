# ELVES tutorial notebooks

Small, self-contained examples for working with public ELVES data products.

## Notebooks

- `01_quenched_fraction.ipynb` — select confirmed ELVES-Dwarf satellites,
  classify them with the color--magnitude quenching cut, and calculate binned
  quenched fractions with Jeffreys binomial intervals. The rendered tutorial is
  published at `/tutorials/quenched-fraction/`.

## Refreshing the website view

The website uses a checked-in, executed JupyterLab-style HTML document so an
ordinary Astro build does not require a Python or Jupyter environment. After
editing a notebook, run:

```bash
npm run render:notebooks
```

Install the pinned rendering environment first:

```bash
python3 -m pip install --requirement requirements-notebooks.txt
```

This installs nbconvert, IPython's execution kernel, NumPy, SciPy, Astropy, and
Matplotlib. SciPy is required by Astropy's Jeffreys binomial interval used in
the tutorial. The render command executes the notebook and replaces its
generated document under `public/tutorials/rendered/`; a failed cell stops the
render instead of publishing stale output.

Each notebook should:

- use only public data products;
- run without project-specific modules or private filesystem paths;
- state its sample definition and assumptions explicitly;
- keep dependencies and runtime modest;
- use a numbered filename so future tutorials have a stable order.
