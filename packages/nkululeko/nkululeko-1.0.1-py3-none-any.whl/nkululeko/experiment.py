# nkululeko/experiment.py: Main class for an experiment (nkululeko.nkululeko)
import ast
import os
import pickle
import random
import time

import audeer
import audformat
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

import nkululeko.glob_conf as glob_conf
from nkululeko.data.dataset import Dataset
from nkululeko.data.dataset_csv import Dataset_CSV
from nkululeko.demo_predictor import Demo_predictor
from nkululeko.feat_extract.feats_analyser import FeatureAnalyser
from nkululeko.feature_extractor import FeatureExtractor
from nkululeko.file_checker import FileChecker
from nkululeko.filter_data import DataFilter
from nkululeko.plots import Plots
from nkululeko.reporting.report import Report
from nkululeko.runmanager import Runmanager
from nkululeko.scaler import Scaler
from nkululeko.testing_predictor import TestPredictor
from nkululeko.utils.util import Util


class Experiment:
    """Main class specifying an experiment."""

    def __init__(self, config_obj):
        """Constructor.

        Args:
            - config_obj : a config parser object that sets the experiment parameters and being set as a global object.
        """
        self.set_globals(config_obj)
        self.name = glob_conf.config["EXP"]["name"]
        self.root = os.path.join(glob_conf.config["EXP"]["root"], "")
        self.data_dir = os.path.join(self.root, self.name)
        audeer.mkdir(self.data_dir)  # create the experiment directory
        self.util = Util("experiment")
        glob_conf.set_util(self.util)
        self.split3 = eval(self.util.config_val("EXP", "traindevtest", "False"))
        fresh_report = eval(self.util.config_val("REPORT", "fresh", "False"))
        if not fresh_report:
            try:
                with open(os.path.join(self.data_dir, "report.pkl"), "rb") as handle:
                    self.report = pickle.load(handle)
            except FileNotFoundError:
                self.report = Report()
        else:
            self.util.debug("starting a fresh report")
            self.report = Report()
        glob_conf.set_report(self.report)
        self.loso = self.util.config_val("MODEL", "loso", False)
        self.logo = self.util.config_val("MODEL", "logo", False)
        self.xfoldx = self.util.config_val("MODEL", "k_fold_cross", False)
        self.start = time.process_time()

    def set_module(self, module):
        glob_conf.set_module(module)

    def store_report(self):
        with open(os.path.join(self.data_dir, "report.pkl"), "wb") as handle:
            pickle.dump(self.report, handle)
        if eval(self.util.config_val("REPORT", "show", "False")):
            self.report.print()
        if self.util.config_val("REPORT", "latex", False):
            self.report.export_latex()

    # moved to util
    # def get_name(self):
    #     return self.util.get_exp_name()

    def set_globals(self, config_obj):
        """Install a config object in the global space."""
        glob_conf.init_config(config_obj)

    def load_datasets(self):
        """Load all databases specified in the configuration and map the labels."""
        ds = ast.literal_eval(glob_conf.config["DATA"]["databases"])
        self.datasets = {}
        self.got_speaker, self.got_gender, self.got_age = False, False, False
        for d in ds:
            ds_type = self.util.config_val_data(d, "type", "audformat")
            if ds_type == "audformat":
                data = Dataset(d)
            elif ds_type == "csv":
                data = Dataset_CSV(d)
            else:
                self.util.error(f"unknown data type: {ds_type}")
            data.load()
            data.prepare()
            if data.got_gender:
                self.got_gender = True
            if data.got_age:
                self.got_age = True
            if data.got_speaker:
                self.got_speaker = True
            self.datasets.update({d: data})
        self.target = self.util.config_val("DATA", "target", "none")
        glob_conf.set_target(self.target)
        # print target via debug
        self.util.debug(f"target: {self.target}")
        # print keys/column
        dbs = ",".join(list(self.datasets.keys()))
        if self.target == "none":
            self.util.debug(f"loaded databases {dbs}")
            return
        labels = self.util.config_val("DATA", "labels", False)
        auto_labels = list(next(iter(self.datasets.values())).df[self.target].unique())
        if labels:
            self.labels = ast.literal_eval(labels)
            self.util.debug(f"Using target labels (from config): {labels}")
        else:
            self.labels = auto_labels
        # print autolabel no matter it is specified or not
        self.util.debug(f"Labels (from database): {auto_labels}")
        glob_conf.set_labels(self.labels)
        self.util.debug(f"loaded databases {dbs}")

    def _import_csv(self, storage):
        # df = pd.read_csv(storage, header=0, index_col=[0,1,2])
        # df.index.set_levels(pd.to_timedelta(df.index.levels[1]), level=1)
        # df.index.set_levels(pd.to_timedelta(df.index.levels[2]), level=2)
        try:
            df = audformat.utils.read_csv(storage)
        except ValueError:
            # split might be empty
            return pd.DataFrame()
        if isinstance(df, pd.Series):
            df = df.to_frame()
        elif isinstance(df, pd.Index):
            df = pd.DataFrame(index=df)
        df.is_labeled = True if self.target in df else False
        # print(df.head())
        return df

    def fill_tests(self):
        """Only fill a new test set"""

        test_dbs = ast.literal_eval(glob_conf.config["DATA"]["tests"])
        self.df_test = pd.DataFrame()
        start_fresh = eval(self.util.config_val("DATA", "no_reuse", "False"))
        store = self.util.get_path("store")
        storage_test = f"{store}extra_testdf.csv"
        if os.path.isfile(storage_test) and not start_fresh:
            self.util.debug(f"reusing previously stored {storage_test}")
            self.df_test = self._import_csv(storage_test)
        else:
            for d in test_dbs:
                ds_type = self.util.config_val_data(d, "type", "audformat")
                if ds_type == "audformat":
                    data = Dataset(d)
                elif ds_type == "csv":
                    data = Dataset_CSV(d)
                else:
                    self.util.error(f"unknown data type: {ds_type}")
                data.load()
                if data.got_gender:
                    self.got_gender = True
                if data.got_age:
                    self.got_age = True
                if data.got_speaker:
                    self.got_speaker = True
                data.split()
                data.prepare_labels()
                self.df_test = pd.concat(
                    [self.df_test, self.util.make_segmented_index(data.df_test)]
                )
                self.df_test.is_labeled = data.is_labeled
            self.df_test.got_gender = self.got_gender
            self.df_test.got_speaker = self.got_speaker
            # self.util.set_config_val('FEATS', 'needs_features_extraction', 'True')
            # self.util.set_config_val('FEATS', 'no_reuse', 'True')
            self.df_test["class_label"] = self.df_test[self.target]
            self.df_test[self.target] = self.label_encoder.transform(
                self.df_test[self.target]
            )
            self.df_test.to_csv(storage_test)

    def fill_train_and_tests(self):
        """Set up train and development sets. The method should be specified in the config."""
        store = self.util.get_path("store")
        storage_test = f"{store}testdf.csv"
        storage_train = f"{store}traindf.csv"
        self.df_dev = None
        self.feats_dev = None
        if self.split3:
            storage_dev = f"{store}devdf.csv"
        start_fresh = eval(self.util.config_val("DATA", "no_reuse", "False"))
        if (
            os.path.isfile(storage_train)
            and os.path.isfile(storage_test)
            and not start_fresh
        ):
            self.util.debug(
                f"reusing previously stored {storage_test} and {storage_train}"
            )
            self.df_test = self._import_csv(storage_test)
            self.df_train = self._import_csv(storage_train)
            self.train_empty = True if self.df_train.shape[0] == 0 else False
            self.test_empty = True if self.df_test.shape[0] == 0 else False
            if self.split3:
                self.df_dev = self._import_csv(storage_dev)
                self.dev_empty = True if self.df_dev.shape[0] == 0 else False
        else:
            self.df_train, self.df_test = pd.DataFrame(), pd.DataFrame()
            if self.split3:
                self.df_dev = pd.DataFrame()
            else:
                self.df_dev = None
            for d in self.datasets.values():
                if self.split3:
                    d.split_3()
                else:
                    d.split()
                if self.target != "none":
                    d.prepare_labels()
                if d.df_train.shape[0] == 0:
                    self.util.debug(f"warn: {d.name} train empty")
                else:
                    self.df_train = pd.concat([self.df_train, d.df_train])
                    self.util.copy_flags(d, self.df_train)
                if d.df_test.shape[0] == 0:
                    self.util.debug(f"warn: {d.name} test empty")
                else:
                    self.df_test = pd.concat([self.df_test, d.df_test])
                    self.util.copy_flags(d, self.df_test)
                if self.split3:
                    if d.df_dev.shape[0] == 0:
                        self.util.debug(f"warn: {d.name} dev empty")
                    else:
                        self.df_dev = pd.concat([self.df_dev, d.df_dev])
                        self.util.copy_flags(d, self.df_dev)
            self.train_empty = True if self.df_train.shape[0] == 0 else False
            self.test_empty = True if self.df_test.shape[0] == 0 else False
            if self.split3:
                self.dev_empty = True if self.df_dev.shape[0] == 0 else False
            store = self.util.get_path("store")
            storage_test = f"{store}testdf.csv"
            storage_train = f"{store}traindf.csv"
            self.df_test.to_csv(storage_test)
            self.df_train.to_csv(storage_train)
            if self.split3:
                storage_dev = f"{store}devdf.csv"
                self.df_dev.to_csv(storage_dev)

        if self.target == "none":
            return
        self.util.copy_flags(self, self.df_test)
        self.util.copy_flags(self, self.df_train)
        if self.split3:
            self.util.copy_flags(self, self.df_dev)
        # Try data checks
        datachecker = FileChecker(self.df_train)
        self.df_train = datachecker.all_checks()
        datachecker.set_data(self.df_test)
        self.df_test = datachecker.all_checks()
        if self.split3:
            datachecker.set_data(self.df_dev)
            self.df_dev = datachecker.all_checks()

        # Check for filters
        filter_sample_selection = self.util.config_val(
            "DATA", "filter.sample_selection", "all"
        )
        if filter_sample_selection == "all":
            datafilter = DataFilter(self.df_train)
            self.df_train = datafilter.all_filters()
            datafilter = DataFilter(self.df_test)
            self.df_test = datafilter.all_filters()
            if self.split3:
                datafilter = DataFilter(self.df_dev)
                self.df_dev = datafilter.all_filters()
        elif filter_sample_selection == "train":
            datafilter = DataFilter(self.df_train)
            self.df_train = datafilter.all_filters()
        elif filter_sample_selection == "test":
            datafilter = DataFilter(self.df_test)
            self.df_test = datafilter.all_filters()
        else:
            msg = (
                "unkown filter sample selection specifier"
                f" {filter_sample_selection}, should be [all | train | test]"
            )
            self.util.error(msg)

        # encode the labels
        if self.util.exp_is_classification():
            datatype = self.util.config_val("DATA", "type", "dummy")
            if datatype == "continuous":
                if not self.test_empty:
                    test_cats = self.df_test["class_label"].unique()
                if not self.train_empty:
                    train_cats = self.df_train["class_label"].unique()
                if self.split3 and not self.dev_empty:
                    dev_cats = self.df_dev["class_label"].unique()
            else:
                if not self.test_empty:
                    if self.df_test.is_labeled:
                        # get printable string of categories and their counts
                        test_cats = self.df_test[self.target].value_counts().to_string()
                    else:
                        # if there is no target, copy a dummy label
                        self.df_test = self._add_random_target(self.df_test).astype(
                            "str"
                        )
                if not self.train_empty:
                    train_cats = self.df_train[self.target].value_counts().to_string()
                if self.split3 and not self.dev_empty:
                    dev_cats = self.df_dev[self.target].value_counts().to_string()
            # encode the labels as numbers
            self.label_encoder = LabelEncoder()
            glob_conf.set_label_encoder(self.label_encoder)
            if not self.train_empty:
                self.util.debug(f"Categories train: {train_cats}")
                self.df_train[self.target] = self.label_encoder.fit_transform(
                    self.df_train[self.target]
                )
            if not self.test_empty:
                if self.df_test.is_labeled:
                    self.util.debug(f"Categories test: {test_cats}")
                if not self.train_empty:
                    self.df_test[self.target] = self.label_encoder.transform(
                        self.df_test[self.target]
                    )
            if self.split3 and not self.dev_empty:
                self.util.debug(f"Categories dev: {dev_cats}")
                if not self.train_empty:
                    self.df_dev[self.target] = self.label_encoder.transform(
                        self.df_dev[self.target]
                    )
        if self.got_speaker:
            speakers_train = 0 if self.train_empty else self.df_train.speaker.nunique()
            speakers_test = 0 if self.test_empty else self.df_test.speaker.nunique()
            self.util.debug(
                f"{speakers_test} speakers in test and"
                f" {speakers_train} speakers in train"
            )
            if self.split3:
                speakers_dev = 0 if self.dev_empty else self.df_dev.speaker.nunique()
                self.util.debug(f"{speakers_dev} speakers in dev")

        target_factor = self.util.config_val("DATA", "target_divide_by", False)
        if target_factor:
            self.df_test[self.target] = self.df_test[self.target] / float(target_factor)
            self.df_train[self.target] = self.df_train[self.target] / float(
                target_factor
            )
            if self.split3:
                self.df_dev[self.target] = self.df_dev[self.target] / float(
                    target_factor
                )
            if not self.util.exp_is_classification():
                self.df_test["class_label"] = self.df_test["class_label"] / float(
                    target_factor
                )
                self.df_train["class_label"] = self.df_train["class_label"] / float(
                    target_factor
                )
                if self.split3:
                    self.df_dev["class_label"] = self.df_dev["class_label"] / float(
                        target_factor
                    )
        if self.split3:
            shapes = f"{self.df_train.shape}/{self.df_dev.shape}/{self.df_test.shape}"
            self.util.debug(f"train/dev/test shape: {shapes}")
        else:
            self.util.debug(
                f"train/test shape: {self.df_train.shape}/{self.df_test.shape}"
            )

    def _add_random_target(self, df):
        labels = glob_conf.labels
        a = [None] * len(df)
        for i in range(0, len(df)):
            a[i] = random.choice(labels)
        df[self.target] = a
        return df

    def plot_distribution(self, df_labels):
        """Plot the distribution of samples and speakers.

        Per target class and biological sex.
        """
        plot = Plots()
        plot.plot_distributions(df_labels)
        if self.got_speaker:
            plot.plot_distributions_speaker(df_labels)

    def extract_test_feats(self):
        self.feats_test = pd.DataFrame()
        feats_name = "_".join(ast.literal_eval(glob_conf.config["DATA"]["tests"]))
        feats_types = self.util.config_val_list("FEATS", "type", ["os"])
        self.feature_extractor = FeatureExtractor(
            self.df_test, feats_types, feats_name, "test"
        )
        self.feats_test = self.feature_extractor.extract()
        self.util.debug(f"Test features shape:{self.feats_test.shape}")

    def extract_feats(self):
        """Extract the features for train and dev sets.

        They will be stored on disk and need to be removed manually.

        The string FEATS.feats_type is read from the config, defaults to os.

        """
        df_train, df_test = self.df_train, self.df_test
        if self.split3:
            df_dev = self.df_dev
        else:
            df_dev = None
        feats_name = "_".join(ast.literal_eval(glob_conf.config["DATA"]["databases"]))
        self.feats_test, self.feats_train = pd.DataFrame(), pd.DataFrame()
        if self.split3:
            self.feats_dev = pd.DataFrame()
        else:
            self.feats_dev = None
        feats_types = self.util.config_val("FEATS", "type", "os")
        # Ensure feats_types is always a list of strings
        if isinstance(feats_types, str):
            if feats_types.startswith("[") and feats_types.endswith("]"):
                feats_types = ast.literal_eval(feats_types)
            else:
                feats_types = [feats_types]
        # print(f"feats_types: {feats_types}")
        # for some models no features are needed
        if len(feats_types) == 0:
            self.util.debug("no feature extractor specified.")
            return
        if not self.train_empty:
            self.feature_extractor = FeatureExtractor(
                df_train, feats_types, feats_name, "train"
            )
            self.feats_train = self.feature_extractor.extract()
        if not self.test_empty:
            self.feature_extractor = FeatureExtractor(
                df_test, feats_types, feats_name, "test"
            )
            self.feats_test = self.feature_extractor.extract()
        if self.split3:
            if not self.dev_empty:
                self.feature_extractor = FeatureExtractor(
                    df_dev, feats_types, feats_name, "dev"
                )
                self.feats_dev = self.feature_extractor.extract()
                shps = f"{self.feats_train.shape}/{self.feats_dev.shape}/{self.feats_test.shape}"
                self.util.debug(f"Train/dev/test features:{shps}")
        else:
            self.util.debug(
                f"All features: train shape : {self.feats_train.shape}, test"
                f" shape:{self.feats_test.shape}"
            )
        if self.feats_train.shape[0] < self.df_train.shape[0]:
            self.util.warn(
                f"train feats ({self.feats_train.shape[0]}) != train labels"
                f" ({self.df_train.shape[0]})"
            )
            self.df_train = self.df_train[
                self.df_train.index.isin(self.feats_train.index)
            ]
            self.util.warn(f"new train labels shape: {self.df_train.shape[0]}")
        if self.feats_test.shape[0] < self.df_test.shape[0]:
            self.util.warn(
                f"test feats ({self.feats_test.shape[0]}) != test labels"
                f" ({self.df_test.shape[0]})"
            )
            self.df_test = self.df_test[self.df_test.index.isin(self.feats_test.index)]
            self.util.warn(f"new test labels shape: {self.df_test.shape[0]}")
        if self.split3:
            if self.feats_dev.shape[0] < self.df_dev.shape[0]:
                self.util.warn(
                    f"dev feats ({self.feats_dev.shape[0]}) != dev labels"
                    f" ({self.df_dev.shape[0]})"
                )
                self.df_dev = self.df_dev[self.df_dev.index.isin(self.feats_dev.index)]
                self.util.warn(f"new dev labels shape: {self.df_dev.shape[0]}")

        self._check_scale()

    def augment(self):
        """Augment the selected samples."""
        from nkululeko.augmenting.augmenter import Augmenter

        sample_selection = self.util.config_val("AUGMENT", "sample_selection", "all")
        if sample_selection == "all":
            df = pd.concat([self.df_train, self.df_test])
        elif sample_selection == "train":
            df = self.df_train
        elif sample_selection == "test":
            df = self.df_test
        else:
            self.util.error(
                f"unknown augmentation selection specifier {sample_selection},"
                " should be [all | train | test]"
            )

        augmenter = Augmenter(df)
        df_ret = augmenter.augment(sample_selection)
        return df_ret

    def autopredict(self):
        """Predict labels for samples with existing models and add to the dataframe."""
        sample_selection = self.util.config_val("PREDICT", "sample_selection", "all")
        if sample_selection == "all":
            df = pd.concat([self.df_train, self.df_test])
        elif sample_selection == "train":
            df = self.df_train
        elif sample_selection == "test":
            df = self.df_test
        else:
            self.util.error(
                f"unknown augmentation selection specifier {sample_selection},"
                " should be [all | train | test]"
            )
        targets = self.util.config_val_list("PREDICT", "targets", None)
        if targets is None:
            self.util.error("no prediction target specified")
        for target in targets:
            if target == "speaker":
                from nkululeko.autopredict.ap_sid import SIDPredictor

                predictor = SIDPredictor(df)
                df = predictor.predict(sample_selection)
            elif target == "gender":
                from nkululeko.autopredict.ap_gender import GenderPredictor

                predictor = GenderPredictor(df)
                df = predictor.predict(sample_selection)
            elif target == "age":
                from nkululeko.autopredict.ap_age import AgePredictor

                predictor = AgePredictor(df)
                df = predictor.predict(sample_selection)
            elif target == "snr":
                from nkululeko.autopredict.ap_snr import SNRPredictor

                predictor = SNRPredictor(df)
                df = predictor.predict(sample_selection)
            elif target == "mos":
                from nkululeko.autopredict.ap_mos import MOSPredictor

                predictor = MOSPredictor(df)
                df = predictor.predict(sample_selection)
            elif target == "pesq":
                from nkululeko.autopredict.ap_pesq import PESQPredictor

                predictor = PESQPredictor(df)
                df = predictor.predict(sample_selection)
            elif target == "sdr":
                from nkululeko.autopredict.ap_sdr import SDRPredictor

                predictor = SDRPredictor(df)
                df = predictor.predict(sample_selection)
            elif target == "stoi":
                from nkululeko.autopredict.ap_stoi import STOIPredictor

                predictor = STOIPredictor(df)
                df = predictor.predict(sample_selection)
            elif target == "text":
                from nkululeko.autopredict.ap_text import TextPredictor

                predictor = TextPredictor(df, self.util)
                df = predictor.predict(sample_selection)
            elif target == "textclassification":
                from nkululeko.autopredict.ap_textclassifier import (
                    TextClassificationPredictor,
                )

                predictor = TextClassificationPredictor(df, self.util)
                df = predictor.predict(sample_selection)
            elif target == "translation":
                from nkululeko.autopredict.ap_translate import TextTranslator

                predictor = TextTranslator(df, self.util)
                df = predictor.predict(sample_selection)
            elif target == "arousal":
                from nkululeko.autopredict.ap_arousal import ArousalPredictor

                predictor = ArousalPredictor(df)
                df = predictor.predict(sample_selection)
            elif target == "valence":
                from nkululeko.autopredict.ap_valence import ValencePredictor

                predictor = ValencePredictor(df)
                df = predictor.predict(sample_selection)
            elif target == "dominance":
                from nkululeko.autopredict.ap_dominance import DominancePredictor

                predictor = DominancePredictor(df)
                df = predictor.predict(sample_selection)
            elif target == "emotion":
                from nkululeko.autopredict.ap_emotion import EmotionPredictor

                predictor = EmotionPredictor(df)
                df = predictor.predict(sample_selection)
            else:
                self.util.error(f"unknown auto predict target: {target}")
        return df

    def random_splice(self):
        """
        Random-splice the selected samples
        """
        from nkululeko.augmenting.randomsplicer import Randomsplicer

        sample_selection = self.util.config_val("AUGMENT", "sample_selection", "all")
        if sample_selection == "all":
            df = pd.concat([self.df_train, self.df_test])
        elif sample_selection == "train":
            df = self.df_train
        elif sample_selection == "test":
            df = self.df_test
        else:
            self.util.error(
                f"unknown augmentation selection specifier {sample_selection},"
                " should be [all | train | test]"
            )
        randomsplicer = Randomsplicer(df)
        df_ret = randomsplicer.run(sample_selection)
        return df_ret

    def analyse_features(self, needs_feats):
        """Do a feature exploration."""
        plot_feats = eval(
            self.util.config_val("EXPL", "feature_distributions", "False")
        )
        sample_selection = self.util.config_val("EXPL", "sample_selection", "all")
        # get the data labels
        if sample_selection == "all":
            df_labels = pd.concat([self.df_train, self.df_test])
            self.util.copy_flags(self.df_train, df_labels)
        elif sample_selection == "train":
            df_labels = self.df_train
            self.util.copy_flags(self.df_train, df_labels)
        elif sample_selection == "test":
            df_labels = self.df_test
            self.util.copy_flags(self.df_test, df_labels)
        else:
            self.util.error(
                f"unknown sample selection specifier {sample_selection}, should"
                " be [all | train | test]"
            )
        self.util.debug(f"sampling selection: {sample_selection}")
        if self.util.config_val("EXPL", "value_counts", False):
            self.plot_distribution(df_labels)
        print_colvals = eval(self.util.config_val("EXPL", "print_colvals", "False"))
        if print_colvals:
            self.util.debug(f"columns in data: {df_labels.columns}")
            for col in df_labels.columns:
                self.util.debug(f"{col}: {df_labels[col].unique()}")

        # check if data should be shown with the spotlight data visualizer
        spotlight = eval(self.util.config_val("EXPL", "spotlight", "False"))
        if spotlight:
            self.util.debug("opening spotlight tab in web browser")
            from renumics import spotlight

            spotlight.show(df_labels.reset_index())

        if not needs_feats:
            return
        # get the feature values
        if sample_selection == "all":
            df_feats = pd.concat([self.feats_train, self.feats_test])
        elif sample_selection == "train":
            df_feats = self.feats_train
        elif sample_selection == "test":
            df_feats = self.feats_test
        else:
            self.util.error(
                f"unknown sample selection specifier {sample_selection}, should"
                " be [all | train | test]"
            )
        feat_analyser = FeatureAnalyser(sample_selection, df_labels, df_feats)
        # check if SHAP features should be analysed
        shap = eval(self.util.config_val("EXPL", "shap", "False"))
        if shap:
            feat_analyser.analyse_shap(self.runmgr.get_best_model())

        if plot_feats:
            feat_analyser.analyse()

        # check if a scatterplot should be done
        list_of_dimreds = eval(self.util.config_val("EXPL", "scatter", "False"))

        # Priority: use [EXPL][scatter.target] if available, otherwise use [DATA][target] value
        if hasattr(self, "target") and self.target != "none":
            default_scatter_target = f"['{self.target}']"
        else:
            default_scatter_target = "['class_label']"

        scatter_target = self.util.config_val(
            "EXPL", "scatter.target", default_scatter_target
        )

        if scatter_target == default_scatter_target:
            self.util.debug(
                f"scatter.target using default from [DATA][target]: {scatter_target}"
            )
        else:
            self.util.debug(
                f"scatter.target from [EXPL][scatter.target]: {scatter_target}"
            )
        if list_of_dimreds:
            dimreds = list_of_dimreds
            scat_targets = ast.literal_eval(scatter_target)
            plots = Plots()
            for scat_target in scat_targets:
                if self.util.is_categorical(df_labels[scat_target]):
                    for dimred in dimreds:
                        plots.scatter_plot(df_feats, df_labels, scat_target, dimred)
                else:
                    self.util.debug(
                        f"{self.name}: binning continuous variable to categories"
                    )
                    cat_vals = self.util.continuous_to_categorical(
                        df_labels[scat_target]
                    )
                    df_labels[f"{scat_target}_bins"] = cat_vals.values
                    for dimred in dimreds:
                        plots.scatter_plot(
                            df_feats, df_labels, f"{scat_target}_bins", dimred
                        )

        # check if t-SNE plot should be generated
        tsne = eval(self.util.config_val("EXPL", "tsne", "False"))
        if tsne:
            target_column = self.util.config_val("DATA", "target", "emotion")
            plots = Plots()
            self.util.debug("generating t-SNE plot...")
            plots.scatter_plot(df_feats, df_labels, target_column, "tsne")

        # check if UMAP plot should be generated
        umap_plot = eval(self.util.config_val("EXPL", "umap", "False"))
        if umap_plot:
            target_column = self.util.config_val("DATA", "target", "emotion")
            plots = Plots()
            self.util.debug("generating UMAP plot...")
            plots.scatter_plot(df_feats, df_labels, target_column, "umap")

        # check if PCA plot should be generated
        pca_plot = eval(self.util.config_val("EXPL", "pca", "False"))
        if pca_plot:
            target_column = self.util.config_val("DATA", "target", "emotion")
            plots = Plots()
            self.util.debug("generating PCA plot...")
            plots.scatter_plot(df_feats, df_labels, target_column, "pca")

    def _check_scale(self):
        self.util.save_to_store(self.feats_train, "feats_train")
        self.util.save_to_store(self.feats_test, "feats_test")
        if self.split3:
            self.util.save_to_store(self.feats_dev, "feats_dev")
        scale_feats = self.util.config_val("FEATS", "scale", False)
        # print the scale
        self.util.debug(f"scaler: {scale_feats}")
        if scale_feats:
            self.scaler_feats = Scaler(
                self.df_train,
                self.df_test,
                self.feats_train,
                self.feats_test,
                scale_feats,
                dev_x=self.df_dev,
                dev_y=self.feats_dev,
            )
            if self.split3:
                self.feats_train, self.feats_dev, self.feats_test = (
                    self.scaler_feats.scale()
                )
                # store versions
                self.util.save_to_store(self.feats_train, "feats_train_scaled")
                self.util.save_to_store(self.feats_test, "feats_test_scaled")
                self.util.save_to_store(self.feats_dev, "feats_dev_scaled")
            else:
                self.feats_train, self.feats_test = self.scaler_feats.scale()
                # store versions
                self.util.save_to_store(self.feats_train, "feats_train_scaled")
                self.util.save_to_store(self.feats_test, "feats_test_scaled")

    def init_runmanager(self):
        """Initialize the manager object for the runs."""
        if self.split3:
            self.runmgr = Runmanager(
                self.df_train,
                self.df_test,
                self.feats_train,
                self.feats_test,
                dev_x=self.df_dev,
                dev_y=self.feats_dev,
            )
        else:
            self.runmgr = Runmanager(
                self.df_train, self.df_test, self.feats_train, self.feats_test
            )

    def run(self):
        """Do the runs."""
        self.runmgr.do_runs()

        # access the best results all runs
        self.reports = self.runmgr.best_results
        last_epochs = self.runmgr.last_epochs
        # try to save yourself
        save = self.util.config_val("EXP", "save", False)
        if save:
            # save the experiment for future use
            self.save(self.util.get_save_name())
            # self.save_onnx(self.util.get_save_name())

        # self.__collect_reports()
        self.util.print_best_results(self.reports)

        # check if the test predictions should be saved to disk
        test_pred_file = self.util.config_val("EXP", "save_test", False)
        if test_pred_file:
            self.predict_test_and_save(test_pred_file)

        # check if the majority voting for all speakers should be plotted
        conf_mat_per_speaker_function = self.util.config_val(
            "PLOT", "combine_per_speaker", False
        )
        if conf_mat_per_speaker_function:
            self.plot_confmat_per_speaker(conf_mat_per_speaker_function)

        # check if a summary of multiple runs should be plotted
        plot_runs = self.util.config_val("PLOT", "runs_compare", False)
        run_num = int(self.util.config_val("EXP", "runs", 1))
        if plot_runs and run_num > 1:
            from nkululeko.reporting.run_plotter import Run_plotter

            rp = Run_plotter(self)
            rp.plot(plot_runs)

        used_time = time.process_time() - self.start
        self.util.debug(f"Done, used {used_time:.3f} seconds")

        # check if a test set should be labeled by the model:
        label_data = self.util.config_val("DATA", "label_data", False)
        label_result = self.util.config_val("DATA", "label_result", False)
        if label_data and label_result:
            self.predict_test_and_save(label_result)

        return self.reports, last_epochs

    def plot_confmat_per_speaker(self, function):
        if self.loso or self.logo or self.xfoldx:
            self.util.debug(
                "plot combined speaker predictions not possible for cross" " validation"
            )
            return
        best = self.get_best_report(self.reports)
        if best.is_classification:
            truths = best.truths
            preds = best.preds
        else:
            truths = best.truths_cont
            preds = best.preds_cont
        speakers = self.df_test.speaker.values
        df = pd.DataFrame(data={"truths": truths, "preds": preds, "speakers": speakers})
        plot_name = f"{self.util.get_exp_name()}_speakercombined_{function}"
        self.util.debug(
            f"plotting speaker combination ({function}) confusion matrix to"
            f" {plot_name}"
        )
        best.plot_per_speaker(df, plot_name, function)

    def get_best_report(self, reports):
        return self.runmgr.get_best_result(reports)

    def print_best_model(self):
        self.runmgr.print_best_result_runs()

    def demo(self, file, is_list, outfile):
        model = self.runmgr.get_best_model()
        lab_enc = None
        try:
            lab_enc = self.label_encoder
        except AttributeError:
            pass
        demo = Demo_predictor(
            model, file, is_list, self.feature_extractor, lab_enc, outfile
        )
        demo.run_demo()

    def predict_test_and_save(self, result_name):
        model = self.runmgr.get_best_model()
        model.set_testdata(self.df_test, self.feats_test)
        test_predictor = TestPredictor(
            model, self.df_test, self.label_encoder, result_name
        )
        result = test_predictor.predict_and_store()
        return result

    def load(self, filename):
        try:
            f = open(filename, "rb")
            tmp_dict = pickle.load(f)
            f.close()
        except EOFError as eof:
            self.util.error(f"can't open file {filename}: {eof}")
        self.__dict__.update(tmp_dict)
        glob_conf.set_labels(self.labels)

    def save(self, filename):
        if self.runmgr.modelrunner.model.is_ann():
            self.runmgr.modelrunner.model = None
            self.util.warn(
                "Save experiment: Can't pickle the trained model so saving without it. (it should be stored anyway)"
            )
        try:
            f = open(filename, "wb")
            pickle.dump(self.__dict__, f)
            f.close()
        except (TypeError, AttributeError) as error:
            self.feature_extractor.feat_extractor.model = None
            f = open(filename, "wb")
            pickle.dump(self.__dict__, f)
            f.close()
            self.util.warn(
                "Save experiment: Can't pickle the feature extraction model so saving without it."
                + f"{type(error).__name__} {error}"
            )
        except RuntimeError as error:
            self.util.warn(
                "Save experiment: Can't pickle local object, NOT saving: "
                + f"{type(error).__name__} {error}"
            )

    def save_onnx(self, filename):
        # export the model to onnx
        model = self.runmgr.get_best_model()
        if model.is_ann():
            print("converting to onnx from torch")
        else:
            print("converting to onnx from sklearn")
        # save the rest
        f = open(filename, "wb")
        pickle.dump(self.__dict__, f)
        f.close()
