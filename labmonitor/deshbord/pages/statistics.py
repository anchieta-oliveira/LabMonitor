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


def gpu_use():
    st.subheader("Uso de GPU (H)")
    maquinas = df['Name'].unique()
    df_maquinas_gpu = [{m: (df[df['Name'] == m].loc[:, df.columns.str.contains(r"gpu.*utilization|gpu_.*_name", case=False, regex=True)].dropna(axis=1, how='all'))} for m in maquinas]
    r = []
    for df_gpu in df_maquinas_gpu:
        maq = [*df_gpu][0]
        df_maq = df_gpu[maq]
        for i, (col_uti, col_name) in enumerate(zip(df_maq.loc[:,df_maq.columns.str.contains(r"gpu.*utilization", case=False, regex=True)], df_maq.loc[:,df_maq.columns.str.contains(r"gpu_.*_name", case=False, regex=True)])):
            r.append({"Máquina": maq, "GPU Usage (H)": (df_maq[col_uti]/100).sum(), "GPU Name": df_maq[col_name].iloc[-1]+ str(i*" ")})
    df_gpu_usage = pd.DataFrame(r)
    fig_gpu_use = px.sunburst(df_gpu_usage, names="Máquina", path=['Máquina', 'GPU Name'], values='GPU Usage (H)')
    st.plotly_chart(fig_gpu_use)

cpu_use()
gpu_use()

