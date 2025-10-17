# dataset.py
import ast
import os
import os.path
from random import sample

import numpy as np
import pandas as pd
import audformat

from nkululeko.filter_data import DataFilter
import nkululeko.glob_conf as glob_conf
from nkululeko.plots import Plots
from nkululeko.reporting.report_item import ReportItem
from nkululeko.utils.util import Util


class Dataset:
    """Class to represent datasets"""

    name = ""  # An identifier for the dataset
    config = None  # The configuration
    db = None  # The database object
    df = None  # The whole dataframe
    df_train = None  # The training split
    df_test = None  # The evaluation split

    def __init__(self, name):
        """Constructor setting up name and configuration"""
        self.name = name
        self.util = Util("dataset")
        self.target = self.util.config_val("DATA", "target", "none")
        self.plot = Plots()
        self.limit = int(self.util.config_val_data(self.name, "limit", 0))
        self.target_tables_append = eval(
            self.util.config_val_data(self.name, "target_tables_append", "False")
        )
        self.start_fresh = eval(self.util.config_val("DATA", "no_reuse", "False"))
        self.is_labeled, self.got_speaker, self.got_gender, self.got_age = (
            False,
            False,
            False,
            False,
        )
        self.split3 = eval(self.util.config_val("EXP", "traindevtest", "False"))

    def _get_tables(self):
        tables = []
        targets = self.util.config_val_data(self.name, "target_tables", False)
        if targets:
            target_tables = ast.literal_eval(targets)
            tables += target_tables
        files = self.util.config_val_data(self.name, "files_tables", False)
        if files:
            files_tables = ast.literal_eval(files)
            tables += files_tables
        tests = self.util.config_val_data(self.name, "test_tables", False)
        if tests:
            test_tables = ast.literal_eval(tests)
            tables += test_tables
        trains = self.util.config_val_data(self.name, "train_tables", False)
        if trains:
            train_tables = ast.literal_eval(trains)
            tables += train_tables
        return tables

    def _load_db(self):
        root = self.util.config_val_data(self.name, "", "")
        self.util.debug(f"{self.name}: loading from {root}")
        try:
            self.db = audformat.Database.load(root)
        except FileNotFoundError:
            self.util.error(f"{self.name}: no audformat database found at {root}")
        return root

    def _check_cols(self, df):
        rename_cols = self.util.config_val_data(self.name, "colnames", False)
        if rename_cols:
            col_dict = ast.literal_eval(rename_cols)
            # df = df.rename(columns=col_dict)
            for key in col_dict.keys():
                if key in df.columns:
                    df[col_dict[key]] = df[key]
                else:
                    self.util.warn(
                        f"column {key} not found in {self.name} database, "
                        "not renaming it"
                    )
            self.util.debug(f"renamed data columns: {col_dict}")
        return df

    def _report_load(self):
        speaker_num = 0
        if self.got_speaker:
            speaker_num = self.df.speaker.nunique()
        r_string = (
            f"{self.name}: loaded with {self.df.shape[0]} samples: got targets:"
            f" {self.is_labeled}, got speakers:"
            f" {self.got_speaker} ({speaker_num}), got sexes: {self.got_gender}"
        )
        self.util.debug(r_string)
        if glob_conf.report.initial:
            glob_conf.report.add_item(ReportItem("Data", "Load report", r_string))
            glob_conf.report.initial = False

    def load(self):
        """Load the dataframe with files, speakers and task labels"""
        # store the dataframe
        store = self.util.get_path("store")
        store_format = self.util.config_val("FEATS", "store_format", "pkl")
        store_file = f"{store}{self.name}.{store_format}"
        self.root = self._load_db()
        if not self.start_fresh and os.path.isfile(store_file):
            self.util.debug(f"{self.name}: reusing previously stored file {store_file}")
            self.df = self.util.get_store(store_file, store_format)
            self.is_labeled = self.target in self.df
            self.got_gender = "gender" in self.df
            self.got_age = "age" in self.df
            self.got_speaker = "speaker" in self.df
            self.util.copy_flags(self, self.df)
            self._report_load()
            return
        tables = self._get_tables()
        self.util.debug(f"{self.name}: loading tables: {tables}")
        # db = audb.load(root, )
        # map the audio file paths
        self.db.map_files(lambda x: os.path.join(self.root, x))
        # the dataframes (potentially more than one) with at least the file names
        df_files = self.util.config_val_data(self.name, "files_tables", "['files']")
        df_files_tables = ast.literal_eval(df_files)
        # The label for the target column
        self.col_label = self.util.config_val_data(self.name, "label", self.target)
        (
            df,
            self.is_labeled,
            self.got_speaker,
            self.got_gender,
            self.got_age,
        ) = self._get_df_for_lists(self.db, df_files_tables)
        if df.shape[0] > 0 and self.target == "none":
            self.df = df
            return
        if False in {
            self.is_labeled,
            self.got_speaker,
            self.got_gender,
            self.got_age,
        }:
            try:
                # There might be a separate table with the targets, e.g. emotion or age
                df_targets = self.util.config_val_data(
                    self.name, "target_tables", f"['{self.target}']"
                )
                df_target_tables = ast.literal_eval(df_targets)
                (
                    df_target,
                    got_target2,
                    got_speaker2,
                    got_gender2,
                    got_age2,
                ) = self._get_df_for_lists(self.db, df_target_tables)
                self.is_labeled = got_target2 or self.is_labeled
                self.got_speaker = got_speaker2 or self.got_speaker
                self.got_gender = got_gender2 or self.got_gender
                self.got_age = got_age2 or self.got_age
                if audformat.is_filewise_index(df_target.index):
                    try:
                        df_target = df_target.loc[df.index.get_level_values("file")]
                        df_target = df_target.set_index(df.index)
                    except KeyError:
                        # just a try...
                        pass
                try:
                    if got_target2:
                        df[self.target] = df_target[self.target]
                    if got_speaker2:
                        df["speaker"] = df_target["speaker"]
                    if got_gender2:
                        df["gender"] = df_target["gender"]
                    if got_age2:
                        df["age"] = df_target["age"].astype(int)
                except ValueError as ve:
                    self.util.error(
                        f"{ve}\nYou might need to set "
                        + "data.target_tables_append = True"
                    )
                # copy other column
                for column in df_target.columns:
                    if column not in [self.target, "age", "speaker", "gender"]:
                        df[column] = df_target[column]
            except audformat.core.errors.BadKeyError:
                if not self.is_labeled:
                    self.util.error(
                        f"Giving up: no target ({self.target}) column found"
                    )

        if self.is_labeled:
            # remember the target in case they get labelencoded later
            df["class_label"] = df[self.target]

        self.df = df
        self._report_load()

    def prepare(self):
        # ensure segmented index
        self.df = self.util.make_segmented_index(self.df)
        self.util.copy_flags(self, self.df)
        # check the type of numeric targets
        if not self.util.exp_is_classification():
            self.df[self.target] = self.df[self.target].astype(float)
        # add duration
        if "duration" not in self.df:
            start = self.df.index.get_level_values(1)
            end = self.df.index.get_level_values(2)
            self.df["duration"] = (end - start).total_seconds()
        elif self.df.duration.dtype == "timedelta64[ns]":
            self.df["duration"] = self.df["duration"].map(lambda x: x.total_seconds())
        # Perform some filtering if desired
        required = self.util.config_val_data(self.name, "required", False)
        if required:
            pre = self.df.shape[0]
            self.df = self.df[self.df[required].notna()]
            post = self.df.shape[0]
            self.util.debug(
                f"{self.name}: kept {post} samples with {required} (from {pre},"
                f" filtered {pre-post})"
            )

        datafilter = DataFilter(self.df)
        self.df = datafilter.all_filters(data_name=self.name)

        if self.got_speaker and self.util.config_val_data(
            self.name, "rename_speakers", False
        ):
            # we might need to append the database name to all speakers in case other databases have the same speaker names
            self.df.speaker = self.df.speaker.astype(str)
            self.df.speaker = self.df.speaker.apply(lambda x: self.name + x)

        # check if the target variable should be reversed
        def reverse_array(d, max):
            d = np.array(d)
            res = []
            for n in d:
                res.append(abs(n - max))
            return res

        reverse = eval(self.util.config_val_data(self.name, "reverse", "False"))
        if reverse:
            max = eval(self.util.config_val_data(self.name, "reverse.max", "False"))
            if max:
                max = float(max)
            else:
                max = self.df[self.target].values.max()
            self.util.debug(f"reversing target numbers with max values: {max}")
            self.df[self.target] = reverse_array(self.df[self.target].values, max)

        # check if the target variable should be scaled (z-transformed)
        scale = self.util.config_val_data(self.name, "scale", False)
        if scale:
            from sklearn.preprocessing import StandardScaler

            self.util.debug("scaling target variable to normal distribution")
            scaler = StandardScaler()
            self.df[self.target] = scaler.fit_transform(
                self.df[self.target].values.reshape(-1, 1)
            )

        # store the dataframe
        store = self.util.get_path("store")
        store_format = self.util.config_val("FEATS", "store_format", "pkl")
        store_file = f"{store}{self.name}.{store_format}"
        self.util.write_store(self.df, store_file, store_format)

    def _get_df_for_lists(self, db, df_files):
        is_labeled, got_speaker, got_gender, got_age = (
            False,
            False,
            False,
            False,
        )
        df = pd.DataFrame()
        for table in df_files:
            source_df = db.tables[table].df
            # check if columns should be renamed
            source_df = self._check_cols(source_df)
            # create a dataframe with the index (the filenames)
            df_local = pd.DataFrame(index=source_df.index)
            # try to get the targets from this dataframe
            try:
                # try to get the target values
                df_local[self.target] = source_df[self.col_label]
                is_labeled = True
            except (KeyError, ValueError, audformat.errors.BadKeyError):
                pass
            try:
                # try to get the speaker values
                df_local["speaker"] = source_df["speaker"]
                got_speaker = True
            except (KeyError, ValueError, audformat.errors.BadKeyError):
                pass
            try:
                # try to get the gender values
                if "gender" in source_df:
                    df_local["gender"] = source_df["gender"]
                else:
                    # try to get the gender via the speaker description
                    gender_map = db["speaker"].get().to_dict()["gender"]
                    df_local["gender"] = df_local["speaker"].map(gender_map).astype(str)
                got_gender = True
            except (KeyError, ValueError, audformat.errors.BadKeyError):
                pass
            try:
                # try to get the age values
                if "age" in source_df:
                    df_local["age"] = source_df["age"].astype(int)
                else:
                    # try to get the age via the speaker description
                    age_map = db["speaker"].get().to_dict()["age"]
                    df_local["age"] = df_local["speaker"].map(age_map).astype(int)
                got_age = True
            except (KeyError, ValueError, audformat.errors.BadKeyError):
                pass
            try:
                # also it might be possible that the sex is part of the speaker description
                df_local["gender"] = db[table]["speaker"].get(map="gender")
                got_gender = True
            except (ValueError, audformat.errors.BadKeyError):
                pass
            try:
                # also it might be possible that the sex is part of the speaker description
                df_local["gender"] = db[table]["speaker"].get(map="sex")
                got_gender = True
            except (ValueError, audformat.errors.BadKeyError):
                pass
            try:
                # also it might be possible that the age is part of the speaker description
                df_local["age"] = db[table]["speaker"].get(map="age").astype(int)
                got_age = True
            except (ValueError, audformat.errors.BadKeyError):
                pass
            try:
                # same for the target, e.g. "age"
                df_local[self.target] = db[table]["speaker"].get(map=self.target)
                is_labeled = True
            except (ValueError, audformat.core.errors.BadKeyError):
                pass
            # copy other column
            for column in source_df.columns:
                if column not in [self.target, "age", "speaker", "gender"]:
                    df_local[column] = source_df[column]
            # ensure segmented index
            df_local = self.util.make_segmented_index(df_local)
            if self.target_tables_append:
                df = pd.concat([df, df_local], axis=0)
            else:
                df = pd.concat([df, df_local], axis=1)
        return df, is_labeled, got_speaker, got_gender, got_age

    def split(self):
        """Split the datbase into train and development set"""
        store = self.util.get_path("store")
        storage_test = f"{store}{self.name}_testdf.pkl"
        storage_train = f"{store}{self.name}_traindf.pkl"
        split_strategy = self.util.config_val_data(
            self.name, "split_strategy", "speaker_split"
        )
        self.util.debug(
            f"splitting database {self.name} with strategy {split_strategy}"
        )
        # 'database' (default), 'speaker_split', 'specified', 'reuse'
        if split_strategy != "speaker_split" and not self.start_fresh:
            # check if the splits have been computed previously (not for speaker split)
            if os.path.isfile(storage_train) and os.path.isfile(storage_test):
                # if self.util.config_val_data(self.name, 'test_tables', False):
                self.util.debug(
                    "splits: reusing previously stored test file" f" {storage_test}"
                )
                self.df_test = pd.read_pickle(storage_test)
                self.util.debug(
                    "splits: reusing previously stored train file" f" {storage_train}"
                )
                self.df_train = pd.read_pickle(storage_train)

                return
            elif os.path.isfile(storage_train):
                self.util.debug(
                    "splits: reusing previously stored train file" f" {storage_train}"
                )
                self.df_train = pd.read_pickle(storage_train)
                self.df_test = pd.DataFrame()
                return
            elif os.path.isfile(storage_test):
                self.util.debug(
                    "splits: reusing previously stored test file" f" {storage_test}"
                )
                self.df_test = pd.read_pickle(storage_test)
                self.df_train = pd.DataFrame()
                return
        if split_strategy == "database":
            #  use the splits from the database
            testdf = self.db.tables[self.target + ".test"].df
            traindf = self.db.tables[self.target + ".train"].df
            # use only the train and test samples that were not perhaps filtered out by an earlier processing step
            self.df_test = self.df.loc[self.df.index.intersection(testdf.index)]
            self.df_train = self.df.loc[self.df.index.intersection(traindf.index)]
        elif split_strategy == "train":
            self.df_train = self.df
            self.df_test = pd.DataFrame()
        elif split_strategy == "test":
            self.df_test = self.df
            self.df_train = pd.DataFrame()
        elif split_strategy == "specified":
            traindf, testdf = pd.DataFrame(), pd.DataFrame()
            # try to load some dataframes for testing
            entry_test_tables = self.util.config_val_data(
                self.name, "test_tables", False
            )
            if entry_test_tables:
                test_tables = ast.literal_eval(entry_test_tables)
                for test_table in test_tables:
                    testdf = pd.concat([testdf, self.db.tables[test_table].df])
            entry_train_tables = self.util.config_val_data(
                self.name, "train_tables", False
            )
            if entry_train_tables:
                train_tables = ast.literal_eval(entry_train_tables)
                for train_table in train_tables:
                    traindf = pd.concat([traindf, self.db.tables[train_table].df])
            # use only the train and test samples that were not perhaps filtered out by an earlier processing step
            # testdf.index.map(lambda x: os.path.join(self.root, x))
            #            testdf.index = testdf.index.to_series().apply(lambda x: self.root+x)
            testdf = testdf.set_index(
                audformat.utils.to_segmented_index(testdf.index, allow_nat=False)
            )
            traindf = traindf.set_index(
                audformat.utils.to_segmented_index(traindf.index, allow_nat=False)
            )
            self.df_test = self.df.loc[self.df.index.intersection(testdf.index)]
            self.df_train = self.df.loc[self.df.index.intersection(traindf.index)]
            # it might be necessary to copy the target values
            try:
                self.df_test[self.target] = testdf[self.target]
            except KeyError:
                pass  # if the dataframe is empty
            try:
                self.df_train[self.target] = traindf[self.target]
            except KeyError:
                pass  # if the dataframe is empty
        elif split_strategy == "balanced":
            self.balanced_split()
        elif split_strategy == "speaker_split":
            self.split_speakers()
        elif split_strategy == "speakers_stated":
            self.speakers_stated()
        elif split_strategy == "random":
            self.random_split()
        elif split_strategy == "reuse":
            self.util.debug(f"{self.name}: trying to reuse data splits")
            self.df_test = pd.read_pickle(storage_test)
            self.df_train = pd.read_pickle(storage_train)
        else:
            try:
                if isinstance(ast.literal_eval(split_strategy), list):
                    # treat this as a list of test speakers
                    self.assign_speakers(ast.literal_eval(split_strategy))
            except ValueError:
                self.util.error(f"unknown split strategy: {split_strategy}")

        # check if train or test set should be ignored
        as_test = eval(self.util.config_val_data(self.name, "as_test", "False"))
        if as_test:
            self.df_train = pd.DataFrame()
        as_train = eval(self.util.config_val_data(self.name, "as_train", "False"))
        if as_train:
            self.df_test = pd.DataFrame()

        if self.df_test.shape[0] > 0:
            self.df_test = self.finish_up(self.df_test, storage_test)
        if self.df_train.shape[0] > 0:
            self.df_train = self.finish_up(self.df_train, storage_train)

        self.util.debug(
            f"{self.name}: {self.df_test.shape[0]} samples in test and"
            f" {self.df_train.shape[0]} samples in train"
        )

    def split_3(self):
        """Split the database into train, test and dev set."""
        store = self.util.get_path("store")
        storage_test = f"{store}{self.name}_testdf.pkl"
        storage_train = f"{store}{self.name}_traindf.pkl"
        storage_dev = f"{store}{self.name}_devdf.pkl"
        split_strategy = self.util.config_val_data(
            self.name, "split_strategy", "speaker_split"
        )
        self.util.debug(
            f"splitting database {self.name} into train/dev/test with strategy {split_strategy}"
        )
        # 'database' (default), 'speaker_split', 'specified', 'reuse'
        if split_strategy != "speaker_split" and not self.start_fresh:
            # check if the splits have been computed previously (not for speaker split)
            if (
                os.path.isfile(storage_train)
                and os.path.isfile(storage_test)
                and os.path.isfile(storage_dev)
            ):
                # if self.util.config_val_data(self.name, 'test_tables', False):
                self.util.debug(
                    "splits: reusing previously stored test file" f" {storage_test}"
                )
                self.df_test = pd.read_pickle(storage_test)
                self.util.debug(
                    "splits: reusing previously stored train file" f" {storage_train}"
                )
                self.df_train = pd.read_pickle(storage_train)
                self.util.debug(
                    "splits: reusing previously stored dev file" f" {storage_dev}"
                )
                self.df_dev = pd.read_pickle(storage_train)
                return
            elif os.path.isfile(storage_train):
                self.util.debug(
                    "splits: reusing previously stored train file" f" {storage_train}"
                )
                self.df_train = pd.read_pickle(storage_train)
                self.df_test = pd.DataFrame()
                self.df_dev = pd.DataFrame()
                return
            elif os.path.isfile(storage_test):
                self.util.debug(
                    "splits: reusing previously stored test file" f" {storage_test}"
                )
                self.df_test = pd.read_pickle(storage_test)
                self.df_train = pd.DataFrame()
                self.df_dev = pd.DataFrame()
                return
            elif os.path.isfile(storage_dev):
                self.util.debug(
                    "splits: reusing previously stored dev file" f" {storage_dev}"
                )
                self.df_dev = pd.read_pickle(storage_dev)
                self.df_train = pd.DataFrame()
                self.df_test = pd.DataFrame()
                return
        if split_strategy == "database":
            #  use the splits from the database
            testdf = self.db.tables[self.target + ".test"].df
            traindf = self.db.tables[self.target + ".train"].df
            devdf = self.db.tables[self.target + ".dev"].df
            # use only the train and test samples that were not perhaps filtered out by an earlier processing step
            self.df_test = self.df.loc[self.df.index.intersection(testdf.index)]
            self.df_train = self.df.loc[self.df.index.intersection(traindf.index)]
            self.df_dev = self.df.loc[self.df.index.intersection(devdf.index)]
        elif split_strategy == "train":
            self.df_train = self.df
            self.df_test = pd.DataFrame()
            self.df_dev = pd.DataFrame()
        elif split_strategy == "test":
            self.df_test = self.df
            self.df_train = pd.DataFrame()
            self.df_dev = pd.DataFrame()
        elif split_strategy == "dev":
            self.df_dev = self.df
            self.df_train = pd.DataFrame()
            self.df_test = pd.DataFrame()
        elif split_strategy == "specified":
            traindf, testdf, devdf = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            # try to load some dataframes for testing
            entry_test_tables = self.util.config_val_data(
                self.name, "test_tables", False
            )
            if entry_test_tables:
                test_tables = ast.literal_eval(entry_test_tables)
                for test_table in test_tables:
                    testdf = pd.concat([testdf, self.db.tables[test_table].df])
            entry_train_tables = self.util.config_val_data(
                self.name, "train_tables", False
            )
            if entry_train_tables:
                train_tables = ast.literal_eval(entry_train_tables)
                for train_table in train_tables:
                    traindf = pd.concat([traindf, self.db.tables[train_table].df])
            entry_dev_tables = self.util.config_val_data(self.name, "dev_tables", False)
            if entry_dev_tables:
                dev_tables = ast.literal_eval(entry_dev_tables)
                for dev_table in dev_tables:
                    devdf = pd.concat([devdf, self.db.tables[dev_table].df])
            testdf = testdf.set_index(
                audformat.utils.to_segmented_index(testdf.index, allow_nat=False)
            )
            traindf = traindf.set_index(
                audformat.utils.to_segmented_index(traindf.index, allow_nat=False)
            )
            devdf = devdf.set_index(
                audformat.utils.to_segmented_index(devdf.index, allow_nat=False)
            )
            self.df_test = self.df.loc[self.df.index.intersection(testdf.index)]
            self.df_train = self.df.loc[self.df.index.intersection(traindf.index)]
            self.df_dev = self.df.loc[self.df.index.intersection(devdf.index)]
            # it might be necessary to copy the target values
            if not self.df_test.empty:
                self.df_test[self.target] = testdf[self.target]
            if not self.df_train.empty:
                self.df_train[self.target] = traindf[self.target]
            if not self.df_dev.empty:
                self.df_dev[self.target] = devdf[self.target]
        elif split_strategy == "balanced":
            self.balanced_split(with_dev=True)
        elif split_strategy == "speaker_split":
            self.split_speakers_3()
        elif split_strategy == "speakers_stated":
            self.speakers_stated_3()
        elif split_strategy == "random":
            self.random_split_3()
        elif split_strategy == "reuse":
            self.util.debug(f"{self.name}: trying to reuse data splits")
            self.df_test = pd.read_pickle(storage_test)
            self.df_train = pd.read_pickle(storage_train)
            self.df_dev = pd.read_pickle(storage_dev)
        else:
            try:
                if isinstance(ast.literal_eval(split_strategy), list):
                    # treat this as a list of test speakers
                    self.assign_speakers(ast.literal_eval(split_strategy))
            except ValueError:
                self.util.error(f"unknown split strategy: {split_strategy}")

        # check if train or test set should be ignored
        as_test = eval(self.util.config_val_data(self.name, "as_test", "False"))
        if as_test:
            self.df_train = pd.DataFrame()
            self.df_dev = pd.DataFrame()
        as_train = eval(self.util.config_val_data(self.name, "as_train", "False"))
        if as_train:
            self.df_test = pd.DataFrame()
            self.df_dev = pd.DataFrame()

        if self.df_test.shape[0] > 0:
            self.df_test = self.finish_up(self.df_test, storage_test)
        if self.df_train.shape[0] > 0:
            self.df_train = self.finish_up(self.df_train, storage_train)
        if self.df_dev.shape[0] > 0:
            self.df_dev = self.finish_up(self.df_dev, storage_dev)

        self.util.debug(
            f"{self.name}: {self.df_test.shape[0]} samples in test and"
            f" {self.df_train.shape[0]} samples in train"
        )

    def finish_up(self, df, storage):
        df.is_labeled = self.is_labeled
        df.to_pickle(storage)
        return df

    def balanced_split(self, with_dev=False):
        """Split train and eval sets: Generate dataframes for some balancing criterion."""

        from splitutils import (
            binning,
            optimize_traintest_split,
            optimize_traindevtest_split,
        )

        seed = 42
        k = 30
        test_size = int(self.util.config_val_data(self.name, "test_size", 20)) / 100.0
        df = self.df
        # split target
        targets = df[self.target].to_numpy()
        #
        bins = self.util.config_val("DATA", "bin", False)
        if bins:
            nbins = len(ast.literal_eval(bins))
            targets = binning(targets, nbins=nbins)
        # on which variable to split
        speakers = df["speaker"].to_numpy()

        # on which variables (targets, groupings) to stratify
        stratif_vars = self.util.config_val("DATA", "balance", False)
        stratif_vars_array = {}
        if not stratif_vars:
            self.util.error("balanced split needs stratif_vars to stratify the splits")
        else:
            stratif_vars = ast.literal_eval(stratif_vars)
            for stratif_var in stratif_vars.keys():
                if stratif_var == self.target:
                    stratif_vars_array[self.target] = targets
                    continue
                else:
                    data = df[stratif_var].to_numpy()
                    bins = self.util.config_val("DATA", f"{stratif_var}_bins", False)
                    if bins:
                        data = binning(data, nbins=int(bins))
                    stratif_vars_array[stratif_var] = data
        # weights for all stratify_on variables and
        # and for test proportion match. Give target
        # variable EMOTION more weight than groupings.
        size_diff = int(self.util.config_val("DATA", "size_diff_weight", "1"))
        weights = {
            "size_diff": size_diff,
        }
        for key, value in stratif_vars.items():
            weights[key] = value
        # find optimal test indices TEST_I in DF
        # info: dict with goodness of split information

        if with_dev:
            train_i, dev_i, test_i, info = optimize_traindevtest_split(
                X=df,
                y=targets,
                split_on=speakers,
                stratify_on=stratif_vars_array,
                weight=weights,
                test_size=test_size,
                k=k,
                seed=seed,
            )
            self.util.debug(f"stratification info;\n{info}")
            self.df_train = df.iloc[train_i]
            self.df_test = df.iloc[test_i]
            self.df_dev = df.iloc[dev_i]
            msg = (
                f"{self.name} (balanced split): "
                f"[{self.df_train.shape[0]}/{self.df_dev.shape[0]}/{self.df_test.shape[0]}]"
                " samples in train/dev/test"
            )
            self.util.debug(msg)
        else:
            train_i, test_i, info = optimize_traintest_split(
                X=df,
                y=targets,
                split_on=speakers,
                stratify_on=stratif_vars_array,
                weight=weights,
                test_size=test_size,
                k=k,
                seed=seed,
            )
            self.util.debug(f"stratification info;\n{info}")
            self.df_train = df.iloc[train_i]
            self.df_test = df.iloc[test_i]
            msg = (
                f"{self.name} (balanced split): "
                f"[{self.df_train.shape[0]}/{self.df_test.shape[0]}] samples in train/test"
            )
            self.util.debug(msg)
        # because this generates new train/test sample quantities,
        # the feature extraction has to be done again
        glob_conf.config["FEATS"]["needs_feature_extraction"] = "True"

    def assign_speakers(self, speakers):
        """One way to split train and eval sets: Specify test speaker names."""
        self.df_test = self.df[self.df.speaker.isin(speakers)]
        if len(self.df_test) == 0:
            self.util.error(f"no speakers found in {speakers}")
        self.df_train = self.df[~self.df.index.isin(self.df_test.index)]
        self.util.debug(
            f"{self.name} (speakers assigned): "
            f"[{self.df_train.shape[0]}/{self.df_test.shape[0]}] samples in train/test"
        )
        # because this generates new train/test sample quantaties,
        # the feature extraction has to be done again
        glob_conf.config["FEATS"]["needs_feature_extraction"] = "True"

    def speakers_stated(self):
        test_speakers = self.util.config_val_data(self.name, "test", False)
        if test_speakers:
            test_speakers = ast.literal_eval(test_speakers)
            self.df_test = self.df[self.df.speaker.isin(test_speakers)]
        else:
            self.df_test = pd.DataFrame(columns=self.df.columns)
        train_speakers = self.util.config_val_data(self.name, "train", False)
        if not train_speakers:
            self.df_train = self.df[~self.df.index.isin(self.df_test.index)]
            train_speakers = list(self.df_train.speaker.unique())
        else:
            train_speakers = ast.literal_eval(train_speakers)
            self.df_train = self.df[self.df.speaker.isin(train_speakers)]
        self.util.debug(
            f"{self.name} (speakers stated): "
            f"[{self.df_train.shape[0]}/{self.df_test.shape[0]}] samples in train/test"
        )
        self.util.debug(f"train speakers: {train_speakers}")
        self.util.debug(f"test speakers: {test_speakers}")

    def speakers_stated_3(self):
        test_speakers = self.util.config_val_data(self.name, "test", False)
        if test_speakers:
            test_speakers = ast.literal_eval(test_speakers)
            self.df_test = self.df[self.df.speaker.isin(test_speakers)]
        else:
            self.df_test = pd.DataFrame(columns=self.df.columns)
        dev_speakers = self.util.config_val_data(self.name, "dev", False)
        if dev_speakers:
            dev_speakers = ast.literal_eval(dev_speakers)
            self.df_dev = self.df[self.df.speaker.isin(dev_speakers)]
        else:
            self.df_dev = pd.DataFrame(columns=self.df.columns)
        train_speakers = self.util.config_val_data(self.name, "train", False)
        if not train_speakers:
            self.df_train = self.df[~self.df.index.isin(self.df_test.index)]
            self.df_train = self.df_train[~self.df_train.index.isin(self.df_dev.index)]
            train_speakers = list(self.df_train.speaker.unique())
        else:
            train_speakers = ast.literal_eval(train_speakers)
            self.df_train = self.df[self.df.speaker.isin(train_speakers)]
        self.util.debug(
            f"{self.name} (speakers stated): "
            f"[{self.df_train.shape[0]}/{self.df_dev.shape[0]}/{self.df_test.shape[0]}] samples in train/dev/test"
        )
        self.util.debug(f"train speakers: {train_speakers}")
        self.util.debug(f"test speakers: {test_speakers}")
        self.util.debug(f"dev speakers: {dev_speakers}")

    def split_speakers(self):
        """One way to split train and eval sets: Specify percentage of evaluation speakers"""
        test_percent = int(self.util.config_val_data(self.name, "test_size", 20))
        df = self.df
        s_num = df.speaker.nunique()
        test_num = int(s_num * (test_percent / 100))
        test_spkrs = sample(list(df.speaker.unique()), test_num)
        self.df_test = df[df.speaker.isin(test_spkrs)]
        self.df_train = df[~df.index.isin(self.df_test.index)]
        train_spkrs = list(self.df_train.speaker.unique())
        msg = (
            f"{self.name} (speaker splits): "
            f"[{self.df_train.shape[0]}/{self.df_test.shape[0]}]"
            " samples in train/test"
        )
        self.util.debug(msg)
        self.util.debug(f"train speakers: {train_spkrs}")
        self.util.debug(f"test speakers: {test_spkrs}")
        # because this generates new train/test sample quantaties,
        # the feature extraction has to be done again
        try:
            glob_conf.config["FEATS"]["needs_feature_extraction"] = "True"
        except KeyError:
            pass

    def split_speakers_3(self):
        """One way to split train, dev and test sets: Specify percentage speakers."""
        test_percent = int(self.util.config_val_data(self.name, "test_size", 20))
        dev_percent = int(self.util.config_val_data(self.name, "dev_size", 20))
        df = self.df
        s_num = df.speaker.nunique()
        test_num = int(s_num * (test_percent / 100))
        dev_num = int(s_num * (dev_percent / 100))
        testdev_spkrs = sample(list(df.speaker.unique()), test_num + dev_num)
        # sample from testdev speakers for test and dev
        test_spkrs = sample(testdev_spkrs, test_num)
        dev_spkrs = [spkr for spkr in testdev_spkrs if spkr not in test_spkrs]
        self.df_test = df[df.speaker.isin(test_spkrs)]
        self.df_dev = df[df.speaker.isin(dev_spkrs)]
        self.df_train = df[~df.speaker.isin(testdev_spkrs)]
        train_spkrs = list(self.df_train.speaker.unique())
        msg = (
            f"{self.name} (speaker splits): "
            f"[{self.df_train.shape[0]}/{self.df_dev.shape[0]}/{self.df_test.shape[0]}]"
            " samples in train/dev/test"
        )
        self.util.debug(msg)
        self.util.debug(f"train speakers: {train_spkrs}")
        self.util.debug(f"dev speakers: {dev_spkrs}")
        self.util.debug(f"test speakers: {test_spkrs}")
        # because this generates new train/test sample quantaties,
        # the feature extraction has to be done again
        try:
            glob_conf.config["FEATS"]["needs_feature_extraction"] = "True"
        except KeyError:
            pass

    def random_split(self):
        """One way to split train and eval sets: Specify percentage of random samples."""
        test_percent = int(self.util.config_val_data(self.name, "test_size", 20))
        df = self.df
        s_num = len(df)
        test_num = int(s_num * (test_percent / 100))
        test_smpls = sample(list(df.index), test_num)
        self.df_test = df[df.index.isin(test_smpls)]
        self.df_train = df[~df.index.isin(self.df_test.index)]
        self.util.debug(
            f"{self.name}: [{self.df_train.shape[0]}/{self.df_test.shape[0]}]"
            " samples in train/test"
        )
        # because this generates new train/test sample quantaties,
        # the feature extraction has to be done again
        glob_conf.config["FEATS"]["needs_feature_extraction"] = "True"

    def random_split_3(self):
        """One way to split train, dev and test sets: Specify random samples."""
        test_percent = int(self.util.config_val_data(self.name, "test_size", 20))
        dev_percent = int(self.util.config_val_data(self.name, "dev_size", 20))
        df = self.df
        s_num = len(df)
        test_num = int(s_num * (test_percent / 100))
        dev_num = int(s_num * (dev_percent / 100))
        testdev_smpls = sample(list(df.index), test_num + dev_num)
        test_smpls = sample(testdev_smpls, test_num)
        dev_smpls = [spkr for spkr in testdev_smpls if spkr not in test_smpls]
        self.df_test = df[df.speaker.isin(test_smpls)]
        self.df_dev = df[df.speaker.isin(dev_smpls)]
        self.df_train = df[~df.speaker.isin(testdev_smpls)]
        msg = (
            f"{self.name} (sample splits): "
            f"[{self.df_train.shape[0]}/{self.df_dev.shape[0]}/{self.df_test.shape[0]}]"
            " samples in train/dev/test"
        )
        self.util.debug(msg)
        # because this generates new train/test sample quantaties,
        # the feature extraction has to be done again
        glob_conf.config["FEATS"]["needs_feature_extraction"] = "True"

    def _add_labels(self, df):
        df.is_labeled = self.is_labeled
        df.got_gender = self.got_gender
        df.got_age = self.got_age
        df.got_speaker = self.got_speaker
        return df

    def prepare_labels(self):
        # strategy = self.util.config_val("DATA", "strategy", "train_test")
        only_tests = eval(self.util.config_val("DATA", "tests", "False"))
        module = glob_conf.module
        if only_tests and module == "test":
            self.df_test = self.map_labels(self.df_test)
            # Bin target values if they are continuous but a classification experiment should be done
            self.map_continuous_classification(self.df_test)
            self.df_test = self._add_labels(self.df_test)
            if self.util.config_val_data(self.name, "value_counts", False):
                if not self.got_gender or not self.got_speaker:
                    self.util.error(
                        "can't plot value counts if no speaker or gender is" " given"
                    )
                else:
                    self.plot.describe_df(
                        self.name, self.df_test, self.target, f"{self.name}_distplot"
                    )
            return
        self.df_train = self.map_labels(self.df_train)
        self.df_test = self.map_labels(self.df_test)
        self.map_continuous_classification(self.df_train)
        self.map_continuous_classification(self.df_test)
        self.df_train = self._add_labels(self.df_train)
        self.df_test = self._add_labels(self.df_test)
        if self.split3:
            self.df_dev = self.map_labels(self.df_dev)
            self.map_continuous_classification(self.df_dev)
            self.df_dev = self._add_labels(self.df_dev)
        if self.util.config_val_data(self.name, "value_counts", False):
            if not self.got_gender or not self.got_speaker:
                self.util.error(
                    "can't plot value counts if no speaker or gender is" " given"
                )
            else:
                self.plot.describe_df(
                    self.name,
                    self.df_train,
                    self.target,
                    f"{self.name}_train_distplot",
                )
                self.plot.describe_df(
                    self.name,
                    self.df_test,
                    self.target,
                    f"{self.name}_test_distplot",
                )
                if self.split3:
                    self.plot.describe_df(
                        self.name,
                        self.df_dev,
                        self.target,
                        f"{self.name}_dev_distplot",
                    )

    def map_labels(self, df):
        pd.options.mode.chained_assignment = None
        if (
            df.shape[0] == 0
            or not self.util.exp_is_classification()
            or self.check_continuous_classification()
        ):
            return df
        """Rename the labels and remove the ones that are not needed."""
        target = glob_conf.config["DATA"]["target"]
        # see if a special mapping should be used
        mappings = self.util.config_val_data(self.name, "mapping", False)
        if mappings:
            mapping = ast.literal_eval(mappings)
            if self.util.is_dict_with_string_values(mapping):
                df = self.util.map_labels(df, target, mapping)
                # remove any exiting nan values after mapping
                df = df.dropna()
                self.util.debug(f"{self.name}: mapped {mapping}")
            else:
                # mappings should be a dictionary of dictionaries (with mappings)
                for key in mapping.keys():
                    mapping_tar = mapping[key]
                    df = self.util.map_labels(df, key, mapping_tar)
                    self.util.debug(
                        f"{self.name}: for column {key} mapped {mapping_tar}"
                    )

        # remove labels that are not in the labels list
        labels = self.util.config_val("DATA", "labels", False)
        if labels:
            labels = ast.literal_eval(labels)
            df = df[df[target].isin(labels)]
        else:
            labels = list(df[target].unique())
        if df.shape[0] == 0:
            self.util.warn(f"no match in data values for {labels}")
        df["class_label"] = df[target]
        return df

    def check_continuous_classification(self):
        datatype = self.util.config_val("DATA", "type", False)
        if self.util.exp_is_classification() and datatype == "continuous":
            return True
        return False

    def map_continuous_classification(self, df):
        """Map labels to bins for continuous data that should be classified"""
        if df.empty:
            return
        if self.check_continuous_classification():
            self.util.debug(f"{self.name}: binning continuous variable to categories")
            cat_vals = self.util.continuous_to_categorical(df[self.target])
            df[self.target] = cat_vals.values
            labels = ast.literal_eval(glob_conf.config["DATA"]["labels"])
            df["class_label"] = df[self.target]
            for i, l in enumerate(labels):
                df["class_label"] = df["class_label"].replace(i, str(l))
