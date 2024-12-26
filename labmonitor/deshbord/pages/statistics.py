import os
import pandas as pd
import streamlit as st
import plotly.express as px

import plotly.graph_objects as go

st.markdown("# Estatística de uso das máquinas.")
st.sidebar.markdown("# Estatística de uso das máquinas.")

try:
    df = pd.read_excel(f"{os.path.dirname(os.path.abspath(__file__))}/../../../history.xlsx")
except Exception as e:
    st.error(f"Não foi possível carregar as informações de histórico de uso das máquinas. {e}")

def cpu_use():
    st.subheader("Uso de CPU (H) por máquina")
    maquinas = df['Name'].unique()
    cpu_time = [((df[df['Name'] == m]['CPU Usage (%)']/100)).sum() for m in maquinas]
    df_cpu_use = pd.DataFrame({"Name": maquinas, "CPU Usage (H)": cpu_time})

    fig_cpu_use = px.treemap(data_frame=df_cpu_use, values="CPU Usage (H)", path=[px.Constant("All"), "Name"], )

    fig_cpu_use.update_traces(marker=dict(cornerradius=5), root_color="lightgray")
    st.plotly_chart(fig_cpu_use)


cpu_use()

