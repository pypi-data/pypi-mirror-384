# pkgs/mariner/src/mariner/estimator.py
import numpy as np
from sklearn.base import BaseEstimator
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
import matplotlib.pyplot as plt
import seaborn as sns

from hiutils.core import (
    UniLasso, OLS,
    make_interactions, cv
)


class MARINER(BaseEstimator):
    """
    Two-stage regression with marginal selection and UniLasso on both main effects and interactions via CV.

    Parameters
    ----------
    lmda_path : array-like of shape (n_lmdas,)
        Path of the lambda values for UniLasso. If None, it will be generated using generate_lambda_path.  

    n_folds : int
        Number of folds for cross-validation.

    plot_cv_curve : bool  
        If true, plot the CV R2 against -log(λ).

    cv1se : bool 
        If true, use the one-standard error rule at CV. 

    verbose : bool
        If true, print progress messages.

    interaction_candidates : array-like of int, optional
        Restrict interactions to those involving any of these variable indices (0-based indices).

    interaction_pairs : array-like of shape (n_pairs, 2), optional
        Restrict interactions to exactly these pairs of variables (0-based indices).

    Attributes
    ----------
    n_features\_ : int
        Number of features in the dataset.

    regressor\_ : UniLasso object
        Fitted Unilasso model after CV.

    triplet_regressors\_ : dict of dict of OLS
        Dictionary of OLS models for each triplet (X_j, X_k, X_j*X_k).

    selected_pairs\_ : array-like of shape (n_pairs, 2)
        Selected interaction pairs (j, k).

    main_effects_active_set\_ : array-like
        Indices of active main effects.

    interactios_active_set\_ : array-like
        Indices of active interactions.

    n_folds\_ : int
        Number of folds for cross-validation.

    main_effects_names\_ : list of str
        Names of the main effects.

    interactions_names\_ : list of str
        Names of the interaction terms.

    cv_errors\_ : array-like of shape (n_folds, n_lmdas)
        Cross-validation errors.

    lmda_path\_ : array-like
        Lmda path for cv  

    plot_cv_curve\_ : bool
        If true, plot the CV R2 against -log(λ).

    cv1se\_ : bool 
        If true, use the one-standard error rule at CV. 

    verbose\_ : bool
        If true, print progress messages.

    interaction_candidates\_ : array-like of int
        Restrict interactions to those involving any of these variable indices (0-based indices).
    
    interaction_pairs\_ : array-like of shape (n_pairs, 2)
        Restrict interactions to exactly these pairs of variables (0-based indices).
    """
    
    def __init__(self, lmda_path=None, n_folds=10, plot_cv_curve=False, cv1se=False, verbose=False, interaction_candidates=None, interaction_pairs=None):

        """
        Two-stage regression with marginal selection and UniLasso on both main effects and interactions via CV.

        Parameters
        ----------
        lmda_path : array-like of shape (n_lmdas,)
            Path of the lambda values for UniLasso. If None, it will be generated using generate_lambda_path.  

        n_folds : int
            Number of folds for cross-validation.

        plot_cv_curve : bool  
            If true, plot the CV R2 against -log(λ).

        cv1se : bool 
            If true, use the one-standard error rule at CV. 

        verbose : bool
            If true, print progress messages.

        interaction_candidates : array-like of int, optional
            Restrict interactions to those involving any of these variable indices (0-based indices).

        interaction_pairs : array-like of shape (n_pairs, 2), optional
            Restrict interactions to exactly these pairs of variables (0-based indices).

        Attributes
        ----------
        n_features\_ : int
            Number of features in the dataset.

        regressor\_ : UniLasso object
            Fitted Unilasso model after CV.

        triplet_regressors\_ : dict of dict of OLS
            Dictionary of OLS models for each triplet (X_j, X_k, X_j*X_k).

        selected_pairs\_ : array-like of shape (n_pairs, 2)
            Selected interaction pairs (j, k).

        main_effects_active_set\_ : array-like
            Indices of active main effects.

        interactios_active_set\_ : array-like
            Indices of active interactions.

        n_folds\_ : int
            Number of folds for cross-validation.

        main_effects_names\_ : list of str
            Names of the main effects.

        interactions_names\_ : list of str
            Names of the interaction terms.

        cv_errors\_ : array-like of shape (n_folds, n_lmdas)
            Cross-validation errors.

        lmda_path\_ : array-like
            Lmda path for cv  

        plot_cv_curve\_ : bool
            If true, plot the CV R2 against -log(λ).

        cv1se\_ : bool 
            If true, use the one-standard error rule at CV. 

        verbose\_ : bool
            If true, print progress messages.

        interaction_candidates\_ : array-like of int
            Restrict interactions to those involving any of these variable indices (0-based indices).
        
        interaction_pairs\_ : array-like of shape (n_pairs, 2)
            Restrict interactions to exactly these pairs of variables (0-based indices).
        """
        
        if interaction_candidates is not None and interaction_pairs is not None:
            raise ValueError("Specify only one of interaction_candidates or interaction_pairs, not both.")

        self.regressor_ = UniLasso(lmda_path=lmda_path)
        self.triplet_regressors_ = None
        
        self.n_folds_ = n_folds

        self.n_features_ = None
        self.main_effects_active_set_ = None
        self.selected_pairs_ = None

        self.main_effects_names_ = None
        self.interactions_names_ = None
        self.cv_errors = None
        self.lmda_path_ = None
        self.plot_cv_curve_ = plot_cv_curve
        self.cv1se_ = cv1se
        self.verbose_ = verbose
        self.interaction_candidates_ = (
            np.asarray(interaction_candidates, dtype=int)
            if interaction_candidates is not None else None
        )
        self.interaction_pairs_ = (
            np.asarray(interaction_pairs, dtype=int)
            if interaction_pairs is not None else None
        )
        if self.interaction_pairs_ is not None:
            if self.interaction_pairs_.ndim != 2 or self.interaction_pairs_.shape[1] != 2:
                raise ValueError("interaction_pairs must be a 2D array-like with shape (n_pairs, 2).")
        
        if self.interaction_candidates_ is not None:
            if self.interaction_candidates_.ndim != 1:
                raise ValueError("interaction_candidates must be a 1D array-like of variable indices.")



    def fit_triplet_models(self,X, y):
        """
        Regress y on [X_j,X_k,X_j*X_k] with intercept for all j<k

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Design matrix.
        y : array-like of shape (n_samples,)
            Response vector.

        Returns
        -------
        None 
        """
        n, p = X.shape
        assert p>1
        if not (n > 3):
            raise ValueError("Need at least 4 samples to fit triplet OLS models.")
        
        if self.interaction_pairs_ is not None:
            allowed_pairs = [tuple(pair) for pair in self.interaction_pairs_]
        elif self.interaction_candidates_ is not None:
            allowed_pairs = [
                (j, k)
                for j in range(p - 1)
                for k in range(j + 1, p)
                if (j in self.interaction_candidates_ or k in self.interaction_candidates_)
            ]
        else:
            allowed_pairs = [(j, k) for j in range(p - 1) for k in range(j + 1, p)]
    
        total_pairs = len(allowed_pairs)
        if self.verbose_:
            print(f"  Fitting {total_pairs} triplet OLS models...")

        for count, (j, k) in enumerate(allowed_pairs, start=1):
            F = np.hstack([X[:, j : j + 1], X[:, k : k + 1], X[:, j : j + 1] * X[:, k : k + 1]])                        # (n, 3)
            self.triplet_regressors_[j][k].fit(F, y)
            if self.verbose_ and count % max(1, total_pairs // 10) == 0:
                print(f"  Progress: {count}/{total_pairs} triplets fitted...")
        if self.verbose_:
            print("  Triplet model fitting complete.")
    
    def scan_interactions(self):
        """
        Implements the screening procedure for the interactions.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Design matrix.
        y : array-like of shape (n_samples,)
            Response vector.
    
        Returns
        -------
        None
        """

        n_features = self.n_features_

        if self.triplet_regressors_ is None:
            raise RuntimeError("triplet_regressors_ not initialized. Call fit_triplet_models first.")

        if self.verbose_:
            print("Scanning interaction using p-values ...")

        if self.interaction_pairs_ is not None:
            allowed_pairs = [tuple(pair) for pair in self.interaction_pairs_]
        elif self.interaction_candidates_ is not None:
            allowed_pairs = [
                (j, k)
                for j in range(n_features - 1)
                for k in range(j + 1, n_features)
                if (j in self.interaction_candidates_ or k in self.interaction_candidates_)
            ]
        else:
            allowed_pairs = [(j, k) for j in range(n_features - 1) for k in range(j + 1, n_features)]


        scan_coefs = np.zeros((n_features,n_features))
        pvals = np.ones((n_features,n_features))
        for j, k in allowed_pairs:
            pvals[j,k] = self.triplet_regressors_[j][k].p_value_t_test_[-1]
            scan_coefs[j,k] = np.abs(self.triplet_regressors_[j][k].slopes_[-1])
    

        pvals_ea = {(j,k):self.triplet_regressors_[j][k].p_value_t_test_[-1] for (j,k) in allowed_pairs}
        
        # point that best separates the two clusters 
        pvals_ea_sorted = sorted(pvals_ea.items(),key=lambda x: x[1],reverse=False) # ascending order 
        num_zeros_ea = len(pvals_ea_sorted) - len([pval for _,pval in pvals_ea_sorted if pval>1e-20])
        tmp = [pval for _,pval in pvals_ea_sorted if pval>1e-20]
        # forcing strong hierarchy 
        if len(tmp)<=1 : 
            selected_pairs_ea = [pair for (pair,_) in pvals_ea_sorted]
        else : 
            tmp = np.log(np.array(tmp)) # need to investigate why taking log of pvalues does better than using their raw value
            i_tmp = np.argmax(tmp[1:]-tmp[:-1]) + num_zeros_ea
            selected_pairs_ea = [pair for (pair,_) in pvals_ea_sorted[:i_tmp+1]]

        if self.verbose_:
            print(f"  Selected {len(selected_pairs_ea)} interactions.")

        if self.plot_cv_curve_ : 
            
            mask = np.triu(np.ones_like(pvals, dtype=bool), k=1)
            pv = pvals[mask]
            plt.figure(figsize=(8, 5))
            plt.hist(pv, bins=int(len(pv)/20), edgecolor='black')

            sel_pv = [pvals[j,k] for j,k in selected_pairs_ea]
            plt.scatter(sel_pv, np.zeros_like(sel_pv), color='orange', s=50,label='selected pairs', zorder=10)

            plt.xlabel('p-value')
            plt.ylabel('Count')
            plt.legend()
            plt.tight_layout()
            plt.show()

            mask = np.tril(np.ones_like(pvals, dtype=bool), k=0)
            plt.figure(figsize=(8, 8))
            ax = sns.heatmap(
                pvals,
                mask=mask,
                cmap='viridis',
                xticklabels=self.main_effects_names_,
                yticklabels=self.main_effects_names_,
                vmin=0,
                vmax=1,
                square=True,
                cbar_kws={"shrink": .8}
            )
            ax.set_facecolor('white')
            for j, k in selected_pairs_ea:
                ax.text(k + 0.5,j + 0.5,'★',ha='center', va='center',color='white',fontsize=16,zorder=10)
            plt.tight_layout()
            plt.show()

        self.selected_pairs_ = np.array(selected_pairs_ea)
        
    def fit(self, X, y, lmda_path=None, tolerance=1e-10):
        """
        Fit the Unilasso regression model with interactions.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Design matrix.
        y : array-like of shape (n_samples,)
            Response vector.

        Returns
        -------
        None
        """
        
        X, y = check_X_y(X, y, y_numeric=True)
        _, n_features = X.shape
        self.n_features_ = n_features

        if self.interaction_pairs_ is not None:
            max_idx = self.interaction_pairs_.max()
            if max_idx >= n_features:
                raise ValueError("interaction_pairs contain indices out of range for X.")
        if self.interaction_candidates_ is not None:
            max_idx = self.interaction_candidates_.max()
            if max_idx >= n_features:
                raise ValueError("interaction_candidates contain indices out of range for X.")
            
        self.main_effects_names_ = [f'X{j}' for j in range(n_features)]
        self.triplet_regressors_  = {j:{k:OLS(vars_names=[f'X{j}',f'X{k}',f'X{j}*X{k}']) for k in range(j+1,n_features)} for j in range(n_features-1)}
        
        if self.verbose_:
            print(f"Starting MARINER fit with {n_features} features ...")

        if n_features > 1 : 
            if self.verbose_:
                print("Step 1: Fitting triplet models ...")
            self.fit_triplet_models(X, y)
            if self.verbose_:
                print("Step 2: Scanning interactions ...")
            self.scan_interactions()
            if self.verbose_:
                print("Step 3: Constructing interaction matrix ...")
            interactions_X, self.interactions_names_ = make_interactions(X, self.selected_pairs_)                               # (n_samples, n_pairs)
            full_X = np.hstack([X,interactions_X])
        else :
            full_X = X
            self.interactions_names_ = []


        self.regressor_.set_vars_names(self.main_effects_names_+self.interactions_names_)
        if self.verbose_:
            print("Step 4: Cross-validating UniLasso ...")
        cv_results = cv(
            base=self.regressor_,
            X=full_X,
            y=y,
            n_folds=self.n_folds_,
            lmda_path=lmda_path,
            plot_cv_curve=self.plot_cv_curve_,
            cv1se=self.cv1se_
        ) # self.regressor_ is fited in-place after CV
        self.lmda_path_ = cv_results['lmda_path']
        self.cv_errors_ = cv_results['cv_errors']
        main_effects_slopes = self.regressor_.slopes_[:1,:n_features]                                                           # (1, n_features)
        interactions_slopes = self.regressor_.slopes_[:1,n_features:]                                                           # (1, n_pairs)
        self.main_effects_active_set_ = np.where(np.abs(main_effects_slopes) > tolerance)[1] 
        self.interactions_active_set_ = np.where(np.abs(interactions_slopes) > tolerance)[1] 
        if self.verbose_:
            print("MARINER fit complete.\n")
    def get_active_variables(self):
        """
        Get the names of the active variables for the fitted model.
        This includes both main effects and interactions.

        Parameters
        ----------
        None

        Returns
        -------
        active_vars : list of str
            List of names of the active variables.
        """
        check_is_fitted(self.regressor_)
        
        active_vars = []
        
        for i in self.main_effects_active_set_:
            active_vars.append(self.main_effects_names_[i])
    
        if self.n_features_>1:
            for i in self.interactions_active_set_:
                active_vars.append(self.interactions_names_[i])

        return active_vars
    
    def get_fitted_function(self, tolerance=1e-10):
        """
        Get the fitted model string representation.

        Parameters
        ----------
        None

        Returns
        -------
        fitted_model_rep : str
            string representation of the fitted model
        """
        check_is_fitted(self.regressor_)
        
        return self.regressor_.get_fitted_function(self.regressor_.lmda_path_[0],tolerance) 
         
    def predict(self, X):
        """
        Predict using the two-stage regression model with interactions.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Design matrix.

        Returns
        -------
        y_pred : array-like of shape (n_samples,)
            Predicted values using the two-stage regression model.
        """
        check_is_fitted(self.regressor_)
        
        X = check_array(X)

        if self.n_features_>1:
            interactions_X, _ = make_interactions(X,self.selected_pairs_)
            full_X = np.hstack([X,interactions_X])
        else : 
            full_X = X

        return self.regressor_.predict(full_X)[:,0]                                                                             # (n_samples, )
    