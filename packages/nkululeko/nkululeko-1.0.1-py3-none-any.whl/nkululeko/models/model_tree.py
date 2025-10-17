# model_tree.py

from sklearn.tree import DecisionTreeClassifier

from nkululeko.models.model import Model


class Tree_model(Model):
    """An Tree model"""

    is_classifier = True

    def __init__(self, df_train, df_test, feats_train, feats_test):
        super().__init__(df_train, df_test, feats_train, feats_test)
        self.name = "tree"
        self.clf = DecisionTreeClassifier(random_state=42)  # set up the classifier
