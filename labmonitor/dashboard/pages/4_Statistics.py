""" Statistics page of the dashboard. """

# Imports
############################################################################################################

import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Main

st.markdown(
    """
    <div style="text-align: center;">
        <h1>History and Statistics</h1>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("## History")

df = pd.read_csv(f"{os.path.dirname(os.path.abspath(__file__))}/../../../history.csv")


maquinas = df['Name'].unique()
maquina_selecionada = st.selectbox('Choose a machine', maquinas)

df_filtrado = df[df['Name'] == maquina_selecionada].dropna(axis=1, how='all')

csv = df_filtrado.to_csv().encode("utf-8")
st.download_button(
    label=f"Download {maquina_selecionada} in CSV",
    data=csv,
    file_name=f"data_{maquina_selecionada}.csv",
    mime="text/csv", use_container_width=True
)
# --- Gráfico de uso de CPU ---
fig_cpu = px.line(df_filtrado, x='Timestamp', y='CPU Usage (%)', 
                  title=f'CPU usage for {maquina_selecionada}', 
                  labels={'Timestamp': 'Time', 'CPU Usage (%)': 'CPU usage (%)'},
                  line_shape='linear', markers=True)
fig_cpu.update_yaxes(range=[0, 100]) 

st.plotly_chart(fig_cpu)

# --- Gráfico de uso de RAM ---
fig_ram = px.line(df_filtrado, x='Timestamp', y='RAM Used (GB)', 
                  title=f'Use of RAM for {maquina_selecionada}', 
                  labels={'Timestamp': 'Time', 'RAM Used (GB)': 'RAM Used (GB)'},
                  line_shape='linear', markers=True)
fig_ram.update_yaxes(range=[0, df_filtrado['Total RAM (GB)'].iloc[-1]]) 
st.plotly_chart(fig_ram)

# --- Gráfico de uso de GPU ---
gpus = [col for col in df_filtrado.columns if 'gpu' in col.lower() and "utilization" in col.lower()]
gpu_labels = {
    f"GPU_{i}_Utilization (%)": f"{df_filtrado[f'GPU_{i}_Name'].iloc[-1]} (GPU {i})" 
    for i in range(len(gpus))
}

if gpus:
    fig_gpu = px.line(df_filtrado, x='Timestamp', y=gpus, 
                      title=f'Use of GPUs for {maquina_selecionada}', 
                      labels={'Timestamp': 'Time', 'value': 'Usage (%)'},
                      line_shape='linear', markers=True)
    fig_gpu.update_yaxes(range=[0, 100])

    fig_gpu.for_each_trace(lambda trace: trace.update(name=gpu_labels[trace.name]))
    st.plotly_chart(fig_gpu)
else:
    st.write("No GPU column found in the file.")



# --- Gráfico de uso de VRAM  ---
gpus = [col for col in df_filtrado.columns if 'gpu' in col.lower() and "memory used" in col.lower()]

gpu_labels_vram = {
    f"GPU_{i}_Memory Used (GB)": f"{df_filtrado[f'GPU_{i}_Name'].iloc[-1]} (GPU {i})" 
    for i in range(len(gpus))
}

if gpus:
    fig_gpu_vram = px.line(df_filtrado, x='Timestamp', y=gpus, 
                      title=f'Use of VRAM for {maquina_selecionada}', 
                      labels={'Timestamp': 'Time', 'value': 'VRAM usage (GB)'},
                      line_shape='linear', markers=True)
    #fig_gpu.update_yaxes(range=[0, 100])  # Limita o eixo Y de 0 a 100%

    fig_gpu_vram.for_each_trace(lambda trace: trace.update(name=gpu_labels_vram[trace.name]))
    st.plotly_chart(fig_gpu_vram)
else:
    st.write("No GPU column found in the file.")

st.markdown("## Usage Statistics.")
st.sidebar.markdown("# Description")
st.sidebar.markdown("This section allows monitoring the history and generating statistics for both CPU and GPU usage of the machines.")

try:
    df = pd.read_csv(f"{os.path.dirname(os.path.abspath(__file__))}/../../../history.csv")
except Exception as e:
    st.error(f"It was not possible to load the machines' usage history information. {e}")

def cpu_use() -> None:
    """ Show the CPU usage of the machines

    Args:
    - None

    Returns:
    - None
    """

    st.subheader("CPU usage (H) per machine")
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

    st.subheader("GPU usage (H)")
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

st.markdown(
    """
    <div style="text-align: center;">
        <h1 style="font-size: 14px;">The data displayed in this section is updated hourly.</h1>
    </div>
    """,
    unsafe_allow_html=True
)