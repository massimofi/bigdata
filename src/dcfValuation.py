from src.financialData import alldata


def dcf_valuation(
    ticker,
    growth_rate,
    ebit_margin,
    capex_pct,
    nwc_pct,
    wacc,
    terminal_growth,
    years=5,
):
    # 🔹 Load all financials here
    data = alldata(ticker)
    #just for returning the current price
    currentprice = data["currentprice"]

    #raw data
    revenue = data["revenue"]
    tax_rate = data["tax_rate"]
    shares_outstanding = data["shares_outstanding"]
    da_pct = data["da_pct"]
    cash_flows = []
    rev = revenue

    for year in range(years):
        rev *= (1 + growth_rate)

        ebit = rev * ebit_margin
        nopat = ebit * (1 - tax_rate)

        da = rev * da_pct
        capex = rev * capex_pct
        delta_nwc = rev * nwc_pct

        fcf = nopat + da - capex - delta_nwc
        cash_flows.append(fcf)

    terminal_value = (
        cash_flows[-1] * (1 + terminal_growth)
    ) / (wacc - terminal_growth)

    discounted_fcfs = [
        cf / (1 + wacc) ** (i + 1)
        for i, cf in enumerate(cash_flows)
    ]

    discounted_tv = terminal_value / (1 + wacc) ** years

    enterprise_value = sum(discounted_fcfs) + discounted_tv
    implied_price = 1

    return enterprise_value, implied_price, currentprice