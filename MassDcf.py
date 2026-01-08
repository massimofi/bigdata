import streamlit as st
from src.financialData import alldata
from src.dcfValuation import dcf_valuation
from src.assumptions import predicted
import pandas as pd
from src.sqlThingy import insert_standardpoor
from src.sqlThingy import insert_sp500_into_db
#the s&p 











#nabar and linkden

st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: black;
        color: white;
        text-align: Center;
        padding: 12px;
        font-size: 20px;
        z-index: 9999;
    }
    </style>

    <div class="footer">
        MassDCF • Massimo Arellano <a href="https://www.linkedin.com/in/massimo-arellano/" target="_blank">Linkden</a>
    </div>
    """,
    unsafe_allow_html=True
)
page = st.sidebar.radio(
    "Go to",
    ["Financial Data","Overview","DCF Valuation",   "Export to Excel", "Standard and poors five hundy"]
)





if page == "DCF Valuation":
    st.header("DCF Valuation")
    ticker = st.text_input("Ticker", value="AAPL")

    if "growth_rate" not in st.session_state:
        st.session_state.growth_rate = 5.0
        st.session_state.ebit_margin = 0.3000
        st.session_state.capex_pct = 3.5
        st.session_state.nwc_pct = -5.0
        st.session_state.wacc = 0.0825
        st.session_state.terminal_growth = 3.0

    st.subheader("DCF Assumptions")

    if st.button("Autofill Assumptions"):
        gr, em, capx, nwc, w = predicted(ticker)
        st.session_state.growth_rate = float(gr) * 100
        st.session_state.ebit_margin = float(em)
        st.session_state.capex_pct = float(capx) * 100
        st.session_state.nwc_pct = float(nwc) * 100
        st.session_state.wacc = float(w)

    growth_rate = st.number_input(
        "Revenue Growth Rate (%)",
        min_value=0.0,
        max_value=20.0,
        step=0.05,
        format="%.2f",
        key="growth_rate"
    )

    ebit_margin = st.number_input(
        "EBIT Margin",
        min_value=0.0000,
        max_value=0.4000,
        step=0.0010,
        format="%.4f",
        key="ebit_margin"
    )

    capex_pct = st.number_input(
        "CapEx % of Revenue (%)",
        min_value=1.0,
        max_value=15.0,
        step=0.05,
        format="%.2f",
        key="capex_pct"
    )

    nwc_pct = st.number_input(
        "Net Working Capital % of Revenue (%)",
        min_value=-10.0,
        max_value=100.0,
        step=0.05,
        format="%.2f",
        key="nwc_pct"
    )

    wacc = st.number_input(
        "WACC",
        min_value=0.0500,
        max_value=0.1500,
        step=0.0005,
        format="%.4f",
        key="wacc"
    )

    terminal_growth = st.number_input(
        "Terminal Growth Rate (%)",
        min_value=1.0,
        max_value=4.0,
        step=0.05,
        format="%.2f",
        key="terminal_growth"
    )

    if st.button("Calculate DCF Value"):
        with st.spinner("Running DCF..."):
            ev, price, currentprice = dcf_valuation(
                ticker=ticker,
                growth_rate=growth_rate / 100,
                ebit_margin=ebit_margin,
                capex_pct=capex_pct / 100,
                nwc_pct=nwc_pct / 100,
                wacc=wacc,
                terminal_growth=terminal_growth / 100,
            )

        st.metric("Enterprise Value", f"${ev:,.0f}")
        st.metric("Implied Share Price", f"${price:,.2f}")
        st.metric("Real Share Price", f"${currentprice:,.2f}")
        




elif page == "Financial Data":
    st.header("Financial Data")

    ticker = st.text_input("Ticker", value="AAPL", key="data_ticker")

    if st.button("Load Financial Data"):
        with st.spinner("Fetching financials..."):
            data = alldata(ticker)
        
        # ---- Lists of key historical metrics and their display names ----
        financial_lists = [
            ("Revenue", "revlist"),
            ("EBIT", "ebitvalues"),
            ("CapEx", "capexlist"),
            ("Current Assets", "currentassetslist"),
            ("Current Liabilities", "currentliabilitieslist"),
            ("Depreciation & Amortization", "depreciation_amortization_list"),
            ("Net Income", "net_income_list"),
            ("Operating Cash Flow", "operating_cash_flow_list"),
            ("Shares Outstanding", "shares_outstanding_list"),
            ("Earnings Per Share", "earnings_per_share_list"),
            ("Cash", "cash_list"),
            ("Short Term Debt", "short_term_debt_list"),
            ("Long Term Debt", "long_term_debt_list"),
            ("Total Debt", "total_debt_list"),
        ]

        # Prepare dates (columns for history)
        dates = [str(d) for d in data['dates']]
        most_recent_col = dates[0] if dates else "Most Recent"

        # Prepare table dict for DataFrame (rows: metrics, columns: periods)
        table_dict = {}
        for display, key in financial_lists:
            vals = data.get(key, [])
            values_by_date = {}
            for i, date in enumerate(dates):
                val = vals[i] if i < len(vals) else None
                # Show numbers as dollars unless it's EPS or Shares (format as needed)
                if display in ("Earnings Per Share",):
                    values_by_date[date] = f"${val:,.2f}" if val is not None else ""
                elif display == "Shares Outstanding":
                    values_by_date[date] = f"{val:,.0f}" if val is not None else ""
                else:
                    values_by_date[date] = f"${val:,.0f}" if val is not None else ""
            table_dict[display] = values_by_date

        # === Add plain (non-list) fields for the most recent year/period ===
        flat_fields = [
            ("Tax Rate", f"{data['tax_rate']*100:.2f}%"),
            ("DA % of Revenue", f"{data['da_pct']*100:.2f}%"),
            ("NWC", f"${data['nwc']:,.0f}"),
            ("Risk-Free Rate (10Y)", f"{data['risk_free_rate']*100:.2f}%"),
            ("Beta", f"{data['beta']:.2f}"),
            ("Market Risk Premium", f"{data['market_risk_premium']*100:.2f}%"),
            ("Current Price", f"${data['currentprice']:.2f}"),
            ("Cost of Equity", f"{data['costofeq']*100:.2f}%"),
        ]
        for label, value in flat_fields:
            table_dict[label] = {most_recent_col: value}

        # === Add single-value (most recent) entries for base financials ===
        single_keys = [
            ("Revenue", "revenue"),
            ("EBIT", "ebit"),
            ("CapEx", "capex"),
            ("Current Assets", "current_assets"),
            ("Current Liabilities", "current_liabilities"),
            ("Income Tax Expense", "income_tax_expense"),
        ]
        for label, key in single_keys:
            val = data.get(key, None)
            if val is not None:
                if "Income Tax" in label:
                    table_dict[label][most_recent_col] = f"${val:,.0f}"
                else:
                    table_dict[label][most_recent_col] = f"${val:,.0f}"

        # Compose columns (most recent then historical dates)
        cols = [most_recent_col] + [d for d in dates if d != most_recent_col]

        # Build DataFrame
        df = pd.DataFrame.from_dict(table_dict, orient="index")
        df = df[cols]

        st.subheader("Financial Data Historical Lists")
        st.dataframe(df, width="stretch")





elif page == "Overview":
    st.header("About MassDCF")

    st.markdown(
        """
        **MassDCF** is a based dcf tool made by Massimo Arellano that can only be accessed by fellow neurodivergents

        ### What it does
        - DCF Valuation: Tool allows you to use basic predicitve modeling for assuming metrics (that can be adjusted) and also pulls market information for real dcf calculations 5 years into the future. 
        - Financial Data + Excel Export: Just lists all of the financial data which was pulled using edgartool library along with yahoo finance, also allows for it to be exported to an excel sheet.
        - DCF to Excel: Gives you an excel sheet with the past three years of financial data along with the automated asumptions, future predicted values, and the dcf math. Can be downloaded and modified for own use.
        ### Limitations
        - Predictions are very unstable and are based on only the past 2-3 years
        - Still requires human adjustments to account for some errors

        ---
        **Disclaimer:**  
        This tool IS investment advice and I AM liable
        """
    )




    





st.header("EDGAR Financial Statement Explorer")

ticker_input = st.text_input("Enter Ticker for Raw Labels View", value="AAPL")

if ticker_input:
    try:
        # Get raw data frame from edgar
        
        try:
            # Try to fetch the actual EDGAR Company instance via the same method as in financialData.py
            from edgar import Company
            company = Company(ticker_input)
        except Exception:
            pass

        # To get the raw dataframes, we need to recreate the extraction logic for labels:
        income_df = None
        balance_df = None
        cashflow_df = None

        if company:
            financials = company.get_financials()
            income_df = financials.income_statement().to_dataframe()
            cashflow_df = financials.cashflow_statement().to_dataframe()
            balance_df = financials.balance_sheet().to_dataframe()
        else:
            # fallback: error
            st.error("Could not establish EDGAR data source (missing edgar library).")
        
        if income_df is not None and cashflow_df is not None and balance_df is not None:
            st.subheader("Income Statement Labels")
            st.write(list(income_df['label']))

            st.subheader("Cash Flow Statement Labels")
            st.write(list(cashflow_df['label']))

            st.subheader("Balance Sheet Labels")
            st.write(list(balance_df['label']))
        else:
            st.warning("Unable to retrieve financial statement labels. Please check your EDGAR installation.")
    except Exception as e:
        st.error(f"Failed to fetch statements: {e}")

        # INSERT_YOUR_CODE
        # Streamlit UI to call listDebug and display output



elif page == "Standard and poors five hundy":
    st.header("all the stocks")
    if st.button("Load S&P 500 Companies"):
        df = insert_standardpoor()
        insert_sp500_into_db(df)
    