import logging
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from missensemble import criteria
from missensemble import models
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

logging.basicConfig(level=logging.INFO)


class MissEnsemble(BaseEstimator, TransformerMixin):

    def __init__(
        self,
        n_iter: int = 100,
        categorical_vars: list[str] = None,
        ordinal_vars: list[str] = None,
        numerical_vars: list[str] = None,
        ens_method: str = "forest",
        n_estimators: int = 100,
        tol: float = 1e-4,
        random_state: int = 42,
        print_criteria: bool = False,
    ):
        """
        Initialize the MissEnsemble object.

        Parameters
        ----------
        n_iter : int, optional
            The number of iterations to perform for imputation. Defaults to 100.
        categorical_vars : list of str, optional
            List of column names representing categorical variables.
        ordinal_vars : list of str, optional
            List of column names representing ordinal variables.
        numerical_vars : list of str, optional
            List of column names representing numerical variables.
        ens_method : str, optional
            The ensemble method to use for imputation. Defaults to 'forest'.
        n_estimators : int, optional
            The number of estimators to use for the ensemble method. Defaults to 100.
        tol : float, optional
            The tolerance for convergence. Defaults to 1e-4.
        random_state : int, optional
            The random state to use for reproducibility. Defaults to 42.
        print_criteria : bool, optional
            Whether to print the convergence criteria during imputation. Defaults to False.
        """

        # Assign empty lists for data categories that are not provided.
        categorical_vars = categorical_vars or []  # If None, assign empty list
        ordinal_vars = ordinal_vars or []
        numerical_vars = numerical_vars or []

        # Error handling

        if not any([ordinal_vars, numerical_vars, categorical_vars]):
            logging.error("No variables were provided for imputation")
            raise ValueError(
                "At least one variable type must be provided for imputation."
            )

        if not all(
            [
                isinstance(x, list)
                for x in [categorical_vars, ordinal_vars, numerical_vars]
            ]
        ):
            logging.error("Variable lists should be of type list")
            raise TypeError("All variable lists must be of type list.")

        if not all([isinstance(x, str) for x in categorical_vars]):
            logging.error("Categorical variables should be strings")
            raise TypeError(
                "Names of categorical variables within the list must be strings."
            )

        if not all([isinstance(x, str) for x in numerical_vars]):
            logging.error("Numerical variables should be strings")
            raise TypeError(
                "Names of numerical variables within the list must be strings."
            )

        if not all([isinstance(x, str) for x in ordinal_vars]):
            logging.error("Ordinal variables should be strings")
            raise TypeError(
                "Names of ordinal variables within the list must be strings."
            )

        if (
            set(ordinal_vars) & set(categorical_vars)
            or set(ordinal_vars) & set(numerical_vars)
            or set(categorical_vars) & set(numerical_vars)
        ):
            logging.error("Variables cannot be in multiple variable lists")
            raise ValueError(
                "A variable cannot be assigned to more than one variable type list."
            )

        if ens_method not in ["forest", "xgb"]:
            logging.error("Unknown ensemble method provided")
            raise ValueError('The ensemble method should be either "forest", "xgb".')

        if not isinstance(n_iter, int) or n_iter <= 0 or isinstance(n_iter, bool):
            logging.error("Iterations should be a positive integer")
            raise ValueError("n_iter must be a positive integer.")

        if (
            not isinstance(n_estimators, int)
            or n_estimators <= 0
            or isinstance(n_estimators, bool)
        ):
            logging.error("Iterations should be a positive integer")
            raise ValueError("n_iter must be a positive integer.")

        self.n_iter = n_iter
        self.cat_vars = categorical_vars
        self.ord_vars = ordinal_vars
        self.num_vars = numerical_vars
        self.ens_method = ens_method
        self.n_estimators = n_estimators
        self.tol = tol
        self.random_state = random_state
        self.print_criteria = print_criteria

    def fit(self, X: pd.DataFrame, y=None) -> "MissEnsemble":
        """
        Fit the MissEnsemble imputer to the input data.

        Parameters
        ----------
        X : pd.DataFrame
            The input data to be imputed.
        y : Ignored
            Exists only for compatibility with scikit-learn's interface.

        Returns
        -------
        self : MissEnsemble
            The fitted MissEnsemble imputer object.
        """
        self.data_old_ = X.reset_index(drop=True).copy()
        self.na_where_ = self.data_old_.isna().copy()  # where are NAs

        # percentages of NAs per column in ascending order
        self.na_perc_ = (self.na_where_.sum() / self.data_old_.shape[0]).sort_values(
            ascending=True
        )

        # list of all columns with NAs
        self.cols_ = self.na_perc_[self.na_perc_ > 0].index.tolist()

        self.convergence_ = False
        # Raise logging error if there are no NAs

        # check which categories have NAs
        self.cats_missing = self._get_vars_with_missings()

        if not self.cols_:
            logging.error("There are no missing values in the input data.")
            return

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Impute missing values in the input data using the fitted MissEnsemble algorithm.

        Parameters
        ----------
        X : pd.DataFrame
            The input data to be transformed.

        Returns
        -------
        pd.DataFrame
            The transformed data with imputed missing values.

        """

        # Check if the object is fitted
        check_is_fitted(self)

        # Initialize variables

        predictions = {}
        criterion_num = []
        criterion_cat = []

        # Randomly impute variables (only in the beginning)
        for col in self.cols_:

            # generally throughout, I treat ordinal and categorical variables as one type
            if col in (self.cat_vars + self.ord_vars):
                imputer = SimpleImputer(strategy="most_frequent")
                self.data_old_.loc[:, col] = imputer.fit_transform(
                    self.data_old_[col].values.reshape(-1, 1)
                )
            else:
                imputer = SimpleImputer(strategy="mean")
                self.data_old_.loc[:, col] = imputer.fit_transform(
                    self.data_old_[col].values.reshape(-1, 1)
                ).flatten()  # that's important to flatten the array so that the dims are correct

        data_new = self.data_old_.copy()

        # main iteration loop
        for i in np.arange(1, self.n_iter + 1):
            data_prev_step = data_new.copy()

            # main loop to go through columns
            for col in self.cols_:
                is_numeric = not (col in self.cat_vars + self.ord_vars)

                data = self.data_old_ if i == 1 else data_new

                # Transform target variable in the beginning
                if not is_numeric:
                    var_traget_imputer = LabelEncoder()
                    var_target = pd.DataFrame(
                        var_traget_imputer.fit_transform(
                            data[col].values.reshape(
                                -1,
                            )
                        ),
                        columns=[col],
                    )

                elif is_numeric:
                    var_target = data[
                        col
                    ]  # here we don't transform because RFs do not require numeric transformation

                # Transform categorical variables in One-hot and then combine all non-target variables (i.e., dropping target column)

                data_processed = self._process_data(data, col)

                # train/test split
                X_train = data_processed[~self.na_where_[col]]
                y_train = var_target[~self.na_where_[col]]
                X_test = data_processed[self.na_where_[col]]
                # y_test = var_target[self.na_where_[col]] ## y_test is not accessed

                model_parameters = {
                    "n_jobs": -1,
                    "n_estimators": self.n_estimators,
                    "random_state": self.random_state,
                }

                rfc = models.initialize_model(
                    self.ens_method, is_numeric, **model_parameters
                )

                rfc.fit(
                    X_train,
                    y_train.values.reshape(
                        -1,
                    ),
                )

                # save predictions
                predictions.update({col: rfc.predict(X_test)})

                # here I retransform the data back using the encoder i used in the beginning
                if not is_numeric:
                    data_new.loc[self.na_where_[col], col] = (
                        var_traget_imputer.inverse_transform(
                            [int(i) for i in predictions[col]]
                        )
                    )
                else:
                    data_new.loc[self.na_where_[col], col] = predictions[col]

            # Calculate criterion
            # check if there are numerical columns which belong to the columns with NAs
            if bool(self.cats_missing["numerical"]):
                criterion_num.append(
                    criteria.calc_num_criterion(
                        data_new, data_prev_step, self.na_where_, self.num_vars
                    )
                )
            # Note: the criterion for categorical and ordinal variables is the same
            if bool(self.cats_missing["ordinal"]) or bool(
                self.cats_missing["categorical"]
            ):
                criterion_cat.append(
                    criteria.calc_cat_ord_criterion(
                        data_new,
                        data_prev_step,
                        self.na_where_,
                        self.cat_vars + self.ord_vars,
                    )
                )

            self.criteria_ = {
                "criterion_cat": criterion_cat,
                "criterion_num": criterion_num,
            }

            if self.print_criteria:
                logging.info(
                    "Numeric criterion: {}, Categorical/Ordinal criterion: {}".format(
                        (
                            criterion_num[-1]
                            if bool(self.cats_missing["numerical"])
                            else []
                        ),
                        (
                            criterion_cat[-1]
                            if (
                                bool(self.cats_missing["ordinal"])
                                or bool(self.cats_missing["categorical"])
                            )
                            else []
                        ),
                    )
                )

            # Decide based on criterion
            if i > 1:
                if criteria.stopping_rule(criterion_cat, criterion_num, self.tol):
                    self.new_X = data_prev_step.copy()
                    logging.info(
                        "The critirion was satisfied after {} iterations".format(i - 1)
                    )
                    self.iter_run = i - 1
                    self.convergence_ = True
                    return self.new_X
            logging.info("Iteration {} is completed".format(i))

        logging.warning(
            "The critirion was NOT satisfied after {} iterations. "
            "Maybe re-run with more iterations".format(i - 1)
        )
        return X  # This returns the input as we had it.

    def _process_data(self, data: pd.DataFrame, tar_col: str):
        """
        Preprocess the data for model training by encoding numerical, categorical and ordinal variables and combining predictors.

        Parameters
        ----------
        data : pd.DataFrame
            The input data.
        tar_col : str
            The target column to exclude from predictors.

        Returns
        -------
        pd.DataFrame
            The processed data with encoded predictors.
        """
        ord_col_no_tar = [i for i in self.ord_vars if i != tar_col]
        num_col_no_tar = [i for i in self.num_vars if i != tar_col]
        cat_col_no_tar = [i for i in self.cat_vars if i != tar_col]

        # if any([len(i) <= 1 for i in lists_vars]):
        tmp_cat = data[cat_col_no_tar]
        tmp_num = data[num_col_no_tar]
        tmp_ord = data[ord_col_no_tar]

        tmp_df = pd.DataFrame()

        non_empty_lists = np.array(
            [bool(i) for i in [ord_col_no_tar, num_col_no_tar, cat_col_no_tar]]
        )
        non_empty_lists_names = np.array(["ord", "num", "cat"])

        for key in non_empty_lists_names[non_empty_lists]:
            if key == "cat":
                tmp_df = pd.concat(
                    [tmp_df, pd.get_dummies(tmp_cat, dummy_na=False)], axis=1
                )
            elif key == "num":
                tmp_df = pd.concat([tmp_df, tmp_num], axis=1)
            elif key == "ord":
                tmp_df = pd.concat(
                    [
                        tmp_df,
                        tmp_ord.apply(LabelEncoder().fit_transform, axis=0),
                    ],
                    axis=1,
                )

        return tmp_df

    def plot_criteria(self, plot_final: bool = False) -> None:
        """
        Plot the imputation criteria over iterations.

        Parameters
        ----------
        plot_final : bool, optional
            If True, plot the final imputation criteria. If False, plot all iterations' criteria.

        Returns
        -------
        None
        """

        # Prepare dataframe
        criteria_pd = {
            i: self.criteria_[i]
            for i in self.criteria_
            if not len(self.criteria_[i]) == 0
        }  # this drops empty criterion
        criteria_pd = pd.DataFrame(criteria_pd)
        if not plot_final:
            criteria_pd = criteria_pd.iloc[:-1]
        criteria_pd.index = pd.RangeIndex(start=1, stop=len(criteria_pd) + 1, step=1)

        # Plot dataframe
        sns.scatterplot(criteria_pd).set(
            title="Imputation criteria", xlabel="Iterations", ylabel="Error"
        )
        plt.xticks(np.arange(1, len(criteria_pd) + 1))

    def check_imputation_fit(
        self,
        var_name: str,
        true_values: pd.Series,
        plot_type: str = "hist",
        error_type: str = None,
        return_plots: bool = True,
    ):
        """
        Check the fit of imputed values for a specific variable by comparing to true values and plotting error.

        Parameters
        ----------
        var_name : str
            The name of the variable for which imputed values were generated.
        true_values : pd.Series
            The true values of the variable.
        plot_type : str, optional
            The type of plot to generate. Default is 'hist'. Options are 'hist', 'kde', and 'confusion_matrix'.
        error_type : str, optional
            The type of error calculation to perform. Default is None. Options are 'diff', 'std_diff', 'mse', and 'rmse'.
        return_plots : bool, optional
            Whether to display the plot. Default is True.

        """

        # check if plot_type is valid
        if plot_type not in ["hist", "kde", "confusion_matrix"]:
            logging.error("Unknown plot type provided")
            raise ValueError('The plot_type should be either "hist" or "kde".')

        # check if error_type is valid
        if error_type not in [None, "diff", "std_diff", "mse", "rmse"]:
            logging.error("Unknown error type provided.")
            raise ValueError(
                'The error_type should be either "diff", "std_diff", "mse", or "rmse".'
            )
        # check if hist/kde are asked for categorical data
        if (plot_type in ["hist", "kde"]) and (
            var_name in self.cat_vars + self.ord_vars
        ):
            logging.error(
                "Incomptable plot parameter combination for categorical variables."
            )
            raise ValueError(
                'Histogram and KDE plots are not suitable for categorical variables. Please use "confusion_matrix" instead.'
            )
        # check if confusion matrix is asked for numerical data
        if (plot_type == "confusion_matrix") and (
            error_type in ["diff", "std_diff", "mse", "rmse"]
        ):
            logging.error(
                "Incomptable  plot parameter combination  for numerical variables."
            )
            raise ValueError(
                "The error_type should be left out for confusion matrix plots."
            )

        # check if true_values is a Series
        if not isinstance(true_values, pd.Series):
            logging.error("Incomptable type for true values.")
            raise ValueError("The true_values should be a pandas Series.")

        # create errors attribute if not there
        if not hasattr(self, "errors_"):
            self.errors_ = {}

        # check if var_name is in the list of columns
        if not var_name in self.cols_:
            logging.error("Uknown variable for imputation check")
            raise ValueError(
                "The variable name should be a column for which imputed values were generated."
            )

        # prepare dataframe
        true_values = true_values.reset_index(drop=True)
        data_imputed = self.new_X[var_name].copy()

        true_nas = true_values[self.na_where_[var_name]]
        imputed_nas = data_imputed[self.na_where_[var_name]]
        if var_name in self.num_vars:

            # calculate error
            if error_type == "diff":
                self.errors_[var_name] = true_nas - imputed_nas
            elif error_type == "std_diff":
                self.errors_[var_name] = (true_nas - imputed_nas) / np.std(true_nas)
            elif error_type == "mse":
                self.errors_[var_name] = (true_nas - imputed_nas) ** 2
            elif error_type == "rmse":
                self.errors_[var_name] = np.sqrt((true_nas - imputed_nas) ** 2)
        else:
            self.errors_[var_name] = confusion_matrix(
                true_nas, imputed_nas, normalize=None
            )
            heatmaplabels = true_nas.unique()
        # prepare xlabel depending on the error
        if error_type == "diff":
            xlabel = "Difference"
        elif error_type == "std_diff":
            xlabel = "Standardized difference"
        elif error_type == "mse":
            xlabel = "Mean squared error (MSE)"
        elif error_type == "rmse":
            xlabel = "Root mean squared error (RMSE)"
        else:
            xlabel = None

        # plot
        if return_plots:
            plot_args = {
                "x": self.errors_[var_name],
                "plot_type": plot_type,
                "xlabel": xlabel if var_name in self.num_vars else None,
                "error_type": error_type,
                "var_name": var_name,
                "heatmaplabels": (
                    heatmaplabels if var_name not in self.num_vars else None
                ),
            }
            self._plot_func(**plot_args)

    def _plot_func(
        self,
        x,
        plot_type: str,
        xlabel: str,
        error_type: str,
        var_name: str,
        heatmaplabels=None,
    ) -> None:
        """
        Plot the results of imputation fit checks for a variable.

        Parameters
        ----------
        x : array-like
            The data to be plotted.
        plot_type : str
            The type of plot to be generated. Possible values: 'hist', 'kde', 'confusion_matrix'.
        xlabel : str
            The label for the x-axis of the plot.
        error_type : str
            The type of error to be considered. Possible values: 'diff', 'std_diff'.
        var_name : str
            The name of the variable being plotted.
        heatmaplabels : array-like, optional
            Labels for the confusion matrix plot (only applicable if plot_type is 'confusion_matrix').

        """
        title = "Imputation check for " + var_name

        if plot_type == "hist":
            sns.histplot(x, bins=50).set(xlabel=xlabel, title=title)
        elif plot_type == "kde":
            sns.kdeplot(x).set(xlabel=xlabel, title=title)
        elif plot_type == "confusion_matrix":
            ConfusionMatrixDisplay(x, display_labels=heatmaplabels).plot(
                cmap="Blues"
            ).ax_.set_title(title)

        # plot vertical line
        if (
            error_type == "diff" or error_type == "std_diff"
        ) and var_name in self.num_vars:
            plt.axvline(0, color="red")  # Plot a vertical line at corresponding x

    def error_values(self, var_name) -> np.ndarray | pd.Series:
        """
        Return the error values for a specific variable after imputation fit check.

        Parameters
        ----------
        var_name : str
            The name of the variable.

        Returns
        -------
        array-like or float
            The error values for the specified variable.
        """
        # check if var_name is a string
        if not isinstance(var_name, str):
            logging.error("Variable name should be a string.")
            raise ValueError("The variable name should be a string.")

        # check if errors_ exists
        if hasattr(self, "errors_"):
            if var_name in self.errors_:
                return self.errors_[var_name]
            else:
                logging.error("Errors for this variable do not exist.")
                raise ValueError(
                    "Errors for this variable do not exist. Please run the check_imputation_fit() method first."
                )
        else:
            logging.error("Errors have not been calculated.")
            raise ValueError(
                "Errors have not been calculated. Please run the check_imputation_fit() method first."
            )

    def _get_vars_with_missings(self) -> dict:
        """
        Get lists of categorical, ordinal, and numerical variables that have missing values.

        Returns
        -------
        dict
            Dictionary with keys 'categorical', 'ordinal', 'numerical' and lists of columns with missing values.
        """
        return {
            "categorical": list(set(self.cat_vars) & set(self.cols_)),
            "ordinal": list(set(self.ord_vars) & set(self.cols_)),
            "numerical": list(set(self.num_vars) & set(self.cols_)),
        }
