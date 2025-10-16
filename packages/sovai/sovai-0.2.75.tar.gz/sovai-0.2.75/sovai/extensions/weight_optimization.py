# from plotly.io import show
from sklearn.model_selection import GridSearchCV
from skfolio import Population, RatioMeasure, RiskMeasure
from skfolio.cluster import HierarchicalClustering, LinkageMethod
from skfolio.distance import KendallDistance, PearsonDistance
from skfolio.metrics import make_scorer
from skfolio.model_selection import (
    CombinatorialPurgedCV,
    WalkForward,
    cross_val_predict,
    optimal_folds_number,
)
from skfolio.optimization import (
    EqualWeighted,
    HierarchicalEqualRiskContribution,
    HierarchicalRiskParity,
    MeanRisk,
    NestedClustersOptimization,
    ObjectiveFunction,
    RiskBudgeting,
)

# from skfolio.preprocessing import prices_to_returns
from skfolio.moments import (
    DenoiseCovariance,
    DetoneCovariance,
    EWMu,
    GerberCovariance,
    ShrunkMu,
)

import warnings

from datetime import datetime, timedelta

import pandas as pd


class WeightOptimization:
    def __init__(self, df_select):
        self.df_select = df_select
        self.initialize()

    def initialize(self):
        # Set up cross-validation
        self.cv = WalkForward(train_size=252, test_size=90)

        # Initialize models
        self.model_hrp = HierarchicalRiskParity(
            risk_measure=RiskMeasure.CVAR,
            hierarchical_clustering_estimator=HierarchicalClustering(),
        )

        self.model_herc = HierarchicalEqualRiskContribution(
            risk_measure=RiskMeasure.CVAR,
            hierarchical_clustering_estimator=HierarchicalClustering(),
        )

        self.model_nco = NestedClustersOptimization(
            inner_estimator=MeanRisk(), clustering_estimator=HierarchicalClustering()
        )

        self.bench = EqualWeighted()

        # Perform GridSearch for HRP
        grid_search_hrp = GridSearchCV(
            estimator=self.model_hrp,
            cv=self.cv,
            n_jobs=-1,
            param_grid={
                "distance_estimator": [PearsonDistance(), KendallDistance()],
                "hierarchical_clustering_estimator__linkage_method": [
                    LinkageMethod.WARD,
                    LinkageMethod.COMPLETE,
                ],
            },
            scoring=make_scorer(RatioMeasure.CVAR_RATIO),
        )
        grid_search_hrp.fit(self.df_select)
        self.model_hrp = grid_search_hrp.best_estimator_

        # Perform GridSearch for HERC
        grid_search_herc = grid_search_hrp.set_params(estimator=self.model_herc)
        grid_search_herc.fit(self.df_select)
        self.model_herc = grid_search_herc.best_estimator_

        # Perform GridSearch for NCO
        grid_search_nco = GridSearchCV(
            estimator=self.model_nco,
            cv=self.cv,
            n_jobs=-1,
            param_grid={
                "inner_estimator__risk_measure": [
                    RiskMeasure.VARIANCE,
                    RiskMeasure.CVAR,
                ],
                "outer_estimator": [
                    EqualWeighted(),
                    RiskBudgeting(risk_measure=RiskMeasure.CVAR),
                ],
                "clustering_estimator__linkage_method": [
                    LinkageMethod.SINGLE,
                    LinkageMethod.WARD,
                ],
                "distance_estimator": [PearsonDistance(), KendallDistance()],
            },
        )
        grid_search_nco.fit(self.df_select)
        self.model_nco = grid_search_nco.best_estimator_

        # Perform cross-validation predictions
        self.pred_hrp = cross_val_predict(
            self.model_hrp,
            self.df_select,
            cv=self.cv,
            n_jobs=-1,
            portfolio_params=dict(name="HRP", tag="HRP"),
        )

        self.pred_herc = cross_val_predict(
            self.model_herc,
            self.df_select,
            cv=self.cv,
            n_jobs=-1,
            portfolio_params=dict(name="HERC"),
        )

        self.pred_nco = cross_val_predict(
            self.model_nco,
            self.df_select,
            cv=self.cv,
            n_jobs=-1,
            portfolio_params=dict(name="NCO"),
        )

        self.pred_bench = cross_val_predict(
            self.bench,
            self.df_select,
            cv=self.cv,
            n_jobs=-1,
            portfolio_params=dict(name="EQUAL"),
        )

        # Set up combinatorial cross-validation
        n_folds, n_test_folds = optimal_folds_number(
            n_observations=self.df_select.shape[0],
            target_n_test_paths=50,
            target_train_size=252,
        )
        cv_comb = CombinatorialPurgedCV(n_folds=n_folds, n_test_folds=n_test_folds)

        # Perform combinatorial cross-validation predictions
        self.pred_hrp_comb = cross_val_predict(
            self.model_hrp,
            self.df_select,
            cv=cv_comb,
            n_jobs=-1,
            portfolio_params=dict(tag="HRP"),
        )

        self.pred_herc_comb = cross_val_predict(
            self.model_herc,
            self.df_select,
            cv=cv_comb,
            n_jobs=-1,
            portfolio_params=dict(tag="HERC"),
        )

        self.pred_nco_comb = cross_val_predict(
            self.model_nco,
            self.df_select,
            cv=cv_comb,
            n_jobs=-1,
            portfolio_params=dict(tag="NCO"),
        )

        self.pred_bench_comb = cross_val_predict(
            self.bench,
            self.df_select,
            cv=cv_comb,
            n_jobs=-1,
            portfolio_params=dict(tag="EQUAL"),
        )

        # Create summary dictionaries and populations
        self.summary_dict_model = {
            "HRP": self.model_hrp,
            "HERC": self.model_herc,
            "NCO": self.model_nco,
            "EQUAL": self.bench,
        }

        self.summary_dict = {
            "HRP": self.pred_hrp,
            "HERC": self.pred_herc,
            "NCO": self.pred_nco,
            "EQUAL": self.pred_bench,
        }

        self.population = Population(
            [self.pred_hrp, self.pred_herc, self.pred_nco, self.pred_bench]
        )

        self.summary_dict_comb = {
            "HRP": self.pred_hrp_comb,
            "HERC": self.pred_herc_comb,
            "NCO": self.pred_nco_comb,
            "EQUAL": self.pred_bench_comb,
        }

        self.population_combinatorial = (
            self.pred_hrp_comb
            + self.pred_herc_comb
            + self.pred_nco_comb
            + self.pred_bench_comb
        )

        # Initialize portfolio attributes
        self.initialize_portfolio()

        for model_name in ["HRP", "HERC", "NCO", "EQUAL"]:
            self.calculate_daily_weights(model_name)

    def calculate_daily_weights(self, model_name):
        model_composition = self.summary_dict[model_name].composition
        daily_weights = self.create_daily_weights(self.df_select, model_composition)
        getattr(self, model_name).daily_weights = daily_weights

    def create_daily_weights(
        self, df_select, model_composition, train_size=252, test_size=90
    ):
        # Create a DataFrame with the same index and columns as df_select
        daily_weights = pd.DataFrame(
            index=df_select.index, columns=df_select.columns, dtype=float
        )

        # Calculate the start date for the first prediction
        start_date = df_select.index[train_size]

        # Generate rebalancing dates
        rebalancing_dates = [start_date]
        current_date = start_date
        while current_date < df_select.index[-1]:
            current_date += timedelta(days=test_size)
            if current_date <= df_select.index[-1]:
                rebalancing_dates.append(current_date)

        # Determine the number of periods to iterate over
        n_periods = min(len(rebalancing_dates), model_composition.shape[1])

        # Iterate through the rebalancing dates
        for i in range(n_periods):
            rebalance_date = rebalancing_dates[i]
            # Get weights for this period
            weights = model_composition.iloc[:, i]

            # Determine end date for this period
            if i == n_periods - 1:
                end_date = df_select.index[-1]
            else:
                end_date = rebalancing_dates[i + 1] - timedelta(days=1)

            # Align the weights with df_select columns
            aligned_weights = weights.reindex(df_select.columns, fill_value=0)

            # Fill the weights for this period
            daily_weights.loc[rebalance_date:end_date] = aligned_weights.values

        # Forward fill any remaining NaN values
        daily_weights = daily_weights.ffill()

        # Ensure we only have weights for dates after the first prediction date
        daily_weights = daily_weights.loc[start_date:]

        return daily_weights

    def initialize_portfolio(self):
        self.population.set_portfolio_params(compounded=False)
        self.return_plot = self.population.plot_cumulative_returns()
        self.performance_report = self.population.summary()
        self.best_model = (
            self.performance_report.T["Sharpe Ratio"].sort_values().index[-1]
        )
        self.sharpe_plot = self.population_combinatorial.plot_distribution(
            measure_list=[RatioMeasure.ANNUALIZED_SHARPE_RATIO],
            tag_list=["HRP", "HERC", "NCO"],
            n_bins=50,
        )

        population_test = Population([])
        for model in [self.model_hrp, self.model_herc, self.model_nco, self.bench]:
            model.fit(self.df_select.tail(252))
            population_test.append(model.predict(self.df_select.tail(252)))
        self.composition_plot = population_test.plot_composition()

        for model_name in ["HRP", "HERC", "NCO", "EQUAL"]:
            self.initialize_model(model_name)

    def initialize_model(self, model_name):
        model_data = PortfolioItem()

        model_data.backtest_report = (
            self.summary_dict_comb[model_name]
            .summary()
            .T.sort_values("Mean", ascending=False)
        )

        model_data.sharpe_rolling_plot = self.summary_dict[
            model_name
        ].plot_rolling_measure(measure=RatioMeasure.SHARPE_RATIO)
        model_data.sharpe_dist_plot = self.summary_dict_comb[
            model_name
        ].plot_distribution(
            measure_list=[RatioMeasure.ANNUALIZED_SHARPE_RATIO], n_bins=50
        )

        model_data.backtest_plot = self.summary_dict_comb[
            model_name
        ].plot_cumulative_returns()
        model_data.composition_plot = Population(
            [self.summary_dict[model_name]]
        ).plot_composition(display_sub_ptf_name=False)

        model_short_untrained = self.summary_dict_model[model_name]

        model_short = model_short_untrained.fit(self.df_select.tail(252)).predict(
            self.df_select.tail(252)
        )

        model_data.drawdown_contribution_plot = model_short.plot_contribution(
            measure=RiskMeasure.AVERAGE_DRAWDOWN
        )

        model_data.sharpe_contribution_plot = model_short.plot_contribution(
            measure=RatioMeasure.SHARPE_RATIO
        )

        # Get the last date of the df_select
        last_date = self.df_select.index[-1]

        # Create a DataFrame with just the last row
        daily_weights = pd.DataFrame(index=[last_date], columns=self.df_select.columns)

        # Set the weights of the last row to the current model weights
        daily_weights.loc[last_date] = model_short_untrained.weights_

        daily_weights.index.name = model_name

        model_data.recommended_allocation = daily_weights

        if model_name != "EQUAL":
            try:
                dendo = self.summary_dict_model[
                    model_name
                ].clustering_estimator_.plot_dendrogram(heatmap=False)
                dendo_map = self.summary_dict_model[
                    model_name
                ].clustering_estimator_.plot_dendrogram(heatmap=True)
            except AttributeError:
                dendo = self.summary_dict_model[
                    model_name
                ].hierarchical_clustering_estimator_.plot_dendrogram(heatmap=False)
                dendo_map = self.summary_dict_model[
                    model_name
                ].hierarchical_clustering_estimator_.plot_dendrogram(heatmap=True)

            model_data.cluster_plot = dendo
            model_data.heatmap_plot = dendo_map
        else:
            model_data.cluster_plot = (
                "Cluster plot does not exist for EqualWeighted model"
            )
            model_data.heatmap_plot = "Heatmap does not exist for EqualWeighted model"

        setattr(self, model_name, model_data)

        warnings.simplefilter("ignore", RuntimeWarning)

    def __getitem__(self, key):
        return getattr(self, key)


class PortfolioItem:
    pass


# Now you can access the portfolio attributes and model-specific attributes as requested:
# portfolio["HRP"].sharpe_plot
# portfolio.plot_return
