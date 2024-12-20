import os
import pandas as pd
import streamlit as st
import plotly.express as px

st.markdown("# Histórico")
st.sidebar.markdown("# Histórico de uso.")

df = pd.read_excel(f"{os.path.dirname(os.path.abspath(__file__))}/../../../history.xlsx")


maquinas = df['Name'].unique()
maquina_selecionada = st.selectbox('Escolha a máquina', maquinas)

df_filtrado = df[df['Name'] == maquina_selecionada]

csv = df_filtrado.to_csv().encode("utf-8")
st.download_button(
    label=f"Download dados da {maquina_selecionada} em CSV",
    data=csv,
    file_name=f"data_{maquina_selecionada}.csv",
    mime="text/csv", use_container_width=True
)
# --- Gráfico de uso de CPU ---
fig_cpu = px.line(df_filtrado, x='Timestamp', y='CPU Usage (%)', 
                  title=f'Uso de CPU para {maquina_selecionada}', 
                  labels={'Timestamp': 'Tempo', 'CPU Usage (%)': 'Uso de CPU (%)'},
                  line_shape='linear', markers=True)
fig_cpu.update_yaxes(range=[0, 100]) 

st.plotly_chart(fig_cpu)

# --- Gráfico de uso de RAM ---
fig_ram = px.line(df_filtrado, x='Timestamp', y='RAM Used (GB)', 
                  title=f'Uso de RAM para {maquina_selecionada}', 
                  labels={'Timestamp': 'Tempo', 'RAM Used (GB)': 'Uso de RAM (GB)'},
                  line_shape='linear', markers=True)
fig_ram.update_yaxes(range=[0, df_filtrado['Total RAM (GB)'].iloc[-1]]) 
st.plotly_chart(fig_ram)

# --- Gráfico de uso de GPU ---
gpus = [col for col in df.columns if 'gpu' in col.lower() and "utilization" in col.lower()]
gpu_labels = {
    f"GPU_{i}_Utilization (%)": f"{df_filtrado[f'GPU_{i}_Name'].iloc[-1]} (GPU {i})" 
    for i in range(len(gpus))
}

if gpus:
    fig_gpu = px.line(df_filtrado, x='Timestamp', y=gpus, 
                      title=f'Uso de GPUs para {maquina_selecionada}', 
                      labels={'Timestamp': 'Tempo', 'value': 'Uso (%)'},
                      line_shape='linear', markers=True)
    fig_gpu.update_yaxes(range=[0, 100])

    fig_gpu.for_each_trace(lambda trace: trace.update(name=gpu_labels[trace.name]))
    st.plotly_chart(fig_gpu)
else:
    st.write("Nenhuma coluna de GPU encontrada no arquivo.")



# --- Gráfico de uso de VRAM  ---
gpus = [col for col in df.columns if 'gpu' in col.lower() and "memory used" in col.lower()]

gpu_labels_vram = {
    f"GPU_{i}_Memory Used (GB)": f"{df_filtrado[f'GPU_{i}_Name'].iloc[-1]} (GPU {i})" 
    for i in range(len(gpus))
}

if gpus:
    fig_gpu_vram = px.line(df_filtrado, x='Timestamp', y=gpus, 
                      title=f'Uso de VRAM para {maquina_selecionada}', 
                      labels={'Timestamp': 'Tempo', 'value': 'Uso de VRAM (GB)'},
                      line_shape='linear', markers=True)
    #fig_gpu.update_yaxes(range=[0, 100])  # Limita o eixo Y de 0 a 100%

    fig_gpu_vram.for_each_trace(lambda trace: trace.update(name=gpu_labels_vram[trace.name]))
    st.plotly_chart(fig_gpu_vram)
else:
    st.write("Nenhuma coluna de GPU encontrada no arquivo.")