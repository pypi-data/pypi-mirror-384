def get_mat_cat(years_to_maturity:float)->float:
    """Categorize bond maturity into buckets."""
    if years_to_maturity < 3.5:
        return 2.
    elif years_to_maturity < 6.5:
        return 5.
    elif years_to_maturity < 7.5:
        return 7.
    elif years_to_maturity < 12.5:
        return 10.
    elif years_to_maturity < 17.5:
        return 15.
    elif years_to_maturity < 25:
        return 20.
    elif years_to_maturity < 35:
        return 30.
    else:
        return 50.