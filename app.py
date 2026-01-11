from bollinger import BollingerStrategy as bs
from portfolio import MCPortfolio as mc
from SSA_decomposition import SSA_actions
from datetime import timedelta, datetime
import streamlit as st
import altair as alt
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings("ignore")


st.set_page_config(page_title="PaleAlex: Investmenti",
                   page_icon=":globe_with_meridians:",
                   layout="wide")

st.title("🚀 Supporto agli investimenti finanziari 🚀 📈")
days = 425
start = datetime.now()-timedelta(days=days)
end = datetime.now()

with open('all_tickers.txt', 'r') as file:
     content = file.read()
     ticker_list = [ticker.strip() for ticker in content.split(',')] 
#ticker_list = ['NVDA', 'SFL.MI', 'DIA.MI']

def get_data(ticker_list, start, end):
    print(f"Downloading data for {ticker_list} from {start} to {end}")
    raw = yf.download(tickers = ticker_list, start = start, end = end, keepna=False, group_by='ticker')
    ticker_dict = {}
    for ticker in raw.columns.levels[0]:
        ticker_data = raw[ticker].copy()
        ticker_data.index = pd.to_datetime(ticker_data.index)
        print(ticker_data.index.min(), ticker_data.index.max())
        ticker_data.index.rename("Date", inplace = True)
        ticker_data = ticker_data.interpolate(method='linear', limit_direction='both')
        ticker_data['TP'] = (ticker_data["High"] + ticker_data["Low"] + ticker_data["Close"])/3  
        ticker_dict[ticker] = ticker_data
    return ticker_dict

if st.session_state.get('ticker_dict') is None:
    st.session_state['ticker_dict'] = get_data(ticker_list, start, end)

col1, col2, col3= st.columns([1,4,1])
with col1:
    with st.form(key = "search_bar"):
        ticker_selection = st.selectbox("Seleziona lo stock", [""]+ticker_list)
        submit_button = st.form_submit_button("Calcola")

try:
    if submit_button and ticker_selection:
        with col2:
            with st.spinner(text="Calcolando..."):
                ticker_data = st.session_state['ticker_dict'].get(ticker_selection, None)
                obj = bs(ticker_data,start,end)
                sma, devup, devdown, return_ratio = obj.optimizer()
                df = obj.set_parameters(sma,devup,devdown)    

            to_plot = df.reset_index()
            base = alt.Chart(to_plot).encode(
                alt.X('Date:T', axis=alt.Axis(title="t"))
            )

            # Define lines
            line1 = base.mark_line(opacity=0.3, color='#57A44C').encode(
                alt.Y('Upper:Q')
            )
            
            line2 = base.mark_line(opacity=0.3, color='#57A44C').encode(
                alt.Y('Lower:Q')
            )
            
            line3 = base.mark_line(color='blue').encode(
                alt.Y('Close:Q',
                    axis=alt.Axis(title=f'Prezzo {ticker_selection}'),
                    scale=alt.Scale(domain=(0, df["Close"].max()*2)))
            )
            
            # Define selection
            selection = alt.selection_interval(bind='scales')
            
            # Combine lines and selection
            c = alt.layer(line1, line2, line3).add_selection(selection).interactive()
            
            # Add chart to Streamlit app
            st.altair_chart(c, use_container_width=True)

            
        with col3:
            st.write("**Segnale**")
            last = df.iloc[-1:,:]
            last_day = last.index + timedelta(days = 1)
            last_price = last["Close"][0]
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

            if (sma, devup, devdown) != (100, 2.5, 2.5):
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
                st.write(f"Parametri ottimizzati: sma = {sma} | dev_up = {round(devup,1)} | dev_down {round(devdown,1)} | return {round(return_ratio,2)}")
                st.write(f"Exp moving average ultimi 5 giorni: {list(obj.volume_check(sma))}")
except Exception as e:
    print(f"Errore durante il calcolo: {e}")
    with col2:
        st.write("**<br><br><br><p style='text-align:center'>Scegli il titolo da analizzare</p>**", unsafe_allow_html=True)


st.write("#### Verifica più stocks")
col1, col2= st.columns([1,1])

with col1:
    calcola = st.button("Calcola tutti gli stocks")

if calcola:
    with col2:
        for stock in ticker_list:
            with st.spinner(text=f"Calcolando {stock}..."):
                ticker_data = st.session_state['ticker_dict'][stock]
                obj = bs(ticker_data,start,end)
                sma, devup, devdown, return_ratio = obj.optimizer()
                df = obj.set_parameters(sma,devup,devdown)

                lasts = df.iloc[-3:,:]

                #highers = lasts['High'].values
                lowers = lasts['Low'].values
                #last_uppers = lasts["Upper"].values
                last_lowers = lasts["Lower"].values

                #higher_differences = np.subtract.outer(last_uppers, highers).flatten()
                lower_differences = np.subtract.outer(last_lowers, lowers).flatten()

                if np.any(lower_differences>=0):
                    print(lowers, last_lowers, lower_differences)
                    st.write(f"{stock} è da tenere d'occhio!")
                else:
                    continue

st.write("#### Calcolo miglior portfolio")
col1, col2= st.columns([1,1])

with col1:
    with st.form(key = "porfolio"):
        ticker_stocks_list = st.multiselect("Lista di ticker da confrontare", options=ticker_list)
        uniform_weights_bool = st.toggle("Uniform Weights")
        calcola_portfolio = st.form_submit_button("Calcola")

if calcola_portfolio:
    with col2:
        with st.spinner(text="Calcolando..."):
            tester = mc(ticker_stocks_list, st.session_state.get('ticker_dict'))
            res = tester.optimizer(equal_fundamental_weights=uniform_weights_bool)
            st.dataframe(res)



#to be adjusted
# st.write("#### Analisi dei segnali")

# with st.form(key = "signals"):
#     ticker_stock = st.text_input("cerca per ticker...", placeholder="es. AAPL")
#     L_window = st.number_input("Window Length", min_value=12)
#     ssa_components1 = st.slider(
#         'Componenti da aggregare - 1',
#         0, 10, (1, 2)
#         )
#     ssa_components2 = st.slider(
#         'Componenti da aggregare - 2',
#         0, 10, (3, 4)
#         )
    
#     calcola_SSA = st.form_submit_button("Calcola")


# if calcola_SSA:
    
#     # Add this line to ensure plots are displayed in Streamlit
#     st.set_option('deprecation.showPyplotGlobalUse', False)

#     ssa_object = SSA_actions(ticker_stock, start, end, L_window)
#     st.write(f"Lunghezza della TS: {len(ssa_object.orig_TS)-1}")

#     if ssa_object.Wcorr is None:
#         ssa_object.calc_wcorr()

#     fig, ax = plt.subplots(4,1, figsize=(8, 8))
    
#     ax[0].imshow(ssa_object.Wcorr)
#     ax[0].set_xlabel(r"$\tilde{F}_i$")
#     ax[0].set_ylabel(r"$\tilde{F}_j$")

#     ax[0].set_xlim(0-0.5, 10+0.5)
#     ax[0].set_ylim(10+0.5, 0-0.5)

#     ax[1].plot(ssa_object.orig_TS)
#     ax[1].set_title("Adj Close stock price") 

#     ax[2].plot(ssa_object.reconstruct(list(ssa_components1)), linewidth=0.5)
#     ax[2].set_title(f"Derivata dei segnali {ssa_components1}")
#     ax[2].axhline(y=0, color='black')

#     ax[3].plot(ssa_object.reconstruct(list(ssa_components2)), linewidth=0.5)
#     ax[3].set_title(f"Derivata dei segnali {ssa_components2}")
#     ax[3].axhline(y=0, color='black')

#     for i in range(4):
#         ax[i].tick_params(axis='both', labelsize=4)

#     # Display the plot in Streamlit
#     plt.tight_layout()
#     st.pyplot(fig)
