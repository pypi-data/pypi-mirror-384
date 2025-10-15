# quantiletools

`quantiletools` is a Python package that implements the 9 quantile types defined in Hyndman & Fan (1996), with pure Python logic and no dependency on NumPy's `np.quantile()` methods.

---

## 🚀 Features

- Implements Types 1–9 from Hyndman & Fan (1996)
- No reliance on `np.quantile(method=...)`
- Dataset-level and group-level quantile summaries
- Fully vectorized for performance

---

## 📦 Installation

If downloaded locally:

```bash
pip install .

## 📚 Example Usage

```python
# Import from package 
from quantiletools import quantiles_for_vars, quantiles_by_group

# Example DataFrame
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "X1": np.random.randn(10),
    "X2": np.random.randn(10),
    "Group": np.random.choice(["A", "B"], size=10)
})

# Compute quantiles
quantiles_for_vars(df, ["X1", "X2"], probs=[0.1, 0.5, 0.9], qtype=[1, 7])

