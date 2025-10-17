import os

import pandas as pd
from tqdm import tqdm
import transformers
import torch

from nkululeko.feat_extract.featureset import Featureset
import nkululeko.glob_conf as glob_conf


class Bert(Featureset):
    """Class to extract bert embeddings"""

    def __init__(self, name, data_df, feat_type):
        """Constructor.

        If_train is needed to distinguish from test/dev sets,
        because they use the codebook from the training
        """
        super().__init__(name, data_df, feat_type)
        cuda = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = self.util.config_val("MODEL", "device", cuda)
        self.model_initialized = False
        if feat_type == "bert":
            self.feat_type = "google-bert/bert-base-uncased"
        else:
            self.feat_type = feat_type

    def init_model(self):
        # load model
        self.model_path = self.util.config_val(
            "FEATS", "bert.model", f"{self.feat_type}"
        )
        self.util.debug(f"loading {self.model_path} model...")
        config = transformers.AutoConfig.from_pretrained(
            self.model_path, trust_remote_code=True
        )
        layer_num = config.num_hidden_layers
        hidden_layer = int(self.util.config_val("FEATS", "bert.layer", "0"))
        config.num_hidden_layers = layer_num - hidden_layer
        self.util.debug(f"using hidden layer #{config.num_hidden_layers}")

        self.tokenizer = transformers.AutoTokenizer.from_pretrained(
            self.model_path, trust_remote_code=True
        )
        self.model = transformers.AutoModel.from_pretrained(
            self.model_path, config=config
        ).to(self.device)
        print(f"initialized {self.model_path} model on {self.device}")
        self.model.eval()
        self.model_initialized = True

    def extract(self):
        """Extract the features or load them from disk if present."""
        store = self.util.get_path("store")
        storage = os.path.join(store, f"{self.name}.pkl")
        extract = self.util.config_val("FEATS", "needs_feature_extraction", False)
        no_reuse = eval(self.util.config_val("FEATS", "no_reuse", "False"))
        text_column = self.util.config_val("FEATS", "bert.text_column", "text")
        if extract or no_reuse or not os.path.isfile(storage):
            if not self.model_initialized:
                self.init_model()
            self.util.debug(
                f"extracting {self.model_path} embeddings, this might take a while..."
            )
            emb_series = pd.Series(index=self.data_df.index, dtype=object)
            for idx, row in tqdm(self.data_df.iterrows(), total=len(self.data_df)):
                file = idx[0]
                text = row[text_column]
                emb = self.get_embeddings(text, file)
                emb_series[idx] = emb
            # print(f"emb_series shape: {emb_series.shape}")
            self.df = pd.DataFrame(emb_series.values.tolist(), index=self.data_df.index)
            # print(f"df shape: {self.df.shape}")
            self.df.to_pickle(storage)
            try:
                glob_conf.config["DATA"]["needs_feature_extraction"] = "false"
            except KeyError:
                pass
        else:
            model_path = self.util.config_val(
                "FEATS", "bert.model", f"{self.feat_type}"
            )
            self.util.debug(f"reusing extracted {model_path} embeddings")
            self.df = pd.read_pickle(storage)
            if self.df.isnull().values.any():
                self.util.error(
                    f"got nan: {self.df.shape} {self.df.isnull().sum().sum()}"
                )

    def get_embeddings(self, text, file):
        r"""Extract embeddings from text."""
        try:
            with torch.no_grad():
                # Truncate text to model's max length to avoid tensor size mismatch
                inputs = self.tokenizer(
                    text,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                    padding=True,
                ).to(self.device)
                outputs = self.model(**inputs)
                # mean pooling
                y = torch.mean(outputs[0], dim=1)
                y = y.ravel()
        except RuntimeError as re:
            print(str(re))
            self.util.error(
                f"couldn't extract embeddings from text (file reference: {file})"
            )
            y = None
        if y is None:
            return None
        return y.detach().cpu().numpy()

    def extract_sample(self, text):
        self.init_model()
        feats = self.get_embeddings(text, "no file")
        return feats
