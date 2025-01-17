""" History of the machines monitored by the system. """

# Imports
############################################################################################################
import os
import pandas as pd
import streamlit as st
import plotly.express as px

# Main
############################################################################################################

st.markdown("# History")
st.sidebar.markdown("# History of use.")

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