# src/qf_common/timestamps/formatting.py
from __future__ import annotations
import pandas as pd

def to_iso_format(
    df: pd.DataFrame,
    column: str,
    *,
    assume_tz: str = "UTC"
) -> pd.DataFrame:
    """
    Convertit une colonne datetime en format ISO 8601 (UTC, tz-aware).

    Args:
        df: DataFrame d'entrée.
        column: Nom de la colonne datetime.
        assume_tz: Si la colonne est naive (sans timezone), on assume cette timezone (par défaut UTC).
                   Ex: "Europe/Paris", "US/Eastern".

    Returns:
        DataFrame avec la colonne convertie en str ISO 8601 (tz=UTC).
        Exemple: "2025-09-29T10:15:30.000000Z"
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not in DataFrame")

    series = df[column]

    # Ensure datetime dtype
    series = pd.to_datetime(series, errors="coerce")

    # If tz-naive → localize with assume_tz
    if series.dt.tz is None:
        series = series.dt.tz_localize(assume_tz)

    # Normalize to UTC
    series = series.dt.tz_convert("UTC")

    # Convert to ISO format string
    df[column] = series.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return df


def to_timezone(
    df: pd.DataFrame,
    column: str,
    target_tz: str,
    *,
    assume_tz: str = "UTC"
) -> pd.DataFrame:
    """
    Convertit une colonne datetime dans une timezone cible.

    Args:
        df: DataFrame d'entrée.
        column: Nom de la colonne datetime.
        target_tz: Timezone cible (ex: "Europe/London", "US/Eastern").
        assume_tz: Si la colonne est naive (sans timezone), on assume cette timezone (par défaut UTC).

    Returns:
        DataFrame avec la colonne convertie (dtype datetime64[ns, tz]).
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not in DataFrame")

    series = pd.to_datetime(df[column], errors="coerce")

    # Si naive -> localize dans assume_tz
    if series.dt.tz is None:
        series = series.dt.tz_localize(assume_tz)

    # Convertir vers la target timezone
    df[column] = series.dt.tz_convert(target_tz)

    return df
