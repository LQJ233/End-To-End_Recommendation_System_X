from typing import Dict, Iterable

import numpy as np
import pandas as pd


UNKNOWN_INDEX = 0


def build_vocab(values: Iterable) -> Dict[int, int]:
    cleaned = []
    for value in values:
        if pd.isna(value):
            continue
        cleaned.append(int(value))
    return {value: index for index, value in enumerate(sorted(set(cleaned)), start=1)}


def encode_categoricals(
    dataframe: pd.DataFrame,
    columns: list[str],
    vocabs: Dict[str, Dict[int, int]],
) -> np.ndarray:
    encoded = np.zeros((len(dataframe), len(columns)), dtype=np.int64)
    for column_index, column in enumerate(columns):
        vocab = vocabs[column]
        encoded[:, column_index] = (
            dataframe[column].map(lambda value: vocab.get(int(value), UNKNOWN_INDEX)
                                  if not pd.isna(value) else UNKNOWN_INDEX)
        ).to_numpy(dtype=np.int64)
    return encoded


def normalize_price(prices: pd.Series) -> np.ndarray:
    values = pd.to_numeric(prices, errors="coerce").fillna(0.0).clip(lower=0.0)
    return np.log1p(values).to_numpy(dtype=np.float32)
