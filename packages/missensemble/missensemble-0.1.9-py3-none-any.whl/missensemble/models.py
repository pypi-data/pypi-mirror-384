from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from xgboost import XGBClassifier, XGBRegressor


def initialize_model(
    model_type: str, is_numeric: bool, **kwargs
) -> RandomForestClassifier | RandomForestRegressor | XGBClassifier | XGBRegressor:
    """
    Initialize and return an ensemble model for imputation.

    Parameters
    ----------
    model_type : str
        The type of ensemble model to use. Options are 'forest' (Random Forest) or 'xgboost' (XGBoost).
    is_numeric : bool
        If True, returns a regressor for numerical variables. If False, returns a classifier for categorical/ordinal variables.
    **kwargs
        Additional keyword arguments passed to the model constructor (e.g., n_estimators, random_state).

    Returns
    -------
    object
        An instance of the selected ensemble model (regressor or classifier).
    """
    if model_type == "forest":
        model = (
            RandomForestRegressor(**kwargs)
            if is_numeric
            else RandomForestClassifier(**kwargs)
        )

    elif model_type == "xgboost":
        model = XGBRegressor(**kwargs) if is_numeric else XGBClassifier(**kwargs)

    return model
