import sys
import streamlit as st
from datetime import datetime, time
from labmonitor.connection import Connection
from labmonitor.data import Data
from labmonitor.monitor import Monitor
from labmonitor.queue import Queue


def agendar():
    with st.form("entry_form", clear_on_submit=True):
        st.subheader("Adicionar Novo Registro")
        maquina_selecionada = st.selectbox('Escolha a máquina', data.machines['name'])
        maquina = data.machines.loc[data.machines["name"] == maquina_selecionada]

        inicio = st.date_input("Início (Data)", value=datetime.now().date())
        #inicio_hora = st.time_input("Início (Hora)", value=datetime.now().time())
        fim = st.date_input("Fim (Data)", value=datetime.now().date())
        #fim_hora = st.time_input("Fim (Hora)", value=datetime.now().time())
        n_cpu = st.number_input("Número de CPUs", min_value=1, step=1)
        
        con = Connection(ip=maquina['ip'].iloc[0], username=maquina['username'].iloc[0], password=maquina['password'].iloc[0])
        mon = Monitor(con)
        gpu = st.selectbox('Selecione a GPU', ["-1 - Null"]+[f"{gpu['gpu_index']} - {gpu['name']}" for gpu in mon.get_usage_gpu()['gpu_info']])
        gpu_index, gpu_name = gpu.split(" - ")

        username = st.text_input("Username")
        email = st.text_input("E-mail")

        submitted = st.form_submit_button("Agendar")
        if submitted:
            if not username or not n_cpu:
                st.error("Por favor, preencha todos os campos.")
            else:
                try:
                    inicio_datetime = str(datetime.combine(inicio, datetime.now().time()))
                    fim_datetime = str(datetime.combine(fim, time(23, 59, 0, 0)))
                    queue.insert(
                        ip=maquina['ip'].iloc[0],
                        name=maquina['name'].iloc[0],
                        username=username,
                        inicio=inicio_datetime,
                        fim=fim_datetime,
                        n_cpu=n_cpu,
                        gpu_index=gpu_index,
                        gpu_name=gpu_name,
                        email=email
                    )
                    st.success(f"Agendamento feito com Sucesso '{username}' criado com sucesso.")

                except Exception as e:
                    st.error(f"Erro ao agendar: {e}")
                    
st.markdown("# Agendamento de Máquinas")
st.sidebar.markdown("# Agendamento de Máquinas")

data = Data(); data.read_machines(path=f"{sys.argv[1]}/machines.xlsx")
queue = Queue(data=data)

# Exibir a tabela
st.subheader("Agendamentos")
st.write(queue.df, use_container_width=True, hide_index=True)

action = st.selectbox("Escolha uma ação", ["Selecione", "Agendar", "Remover Agendamento"])
fun = {"Selecione": print, "Agendar": agendar, "Remover Agendamento": print}

if "action_state" not in st.session_state: 
    st.session_state.action_state = action

try:
    fun[action]()
except Exception as e:
    st.error(f"Erro ao selecionar ação: {e}")


