from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    import polars as pl


def print_metadata_for_llms() -> str:
    raise NotImplementedError


def to_csv_str(df: pl.DataFrame) -> str:
    import io

    string_io = io.StringIO()
    df.write_csv(string_io)
    string_io.seek(0)
    return string_io.read()
