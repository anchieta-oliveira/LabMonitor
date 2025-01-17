""" Work queue page """

# Imports
############################################################################################################
import os
import sys
import pandas as pd
import streamlit as st

from labmonitor.data import Data
from labmonitor.queue import Queue
from datetime import datetime, time
from labmonitor.connection import Connection
from labmonitor.queue_job import QueueJob


# Functions
############################################################################################################

def submit_job() -> None:
    """ Submit a job to the queue 
    
    Args:
    - None
    
    Returns:
    - None
    """

    global queue
    with st.container(border=True):
        st.subheader("Submit job")
        
        data_g = Data(); data_g.read_machines(path=f"{sys.argv[1]}/machines.csv")

        with st.expander(f"Machines receiving jobs"):
            st.dataframe(queue.data.machines[['name', 'allowed_cpu', 'name_allowed_gpu']],  hide_index=True, use_container_width=True)
        

        n_cpu = st.number_input("Number of CPUs", min_value=1, step=1)

        gpus = ["all"]
        selected_gpus = []
        for i in queue.data.machines['name_allowed_gpu']:
            gpus.extend(i.split(","))

        selected_gpus = st.multiselect("Select the required GPUs", list(set(gpus)))
                
        machine_origin = st.selectbox('Source machine', data_g.machines['name'])
        path_origin = st.text_input("Directory with working files (source machine)")
        script_name = st.text_input("Script name (.sh)")
        job_name = st.text_input("Job name")
        username = st.text_input("Username")
        email = st.text_input("e-mail")
        
        submitted = st.button("Submit")

        if submitted:
            if not username or not n_cpu or not email or not path_origin or not script_name or not machine_origin:
                st.error("Please fill in all the fields.")
            else:
                try:
                    queue.read_csv()
                    queue.submit(username=username,
                                job_name=job_name,
                                machine_origin=machine_origin,
                                script_name=script_name,
                                path_origin=path_origin,
                                n_cpu=n_cpu,
                                email=email,
                                gpus=selected_gpus
                                )

                    st.success(f"Job submitted successfully '{username}'")

                except Exception as e:
                    st.error(f"Error submitting: {e}")


def remove_job() -> None:
    """ Remove a job from the queue

    Args:
    - None

    Returns:
    - None
    """

    pass

def acompanhar() -> None:
    """ Track a job in the queue

    Args:
    - None

    Returns:
    - None
    """

    global queue
    with st.container(border=True):
        st.subheader("Monitoring job")
        
        try:
            trabalhos = queue.df[queue.df['status'] == 'running'].apply(
                                        lambda row: f"{row['name']} -  {row['username']} - {row['job_name']} - {row['submit']}",
                                        axis=1).tolist()
        except Exception as e:
            trabalhos = []
        
        trabalho = st.selectbox('Choose the job', trabalhos)

        email = st.text_input("E-mail")
        sufix = st.text_input("File suffix", value=".log")
        ver = st.button("View")

        if ver:
            nome_maquina, usuario, job_name, submit = trabalho.split(' - ')

            row_job = queue.df[(queue.df['name'] == nome_maquina.strip()) & (queue.df['username'] == usuario.strip()) & (queue.df['job_name'] == job_name.strip()) & (queue.df['submit'] == submit.strip())].iloc[0]
            if not email:
                st.error("Please fill in all the fields.")
            elif email.strip() == row_job['e-mail']:
                logs = queue.view_job_log(job_row=row_job, sufix="*"+sufix)
                try:
                    for log in logs.keys():
                        with st.expander(log):
                            st.markdown(
                                    f"<p style='font-size:16px;'>{logs[log].replace("\n", "<br>")}</p>",
                                    unsafe_allow_html=True
                                )
                except Exception as e:
                    st.error(f"Error viewing job output: {e}")
            
            elif email.strip() != row_job['e-mail']:
                st.error("The indicated email does not match the registered one!")

def script_exemple() -> None:
    """ Show the example of a script

    Args:
    - None

    Returns:
    - None
    """

    with st.container():
        st.subheader("Example Script")
        path = "./labmonitor/example/script/"
        
        if os.path.exists(path):
            for file in os.listdir(path):
                with st.expander(file):
                    with open(os.path.join(path, file), 'r') as f:
                        file_content = f.read()
                        st.text(file_content)
                        st.download_button(
                            label="Download",
                            data=file_content,
                            file_name=file,
                            mime='text/plain'
                        )

def instru() -> None:
    """ Show the instructions

    Args:
    - None

    Returns:
    - None
    """

    txt = """
    1 - Verifique os programas disponíveis e como chamá-los nos scripts de uso.
    2 - Sempre o index da GPU será "0", designe este para aplicação, caso necessário.
    3 - Verifique a funcionalidade dos script (.sh). Caso ele falhe, a fila continuará normalmente, você terá que alocar novamente a fila.
    4 - Ao finalizar o trabalho (com sucesso ou falha) os arquivos serão copiados automaticamente para a máquina de origem, no mesmo diretório. Não altere o local do diretório na máquina de origem até o trabalho ser finalizado. Garanta que tenha espaço para receber os resultados. 
    5 - Você será notificado por e-mail ao finalizar o trabalho (com sucesso ou falha).
    6 - Caso seu trabalho falhe, verifique os resultados, corrija e submeta novamente à fila.
    7 - Não é possível direcionar especificamente a máquina que receberá o trabalho, mas pode-se selecionar o recurso, por exemplo, uma ou mais GPUs específicas.
    8- Sempre coloque o mesmo nome de usuário.
    """

    with st.expander(f"Instruções de uso"):
        st.text(txt)


# Main
############################################################################################################

st.sidebar.markdown("# Job Queue")

data = Data(); data.read_machines(path=f"{sys.argv[1]}/machines_job.csv")
queue = QueueJob(data=data)

st.subheader("Job Queue")
st.dataframe(queue.df[queue.df['status'] != 'finished'][['name', 'username', 'job_name','status', 'submit', 'n_cpu', 'gpu_requested', 'gpu_name']], use_container_width=True, hide_index=True)

def nenhum() -> None:
    """ Do nothing 
    
    Args:
    - None
    
    Returns:
    - None
    """
    
    pass

action = st.selectbox("Action", ["Select", "Submit Job", "Remove job", "Monitoring job", "Script examples"])
fun = {"Select": nenhum, "Submit Job": submit_job, "Remove job": remove_job, "Monitoring job": acompanhar, "Script examples": script_exemple}

if "action_state" not in st.session_state: 
    st.session_state.action_state = action

try:
    fun[action]()
except Exception as e:
    st.error(f"Erro ao selecionar ação: {e}")

instru()
