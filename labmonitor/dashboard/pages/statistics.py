""" Statistics page of the dashboard. """

# Imports
############################################################################################################

import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Main

st.markdown("# Estatística de uso das máquinas.")
st.sidebar.markdown("# Estatística de uso das máquinas.")

try:
    df = pd.read_csv(f"{os.path.dirname(os.path.abspath(__file__))}/../../../history.csv")
except Exception as e:
    st.error(f"Não foi possível carregar as informações de histórico de uso das máquinas. {e}")

def cpu_use() -> None:
    """ Show the CPU usage of the machines

    Args:
    - None

    Returns:
    - None
    """

    st.subheader("Uso de CPU (H) por máquina")
    maquinas = df['Name'].unique()
    cpu_time = [((df[df['Name'] == m]['CPU Usage (%)']/100)).sum() for m in maquinas]
    df_cpu_use = pd.DataFrame({"Name": maquinas, "CPU Usage (H)": cpu_time})

    fig_cpu_use = px.treemap(data_frame=df_cpu_use, values="CPU Usage (H)", path=[px.Constant("All"), "Name"])

    fig_cpu_use.update_traces(marker=dict(cornerradius=5), root_color="lightgray", )
    fig_cpu_use.update_layout(margin = dict(t=0, l=0, r=0, b=0))
    st.plotly_chart(fig_cpu_use)
    with st.expander(f"Tabela."):
        st.dataframe(df_cpu_use.sort_values("CPU Usage (H)", ascending=False), use_container_width=True, hide_index=True)

def gpu_use() -> None:
    """ Show the GPU usage of the machines

    Args:
    - None

    Returns:
    - None
    """

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
    fig_gpu_use = px.treemap(df_gpu_usage, names="Máquina", path=[px.Constant("All"), 'Máquina', 'GPU Name'], values='GPU Usage (H)')
    fig_gpu_use.update_traces(marker=dict(cornerradius=5), root_color="lightgray", )
    fig_gpu_use.update_layout(margin = dict(t=0, l=0, r=0, b=0))
    st.plotly_chart(fig_gpu_use)
    with st.expander(f"Tabela."):
        st.dataframe(df_gpu_usage.sort_values("GPU Usage (H)", ascending=False), use_container_width=True, hide_index=True)

cpu_use()
gpu_use()
