from datetime import datetime
import math
from edgar import Company
import pandas as pd
from edgar import set_identity
import yfinance as yf
import re
set_identity("MassDCF App | gilbert | massimohawk420@gmail.com")

#lists of labels
revenue_labels = [
    "Contract Revenue",
    "Revenue",
    "Revenues",
    "Total Revenue",
    "Total Revenues",
    "Net Revenue",
    "Net Revenues",
    "Sales",
    "Net Sales",
    "Operating Revenue",
    "Operating Revenues"
]

capex_labels = [
    "Purchases of Property and Equipment",
    "Capital Expenditures",
    "Additions to Property and Equipment",
    "Payments for Property  and Equipment",
    "Purchase of Property and Equipment",
    "Purchases of Property, Plant and Equipment",
    "Additions to Property, Plant and Equipment",
    "Payments for Property, Plant and Equipment",
    "Purchase of Property, Plant and Equipment",
    "Purchases related to property and equipment and intangible assets",
    "Capital expenditures"
]

depreciation_amort_labels = [
    "Depreciation and amortization",
    "Depreciation and amortization expense",
    "Depreciation and amortization expense",
    "Depreciation, amortization, and other",
    "Depreciation and Amortization",
    "Depreciation, amortization and other",
    "Depreciation, amortization and accretion",
    "Depreciation and Amortization Expense",
    "Depreciation and Amortization Expense, net"
]

cashlabels = [
    "Cash and Cash Equivalents",
    "Cash and cash equivalents",
    "Cash, cash equivalents, and restricted cash and cash equivalents, ending balances"
]

ebitlabels = [
    "Operating Income",
    "Income Before Tax from Continuing Operations" 
]

# Label lists with just one label for the other variables pulled in the provided snippet

current_assets_labels = [
    "Total Current Assets"
]

current_liabilities_labels = [
    "Total Current Liabilities"
]

income_tax_expense_labels = [
    "Income Tax Expense"
]

net_cash_operating_activities_labels = [
    "Net Cash from Operating Activities"
]

short_term_debt_labels = [
    "Short Term Debt"
]

long_term_debt_labels = [
    "Long Term Debt"
]

shares_outstanding_diluted_labels = [
    "Shares Outstanding (Diluted)"
]
earnings_per_share_labels = [
    "Earnings Per Share",
    "Earnings per share (diluted)",
    "Earnings per share, diluted",
    "Diluted Earnings Per Share",
    "Diluted EPS",
    "Earnings Per Share (Diluted)"
]

net_income_labels = [
    "Net Income",
    "Net Income (Loss)",
    "Net Income (Loss) Available to Common Shareholders",
    "Net Income (Loss) Available to Common Shareholders, Basic",
    "Net Income (Loss) Available to Common Shareholders, Diluted"
]
def get_first_valid_list(statement_df, label_list):
    for label in label_list:
        if label in statement_df.index:

            data = statement_df.loc[label]

            # 🔥 HANDLE DUPLICATE ROWS
            if isinstance(data, pd.DataFrame):
                # keep only numeric columns
                data = data.apply(pd.to_numeric, errors="coerce")
                data = data.max(axis=0)

            # now guaranteed to be a Series
            data = data[data.index.str.match(r"^\d{4}")]
            data = pd.to_numeric(data, errors="coerce").dropna()

            if len(data) == 0:
                continue

            # collapse duplicate years → take max
            collapsed = (
                data
                .groupby(data.index.str[:4])
                .max()
                .sort_index(ascending=False)
            )

            return collapsed.tolist()

    raise KeyError("None of the expected labels found in statement.")


def alldata(ticker: str) -> float:

    #edgar
    company = Company(ticker)
    financials = company.get_financials()
    #retreiveing all the statements and formatting the dataframe
    income_df = financials.income_statement().to_dataframe()
    income_df = income_df.set_index("label")

    balance_df = financials.balance_sheet().to_dataframe()
    balance_df = balance_df.set_index("label")
    
    cashflow_df = financials.cashflow_statement().to_dataframe()
    cashflow_df = cashflow_df.set_index("label")
    
    dates = sorted(
    [c for c in income_df.columns if str(c)[:4].isdigit()],
    key=lambda x: int(str(x)[:4]),
    reverse=True
    )[:3]
    latest = dates[0]

    #GETTING THE DATA

    try:
        depreciation_amortlist = get_first_valid_list(cashflow_df, depreciation_amort_labels)
    except KeyError:
        depreciation_amortlist = [0, 0, 0]
    net_income_list = get_first_valid_list(income_df, net_income_labels)
    ebitlist = get_first_valid_list(income_df, ebitlabels)
    
    revlist = get_first_valid_list(income_df, revenue_labels)

    try:
        capexlist = get_first_valid_list(cashflow_df, capex_labels)
    except KeyError:
        capexlist = [0, 0, 0]

    currentassetslist = get_first_valid_list(balance_df, current_assets_labels)

    currentliabilitieslist = get_first_valid_list(balance_df, current_liabilities_labels)
    
    incomeTaxExp = get_first_valid_list(income_df, income_tax_expense_labels)

    #sharesoutstanding = get_first_valid_list(income_df, shares_outstanding_diluted_labels)

    cashcash = get_first_valid_list(balance_df,cashlabels)
    try:
        shortdebt = get_first_valid_list(balance_df, short_term_debt_labels)
    except KeyError:
        shortdebt = [0, 0, 0]

    try:
        longdebt = get_first_valid_list(balance_df, long_term_debt_labels)
    except KeyError:
        longdebt = [0, 0, 0]
    # Create a total debt list by summing short_term_debt_list and long_term_debt_list element-wise
    total_debt_list = [shortdebt[i] + longdebt[i] for i in range(min(len(shortdebt), len(longdebt)))]
    opcashflow = get_first_valid_list(cashflow_df, net_cash_operating_activities_labels)
    
    earnings_per_share_list = get_first_valid_list(income_df, earnings_per_share_labels)
    
    #CALCULATIONS
    sharesoutstanding = [
        net_income_list[i] / earnings_per_share_list[i]
        for i in range(3)
    ]
    da_pct = depreciation_amortlist[0] / revlist[0]
    nwc = currentassetslist[0]-currentliabilitieslist[0]
    stock = yf.Ticker(ticker)
    ten_year = yf.Ticker("^TNX")
    riskfree = ten_year.history(period="1d")["Close"].iloc[-1] / 100
    beta = stock.info["beta"]
    marketriskprem = 0.055
    taxrate = incomeTaxExp[0] / ebitlist[0]
    taxrate = min(max(taxrate, 0.0), 0.30)
    currentprice = stock.history(period="1d")["Close"].iloc[-1]
    costofeq = riskfree + (beta*marketriskprem)

    #QUARTERS SINCE LAST ANNUAL REPORT
    if dates and len(dates) > 0:
        from dateutil.parser import parse as date_parse
        try:
            last_annual_date = date_parse(dates[0])
        except Exception:
            # fallback: try only the year
            last_annual_date = datetime(int(dates[0][:4]), 12, 31)
        now = datetime.now()
        months_diff = (now.year - last_annual_date.year) * 12 + (now.month - last_annual_date.month)
        quarters_since_last_annual = max(math.floor(months_diff / 3), 0)
    else:
        quarters_since_last_annual = None



    return {
        # Return only lists for things that can be lists
        "revlist": revlist,
        "ebitvalues": ebitlist,
        "capexlist": capexlist,
        "currentassetslist": currentassetslist,
        "currentliabilitieslist": currentliabilitieslist,
        "depreciation_amortization_list": depreciation_amortlist,
        "net_income_list": net_income_list,
        "shares_outstanding_list": sharesoutstanding,
        "income_tax_expense_list": incomeTaxExp,
        "operating_cash_flow_list": opcashflow,
        "cash_list": cashcash,
        "short_term_debt_list": shortdebt,
        "long_term_debt_list": longdebt,
        "earnings_per_share_list": earnings_per_share_list,
        "dates": dates,
        # Non-list single values (if needed, put these elsewhere)
        "lastfiscalyear": latest,
        "risk_free_rate": riskfree,
        "beta": beta,
        "market_risk_premium": marketriskprem,
        "currentprice": currentprice,
        "tax_rate": taxrate,
        "nwc": nwc,
        "da_pct": da_pct,
        "costofeq": costofeq,
        "total_debt_list": total_debt_list,
    }
