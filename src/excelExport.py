import pandas as pd
from openpyxl import load_workbook
import io
from src.financialData import alldata

def excel_export(ticker):
    data = alldata(ticker)
    workbook = load_workbook("CFI-DCF-Model-Template-Updated.xlsx")
    sheet = workbook.active

    #putting allat shit to work
    sheet["D5"] = data["tax_rate"]
    sheet["D6"] = data[""]
    sheet["D7"] = data[""]
    sheet["D8"] = data[""]
    #sheet["D9"] = data[""]
    sheet["D10"] = data["lastfiscalyear"]
    sheet["D11"] = data["currentprice"]
    sheet["D12"] = data["shares_outstanding"]
    sheet["D13"] = data["total_debt"]
    sheet["D14"] = data["cashcash"]
    sheet["D15"] = data["capex"]
