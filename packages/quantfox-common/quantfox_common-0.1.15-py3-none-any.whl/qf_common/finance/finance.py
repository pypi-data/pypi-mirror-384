"""
Utilities for financial computations using QuantLib, including bond pricing.
"""

import math
import QuantLib as ql
import pandas as pd
from sqlalchemy import text
from taskflowbridge.db_config import get_db_connection_pool
from datetime import date
from scipy.optimize import brentq


def calculate_bond_price(
    yield_rate: float,
    coupon_rate: float,
    remaining_maturity: float,
    frequency: int,
    issue_date,
    valuation_date,
    clean: bool = True,
    compounding_frequency: int = 1,
) -> float:
    """
    Calculate the (clean or dirty) price of a fixed-rate bond using QuantLib.

    Parameters
    ----------
    yield_rate : float
        Annual yield to maturity (decimal, e.g. 0.05 for 5%).
    coupon_rate : float
        Annual coupon rate (decimal, e.g. 0.03 for 3%).
    remaining_maturity : float
        Remaining time to maturity in years (approximate).
    frequency : int
        Number of coupon payments per year (1=annual, 2=semiannual).
    issue_date : date or datetime
        Issue date of the bond.
    valuation_date : date or datetime
        Valuation date for pricing.
    clean : bool, default=True
        If True, returns clean price; if False, returns dirty price.

    Returns
    -------
    float
        Bond price per unit of par (e.g., 1.01 = 101%).
    """
    # set evaluation date
    ql_val = ql.Date(valuation_date.day, valuation_date.month, valuation_date.year)
    ql.Settings.instance().evaluationDate = ql_val

    # conventions
    settlement_days = 0
    calendar = ql.TARGET()
    bdc = ql.ModifiedFollowing

    # map frequency to QuantLib Frequency
    if frequency == 1:
        freq_ql = ql.Annual
    elif frequency == 2:
        freq_ql = ql.Semiannual
    else:
        raise ValueError(f"Unsupported frequency: {frequency}")

    if compounding_frequency == 1:
        comp_freq_ql = ql.Annual
    elif compounding_frequency == 2:
        comp_freq_ql = ql.Semiannual
    else:
        raise ValueError(f"Unsupported compounding_frequency: {compounding_frequency}")

    # approximate maturity date by adding days
    days = int(round(remaining_maturity * 365.25))
    maturity_qld = ql_val + days

    # convert issue date to QuantLib Date
    issue_qld = ql.Date(issue_date.day, issue_date.month, issue_date.year)

    # build schedule
    schedule = ql.Schedule(
        issue_qld,
        maturity_qld,
        ql.Period(freq_ql),
        calendar,
        bdc,
        bdc,
        ql.DateGeneration.Backward,
        False,
    )

    # create bond
    bond = ql.FixedRateBond(
        settlement_days,
        100.0,
        schedule,
        [coupon_rate],
        ql.Thirty360(ql.Thirty360.BondBasis),
        bdc,
        100.0,
        issue_qld,
    )

    # flat yield curve
    flat_ts = ql.FlatForward(
        ql_val,
        yield_rate,
        ql.Thirty360(ql.Thirty360.BondBasis),
        ql.Compounded,
        comp_freq_ql,
    )
    curve_handle = ql.YieldTermStructureHandle(flat_ts)
    engine = ql.DiscountingBondEngine(curve_handle)
    bond.setPricingEngine(engine)

    # price
    price = bond.cleanPrice() if clean else bond.dirtyPrice()
    return price / 100


def compute_macaulay_duration(
    price, coupon_rate, yield_to_maturity, years_to_maturity, payment_frequency=1
):
    """
    Description:
    ------------
    Calculates the Macaulay Duration for a given bond using the standard formula.
    Macaulay Duration represents the weighted average time an investor needs to
    hold a bond to recover its initial investment through coupon payments and principal.

    Typically, the duration is less than the bond's time to maturity:
    0 < Macaulay Duration < Time to Maturity

    Args:
    -----
        price (float): The market price of the bond.
        coupon_rate (float): The bond’s annual coupon rate (in decimal form, e.g., 0.05 for 5%).
        yield_to_maturity (float): The bond’s annual yield to maturity (also in decimal).
        years_to_maturity (float): The number of years remaining until the bond matures.
        payment_frequency (int, optional): Number of coupon payments per year (e.g., 1 for annual, 2 for semiannual). Default is 1.

    Returns:
    --------
        float: The Macaulay Duration, expressed in years.

    Example:
    --------
    >>> macaulay_duration(price=1, coupon_rate=0.05, yield_to_maturity=0.03,
    ...                   years_to_maturity=3.81, payment_frequency=1)
    >>> 2.67350467067113
    """
    # Normalize the bond price if it's quoted above 4 (likely given in percentage format)
    if price > 4:
        price = price / 100

    # Calculate accrued time since last coupon payment
    accrued_coupon = years_to_maturity % (1 / payment_frequency)
    years_to_maturity -= accrued_coupon
    number_of_payments = int(years_to_maturity * payment_frequency)

    # Calculate the regular coupon payment
    coupon_payment = coupon_rate / payment_frequency
    q = 1 + (yield_to_maturity / payment_frequency)

    # Calculate the present value weighted time for coupon payments
    macaulay_duration_value = sum(
        (k + accrued_coupon) * coupon_payment / q ** (k + accrued_coupon)
        for k in range(number_of_payments + 1)
    )

    # Add the present value weighted time of the final principal payment
    macaulay_duration_value += (
        (number_of_payments + accrued_coupon)
        * 1
        / q ** (number_of_payments + accrued_coupon)
    )

    # Divide by the bond price to get duration in terms of years
    macaulay_duration_value = macaulay_duration_value / price

    # Adjust for payment frequency
    return macaulay_duration_value / payment_frequency


COUNTRY_DEFAULT_FREQ_MAP = {
    "IT": 2,
    "FR": 1,
    "ES": 1,
    "DE": 1,
    "US": 2,
    "GB": 2,
    "JP": 2,
    "AU": 2,
    "NZ": 2,
    "ZA": 2,
    "CH": 1,
    "SE": 1,
    "NO": 1,
    "FI": 1,
    "PL": 1,
    "CZ": 1,
    "DK": 1,
    "HU": 1,
    "SK": 1,
    "GR": 1,
    "PT": 1,
    "BE": 1,
    "NL": 1,
    "LU": 1,
    "IE": 1,
    "CY": 1,
    "IL": 2,
    "SNAT": 2,
}


def compute_forward_price_bond(
    issue_date,
    maturity_date,
    coupon,
    freq,
    clean_price_today,
    repo_rate,
    horizon_months=3,
    settle_date_py=None,
    country_iso="IT",
    bdc=ql.Following,
    comp=ql.Compounded,
    comp_freq=ql.Annual,
    repo_daycount=ql.Actual360(),
):
    """
    Forward price & forward yield (carry = fwd_yield - settle_yield), style Bloomberg.
    Inputs:
      - issue_date/maturity_date/settle_date_py: datetime.date
      - coupon: taux annuel en décimal (ex 0.05)
      - freq: 1/2/4
      - clean_price_today: prix clean (base 100)
      - repo_rate: annuel décimal (simple)
      - horizon_months: int
    """

    def _instantiate_calendar(cls):
        """Essaye cls(), sinon cls(Market) avec un ordre sensible, sinon Italy()."""
        # 1) sans argument
        try:
            return cls()
        except TypeError:
            pass

        # 2) avec un Market par défaut (ordre: GovernmentBond > Settlement > Exchange > Default)
        for cand in ("GovernmentBond", "Settlement", "Exchange", "Default"):
            if hasattr(cls, cand):
                try:
                    return cls(getattr(cls, cand))
                except Exception:
                    continue

        # 3) fallback
        return ql.Italy()

    def _safe_calendar(name: str) -> ql.Calendar:
        """Retourne ql.<name>() (avec Market si requis). Fallback: ql.Italy()."""
        cls = getattr(ql, name, None)
        if cls is None:
            return ql.Italy()
        return _instantiate_calendar(cls)

    COUNTRY_CALENDAR_MAP = {
        "SK": _safe_calendar("Slovakia"),
        "DK": _safe_calendar("Denmark"),
        "SI": _safe_calendar("Slovenia"),
        "CZ": _safe_calendar("CzechRepublic"),
        "US": _safe_calendar(
            "UnitedStates"
        ),  # exigera GovernmentBond/Settlement en 1.18
        "FR": _safe_calendar("France"),
        "JP": _safe_calendar("Japan"),
        "NZ": _safe_calendar("NewZealand"),
        "CY": _safe_calendar("Cyprus"),  # absent → Italy()
        "AU": _safe_calendar("Australia"),
        "NL": _safe_calendar("Netherlands"),
        "HU": _safe_calendar("Hungary"),
        "AT": _safe_calendar("Austria"),
        "FI": _safe_calendar("Finland"),
        "IE": _safe_calendar("Ireland"),
        "PL": _safe_calendar("Poland"),
        "ZA": _safe_calendar("SouthAfrica"),
        "PT": _safe_calendar("Portugal"),
        "ES": _safe_calendar("Spain"),
        "NO": _safe_calendar("Norway"),
        "SNAT": _safe_calendar(
            "TARGET"
        ),  # supranational → TARGET si dispo, sinon Italy()
        "IL": _safe_calendar("Israel"),
        "GB": _safe_calendar("UnitedKingdom"),  # prendra Settlement/Exchange si requis
        "IT": _safe_calendar("Italy"),
        "SE": _safe_calendar("Sweden"),
        "GR": _safe_calendar("Greece"),
        "CH": _safe_calendar("Switzerland"),
        "BE": _safe_calendar("Belgium"),
        "DE": _safe_calendar("Germany"),
        "LU": _safe_calendar("Luxembourg"),
    }

    def get_calendar(country_iso: str) -> ql.Calendar:
        """Fallback global: Italy() si clé inconnue ou constructeur absent."""
        return COUNTRY_CALENDAR_MAP.get(country_iso.upper(), ql.Italy())

    calendar = get_calendar(country_iso)

    # Day count robuste
    try:
        daycount = ql.ActualActual(ql.ActualActual.ICMA)
    except Exception:
        try:
            daycount = ql.ActualActual(ql.ActualActual.Bond)
        except Exception:
            daycount = ql.ActualActual(ql.ActualActual.ISMA)

    # Dates
    if settle_date_py is None:
        settle_date_py = date.today()
    issue_ql = ql.Date(issue_date.day, issue_date.month, issue_date.year)
    maturity_ql = ql.Date(maturity_date.day, maturity_date.month, maturity_date.year)
    settle_ql = ql.Date(settle_date_py.day, settle_date_py.month, settle_date_py.year)
    horizon_ql = calendar.advance(settle_ql, ql.Period(horizon_months, ql.Months))
    face = 100.0

    if freq is None or (isinstance(freq, float) and math.isnan(freq)):
        freq = COUNTRY_DEFAULT_FREQ_MAP[country_iso]

    # Fréquence
    frequency = {1: ql.Annual, 2: ql.Semiannual, 4: ql.Quarterly}.get(
        int(freq), ql.Semiannual
    )

    # Bond
    schedule = ql.Schedule(
        issue_ql,
        maturity_ql,
        ql.Period(frequency),
        calendar,
        bdc,
        bdc,
        ql.DateGeneration.Backward,
        False,
    )
    bond = ql.FixedRateBond(0, face, schedule, [coupon], daycount)

    # Accrued (points de prix)
    accrued_today_px = 100.0 * bond.accruedAmount(settle_ql) / face
    accrued_horizon_px = 100.0 * bond.accruedAmount(horizon_ql) / face
    accrued_increase_px = accrued_horizon_px - accrued_today_px

    # Dirty today
    dirty_today = clean_price_today + accrued_today_px

    # Coupons dans (t, t+h], réinvestis au repo simple
    h_frac = repo_daycount.yearFraction(settle_ql, horizon_ql)
    coupons_in_window = []
    for cf in bond.cashflows():
        if cf.hasOccurred(settle_ql):
            continue
        # if cf.date() < horizon_ql:
        if cf.date() <= horizon_ql:
            cf_frac = repo_daycount.yearFraction(settle_ql, cf.date())
            reinvest = 1.0 + repo_rate * max(h_frac - cf_frac, 0.0)
            coupons_in_window.append(100.0 * cf.amount() / face * reinvest)

    # if all(cf.date() > horizon_ql for cf in bond.cashflows() if not cf.hasOccurred(settle_ql)):
    #     accrued_increase_px = 0.0

    # Forward dirty & clean
    fwd_dirty = (
        dirty_today * (1.0 + repo_rate * h_frac)
        - accrued_increase_px
        - sum(coupons_in_window)
    )

    fwd_dirty = dirty_today * (1.0 + repo_rate * h_frac) - sum(coupons_in_window)

    # repo_factor = (1 + repo_rate * h_frac)
    # fwd_dirty = dirty_today * repo_factor - sum(coupons_in_window)

    fwd_clean = fwd_dirty - accrued_horizon_px

    def solve_yield(price_clean, settle):
        def f(y):
            return (
                ql.BondFunctions.cleanPrice(bond, y, daycount, comp, comp_freq, settle)
                - price_clean
            )

        # bracket robuste (élargit si nécessaire)
        a, b = -0.05, 0.20  # -5% à 20% par défaut
        fa, fb = f(a), f(b)
        it = 0
        while fa * fb > 0 and it < 10:
            # élargit de 50% autour du centre
            width = (b - a) * 0.5
            a -= width
            b += width
            fa, fb = f(a), f(b)
            it += 1
        if fa * fb > 0:
            raise ValueError(
                "Impossible de bracketter la racine du YTM (check price/conventions)."
            )
        return brentq(f, a, b, maxiter=200, xtol=1e-6)

    # Yields (à partir des CLEAN prices)
    settle_yld = solve_yield(clean_price_today, settle_ql)
    fwd_yld = solve_yield(fwd_clean, horizon_ql)

    carry_bp = (fwd_yld - settle_yld) * 1e4

    return {
        "settle_date": settle_ql.ISO(),
        "horizon_date": horizon_ql.ISO(),
        "dirty_today": dirty_today,
        "forward_dirty": fwd_dirty,
        "forward_clean": fwd_clean,
        "settle_yield": settle_yld,
        "forward_yield": fwd_yld,
        "carry_bp": carry_bp,
        "coupons_in_window": coupons_in_window,
        "accrued_today_px": accrued_today_px,
        "accrued_horizon_px": accrued_horizon_px,
    }
