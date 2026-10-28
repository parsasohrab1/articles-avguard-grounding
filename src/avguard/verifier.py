"""Independent re-derivation: a text classifier predicts the field from the narrative; support score = P(claimed value | narrative)."""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


class Verifier:
    def __init__(self, field):
        self.field = field
        self.vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=60000, sublinear_tf=True)
        self.clf = LogisticRegression(max_iter=300, C=10.0)

    def fit(self, texts, labels):
        self.clf.fit(self.vec.fit_transform(texts), labels); return self

    def proba(self, texts):
        return self.clf.predict_proba(self.vec.transform(texts))

    def score(self, texts, claimed, p=None):
        if p is None:
            p = self.proba(texts)
        idx = {c: i for i, c in enumerate(self.clf.classes_)}
        return p[np.arange(len(claimed)), [idx[c] for c in claimed]]
