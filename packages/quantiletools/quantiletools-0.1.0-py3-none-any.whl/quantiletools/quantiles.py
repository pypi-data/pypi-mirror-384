#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import numpy as np
import pandas as pd

# ======================================================
#  Custom quantile functions (Hyndman & Fan, 1996)
# ======================================================

def qtype1(x, probs):
    x = np.sort(x)
    n = len(x)
    return [x[min(int(np.ceil(n * p)) - 1, n - 1)] for p in probs]

def qtype2(x, probs):
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        j = n * p
        if j.is_integer() and j > 0:
            j = int(j)
            val = (x[j - 1] + x[min(j, n - 1)]) / 2
        else:
            val = x[min(int(np.ceil(j)) - 1, n - 1)]
        out.append(val)
    return out

def qtype3(x, probs):
    x = np.sort(x)
    n = len(x)
    return [x[min(max(int(round(n * p)) - 1, 0), n - 1)] for p in probs]

def qtype4(x, probs):
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        h = n * p
        j = int(np.floor(h))
        g = h - j
        if j <= 0:
            val = x[0]
        elif j >= n:
            val = x[-1]
        else:
            val = (1 - g) * x[j - 1] + g * x[j]
        out.append(val)
    return out

def qtype5(x, probs):
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        h = n * p + 0.5
        j = int(np.floor(h))
        g = h - j
        j = min(max(j, 1), n)
        if j == n:
            val = x[-1]
        else:
            val = (1 - g) * x[j - 1] + g * x[j]
        out.append(val)
    return out

def qtype6(x, probs):
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        h = (n + 1) * p
        j = int(np.floor(h))
        g = h - j
        if j <= 0:
            val = x[0]
        elif j >= n:
            val = x[-1]
        else:
            val = (1 - g) * x[j - 1] + g * x[j]
        out.append(val)
    return out

def qtype7(x, probs):
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        h = 1 + (n - 1) * p
        j = int(np.floor(h))
        g = h - j
        if j >= n:
            val = x[-1]
        else:
            val = (1 - g) * x[j - 1] + g * x[j]
        out.append(val)
    return out

def qtype8(x, probs):
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        h = (n + 1/3) * p + 1/3
        j = int(np.floor(h))
        g = h - j
        if j <= 0:
            val = x[0]
        elif j >= n:
            val = x[-1]
        else:
            val = (1 - g) * x[j - 1] + g * x[j]
        out.append(val)
    return out

def qtype9(x, probs):
    x = np.sort(x)
    n = len(x)
    out = []
    for p in probs:
        h = (n + 0.25) * p + 3/8
        j = int(np.floor(h))
        g = h - j
        if j <= 0:
            val = x[0]
        elif j >= n:
            val = x[-1]
        else:
            val = (1 - g) * x[j - 1] + g * x[j]
        out.append(val)
    return out


# ======================================================
#  Master function: compute all 9 types
# ======================================================

def all_qtypes_custom(x, probs, decimals=9):
    funcs = [qtype1, qtype2, qtype3, qtype4, qtype5,
             qtype6, qtype7, qtype8, qtype9]
    
    res = np.array([func(x, probs) for func in funcs])
    res = np.round(res, decimals)
    
    df = pd.DataFrame(res,
                      index=[f"Type{i}" for i in range(1, 10)],
                      columns=[f"{int(p*100)}%" for p in probs])
    return df


# ======================================================
#  (a) Run Core function — single vector, one type
# ======================================================
def quantile_custom(x, probs, qtype=7):
    """
    Compute quantiles using custom Hyndman & Fan (1996) implementations (Types 1–9).

    Parameters:
        x (array-like): Input data.
        probs (float or list of floats): Probabilities in [0, 1].
        qtype (int, list of ints, or 'all'): Which quantile type(s) to compute.

    Returns:
        pandas.Series or pandas.DataFrame
    """
    x = np.asarray(x)
    probs = np.atleast_1d(probs)

    # Mapping from type number to custom function
    custom_funcs = {
        1: qtype1, 2: qtype2, 3: qtype3,
        4: qtype4, 5: qtype5, 6: qtype6,
        7: qtype7, 8: qtype8, 9: qtype9
    }

    if qtype == "all":
        out = {
            f"Type{qt}": custom_funcs[qt](x, probs)
            for qt in range(1, 10)
        }
        return pd.DataFrame(out, index=probs)

    elif isinstance(qtype, list):
        out = {
            f"Type{qt}": custom_funcs[qt](x, probs)
            for qt in qtype
        }
        return pd.DataFrame(out, index=probs)

    else:
        return pd.Series(custom_funcs[qtype](x, probs), index=probs)


# def quantile_custom(x, probs, qtype=7):
#     """
#     Compute quantiles for a 1D array using Hyndman & Fan (1996) definitions.
#
#     Parameters
#     ----------
#     x : array-like
#         Input numeric data.
#     probs : float or list of floats
#         Probabilities between 0 and 1.
#     qtype : int, list of ints, or 'all', default=7
#         Quantile type(s) (1–9) or 'all' to compute all nine.
#
#     Returns
#     -------
#     pandas.Series or pandas.DataFrame
#     """
#     x = np.asarray(x)
#     mapping = {
#         1: "inverted_cdf", 2: "averaged_inverted_cdf", 3: "closest_observation",
#         4: "interpolated_inverted_cdf", 5: "hazen", 6: "weibull",
#         7: "linear", 8: "median_unbiased", 9: "normal_unbiased"
#     }
#
#     if qtype == "all":
#         out = {
#             f"Type{i + 1}": np.quantile(x, probs, method=m)
#             for i, m in enumerate(mapping.values())
#         }
#         return pd.DataFrame(out, index=np.atleast_1d(probs))
#
#     elif isinstance(qtype, list):
#         out = {}
#         for q in qtype:
#             method = mapping.get(q, "linear")
#             out[f"Type{q}"] = np.quantile(x, probs, method=method)
#         return pd.DataFrame(out, index=np.atleast_1d(probs))
#
#     else:
#         method = mapping.get(qtype, "linear")
#         return pd.Series(np.quantile(x, probs, method=method), index=np.atleast_1d(probs))
#
#
# ======================================================
#(b) Dataset-level function — multiple variables
# ======================================================
def quantiles_for_vars(df, vars, probs=[0.05, 0.5, 0.9], qtype="all"):
    results = []
    for v in vars:
        x = df[v].dropna()
        res = quantile_custom(x, probs, qtype)
        if isinstance(res, pd.Series):
            res = res.to_frame().T
        res.insert(0, "Variable", v)
        results.append(res)
    return pd.concat(results, ignore_index=True)
# ======================================================
#(b) (c) Group-level function
# ======================================================
def quantiles_by_group(df, group_var, num_vars, probs=[0.05, 0.5, 0.9], qtype="all"):
    results = []
    for grp, sub in df.groupby(group_var):
        temp = quantiles_for_vars(sub, num_vars, probs, qtype)
        temp.insert(1, group_var, grp)
        results.append(temp)
    return pd.concat(results, ignore_index=True)

# ======================================================
#  Example usage
# ======================================================
def main():
    import pandas as pd
    import numpy as np

    np.random.seed(42)

    df = pd.DataFrame({
        "X1": np.random.randn(10),
        "X2": np.random.randn(10),
        "X3": np.random.randn(10),
        "Group": np.random.choice(["A", "B"], size=10)
    })

    r1=quantiles_for_vars(df, ["X1"], probs=[0.1,0.5,0.9], qtype=[1,7])
    r2=quantiles_for_vars(df, ["X2","X3"], probs=[0.1,0.5,0.9], qtype=[1,7])
    r3=quantiles_by_group(df, "Group", ["X1","X3"], probs=[0.1,0.5,0.9], qtype="all")

    print("output 1: Percentiles for Chosen Columns and Types")
    print(r1)
    print("output 2: Percentiles for Chosen Columns and Types")
    print(r2)
    print("output 3: Group wisePercentiles for Chosen Columns and Types")
    print(r3)

if __name__ == "__main__":
    main()
