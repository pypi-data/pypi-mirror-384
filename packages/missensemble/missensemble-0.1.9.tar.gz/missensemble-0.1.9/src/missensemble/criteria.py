# convergence criteria
import pandas as pd


# criterion for numerical variables
def calc_num_criterion(
    new_data: pd.DataFrame,
    old_data: pd.DataFrame,
    nas: pd.DataFrame,
    vars: list[str] = [],
) -> float:
    """
    Calculate the numerical convergence criterion for imputation.

    This function computes the relative change in imputed values for numerical variables
    between two consecutive iterations. It calculates the sum of squared differences
    between the new and old imputed values (for missing entries only), normalized by
    the sum of squares of the new imputed values. A lower value indicates better convergence.

    Parameters
    ----------
    new_data : pd.DataFrame
        DataFrame containing the newly imputed data.
    old_data : pd.DataFrame
        DataFrame containing the data from the previous iteration.
    nas : pd.DataFrame
        DataFrame indicating the locations of missing values.
    vars : list of str, optional
        List of numerical variable names to check.

    Returns
    -------
    float
        The numerical convergence criterion value.
    """

    sum_squared_diff = sum(
        ((new_data[nas[vars]][vars] - old_data[nas[vars]][vars]) ** 2).sum()
    )
    sum_squared_new = sum((new_data[nas[vars]][vars] ** 2).sum())
    num_criterion = sum_squared_diff / sum_squared_new
    return num_criterion


def calc_cat_ord_criterion(
    new_data: pd.DataFrame,
    old_data: pd.DataFrame,
    nas: pd.DataFrame,
    vars: list[str] = [],
) -> float:
    """
    Calculate the categorical or ordinal convergence criterion for imputation.

    This function measures the proportion of changed imputed values for categorical or
    ordinal variables between two consecutive iterations. It counts the number of entries
    where the imputed value has changed for missing entries, and normalizes by the total
    number of missing values. A lower value indicates better convergence.

    Parameters
    ----------
    new_data : pd.DataFrame
        DataFrame containing the newly imputed data.
    old_data : pd.DataFrame
        DataFrame containing the data from the previous iteration.
    nas : pd.DataFrame
        DataFrame indicating the locations of missing values.
    vars : list of str, optional
        List of categorical or ordinal variable names to check.

    Returns
    -------
    float
        The categorical/ordinal convergence criterion value.
    """

    matches_cat = []
    for col in vars:
        matches_cat.append(
            sum(new_data[nas][col].dropna() != old_data[nas][col].dropna())
        )
    return sum(matches_cat) / sum(nas.sum())


def stopping_rule(
    criterion_cat: list[float], criterion_num: list[float], tol: float
) -> bool:
    """
    Determine whether the stopping rule for convergence is met.

    This function checks if the convergence criteria for numerical and/or categorical/ordinal
    variables indicate that the imputation process should stop. It returns True if either:
    - The criterion increases (indicating no further improvement), or
    - The last three values of the criterion are within the specified tolerance (indicating stability).
    The function works for cases where only one type of variable is present, or both.

    Parameters
    ----------
    criterion_cat : list of float
        List of categorical/ordinal criterion values over iterations.
    criterion_num : list of float
        List of numerical criterion values over iterations.
    tol : float
        Tolerance threshold for convergence.

    Returns
    -------
    bool
        True if the stopping rule is met, False otherwise.
    """

    if not criterion_cat:
        if (criterion_num[-1] > criterion_num[-2]) or tolerance_check(
            criterion_num, tol
        ):
            return True
    elif not criterion_num:
        if (criterion_cat[-1] > criterion_cat[-2]) or tolerance_check(
            criterion_cat, tol
        ):
            return True
    elif (
        (criterion_cat[-1] > criterion_cat[-2])
        and (criterion_num[-1] > criterion_num[-2])
    ) or (
        tolerance_check(criterion_num, tol) or tolerance_check(criterion_cat, tol)
    ):  # the second or is crucial
        return True


def tolerance_check(criterion: list[float], tol: float) -> bool:
    """
    Check if the last three values of the criterion are within a specified tolerance.

    This function checks if the absolute difference between the last three consecutive
    values of a convergence criterion are all less than the specified tolerance. This
    indicates that the imputation process has stabilized and further iterations are
    unlikely to improve the result.

    Parameters
    ----------
    criterion : list of float
        List of criterion values over iterations.
    tol : float
        Tolerance threshold for convergence.

    Returns
    -------
    bool
        True if the last three values are within tolerance, False otherwise.
    """

    if len(criterion) >= 3:
        last_three = criterion[-3:]
        if (abs(last_three[-1] - last_three[-2]) < tol) and (
            abs(last_three[-2] - last_three[-3]) < tol
        ):
            return True
        else:
            return False
    else:
        return False
