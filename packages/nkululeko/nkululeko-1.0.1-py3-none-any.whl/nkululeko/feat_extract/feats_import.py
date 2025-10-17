# feats_import.py

import ast
import os

import audformat
import pandas as pd

from nkululeko.feat_extract.featureset import Featureset


class ImportSet(Featureset):
    """Class to import features that have been compiled elsewhere"""

    def __init__(self, name, data_df, feats_type):
        super().__init__(name, data_df, feats_type)

    def extract(self):
        """Import the features."""
        self.util.debug(f"importing features for {self.name}")
        # import_files_append: set this to True if the multiple tables should be combined row-wise, else they are combined column-wise
        import_files_append = eval(
            self.util.config_val("FEATS", "import_files_append", "True")
        )
        try:
            feat_import_files = self.util.config_val("FEATS", "import_file", False)
            feat_import_files = ast.literal_eval(feat_import_files)
        except ValueError:
            self.util.error(
                "feature type == import needs import_file = ['file1', 'filex']"
            )
        except SyntaxError:
            if type(feat_import_files) is str:
                feat_import_files = [feat_import_files]
            else:
                self.util.error(f"import_file is wrong: {feat_import_files}")

        feat_df = pd.DataFrame()
        for feat_import_file in feat_import_files:
            if not os.path.isfile(feat_import_file):
                self.util.error(f"no import file: {feat_import_file}")
            df = audformat.utils.read_csv(feat_import_file)
            if df.isnull().values.any():
                self.util.warn(
                    f"imported features contain {df.isna().sum()} NAN, filling with zero."
                )
                df = df.fillna(0)
            df = self.util.make_segmented_index(df)
            df = df[df.index.isin(self.data_df.index)]
            if import_files_append:
                feat_df = pd.concat([feat_df, df], axis=0)
            else:
                feat_df = pd.concat([feat_df, df], axis=1)
        if feat_df.shape[0] == 0:
            self.util.error(f"Imported features for data set {self.name} not found!")
        # and assign to be the "official" feature set
        self.df = feat_df
