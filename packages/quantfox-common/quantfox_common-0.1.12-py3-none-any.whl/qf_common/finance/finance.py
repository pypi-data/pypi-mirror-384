"""
Utilities for financial computations using QuantLib, including bond pricing.
"""

import QuantLib as ql
import pandas as pd
from sqlalchemy import text
from taskflowbridge.db_config import db


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


class Bond:
    """Bond instrument class for loading and managing bond securities data.

    Loads bond information from database by ISIN and provides maturity calculations.

    Args:
        isin (str): International Securities Identification Number

    Attributes:
        All fields from securities table (ticker, cusip, coupon, maturity_date, etc.)

    Properties:
        years_to_maturity (float): Remaining years to maturity from today (UTC)

    Raises:
        ValueError: If ISIN not found in securities database"""

    def __init__(self, isin):
        self.isin = isin
        query = text(
            """
SELECT
    ticker,
    cusip,
    isin,
    security_des,
    country_iso,
    currency,
    issued_amount,
    outstanding_amount,
    collateral_type,
    announce_date,
    issue_date,
    first_settlement_date,
    maturity_type,
    cpn_freq,
    first_coupon_date,
    cpn_typ,
    inflation_coupon_type,
    strip_type,
    day_cnt_des,
    name,
    exchange,
    fitch_rating,
    dbrs_rating,
    bloomberg_composite_rating,
    bloomberg_type,
    green_bond,
    coupon,
    maturity_date,
    series,
    ref_infla_index,
    inflation_lag,
    base_cpi,
    reset_index,
    quoted_margin
FROM securities
WHERE isin = :isin
"""
        )
        with db.session() as session:
            result = session.execute(query, {"isin": isin}).fetchall()

            colonnes = [
                "ticker",
                "cusip",
                "isin",
                "security_des",
                "country_iso",
                "currency",
                "issued_amount",
                "outstanding_amount",
                "collateral_type",
                "announce_date",
                "issue_date",
                "first_settlement_date",
                "maturity_type",
                "cpn_freq",
                "first_coupon_date",
                "cpn_typ",
                "inflation_coupon_type",
                "strip_type",
                "day_cnt_des",
                "name",
                "exchange",
                "fitch_rating",
                "dbrs_rating",
                "bloomberg_composite_rating",
                "bloomberg_type",
                "green_bond",
                "coupon",
                "maturity_date",
                "series",
                "ref_infla_index",
                "inflation_lag",
                "base_cpi",
                "reset_index",
                "quoted_margin",
            ]

            if result:
                securities = pd.DataFrame(result, columns=colonnes)
                securities["maturity_date"] = pd.to_datetime(
                    securities["maturity_date"]
                )
            else:
                securities = pd.DataFrame(columns=colonnes)
        if securities.empty:
            raise ValueError(f"ISIN {isin} not found in securities")
        row = securities.iloc[0]
        for col in securities.columns:
            setattr(self, col, row[col])

    @property
    def years_to_maturity(self) -> float:
        """
        Retourne la maturité résiduelle du bond (en années) à aujourd’hui (UTC).
        """
        ts = pd.Timestamp.now(tz="UTC").normalize()
        mat_dt = pd.to_datetime(self.maturity_date)
        if mat_dt.tzinfo is None:
            mat_dt = mat_dt.tz_localize("UTC")
        else:
            mat_dt = mat_dt.tz_convert("UTC")
        years_to_maturity = (mat_dt - ts).days / 365.25
        return max(years_to_maturity, 0.0)
