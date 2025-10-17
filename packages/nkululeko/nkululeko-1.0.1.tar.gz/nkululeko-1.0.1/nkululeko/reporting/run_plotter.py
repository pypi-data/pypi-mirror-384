import matplotlib.pyplot as plt
import seaborn as sns
from statistics import mean, stdev
import pandas as pd
import numpy as np
import os
import audeer
import math

# from torch import is_tensor
from audmetric import accuracy
from audmetric import concordance_cc
from audmetric import mean_absolute_error
from audmetric import mean_squared_error
from audmetric import unweighted_average_recall

from nkululeko.experiment import Experiment
from nkululeko.plots import Plots
from nkululeko.reporting.defines import Header
from nkululeko.reporting.report_item import ReportItem
from nkululeko.reporting.result import Result
from nkululeko.utils.util import Util
from nkululeko.utils.files import find_files_by_name
from nkululeko.utils.stats import find_most_significant_difference


class Run_plotter:
    def __init__(self, experiment):
        self.util = Util("run_plotter")
        self.format = self.util.config_val("PLOT", "format", "png")
        self.exp = experiment
        self.titles = eval(self.util.config_val("PLOT", "titles", "True"))

    def get_compare(self, compare: str = "features", file_name: str = ""):
        parts = file_name.split("_")
        if len(parts) < 4:
            self.util.error(
                f"file name '{file_name}' does not have at least 4 underscore-separated parts"
            )
            return None
        if compare == "features":
            return parts[3]
        elif compare == "model":
            return parts[2]
        elif compare == "target":
            return parts[1]
        elif compare == "databases":
            return parts[0]
        else:
            self.util.error(f"unknown compare option {compare} with {file_name}")
            return None

    def plot(self, compare_target: str = "features"):
        run_num = int(self.util.config_val("EXP", "runs", 1))
        print_stats = eval(self.util.config_val("EXPL", "print_stats", "False"))
        plot_name = f"{self.exp.util.get_exp_name()}_runs_plot"
        # one up because of the runs
        results_dir = audeer.path(self.exp.util.get_path("res_dir"), "..")
        run_files = find_files_by_name(directory=results_dir, pattern="_runs")
        run_results = []
        compares = []
        for file in run_files:
            results = self.util.read_first_line_floats(file_path=file, delimiter=",")
            run_results.append(results)
            file_name = os.path.basename(file)
            compare = self.get_compare(compare_target, file_name)
            compares.append(compare)
        if len(run_results) < 2:
            self.util.warn(
                f"need at least two different {compare_target} to compare, found {len(run_results)}"
            )
            return
        data = dict(zip(compares, run_results))
        df_plot = pd.DataFrame(
            data=data,
            index=[f"run {i+1}" for i in range(len(run_results[0]))],
        )
        pairwise_results, overall_results = find_most_significant_difference(
            data, run_num
        )
        # 'approach', 'combo', test statistic, 'p_value', 'significance','all_results'
        if print_stats:
            if overall_results is not None:
                self.util.debug(
                    f"overall results from statistical test: {overall_results['all_results']}"
                )
            self.util.debug(
                f"pairwise results from statistical test: {pairwise_results['all_results']}"
            )
        metric = self.util.config_val("MODEL", "measure", "uar").upper()
        sns.boxplot(data=df_plot)
        if self.titles:
            if len(run_results) > 2:
                plt.title(
                    f"Comparison of {compare_target} over {run_num} runs\n"
                    + f"{overall_results['approach']}: {overall_results['combo']}: "
                    f"{overall_results['significance']}\n"
                    + f"{pairwise_results['approach']}: {pairwise_results['combo']}: "
                    f"{pairwise_results['significance']}"
                )
            else:
                plt.title(
                    f"Comparison of {compare_target} over {run_num} runs\n"
                    + f"{pairwise_results['approach']}: {pairwise_results['combo']}: "
                    f"{pairwise_results['significance']} (p={pairwise_results['p_value']:.3f})"
                )
        plt.ylabel(metric)
        plt.xlabel(compare_target)
        plt.tight_layout()
        fig_dir = audeer.path(self.exp.util.get_path("fig_dir"), "..")
        img_path = f"{fig_dir}/{plot_name}.{self.format}"
        self.util.debug(f"plotted overview on runs as boxplots to {img_path}")

        plt.savefig(img_path)
        plt.close()

        res_lists = []
        for i, run_result in enumerate(run_results):
            res_list = [
                min(run_result),
                max(run_result),
                mean(run_result),
            ]
            res_lists.append(res_list)
        data = dict(zip(compares, res_lists))
        df = pd.DataFrame(
            data=data,
            index=["min", "max", "mean"],
        )
        plot_df = df.unstack().reset_index(name=metric)
        plot_df.rename(
            columns={"level_0": compare_target, "level_1": "statistic"}, inplace=True
        )
        f = lambda x: math.trunc(1000 * float(x)) / 1000
        plot_df[metric] = plot_df[metric].apply(f)
        ax = sns.barplot(data=plot_df, x=compare_target, y=metric, hue="statistic")
        ax.bar_label(ax.containers[0])
        ax.bar_label(ax.containers[1])
        ax.bar_label(ax.containers[2])
        plt.title(f"Comparison of {compare_target} over {run_num} runs")
        plt.tight_layout()
        img_path = f"{fig_dir}/{plot_name}_bar.{self.format}"
        self.util.debug(f"plotted overview on runs as barplot to {img_path}")
        plt.savefig(img_path)
        plt.close()
