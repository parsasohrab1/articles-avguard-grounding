"""Support score for one claimed field value, from a text classifier fit on other narratives."""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


class Verifier:
    def __init__(self, field, min_df=3, max_features=60000):
        self.field = field
        self.vec = TfidfVectorizer(
            ngram_range=(1, 2), min_df=min_df, max_features=max_features, sublinear_tf=True
        )
        self.clf = LogisticRegression(max_iter=300, C=10.0)

    def fit(self, texts, labels):
        self.clf.fit(self.vec.fit_transform(texts), labels)
        return self

    def proba(self, texts):
        return self.clf.predict_proba(self.vec.transform(texts))

    def score(self, texts, claimed, p=None):
        if p is None:
            p = self.proba(texts)
        idx = {c: i for i, c in enumerate(self.clf.classes_)}
        out = np.zeros(len(claimed), dtype=float)
        for i, value in enumerate(claimed):
            j = idx.get(value)
            if j is not None:
                out[i] = p[i, j]
        return out
