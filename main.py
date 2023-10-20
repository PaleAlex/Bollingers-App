from datetime import timedelta, datetime
from bollinger import BollingerStrategy as bs
from portfolio import MCPortfolio as mc
import streamlit as st
import altair as alt
import numpy as np

st.set_page_config(page_title="PaleAlex: Investmenti",
                   page_icon=":globe_with_meridians:",
                   layout="wide")

st.title("🚀 Supporto agli investimenti finanziari 🚀 📈")

start = datetime.now()-timedelta(days=420)
end = datetime.now()

ticker_diz = {"Stellantis": "STLAM.MI",
              "Safilo": "SFL.MI",
              "Saipem": "SPM.MI",
              "Prysmian": "PRY.MI",
              "Ferrari": "RACE.MI",
              "Industrie De Nora": "DNR.MI",
              "WeBuild": "WBD.MI",
              "Alerion": "ARN.MI",
              "Eurotech": "ETH.MI",
              "TISG": "TISG.MI",
              "Digitouch": "DGT.MI",
              "CY4": "CY4.MI",
              "Nvidia": "NVDA",
              "Tesla": "TSLA"}

col1, col2, col3= st.columns([1,4,1])
with col1:
    with st.form(key = "search_bar"):
        sel1 = st.selectbox("Seleziona lo stock", [""]+list(ticker_diz.keys()))
        sel2 = st.text_input("oppure cerca un altro ticker...", placeholder="es. AAPL")
        st.form_submit_button("Calcola")

try:
    with col2:
        if sel2:
            selection = sel2.upper()
        else:
            if not sel1:
                raise Exception()
            selection = ticker_diz[sel1]
        with st.spinner(text="Calcolando..."):
            obj = bs(selection,start,end)
            sma, devup, devdown = obj.optimizer()
            df = obj.set_parameters(sma,devup,devdown)    

        to_plot = df.reset_index()
        base = alt.Chart(to_plot).encode(
            alt.X('Date:T', axis=alt.Axis(title="t"))
        )

        line1 = base.mark_line(opacity=0.3, color='#57A44C').encode(
            alt.Y('Upper:Q')
        )

        line2 = base.mark_line(opacity=0.3, color='#57A44C').encode(
        alt.Y('Lower:Q')
        )

        # Add tooltips
        line3 = base.mark_line(color='blue').encode(
            alt.Y('Adj Close:Q',
                axis=alt.Axis(title=f'Prezzo {selection}'),
                scale=alt.Scale(domain=(0, df["Adj Close"].max()*2))),
            tooltip=['Date', 'Adj Close']
        )
        
        # Enable zooming and panning
        c = alt.layer(line1, line2, line3).interactive()
        
        # Add a selection for the x-axis range
        brush = alt.selection_interval(encodings=['x'])
        
        # Bind the selection to the x-axis scale
        base = base.add_selection(brush)
        
        # Add a conditional encoding for the selected range
        line3 = line3.encode(
            color=alt.condition(brush, alt.value('blue'), alt.value('lightgray'))
        )
        
        # Bind the selection to the x-axis scale
        line3 = line3.add_selection(brush)
        
        # Add a slider to control the opacity of the lines
        opacity_slider = alt.binding_range(min=0, max=1, step=0.1, name='Opacity:')
        opacity_selection = alt.selection_single(bind=opacity_slider, fields=['opacity'], init={'opacity': 0.3})
        line1 = line1.encode(
            opacity=alt.condition(opacity_selection, alt.value(0.3), alt.value(0))
        )
        line2 = line2.encode(
            opacity=alt.condition(opacity_selection, alt.value(0.3), alt.value(0))
        )
        
        # Bind the opacity selection to the opacity slider
        opacity_slider = opacity_slider.add_selection(opacity_selection)
        
        # Combine the chart and the slider
        c = alt.vconcat(c, opacity_slider)
        
        # Add a radio button to switch between different data sources
        data_source_radio = alt.binding_radio(options=['Upper', 'Lower'], name='Data Source:')
        data_source_selection = alt.selection_single(bind=data_source_radio, fields=['data_source'], init={'data_source': 'Upper'})
        line1 = line1.transform_filter(data_source_selection)
        line2 = line2.transform_filter(data_source_selection)
        
        # Bind the radio button to the data source selection
        data_source_radio = data_source_radio.add_selection(data_source_selection)
        
        # Combine the chart, the slider, and the radio button
        c = alt.vconcat(c, data_source_radio)
        
        # Display the chart
        st.altair_chart(c, use_container_width=True)

        
    with col3:
        st.write("**Segnale**")
        last = df.iloc[-1:,:]
        last_day = last.index + timedelta(days = 1)
        last_price = last["Adj Close"][0]
        last_upper = last["Upper"][0]
        last_lower = last["Lower"][0]

        if last_price>=last_upper:
            s=" SELL"
        elif last_price<=last_lower:
            s=" BUY"
        else:
            s="Neutro"

        
        st.markdown(f"*Il segnale per il giorno {last_day[0].strftime('%d/%m/%Y')}* è <p style='background-color:#0066cc;color:#33ff33;font-size:24px;border-radius:2%;text-align:center'> {s} </p>", unsafe_allow_html=True)
        
        st.write("**Check ottimizzazione strategia**")

        if (sma, devup, devdown) != (60, 2.6, 2.6):
            st.write(f"✅")
        else:
            st.write("❌")

        st.write("**Check volumi**")
        if (obj.volume_check(sma)[-1]) > 0.95:
            st.write(f"✅")
        else:
            st.write("❌")

    with col1:
        with st.expander("Dettagli tecnici"):
            st.write(f"Parametri ottimizzati: sma = {sma} | dev_up = {round(devup,1)} | dev_down {round(devdown,1)}")
            st.write(f"Exp moving average ultimi 5 giorni: {list(obj.volume_check(sma))}")
except:
    with col2:
        st.write("**<br><br><br><p style='text-align:center'>Scegli il titolo da analizzare</p>**", unsafe_allow_html=True)


st.write("#### Verifica più stocks")
col1, col2= st.columns([1,1])

with col1:
    with st.form(key = "more_searches"):
        more_stocks = st.text_input("Lista di ticker separati da virgola", placeholder="es. AAPL,TSLA,GOOG")
        calcola = st.form_submit_button("Calcola")

if calcola:
    more_stocks = more_stocks.upper().strip().split(",")

    with col2:
        for stock in more_stocks:
            if stock:
                with st.spinner(text=f"Calcolando {stock}..."):
                    obj = bs(stock,start,end)
                    sma, devup, devdown = obj.optimizer()
                    df = obj.set_parameters(sma,devup,devdown)
                    lasts = df.iloc[-3:,:]

                    highers = lasts['High'].values
                    lowers = lasts['Low'].values
                    last_uppers = lasts["Upper"].values
                    last_lowers = lasts["Lower"].values

                    higher_differences = np.subtract.outer(last_uppers, highers).flatten()
                    lower_differences = np.subtract.outer(last_lowers, lowers).flatten()

                    if np.any(higher_differences<=0) or np.any(lower_differences>=0):
                        st.write(f"**{stock} è da tenere d'occhio!**")
                    else:
                        st.write(f"{stock} neutro")

st.write("#### Calcolo miglior portfolio")
col1, col2= st.columns([1,1])

with col1:
    with st.form(key = "porfolio"):
        ticker_stocks = st.text_input("Lista di ticker separati da virgola", placeholder="es. AAPL,TSLA,GOOG")
        days_ago = int(st.number_input("Analisi da _ giorni fa (min 365, max 1299)", min_value=365, max_value=1299))
        calcola_portfolio = st.form_submit_button("Calcola")

if calcola_portfolio:
    ticker_stocks_list = ticker_stocks.upper().strip().split(",")
    start = datetime.now()-timedelta(days=days_ago)
    with col2:
        with st.spinner(text="Calcolando..."):
            tester = mc(ticker_stocks_list, start, end)
            res = tester.optimizer()
            st.dataframe(res)
