import pandas as pd
import numpy as np

def uni_emp(X, method='Gringorten') -> pd.Series:
    """
    Compute the univariate empirical cumulative distribution function (CDF).

    Parameters
    ----------
    X : pd.Series or array-like
        1D input data (e.g., precipitation, temperature).
    method : str, default='Gringorten'
        Plotting position formula to use. Options:
        - 'Gringorten' : recommended for hydrology
        - 'Weibull'    : standard Weibull formula

    Returns
    -------
    pd.Series
        Empirical CDF values corresponding to input data, preserving the original index.

    Notes
    -----
    Empirical CDF is computed by ranking each value and applying the plotting position formula.

    References
    ----------
    Gringorten, I. I. (1963). A plotting rule for extreme probability paper.
    Journal of Geophysical Research, 68(3), 813–814.

    Weibull, W. (1939). A statistical distribution function of wide applicability.
    Journal of Applied Mechanics, 18, 293–297.
    """
    if not isinstance(X, pd.Series):
        X = pd.Series(X)
    
    X = X.dropna()
    n = len(X)
    
    S = X.apply(lambda xi: (X <= xi).sum())

    if method == 'Gringorten':
        cdf = (S - 0.44) / (n + 0.12)
    elif method == 'Weibull':
        cdf = S / (n + 1)
    else:
        raise ValueError("method must be 'Gringorten' or 'Weibull'")

    return pd.Series(cdf.values, index=X.index)

def accu(X, ts):
    """
    Compute accumulated or averaged values over a specified time scale.

    Parameters
    ----------
    X : pd.Series or array-like
        Input 1D data (e.g., monthly precipitation or temperature).
    ts : int
        Time scale for accumulation (e.g., 3 for a 3-month accumulation).

    Returns
    -------
    pd.Series
        Accumulated/averaged values with NaNs for initial positions where insufficient data exists.

    Notes
    -----
    This function uses rolling slices to compute the mean of `ts` consecutive values.
    Useful for creating time-scaled indices such as SPI or SPEI.
    """
    if isinstance(X, pd.Series):
        index = X.index
        X_values = X.values
    else:
        X_values = np.asarray(X).flatten()
        index = pd.RangeIndex(len(X_values))

    if ts < 1:
        raise ValueError("Time scale (ts) must be a positive integer.")
    if len(X_values) < ts:
        raise ValueError("Length of input data must be >= time scale.")

    slices = [X_values[i:len(X_values) - ts + i + 1] for i in range(ts)]
    stacked = np.stack(slices, axis=1)

    averaged = stacked.mean(axis=1)

    valid_index = index[ts-1:]

    return pd.Series(averaged, index=valid_index, name=getattr(X, 'name', None))

def multi_emp(X, Y, method='Gringorten') -> pd.Series:
    """
    Compute joint empirical probabilities for bivariate data using a plotting position formula.

    Parameters
    ----------
    X : pd.Series or array-like
        First variable.
    Y : pd.Series or array-like
        Second variable.
    method : str, default='Gringorten'
        Plotting position formula. Options: 'Gringorten', 'Weibull'.

    Returns
    -------
    pd.Series
        Joint empirical probabilities, indexed like X.
        
    Notes
    -----
    Joint empirical probability is calculated as the proportion of observations
    less than or equal to both X_i and Y_i. Useful for multivariate analyses.
    """
    X = pd.Series(X) if not isinstance(X, pd.Series) else X
    Y = pd.Series(Y) if not isinstance(Y, pd.Series) else Y

    df = pd.concat([X, Y], axis=1).dropna()
    X, Y = df.iloc[:, 0], df.iloc[:, 1]

    n = len(X)
    S = np.empty(n)

    for k in range(n):
        count = np.sum((X <= X.iloc[k]) & (Y <= Y.iloc[k]))
        if method == 'Gringorten':
            S[k] = (count - 0.44) / (n + 0.12)
        elif method == 'Weibull':
            S[k] = count / (n + 1)
        else:
            raise ValueError("method must be 'Gringorten' or 'Weibull'")

    return pd.Series(S, index=X.index)
