import numpy as np

def ScoS(y_true, y_pred, method="linear", factor=1):
    """

    Compute Scolz's Score (ScoS) between true and predicted values.

    The score measures the distance between predicted and true classes,
    considering their logical order (ex. No effect, Low effect, High effect). Different weighting methods can be
    applied to penalize errors more or less severely.

    Parameters
    ----------
    y_true : array-like
        True values (list, NumPy array, Pandas Series, etc.).
    y_pred : array-like
        Predicted values (same length as y_true).
    method : str, default="linear"
        Weighting method for errors. Options:
        - "linear"    : absolute difference
        - "quadratic" : squared difference, penalizes large errors
        - "sqrt"      : square root of difference, reduces impact of large errors
        - "custom"    : difference raised to `factor`
    factor : float, default=1
        Exponent used if `method="custom"`. Controls how strongly
        large errors are penalized (higher factor → stronger penalty).


    Returns
    -------
    score : float
        Normalized score in [0, 1], where:
        - 1.0 = perfect prediction (no error)
        - 0.0 = worst-case prediction


    Examples
    --------
    >>> from databoost.metrics import ScoS
    >>> y_true = [1, 1, 2]   # e.g. Low effect, Low effect, High effect
    >>> y_pred = [0, 2, 2]   # e.g. No effect, High effect, High effect
    >>> ScoS(y_true, y_pred, method="quadratic")
    0.7278...

    """

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    pred_range = len(np.unique(np.concatenate([y_true, y_pred])))

    if pred_range == 0:
        return 1
    
    diff = np.abs(y_true - y_pred)

    if method == "linear":
        weighted = diff
        factor = 1
    elif method == "quadratic":
        weighted = diff**2
        factor = 2
    elif method == "sqrt":
        weighted = diff**0.5
        factor = 0.5
    elif method == "custom":
        weighted = diff**factor
    else:
        raise ValueError(f'Method "{method}" is not supported, please choose between "linear", "quadratic", "sqrt" or "custom"')
    
    score = weighted.mean()

    normalized_score = score ** (1/factor) / pred_range

    goodness_score = 1 - normalized_score
    
    return goodness_score # from 0 (worst fit) to 1 (perfect fit)
