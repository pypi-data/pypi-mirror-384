import numpy as np
import adelie as ad
from sklearn.base import BaseEstimator
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
import matplotlib.pyplot as plt
from scipy.stats import t as t_dist


def generate_lambda_path(X, y, base=None, n_lmdas=1000, lambda_min_ratio=None):
    """
    Generate a path of lambda values for Lasso-like regression. (same logic as in R)

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Design matrix.
    y : array-like of shape (n_samples,)
        Response vector.
    base : object
        Base model that will use the generated lambda path for cross-validation.
    n_lmdas : int, optional
        Number of lambda values to generate. Default is 1000.
    lambda_min_ratio : float, optional
        Minimum ratio of the smallest lambda to the largest lambda. Default is None,
        which sets it to 0.0001 if n > p and 0.01 if n <= p.

    Returns
    -------
    lmda_path : array-like of shape (n_lmdas,)
        Path of lambda values.
    """
    n, p = X.shape
    if lambda_min_ratio is None:
        lambda_min_ratio = 1e-4 if n > p else 1e-2
    if (base is not None) and (isinstance(base, UniLasso)):
        Z = UniLasso()._fit_univariate_model(X, y)["loo_preds"]                                                             # (n,p)
        z_mean = np.mean(Z, axis=0, keepdims=True)                                                                          # (1,p)
        z_std = np.std(Z, axis=0, keepdims=True)                                                                            # (1,p)
        z_std[z_std == 0] = 1  
        zty = (Z.T@y-(np.ravel(z_mean) * np.sum(y)))/np.ravel(z_std)                                                        # (p,)
    else:
        x_mean = np.mean(X,axis=0)                                                                                          # (p,)
        x_std = np.std(X,axis=0)                                                                                            # (p,)
        x_std[x_std == 0] = 1   
        zty = (X.T @ y - x_mean * np.sum(y)) / x_std 

    lambda_max = 2 * np.max(np.abs(zty)) / n
    lambda_min = lambda_min_ratio * lambda_max
    return np.logspace(np.log10(lambda_max), np.log10(lambda_min), num=n_lmdas)

class UniLasso(BaseEstimator):
    """
    Univariate Lasso regression

    Parameters
    ----------
    lmda_path : array-like of shape (n_lmdas,), optional
        Path of the lambda values.
    fit_intercept : bool, optional
        Whether to fit the intercept. Default is True.
        Even if False, recall that stage 2 will lead to an intercept from univariate models.
    vars_names : list of str, optional
        List of variable names. If None, the variables will be named X0, X1, ..., Xp-1.

    Attributes
    ----------
    slopes_ : array-like of shape (n_lmdas, n_features)
        final slopes
    intercept_ : array-like of shape (n_lmdas, 1)
        final intercepts
    lmda_path_ : array-like of shape (n_lmdas,)
        Path of the lambda values.
    fit_intercept_ : bool
        Whether to fit the intercept.
    loo_slopes_ : array-like of shape (n_samples, n_features)
        LOO slopes (stage 1)
    loo_intercept_ : array-like of shape (n_samples, 1)
        LOO intercepts (stage 1)
    loo_preds_ : array-like of shape (n_samples, n_features)
        LOO predictions (stage 1)
    uni_slopes_ : array-like of shape (n_features, )
        univariate slopes (stage 1)
    uni_intercepts_ : array-like of shape (n_features, )
        univariate intercepts (stage 1)
    vars_names_ : list of str
        List of variable names. If None, the variables will be named X0, X1, ..., Xp-1.
    """

    def __init__(self, lmda_path=None, fit_intercept=True, vars_names=None):
        self.lmda_path_ = lmda_path                                                                                         # (n_lmdas, )
        self.slopes_ = None                                                                                                 # (n_lmdas, n_features)
        self.intercept_ = None                                                                                              # (n_lmdas, 1)
        self.loo_slopes_ = None                                                                                             # (n_samples, n_features)
        self.loo_intercept_ = None                                                                                          # (n_samples, 1)
        self.loo_preds_ = None                                                                                              # (n_samples, n_features)
        self.uni_slopes_ = None                                                                                             # (n_features, )
        self.vars_names_ = vars_names                                                                                       # list of str
        self.fit_intercept_ = fit_intercept                                                                                 # bool

    def set_vars_names(self, vars_names):
        self.vars_names_ = vars_names                                                                                       # list of str

    def set_lmda_path(self, lmda_path):
        self.lmda_path_ = lmda_path                                                                                         # (n_lmdas, )

    def _fit_univariate_model(self, X, y, keep_stage1_diagnostics=False):
        """
        Fit univariate models (stage 1) and compute LOO predictions.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Design matrix.
        y : array-like of shape (n_samples,)
            Response vector.
        keep_stage1_diagnostics : bool
            If False, then loo_intercepts and loo_slopes are not computed (memory saving)

        Returns
        -------
        results : dict
            Dictionary containing:
              - intercepts : (n_features,)
              - slopes : (n_features,)
              - loo_intercepts : (n_samples, n_features)
              - loo_slopes : (n_samples, n_features)
              - preds : (n_samples, n_features)
              - loo_preds : (n_samples, n_features)
        """
        n_samples, _ = X.shape

        y = y[:, np.newaxis]                                                                                                # n x 1
        x_mean = np.mean(X, axis=0, keepdims=True)                                                                          # 1 x p
        x_std = np.std(X, axis=0, keepdims=True)
        x_std[x_std == 0] = 1.0  
        x_prec = 1.0 / x_std                                                                                                # 1 x p
        y_mean = np.mean(y)                                                                                                 # float
        Z = (X - x_mean) * x_prec                                                                                           # n x p
        szy = np.mean(Z * y, axis=0, keepdims=True)                                                                         # 1 x p

        intercepts = y_mean - szy * x_mean * x_prec                                                                         # 1 x p
        slopes = szy * x_prec                                                                                               # 1 x p
        preds = szy * Z + y_mean                                                                                            # n x p
        H = (1.0 + Z*Z) / n_samples                                                                                         # n x p
        loo_slopes = slopes / (1.0 - H) if keep_stage1_diagnostics else None                                                # n x p
        loo_intercepts = (intercepts - H * y) / (1.0 - H)  if keep_stage1_diagnostics else None                             # n x p
        loo_preds = (-H * y + preds) / (1.0 - H)                                                                            # n x p

        return {
            "intercepts": intercepts[0, :],
            "slopes": slopes[0, :],
            "loo_intercepts": loo_intercepts,
            "loo_slopes": loo_slopes,
            "preds": preds,
            "loo_preds": loo_preds,
        }

    def fit(self, X, y):
        """
        Fit the UniLasso model.
        """
        X, y = check_X_y(X, y, y_numeric=True)

        if self.vars_names_ is None:
            self.vars_names_ = [f"X{i}" for i in range(X.shape[1])]

        _, n_features = X.shape

        # Step 1: Fit univariate models and compute LOO predictions
        stage1_results = self._fit_univariate_model(X, y)
        self.uni_intercepts_ = stage1_results["intercepts"]                                                                 # (n_features,)
        self.uni_slopes_ = stage1_results["slopes"]                                                                         # (n_features,)
        self.loo_preds_ = stage1_results["loo_preds"]                                                                       # (n_samples, n_features)
        self.loo_slopes_ = stage1_results["loo_slopes"]                                                                     # (n_samples, n_features)
        self.loo_intercept_ = stage1_results["loo_intercepts"]                                                              # (n_samples, n_features)

        # Step 2: Fit Lasso to the LOO predictions with non-negativity constraints
        if self.lmda_path_ is None:
            self.lmda_path_ = generate_lambda_path(self.loo_preds_, y)
        state = ad.grpnet(
            X=np.asfortranarray(self.loo_preds_),
            glm=ad.glm.gaussian(y=y),
            lmda_path=self.lmda_path_,
            intercept=self.fit_intercept_,
            early_exit=False,
            constraints=[ad.constraint.lower(np.zeros(1)) for _ in range(n_features)],
            progress_bar=False,
            alpha=1.0,  # added elastic net penalty
        )

        ad_slopes = state.betas.toarray()                                                                                   # (n_lmdas, n_features)
        ad_intercepts = state.intercepts                                                                                    # (n_lmdas, )

        # Step 3: Compute final coefficients
        self.slopes_ = ad_slopes * self.uni_slopes_                                                                         # (n_lmdas, n_features)
        self.intercept_ = ad_intercepts + np.sum(self.uni_intercepts_ * ad_slopes, axis=1)                                  # (n_lmdas, )
        self.intercept_ = self.intercept_[:, np.newaxis]                                                                    # (n_lmdas, 1)

    def predict_uni(self, X):
        """
        Predict using the univariate model (stage 1).

        Returns
        -------
        y_pred : array-like of shape (n_samples, n_features)
        """
        check_is_fitted(self)
        X = check_array(X)
        return X * self.uni_slopes_[None, :] + self.uni_intercepts_[None, :]                                                # (n_samples, n_features)

    def predict(self, X):
        """
        Predict using the final model (stage 2).

        Returns
        -------
        y_pred : array-like of shape (n_samples, n_lmdas)
        """
        check_is_fitted(self)
        X = check_array(X)
        return X @ self.slopes_.T + self.intercept_.T                                                                       # (n_samples, n_lmdas)

    def get_active_variables(self, lmda=None, tolerance=1e-10):
        """
        Get the names of the active variables for a given lambda value.
        """
        check_is_fitted(self)
        if lmda is None:
            if len(self.lmda_path_) != 1:
                raise ValueError("lmda is None but lmda_path_ has multiple values.")
            lmda = float(self.lmda_path_[0])
        j = int(np.argmin(np.abs(self.lmda_path_ - lmda)))
        active_vars = [self.vars_names_[i] for i, slp in enumerate(self.slopes_[j]) if abs(slp) > tolerance]
        return active_vars

    def get_fitted_function(self, lmda=None, tolerance=1e-10):
        """
        Get the fitted model string representation.
        """
        check_is_fitted(self)
        if lmda is None:
            if len(self.lmda_path_) != 1:
                raise ValueError("lmda is None but lmda_path_ has multiple values.")
            lmda = float(self.lmda_path_[0])
        j = int(np.argmin(np.abs(self.lmda_path_ - lmda)))
        fitted_model_rep = [f"{self.intercept_[j,0]:.3f}"] + [
            f"{self.slopes_[j,i]:.3f}*" + var
            for i, var in enumerate(self.vars_names_)
            if np.abs(self.slopes_[j, i]) > tolerance
        ]
        return " + ".join(fitted_model_rep)


class Lasso(BaseEstimator):
    """
    Lasso regression

    Parameters
    ----------
    lmda_path : array-like of shape (n_lmdas,), optional
        Path of the lambda values.
    vars_names : list of str, optional
        List of variable names. If None, the variables will be named X0, X1, ..., Xp-1.
    fit_intercept : bool, optional
        Whether to fit the intercept. Default is True.

    Attributes
    ----------
    slopes_ : array-like of shape (n_lmdas, n_features)
        final slopes
    intercept_ : array-like of shape (n_lmdas, 1)
        final intercepts
    lmda_path_ : array-like of shape (n_lmdas,)
        Path of the lambda values.
    vars_names_ : list of str
        Variable names.
    fit_intercept_ : bool
        Whether to fit the intercept.
    X_mean_ : array-like of shape (n_features,)
        Column means of X from training data.
    X_std_ : array-like of shape (n_features,)
        Column standard deviations of X from training data.
    """

    def __init__(self, lmda_path=None, fit_intercept=True, vars_names=None):
        self.lmda_path_ = lmda_path                                                                                         # (n_lmdas, )
        self.slopes_ = None                                                                                                 # (n_lmdas, n_features)
        self.intercept_ = None                                                                                              # (n_lmdas, 1)
        self.vars_names_ = vars_names                                                                                       # list of str
        self.fit_intercept_ = fit_intercept                                                                                 # bool
        self.X_mean_ = None
        self.X_std_ = None

    def set_vars_names(self, vars_names):
        self.vars_names_ = vars_names                                                                                       # list of str

    def set_lmda_path(self, lmda_path):
        self.lmda_path_ = lmda_path

    def fit(self, X, y):
        """
        Fit the Lasso model.
        """
        X, y = check_X_y(X, y, y_numeric=True)

        if self.vars_names_ is None:
            self.vars_names_ = [f"X{i}" for i in range(X.shape[1])]

        self.X_mean_ = np.mean(X, axis=0)
        self.X_std_ = np.std(X, axis=0)
        self.X_std_[self.X_std_ == 0] = 1.0
        X_std = (X - self.X_mean_) / self.X_std_

        if self.lmda_path_ is None:
            self.lmda_path_ = generate_lambda_path(X_std, y)

        state = ad.grpnet(
            X=np.asfortranarray(X_std),
            glm=ad.glm.gaussian(y=y),
            lmda_path=self.lmda_path_,
            intercept=self.fit_intercept_,
            early_exit=False,
            progress_bar=False,
        )

        slopes_std = state.betas.toarray()                                                                                  # (n_lambdas, n_features)
        intercept_std = state.intercepts                                                                                    # (n_lambdas,)

        self.slopes_ = slopes_std / self.X_std_[np.newaxis, :]
        correction = (self.X_mean_ / self.X_std_) @ slopes_std.T
        self.intercept_ = intercept_std - correction
        self.intercept_ = self.intercept_[:, None]

    def predict(self, X):
        """
        Predict using the Lasso model.

        Returns
        -------
        y_pred : array-like of shape (n_samples, n_lmdas)
        """
        check_is_fitted(self)
        X = check_array(X)
        return X @ self.slopes_.T + self.intercept_.T                                                                       # (n_samples, n_lmdas)

    def get_active_variables(self, lmda=None, tolerance=1e-10):
        """
        Return active variable names at the specified lambda.
        """
        check_is_fitted(self)
        if lmda is None:
            if len(self.lmda_path_) != 1:
                raise ValueError("lmda is None but lmda_path_ has multiple values.")
            lmda = float(self.lmda_path_[0])
        j = int(np.argmin(np.abs(self.lmda_path_ - lmda)))
        active_vars = [self.vars_names_[i] for i, slp in enumerate(self.slopes_[j]) if abs(slp) > tolerance]
        return active_vars

    def get_fitted_function(self, lmda=None, tolerance=1e-10):
        """
        Get the fitted model string representation.
        """
        check_is_fitted(self)
        if lmda is None:
            if len(self.lmda_path_) != 1:
                raise ValueError("lmda is None but lmda_path_ has multiple values.")
            lmda = float(self.lmda_path_[0])
        j = int(np.argmin(np.abs(self.lmda_path_ - lmda)))
        fitted_model_rep = [f"{self.intercept_[j,0]:.3f}"] + [
            f"{self.slopes_[j,i]:.3f}*" + var
            for i, var in enumerate(self.vars_names_)
            if np.abs(self.slopes_[j, i]) > tolerance
        ]
        return " + ".join(fitted_model_rep)


class OLS(BaseEstimator):
    """
    Linear regression

    Parameters
    ----------
    vars_names : list of str, optional
        List of variable names. If None, the variables will be named X0, X1, ..., Xp-1.
    fit_intercept : bool, optional
        Whether to fit the intercept. Default is True.

    Attributes
    ----------
    slopes_ : array-like of shape (n_features,)
        final slopes
    intercept_ : float
        final intercept
    preds_loo_ : array-like of shape (n_samples,)
        loo predictions
    vars_names_ : list of str
        List of variable names.
    fit_intercept_ : bool
        Whether to fit the intercept.
    p_value_t_test_ : array-like of shape (n_features,)
    """

    def __init__(self, fit_intercept=True, vars_names=None):
        self.slopes_ = None                                                                                                 # (n_features, )
        self.intercept_ = None                                                                                              # float
        self.vars_names_ = vars_names                                                                                       # list of str
        self.fit_intercept_ = fit_intercept                                                                                 # bool
        self.preds_loo_ = None
        self.p_value_t_test_ = None

    def set_vars_names(self, vars_names):
        self.vars_names_ = vars_names                                                                                       # list of str

    def fit(self, X, y):
        """
        Fit the OLS model.
        """
        X, y = check_X_y(X, y, y_numeric=True)
        n_samples, n_features = X.shape
        if self.vars_names_ is None:
            self.vars_names_ = [f"X{i}" for i in range(n_features)]

        if self.fit_intercept_:
            n_features += 1
            X = np.hstack([np.ones((n_samples, 1)), X])                                                                     # (n_samples, n_features+1)

        M = np.linalg.pinv(X.T @ X)
        # beta = M @ X.T @ y
        beta, *_ = np.linalg.lstsq(X,y,rcond=None)  # to check later

        XM = X @ M
        h = np.einsum('ij,ij->i',X, XM)

        self.slopes_ = beta[1:]
        self.intercept_ = beta[0]
        self.preds_loo_ = y - (y - X @ beta) / (1.0 - h)

        yhat = X @ beta
        residuals = y - yhat
        rss = np.sum(residuals**2)
        sigma2 = rss / (n_samples - n_features)
        cov_beta = sigma2 * M
        se_beta = np.sqrt(np.diag(cov_beta))[:, None]
        t = beta / se_beta
        self.p_value_t_test_ = 2 * (1 - t_dist.cdf(np.abs(t), n_samples - n_features)).flatten()

    def predict(self, X):
        """
        Predict using the OLS model.

        Returns
        -------
        y_pred : array-like of shape (n_samples,)
        """
        check_is_fitted(self)
        X = check_array(X)
        return X @ self.slopes_ + self.intercept_                                                                            # (n_samples, )

    def get_active_variables(self, tolerance=1e-10):
        """
        Return names of variables with |coef| > tolerance.
        """
        check_is_fitted(self)
        active_vars = [self.vars_names_[i] for i, slp in enumerate(self.slopes_) if abs(slp) > tolerance]
        return active_vars

    def get_fitted_function(self):
        """
        Get the fitted model string representation.
        """
        check_is_fitted(self)
        fitted_model_rep = [f"{self.intercept_:.3f}"] + [
            f"{self.slopes_[i]:.3f}*" + var for i, var in enumerate(self.vars_names_)
        ]
        return " + ".join(fitted_model_rep)


def pw(X, S=None):
    """
    Compute pairwise products of the columns of X indexed by S.
    Use the convention X_j*X_k for j < k.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Design matrix.
    S : array-like
        Indices of the columns to compute pairwise products.
        If None, use np.arange(p)

    Returns
    -------
    out : array-like of shape (n_samples, n_pairs)
        Pairwise products of the columns of X indexed by S.
    colnames : list of str
        List of column names for the pairwise products.
    """
    n_samples, n_features = X.shape
    if S is None:
        S = np.arange(n_features)
    pp = len(S)
    if pp > n_features:
        raise ValueError("S must be a subset of the columns of X")
    num_pairs = (pp * (pp - 1)) // 2
    out = np.empty((n_samples, num_pairs))
    colnames = []
    idx = 0
    for j in range(pp - 1):
        for k in range(j + 1, pp):
            out[:, idx] = X[:, S[j]] * X[:, S[k]]
            colnames.append(f"X{S[j]}*X{S[k]}")
            idx += 1
    return out, colnames


def cv(
    base,
    X,
    y,
    n_folds,
    lmda_path=None,
    plot_cv_curve=False,
    cv1se=False,
    random_state=None,
    memory_efficient=True,
):
    """
    Cross-validation for Lasso-like regression.

    Parameters
    ----------
    base : object
        Base model to use for cross-validation. The function will modify base in place.
    X : array-like of shape (n_samples, n_features)
        Design matrix.
    y : array-like of shape (n_samples,)
        Response vector.
    n_folds : int
        Number of folds for cross-validation.
    lmda_path : array-like of shape (n_lmdas,), optional
        Path of the lambda values. If None, it will be generated using generate_lambda_path.
    plot_cv_curve : bool
        If True, plot CV diagnostics.
    cv1se : bool
        If True, pick the most regularized model within 1 standard error of the minimum.
    random_state : int, optional
        Seed for deterministic folds.
    memory_efficient : bool
        If True, it doubles the model fits but cut the memory from O(nxn_lmdas) to O(n)

    Returns
    -------
    results : dict with keys:
        - cv_errors : (n_folds, n_lmdas)
        - lmda_path : (n_lmdas,)
        - prevalidated_preds : (n_samples,)
        - best_lmda : float
        - n_folds : int
        - active_set : list[str]
    """
    n_samples, _ = X.shape
    rng = np.random.RandomState(random_state) if random_state is not None else np.random
    permutation = rng.permutation(n_samples)
    fold_indices = np.array_split(permutation, n_folds)
    cv_errors = []
    cv_r2s = []

    if lmda_path is None:
        if getattr(base, "lmda_path_", None) is not None:
            lmda_path = base.lmda_path_
        else:
            lmda_path = generate_lambda_path(X, y, base)
    base.set_lmda_path(lmda_path)
    n_lmdas = len(lmda_path)

    if memory_efficient : 

        # first fit : get the best lmda
        for i in range(n_folds):
            train_indices = np.concatenate([fold_indices[j] for j in range(n_folds) if j != i])
            val_indices = fold_indices[i]
            X_train, y_train = X[train_indices], y[train_indices]
            X_val, y_val = X[val_indices], y[val_indices]
            base.fit(X_train, y_train)
            y_val_hat = base.predict(X_val)                                                                                 # (n_val_samples, n_lmdas)
            val_error = np.mean((y_val[:, None] - y_val_hat) ** 2, axis=0)                                                  # (n_lmdas, )
            cv_errors.append(val_error)
            cv_r2s.append(1 - val_error / np.var(y_val))
        cv_errors = np.stack(cv_errors)                                                                                     # (n_folds, n_lmdas)
        cv_r2s = np.stack(cv_r2s)                                                                                           # (n_folds, n_lmdas)
        cv_errors_mean = cv_errors.mean(axis=0)                                                                             # (n_lmdas, )
        col = int(np.argmin(cv_errors_mean))
        if cv1se:
            se = float(np.std(cv_errors[:, col], ddof=1) / np.sqrt(n_folds))
            mask = cv_errors_mean <= (cv_errors_mean.min() + se)
            # pick the first index satisfying the 1-SE threshold
            best_lmda_index = int(np.where(mask)[0][0])
        else:
            best_lmda_index = col
        best_lmda = float(lmda_path[best_lmda_index])

        # second fit : get the prevalidated predictions
        prevalidated_preds = np.zeros(n_samples)
        for i in range(n_folds):
            train_indices = np.concatenate([fold_indices[j] for j in range(n_folds) if j != i])
            val_indices = fold_indices[i]
            X_train, y_train = X[train_indices], y[train_indices]
            X_val, y_val = X[val_indices], y[val_indices]
            base.fit(X_train, y_train)
            prevalidated_preds[val_indices] = base.predict(X_val)[:, best_lmda_index]                                       # (n_val_samples,)
         
    else : 
        prevalidated_preds = np.zeros((n_samples, n_lmdas))
        for i in range(n_folds):
            train_indices = np.concatenate([fold_indices[j] for j in range(n_folds) if j != i])
            val_indices = fold_indices[i]
            X_train, y_train = X[train_indices], y[train_indices]
            X_val, y_val = X[val_indices], y[val_indices]
            base.fit(X_train, y_train)
            y_val_hat = base.predict(X_val)                                                                                  # (n_val_samples, n_lmdas)
            val_error = np.mean((y_val[:, None] - y_val_hat) ** 2, axis=0)                                                   # (n_lmdas, )
            cv_errors.append(val_error)
            cv_r2s.append(1 - val_error / np.var(y_val))
            prevalidated_preds[val_indices, :] = y_val_hat

        cv_errors = np.stack(cv_errors)                                                                                      # (n_folds, n_lmdas)
        cv_r2s = np.stack(cv_r2s)                                                                                            # (n_folds, n_lmdas)
        cv_errors_mean = cv_errors.mean(axis=0)                                                                              # (n_lmdas, )
        col = int(np.argmin(cv_errors_mean))
        if cv1se:
            se = float(np.std(cv_errors[:, col], ddof=1) / np.sqrt(n_folds))
            mask = cv_errors_mean <= (cv_errors_mean.min() + se)
            # pick the first index satisfying the 1-SE threshold
            best_lmda_index = int(np.where(mask)[0][0])
        else:
            best_lmda_index = col
        best_lmda = float(lmda_path[best_lmda_index])

        prevalidated_preds = prevalidated_preds[:, best_lmda_index]                                                           # (n_samples, )

    # get model size per lmda for plotting purposes
    if plot_cv_curve:
        base.fit(X, y)
        model_sizes = np.array([len(base.get_active_variables(lmda)) for lmda in base.lmda_path_])                            # (n_lmdas, )

    # fit model to the entire dataset using the best lambda
    base.set_lmda_path(np.array([best_lmda]))
    base.fit(X, y)

    if plot_cv_curve:
        fig, ax = plt.subplots(figsize=(10, 5))
        xs = -np.log(lmda_path)
        cv_means = np.mean(cv_r2s, axis=0)
        cv_stds = np.std(cv_r2s, axis=0) / np.sqrt(n_folds)
        ax.plot(xs, cv_means, color="red", linewidth=2, label="CV R2")

        n_points = len(xs)
        n_labels = min(20, n_points)
        label_idxs = np.linspace(0, n_points - 1, n_labels, dtype=int)

        ax.errorbar(
            xs[label_idxs],
            cv_means[label_idxs],
            yerr=cv_stds[label_idxs],
            fmt="o",
            color="red",
            ecolor="black",
            elinewidth=0.8,
            capsize=3,
        )

        ymin, ymax = ax.get_ylim()
        y_offset = 0.02 * (ymax - ymin)
        for idx in label_idxs:
            x = xs[idx]
            yv = cv_means[idx]
            sz = model_sizes[idx]
            ax.text(x, yv + y_offset, str(sz), ha="center", va="bottom", fontsize=10, color="darkred")

        ax.set_title(f"best -log(λ) = {-np.log(best_lmda):.2f} | n_folds={n_folds}", fontsize=16, pad=15)
        ax.set_xlabel(r"$-\log(\lambda)$", fontsize=14)
        ax.set_ylabel("CV R2", fontsize=14)
        ax.legend(loc="upper right", fontsize=12)
        ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)
        active_vars = base.get_active_variables(best_lmda)
        chunk_size = 10
        chunks = [active_vars[i : i + chunk_size] for i in range(0, len(active_vars), chunk_size)]
        lines = [", ".join(map(str, chunk)) for chunk in chunks]
        text_str = "Active Set:\n" + "\n".join(lines)
        ax.text(
            0.50,
            0.10,
            text_str,
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=11,
            bbox=dict(facecolor="white", edgecolor="gray", alpha=0.6),
        )
        plt.tight_layout()
        plt.show()

    return {
            "cv_errors": cv_errors,
            "lmda_path": lmda_path,
            "prevalidated_preds": prevalidated_preds,
            "best_lmda": best_lmda,
            "n_folds": n_folds,
            "active_set": base.get_active_variables(best_lmda),
        }


def make_interactions(X, S, M=None):
        """
        Compute pairwise products of the columns of X indexed by S, with multiplier M 
        Use the convention X_j*X_k for j < k.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Design matrix.
        S : array-like of shape (n_pairs, 2) or (n_selected_features,)
            Indices of the columns to compute pairwise products.
            If one-dimensional, S must be sorted in increasing order 
        M : array-like of shape (n_features, n_features), optional
            Multiplier of the pairwise products 
            useful only on subset j<k

        Returns
        -------
        out : array-like of shape (n_samples, n_pairs)
            Pairwise products of the columns of X indexed by S.
        colnames : list of str
            List of column names for the pairwise products.
        """
        n_samples, n_features = X.shape
        assert isinstance(S, np.ndarray)
        if M is None : 
            M = np.ones((n_features,n_features))

        if S.ndim == 1:
            assert np.all(S[:-1]<=S[1:]) 
            pp = len(S)
            num_pairs = pp * (pp - 1) // 2
            out = np.empty((n_samples, num_pairs))
            colnames = []
            idx = 0
            for j in range(pp - 1):
                for k in range(j + 1, pp):
                    out[:, idx] = X[:, S[j]] * X[:, S[k]] * M[S[j],S[k]]
                    colnames.append(f"X{S[j]}*X{S[k]}")
                    idx += 1  
        elif S.ndim == 2:
            # S has shape (n_pairs, 2)
            num_pairs = S.shape[0]
            out = np.empty((n_samples, num_pairs))
            colnames = []
            for i in range(num_pairs):
                j, k = S[i]
                assert j < k
                out[:, i] = X[:, j] * X[:, k] * M[j,k]
                colnames.append(f"X{j}*X{k}")
        else:
            raise ValueError("S must be either 1D or 2D array")
        
        return out, colnames

