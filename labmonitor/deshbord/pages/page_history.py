import os
import streamlit as st
import pandas as pd
import plotly.express as px

st.markdown("# Histórico")
st.sidebar.markdown("# Histórico de uso.")

df = pd.read_excel(f"{os.path.dirname(os.path.abspath(__file__))}/../../../history.xlsx")


maquinas = df['Name'].unique()
maquina_selecionada = st.selectbox('Escolha a máquina', maquinas)

df_filtrado = df[df['Name'] == maquina_selecionada]

# --- Gráfico de uso de CPU ---
fig_cpu = px.line(df_filtrado, x='Timestamp', y='CPU Usage (%)', 
                  title=f'Uso de CPU para {maquina_selecionada}', 
                  labels={'Timestamp': 'Tempo', 'CPU Usage (%)': 'Uso de CPU (%)'},
                  line_shape='linear', markers=True)
fig_cpu.update_yaxes(range=[0, 100])  # Limita o eixo Y de 0 a 100%
fig_cpu.update_xaxes(
    tickformat="%H:%M:%S", 
    dtick="3600000",  # Intervalo de 1 hora
)
st.plotly_chart(fig_cpu)

# --- Gráfico de uso de RAM ---
fig_ram = px.line(df_filtrado, x='Timestamp', y='Total RAM (GB)', 
                  title=f'Uso de RAM para {maquina_selecionada}', 
                  labels={'Timestamp': 'Tempo', 'Total RAM (GB)': 'Uso de RAM (GB)'},
                  line_shape='linear', markers=True)
fig_ram.update_xaxes(
    tickformat="%H:%M:%S", 
    dtick="3600000", 
)
st.plotly_chart(fig_ram)

# --- Gráfico de uso de GPU ---
gpus = [col for col in df.columns if 'gpu' in col.lower() and "utilization" in col.lower()]

if gpus:
    fig_gpu = px.line(df_filtrado, x='Timestamp', y=gpus, 
                      title=f'Uso de GPUs para {maquina_selecionada}', 
                      labels={'Timestamp': 'Tempo', 'value': 'Uso (%)'},
                      line_shape='linear', markers=True)
    fig_gpu.update_yaxes(range=[0, 100])  # Limita o eixo Y de 0 a 100%
    fig_gpu.update_xaxes(
        tickformat="%H:%M:%S", 
        dtick="3600000", 
    )
    st.plotly_chart(fig_gpu)
else:
    st.write("Nenhuma coluna de GPU encontrada no arquivo.")



# --- Gráfico de uso de GRAM  ---
gpus = [col for col in df.columns if 'gpu' in col.lower() and "memory used" in col.lower()]

if gpus:
    fig_gpu = px.line(df_filtrado, x='Timestamp', y=gpus, 
                      title=f'Uso de VRAM para {maquina_selecionada}', 
                      labels={'Timestamp': 'Tempo', 'value': 'Uso de VRAM (GB)'},
                      line_shape='linear', markers=True)
    #fig_gpu.update_yaxes(range=[0, 100])  # Limita o eixo Y de 0 a 100%
    fig_gpu.update_xaxes(
        tickformat="%H:%M:%S", 
        dtick="3600000", 
    )
    st.plotly_chart(fig_gpu)
else:
    st.write("Nenhuma coluna de GPU encontrada no arquivo.")