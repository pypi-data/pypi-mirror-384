# feats_trill.py
import os

import audiofile as af
import pandas as pd

import tensorflow as tf
import tensorflow_hub as hub
from tqdm import tqdm

import nkululeko.glob_conf as glob_conf
from nkululeko.feat_extract.featureset import Featureset

# Import TF 2.X and make sure we're running eager.
# assert tf.executing_eagerly()


class TRILLset(Featureset):
    """A feature extractor for the Google TRILL embeddings.

    See https://ai.googleblog.com/2020/06/improving-speech-representations-and.html.
    """

    # Initialization of the class
    def __init__(self, name, data_df, feats_type):
        """Initialize the class with name, data and Util instance.

        Also loads the model from hub
        Args:
            :param name: Name of the class
            :type name: str
            :param data_df: Data of the class
            :type data_df: DataFrame
            :return: None
        """
        super().__init__(name, data_df, feats_type)
        # Load the model from the configured path
        model_path = self.util.config_val(
            "FEATS",
            "trill.model",
            "https://tfhub.dev/google/nonsemantic-speech-benchmark/trill/3",
        )
        # self.model = hub.load(model_path)
        self.feats_type = feats_type

    def extract(self):
        store = self.util.get_path("store")
        storage = f"{store}{self.name}.pkl"
        extract = self.util.config_val("FEATS", "needs_feature_extraction", False)
        no_reuse = eval(self.util.config_val("FEATS", "no_reuse", "False"))
        if extract or no_reuse or not os.path.isfile(storage):
            self.util.debug("extracting TRILL embeddings, this might take a while...")
            emb_series = pd.Series(index=self.data_df.index, dtype=object)
            for idx, file in enumerate(tqdm(self.data_df.index.get_level_values(0))):
                emb = self.get_embeddings(file)
                emb_series.iloc[idx] = emb
            self.df = pd.DataFrame(emb_series.values.tolist(), index=self.data_df.index)
            self.df.to_pickle(storage)
            try:
                glob_conf.config["DATA"]["needs_feature_extraction"] = "false"
            except KeyError:
                pass
        else:
            self.util.debug("reusing extracted TRILL embeddings")
            self.df = pd.read_pickle(storage)

    def embed_wav(self, wav):
        if len(wav.shape) > 1:
            wav = tf.reduce_mean(wav, axis=0)

        emb_dict = self.model(samples=wav, sample_rate=tf.constant(16000))
        return emb_dict["embedding"]

    def get_embeddings(self, file):
        wav = af.read(file)[0]
        emb_short = self.get_embeddings_signal(wav, 16000)
        return emb_short

    def get_embeddings_signal(self, signal, sr):
        wav = tf.convert_to_tensor(signal)
        emb_short = self.embed_wav(wav)
        # you get one embedding per frame, we use the mean for all the frames
        emb_short = emb_short.numpy().mean(axis=0)
        return emb_short

    def extract_sample(self, signal, sr):
        if self.model == None:
            self.__init__("na", None)
        feats = self.get_embeddings_signal(signal, sr)
        return feats
