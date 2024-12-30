import sys
import pandas as pd
import streamlit as st
from labmonitor.data import Data
from labmonitor.queue import Queue
from datetime import datetime, time
from labmonitor.connection import Connection
from labmonitor.queue_job import QueueJob

# Funções 
def submit_job():
    global queue
    with st.container(border=True):
        st.subheader("Submeter trabalho")
        queue.update_status_machines()
        data_g = Data(); data_g.read_machines(path=f"{sys.argv[1]}/machines.xlsx")

        with st.expander(f"Máquinas recebendo trabalhos"):
            st.dataframe(queue.data.machines[['name', 'allowed_cpu', 'name_allowed_gpu']],  hide_index=True, use_container_width=True)
        

        n_cpu = st.number_input("Número de CPUs", min_value=1, step=1)

        gpus = ["all"]
        selected_gpus = []
        for i in queue.data.machines['name_allowed_gpu']:
            gpus.extend(i.split(","))

        for g in gpus:
            if st.checkbox(g.strip()):
                selected_gpus.append(g)

                
        machine_origin = st.selectbox('Máquina de origem', data_g.machines['name'])
        path_origin = st.text_input("Diretorio com arquivos de trabalho")
        script_name = st.text_input("Nome do script")
        username = st.text_input("Username")
        email = st.text_input("e-mail")
        

        queue.submit(username=username,
                     machine_origin=machine_origin,
                     script_name=script_name,
                     path_origin=path_origin,
                     n_cpu=n_cpu,
                     email=email,
                     gpus=selected_gpus
                     )
        


def remove_job():
    pass




# Exc 
st.markdown("# Agendamento de Máquinas")
st.sidebar.markdown("# Agendamento de Máquinas")

data = Data(); data.read_machines(path=f"{sys.argv[1]}/machines_job.xlsx")
queue = QueueJob(data=data)

st.subheader("Agendamentos")
st.dataframe(queue.df[['name', 'username', 'submit', 'n_cpu', 'gpu_name']], use_container_width=True, hide_index=True)


action = st.selectbox("Escolha uma ação", ["Selecione", "Submeter Trabalho", "Remover trabalho"])
fun = {"Selecione": print, "Submeter Trabalho": submit_job, "Remover trabalho": remove_job}

if "action_state" not in st.session_state: 
    st.session_state.action_state = action

try:
    fun[action]()
except Exception as e:
    st.error(f"Erro ao selecionar ação: {e}")