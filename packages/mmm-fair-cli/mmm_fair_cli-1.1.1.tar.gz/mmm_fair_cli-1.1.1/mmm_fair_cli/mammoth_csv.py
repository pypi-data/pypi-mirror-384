'''
CSV class implementation copied from https://github.com/mammoth-eu/mammoth-commons
'''

import numpy as np
from .dataset import Dataset, Labels


from typing import Iterable
import importlib



def pdt(col, numeric: bool):
    pd = importlib.import_module("pandas")
    preprocessing = importlib.import_module("sklearn.preprocessing")
    if numeric:
        col = col.fillna(0)
        arr_2d = col.values.reshape(-1, 1)
        return pd.DataFrame(preprocessing.StandardScaler().fit_transform(arr_2d))
    col = col.fillna("missing")
    return pd.DataFrame(preprocessing.LabelBinarizer().fit_transform(col))


def pd_features(
    df,
    num: list[str],
    cat: list[str],
    sens: list[str] | None = None,
    transform=lambda x, numeric: x,
):
    sens = set() if sens is None else set(sens)
    pd = importlib.import_module("pandas")
    dfs = [transform(df[col], True) for col in num if col not in sens]
    dfs += [transform(pd.get_dummies(df[col]), False) for col in cat if col not in sens]
    return pd.concat(dfs, axis=1).values


class CSV(Dataset):
    def __init__(
        self,
        df,
        num: list[str],
        cat: list[str],
        labels: str | dict | Iterable | None,
        sens: list[str] | None = None,
    ):
        pd = importlib.import_module("pandas")
        super().__init__(Labels(dict()))
        self.df = df
        self.num = num
        self.cat = cat
        self.cols = num + cat
        sens = set() if sens is None else set(sens)
        if isinstance(labels, str):
            sens.add(labels)
        self.feats = [col for col in self.cols if col not in sens]
        self.labels = (
            Labels(
                pd.get_dummies(df[labels]).to_dict(orient="list")
                if isinstance(labels, str)
                else (
                    pd.get_dummies(labels).to_dict(orient="list")
                    if isinstance(labels, pd.Series)
                    else (
                        labels
                        if isinstance(labels, dict)
                        else {"1": labels, "0": 1 - labels}
                    )
                )
            )
            if not isinstance(labels, Labels)
            else labels
        )

    def to_numpy(self, features: list[str] | None = None):
        assert (
            features
        ), "Internal error: misused to_numpy - a selection of features is required"
        assert (
            len(features) > 2
        ), "Internal error: misused to_numpy - a selection of features is required"
        feats = set(features if features is not None else self.cols)
        return pd_features(
            self.df,
            [col for col in self.num if col not in feats],
            [col for col in self.cat if col not in feats],
        )

    def to_pred(self, exclude: list[str]):
        return pd_features(self.df, self.num, self.cat, exclude, transform=pdt)

    def to_csv(self, sensitive: list[str]):
        return self