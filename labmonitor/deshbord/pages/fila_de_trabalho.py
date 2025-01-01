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

def acompanhar():
    global queue
    with st.container(border=True):
        st.subheader("Acompanhar trabalho")
        
        try:
            trabalhos = queue.df[queue.df['status'] == 'executando'].apply(
                                        lambda row: f"{row['name']} -  {row['username']} - {row['job_name']} - {row['submit']}",
                                        axis=1).tolist()
        except Exception as e:
            trabalhos = []
        
        trabalho = st.selectbox('Escolha o trabalho', trabalhos)

        email = st.text_input("E-mail")
        sufix = st.text_input("Sufixo dos arquivos", value=".log")
        ver = st.button("Ver")

        if ver:
            nome_maquina, usuario, job_name, submit = trabalho.split(' - ')

            row_job = queue.df[(queue.df['name'] == nome_maquina.strip()) & (queue.df['username'] == usuario.strip()) & (queue.df['job_name'] == job_name.strip()) & (queue.df['submit'] == submit.strip())].iloc[0]
            if not email:
                st.error("Por favor, preencha todos os campos.")
            elif email.strip() == row_job['e-mail']:
                logs = queue.view_job_log(job_row=row_job, sufix="*"+sufix)
                try:
                    for log in logs.keys():
                        with st.expander(log):
                            st.text(logs[log])

                except Exception as e:
                    st.error(f"Erro ao ver saída de trabalhos: {e}")



# Exc 
st.sidebar.markdown("# Fila de trabalhos")

data = Data(); data.read_machines(path=f"{sys.argv[1]}/machines_job.xlsx")
queue = QueueJob(data=data)

st.subheader("Fila de trabalhos")
st.dataframe(queue.df[queue.df['status'] != 'finalizado'][['name', 'username', 'job_name','status', 'submit', 'n_cpu', 'gpu_requested', 'gpu_name']], use_container_width=True, hide_index=True)


def nenhum():
    pass

action = st.selectbox("Escolha uma ação", ["Selecione", "Submeter Trabalho", "Remover trabalho", "Acompanhar trabalho"])
fun = {"Selecione": nenhum, "Submeter Trabalho": submit_job, "Remover trabalho": remove_job, "Acompanhar trabalho": acompanhar}

if "action_state" not in st.session_state: 
    st.session_state.action_state = action

try:
    fun[action]()
except Exception as e:
    st.error(f"Erro ao selecionar ação: {e}")