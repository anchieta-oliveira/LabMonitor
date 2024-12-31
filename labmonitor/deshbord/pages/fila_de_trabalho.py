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
        path_origin = st.text_input("Diretorio com arquivos de trabalho (máquina de origem)")
        script_name = st.text_input("Nome do script")
        job_name = st.text_input("Nome do trabalho")
        username = st.text_input("Username")
        email = st.text_input("e-mail")
        
        submitted = st.button("Submeter")

        if submitted:
            if not username or not n_cpu or not email or not path_origin or not script_name or not machine_origin:
                st.error("Por favor, preencha todos os campos.")
            else:
                try:
                    queue.submit(username=username,
                                job_name=job_name,
                                machine_origin=machine_origin,
                                script_name=script_name,
                                path_origin=path_origin,
                                n_cpu=n_cpu,
                                email=email,
                                gpus=selected_gpus
                                )

                    st.success(f"Trabalho submetido com sucesso '{username}'")
                    queue.update_status_machines()
                except Exception as e:
                    st.error(f"Erro ao submeter: {e}")


def remove_job():
    pass




# Exc 
st.sidebar.markdown("# Fila de trabalhos")

data = Data(); data.read_machines(path=f"{sys.argv[1]}/machines_job.xlsx")
queue = QueueJob(data=data)

st.subheader("Fila de trabalhos")
st.dataframe(queue.df[queue.df['status'] != 'finalizado'][['name', 'username', 'job_name','status', 'submit', 'n_cpu', 'gpu_name']], use_container_width=True, hide_index=True)


def nenhum():
    pass

action = st.selectbox("Escolha uma ação", ["Selecione", "Submeter Trabalho", "Remover trabalho"])
fun = {"Selecione": nenhum, "Submeter Trabalho": submit_job, "Remover trabalho": remove_job}

if "action_state" not in st.session_state: 
    st.session_state.action_state = action

try:
    fun[action]()
except Exception as e:
    st.error(f"Erro ao selecionar ação: {e}")