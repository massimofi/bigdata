from src.financialData import alldata



def predicted (
ticker
):

    data = alldata(ticker)
    revlist = data["revlist"]
    ebitvalues = data["ebitvalues"]
    capexlist = data["capexlist"]
    currentassetslist = data["currentassetslist"]
    currentliabilitieslist = data["currentliabilitieslist"]
    costofeq = data["costofeq"]





    #cagr 
    growth_rate = (revlist[0]/revlist[2])**(1/2)-1

    #ebitmargin 3 year avergye
    ebit_margin = 0
    for i in range(3):
        ebit_margin += (ebitvalues[i]/revlist[i])
        print(ebit_margin)
    ebit_margin /= 3
    print(ebit_margin)
    #capx average 3 years
    capex_pct = 0
    for i in range(3):
        capex_pct += (capexlist[i]/revlist[i])
    capex_pct /= 3
    
    #2 year nwc % of rev kinda cuck tho
    nwc_pct = 0
    for i in range(2):
        nwclocal = currentassetslist[i]- currentliabilitieslist[i]
        nwc_pct += nwclocal / revlist[i]
    nwc_pct/=2

    #COVEN
    wacc = costofeq


    return(growth_rate,ebit_margin,capex_pct,nwc_pct,wacc)