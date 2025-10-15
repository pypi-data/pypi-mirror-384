# src/qf_common/timecal/generators.py
from __future__ import annotations
from datetime import datetime, time as dtime
from typing import Sequence
import pandas as pd
from zoneinfo import ZoneInfo
import numpy as np
from typing import Tuple, Optional


# ---------- Helpers communs ----------

def _to_tz_aware(date_like: str | pd.Timestamp, tz: ZoneInfo) -> pd.Timestamp:
    ts = pd.to_datetime(date_like).normalize()
    return ts.tz_localize(tz) if ts.tzinfo is None else ts.tz_convert(tz)

def _business_days_between(start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DatetimeIndex:
    # start/end doivent déjà être tz-aware et dans la même TZ
    return pd.bdate_range(start=start_date, end=end_date, tz=start_date.tz)

def _exclude_today(days: pd.DatetimeIndex, tz_out: ZoneInfo, flag: bool) -> pd.DatetimeIndex:
    if not flag:
        return days
    today = pd.Timestamp.today(tz=tz_out).normalize()
    return days[days < today]

def _hours_minutes_to_points(
    days: pd.DatetimeIndex,
    hours_minutes: Sequence[tuple[int, int]],
    assume_tz: ZoneInfo,
    output_tz: ZoneInfo,
) -> list[pd.Timestamp]:
    out: list[pd.Timestamp] = []
    for day in days:
        for (h, m) in hours_minutes:
            wall = pd.Timestamp.combine(day.date(), dtime(h, m))      # naive wall time
            wall_local = wall.tz_localize(assume_tz)                  # localise selon assume_tz
            out.append(wall_local.tz_convert(output_tz))              # convert en output_tz
    return out

def _intraday_range_points(
    days: pd.DatetimeIndex,
    start_hour: int, start_minute: int,
    end_hour: int, end_minute: int,
    freq: str,
    assume_tz: ZoneInfo,
    output_tz: ZoneInfo,
) -> list[pd.Timestamp]:
    out: list[pd.Timestamp] = []
    for day in days:
        start_wall = datetime.combine(day.date(), dtime(start_hour, start_minute))
        end_wall   = datetime.combine(day.date(), dtime(end_hour,   end_minute))
        rng = pd.date_range(start=start_wall, end=end_wall, freq=freq)   # naive
        rng_local = rng.tz_localize(assume_tz)                           # localise
        out.extend(rng_local.tz_convert(output_tz).to_list())            # convert
    return out


# ---------- APIs “between” (source unique de vérité) ----------

def business_timestamps_between(
    *,
    start_date: str | pd.Timestamp,
    end_date: str | pd.Timestamp | None = None,
    hours_minutes: Sequence[tuple[int, int]] = ((16, 15),),
    assume_tz: str = "Europe/London",
    output_tz: str = "UTC",
    exclude_today: bool = True,
) -> list[pd.Timestamp]:
    """
    Jours ouvrés entre start_date et end_date, aux heures de `hours_minutes`.

    - start/end peuvent être naïfs ou tz-aware; on force en `output_tz`.
    - Les heures sont interprétées dans `assume_tz`, puis converties en `output_tz`.
    """
    tz_out = ZoneInfo(output_tz)
    tz_assume = ZoneInfo(assume_tz)

    end_date = _to_tz_aware(end_date or pd.Timestamp.today(tz=tz_out), tz_out)
    start_date = _to_tz_aware(start_date, tz_out)

    days = _exclude_today(_business_days_between(start_date, end_date), tz_out, exclude_today)
    return _hours_minutes_to_points(days, hours_minutes, tz_assume, tz_out)


def intraday_timestamps_between(
    *,
    start_date: str | pd.Timestamp,
    end_date: str | pd.Timestamp | None = None,
    start_hour: int = 9, start_minute: int = 0,
    end_hour: int = 16, end_minute: int = 0,
    freq: str = "T",
    assume_tz: str = "Europe/London",
    output_tz: str = "UTC",
    exclude_today: bool = True,
) -> list[pd.Timestamp]:
    """
    Jours ouvrés entre start_date et end_date, timestamps INTRADAY de start→end selon `freq`.
    """
    tz_out = ZoneInfo(output_tz)
    tz_assume = ZoneInfo(assume_tz)

    end_date = _to_tz_aware(end_date or pd.Timestamp.today(tz=tz_out), tz_out)
    start_date = _to_tz_aware(start_date, tz_out)

    days = _exclude_today(_business_days_between(start_date, end_date), tz_out, exclude_today)
    return _intraday_range_points(
        days, start_hour, start_minute, end_hour, end_minute, freq, tz_assume, tz_out
    )


# ---------- Wrappers “from_n_last_days” (délèguent à *between*) ----------

def business_timestamps_from_n_last_days(
    *,
    n_last_days: int,
    end_date: str | pd.Timestamp | None = None,
    hours_minutes: Sequence[tuple[int, int]] = ((16, 15),),
    assume_tz: str = "Europe/London",
    output_tz: str = "UTC",
    exclude_today: bool = True,
) -> list[pd.Timestamp]:
    """
    Calcule start_date = bdate_range(end=end_date, periods=n_last_days)[0], puis délègue à business_timestamps_between.
    """
    tz_out = ZoneInfo(output_tz)
    end_anchor = _to_tz_aware(end_date or pd.Timestamp.today(tz=tz_out), tz_out)
    start_date = pd.bdate_range(end=end_anchor, periods=n_last_days, tz=tz_out)[0]
    return business_timestamps_between(
        start_date=start_date, end_date=end_anchor, hours_minutes=hours_minutes,
        assume_tz=assume_tz, output_tz=output_tz, exclude_today=exclude_today
    )


def intraday_timestamps_from_n_last_days(
    *,
    n_last_days: int,
    end_date: str | pd.Timestamp | None = None,
    start_hour: int = 9, start_minute: int = 0,
    end_hour: int = 16, end_minute: int = 0,
    freq: str = "T",
    assume_tz: str = "Europe/London",
    output_tz: str = "UTC",
    exclude_today: bool = True,
) -> list[pd.Timestamp]:
    """
    Calcule start_date via n_last_days puis délègue à intraday_timestamps_between.
    """
    tz_out = ZoneInfo(output_tz)
    end_anchor = _to_tz_aware(end_date or pd.Timestamp.today(tz=tz_out), tz_out)
    start_date = pd.bdate_range(end=end_anchor, periods=n_last_days, tz=tz_out)[0]
    return intraday_timestamps_between(
        start_date=start_date, end_date=end_anchor,
        start_hour=start_hour, start_minute=start_minute,
        end_hour=end_hour, end_minute=end_minute,
        freq=freq, assume_tz=assume_tz, output_tz=output_tz, exclude_today=exclude_today
    )


def generate_time_points(
    open_time: Tuple[int, int] = (8,0),
    close_time: Tuple[int, int] = (16, 0),
    points_chosen: Optional[int] = 1
) -> Tuple[Tuple[int, int], ...]:
    """
    Génère une série de timestamps (heures, minutes) entre open_time et close_time.

    Args:
        open_time (Tuple[int, int]): heure et minute d'ouverture, ex: (8, 0)
        close_time (Tuple[int, int]): heure et minute de fermeture, ex: (16, 0)
        points_chosen (int, optional): nombre de points souhaités.
            - Si 1 → un seul point à la fermeture.
            - Si >1 → interpolation linéaire entre open et close.
            - Si None ou 0 → toutes les minutes.

    Returns:
        Tuple[Tuple[int, int], ...]: tuple d'heures/minutes ((h1, m1), (h2, m2), ...)
    """
    opening_minute = open_time[0] * 60 + open_time[1]
    closing_minute = close_time[0] * 60 + close_time[1]

    if points_chosen == 1:
        minutes_list = [closing_minute]
    elif points_chosen and points_chosen > 1:
        minutes_list = np.linspace(
            opening_minute, closing_minute, num=points_chosen, dtype=int
        ).tolist()
    else:
        minutes_list = list(range(opening_minute, closing_minute + 1))

    hours_minutes = tuple(divmod(m, 60) for m in minutes_list)
    return hours_minutes

