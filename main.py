from datetime import timedelta, datetime
from bollinger import BollingerStrategy as bs
import streamlit as st
import altair as alt

st.set_page_config(page_title="Silver&Ale - Investments",
                   page_icon=":globe_with_meridians:",
                   layout="wide")

st.title("🚀 Silver & Ale - Grandi investimenti 🚀 📈")

start = datetime.now()-timedelta(days=400)
end = datetime.now()



ticker_diz = {"Stellantis": "STLA.MI",
              "Safilo": "SFL.MI",
              "Saipem": "SPM.MI",
              "Prysmian": "PRY.MI",
              "Ferrari": "RACE.MI",
              "Industrie De Nora": "DNR.MI",
              "WeBuild": "WBD.MI",
              "Alerion": "ARN.MI",
              "Nvidia": "NVDA",
              "Tesla": "TSLA"}

col1, col2, col3, col4 = st.columns([1,4,1,1])
with col1:
    with st.form(key = "search_bar"):
        sel1 = st.selectbox("Seleziona lo stock", ticker_diz.keys())
        sel2 = st.text_input("oppure cerca un altro ticker...")
        st.form_submit_button("Calcola")

try:
    with col2:
        if sel2:
            selection = sel2
        else:
            selection = ticker_diz[sel1]
        with st.spinner(text="Calcolando..."):
            obj = bs(selection,start,end)
            sma, devup, devdown = obj.optimizer()
            df = obj.set_parameters(sma,devup,devdown)    

        to_plot = df.reset_index()
        base = alt.Chart(to_plot).encode(
        alt.X('Date:T', axis=alt.Axis(title="t"),
                        scale=alt.Scale(domain=(to_plot["Date"].min()-timedelta(days=1), to_plot["Date"].max()+timedelta(days=6))))
        )

        line1 = base.mark_line(opacity=0.3, color='#57A44C').encode(
            alt.Y('Upper:Q')
        )

        line2 = base.mark_line(opacity=0.3, color='#57A44C').encode(
        alt.Y('Lower:Q')
        )

        line3 = base.mark_line(color='blue').encode(
        alt.Y('Adj Close:Q',
            axis=alt.Axis(title='Prezzo'),
            scale=alt.Scale(domain=(0, df["Adj Close"].max()*2)))
        )

        c = alt.layer(line1, line2, line3).interactive()
        

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

        if (sma, devup, devdown) != (20, 2.0, 2.0):
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
    st.experimental_rerun()
