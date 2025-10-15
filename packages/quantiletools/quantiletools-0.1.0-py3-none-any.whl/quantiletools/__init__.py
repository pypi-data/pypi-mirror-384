#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# quantiletools/__init__.py
from .quantiles import (
    quantile_custom,
    quantiles_for_vars,
    quantiles_by_group
)

__all__ = [
    "quantile_custom",
    "quantiles_for_vars",
    "quantiles_by_group"
]

