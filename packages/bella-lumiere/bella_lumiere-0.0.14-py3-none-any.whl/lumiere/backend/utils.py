import re
from pathlib import Path

import numpy as np
import polars as pl

from lumiere.typing import Weights


def read_log_file(log_file: str | Path, burn_in: int | float = 0.1) -> pl.DataFrame:
    df = pl.read_csv(
        log_file,
        separator="\t",
        comment_prefix="#",
    )
    if isinstance(burn_in, float):
        chain_length: int = df["Sample"].max()  # pyright: ignore
        burn_in = int(chain_length * burn_in)
    df = df.filter(pl.col("Sample") > burn_in)
    df = df.drop("Sample")
    return df


def read_weights(
    log_file: str | Path, burn_in: int | float = 0.1, n_samples: int = 100
) -> dict[str, list[Weights]]:
    df = read_log_file(log_file=log_file, burn_in=burn_in)
    if n_samples > len(df):
        raise ValueError("n_samples is greater than the number of available samples")
    df = df.tail(n_samples)

    targets = {
        m.group(1)
        for c in df.columns
        if (m := re.match(r"(.+?)W\.Layer\d+\[\d+\]\[\d+\]", c)) is not None
    }

    weights: dict[str, list[Weights]] = {}
    for target in targets:
        n_layers = max(
            int(re.search(r"Layer(\d+)", c).group(1))  # pyright: ignore
            for c in df.columns
            if c.startswith(f"{target}W.Layer")
        )
        n_inputs: list[int] = []
        n_outputs: list[int] = []
        for layer in range(1, n_layers + 1):
            ms = [
                re.search(r"\[(\d+)\]\[(\d+)\]", c)
                for c in df.columns
                if f"{target}W.Layer{layer}" in c
            ]
            n_inputs.append(max(int(m.group(1)) + 1 for m in ms))  # pyright: ignore
            n_outputs.append(max(int(m.group(2)) + 1 for m in ms))  # pyright: ignore

        weights[target] = [
            [
                np.array(
                    [
                        [
                            row[f"{target}W.Layer{layer + 1}[{i}][{j}]"]
                            for j in range(n_outputs[layer])
                        ]
                        for i in range(n_inputs[layer])
                    ]
                )
                for layer in range(n_layers)
            ]
            for row in df.iter_rows(named=True)
        ]

    return weights
