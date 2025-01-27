""" Machine reservation page """

# Imports
############################################################################################################
import sys
import pandas as pd
import streamlit as st

from datetime import datetime, time
from labmonitor.connection import Connection
from labmonitor.data import Data
from labmonitor.monitor import Monitor
from labmonitor.queue import Queue


# Functions
############################################################################################################

def agendar() -> None:
    """ Schedule a new job in the queue

    Args:
    - None

    Returns:
    - None
    """

    global queue
    with st.container(border=True):
        st.subheader("New Schedule")
        maquina_selecionada = st.selectbox('Choose a machine', data.machines['name'])
        maquina = data.machines.loc[data.machines["name"] == maquina_selecionada]

        lista_espera_maquina = queue.df[queue.df['name'] == maquina_selecionada][queue.df['status'] == "Waiting"].drop(columns=['ip', 'e-mail', 'notification_last_day', 'notification_fist_day'])
        if lista_espera_maquina.size > 0:
            with st.expander(f"Waiting list for {maquina_selecionada}"):
                st.dataframe(lista_espera_maquina,  hide_index=True, use_container_width=True)

        n_cpu = st.number_input("Number of CPUs", min_value=1, step=1)
        try:
            con = Connection(ip=maquina['ip'].iloc[0], username=maquina['username'].iloc[0], password=maquina['password'].iloc[0])
            mon = Monitor(con)
            gpu = st.selectbox('Select a GPU', ["-1 - Null"]+[f"{gpu['gpu_index']} - {gpu['name']}" for gpu in mon.get_usage_gpu()['gpu_info']])
            gpu_index, gpu_name = gpu.split(" - ")
        
        except Exception as e:
            gpu = st.selectbox('Selecione a GPU', ["-1 - Null"])
            gpu_index, gpu_name = gpu.split(" - ")
            st.error(f"Erro ao obeter informações de GPU. Provavelmente {maquina_selecionada} não tem GPU, está offline ou com falha.")

        min_data = pd.to_datetime(queue.df.loc[(queue.df['name'] == maquina_selecionada) & (queue.df['gpu_name'] == gpu_name.strip()) & (queue.df['gpu_index'] == int(gpu_index)), 'end'].max())
        if str(min_data) == "NaT": min_data = datetime.now()

        start = st.date_input("Start (Date)", min_value=min_data)
        #start_hora = st.time_input("Início (Hora)", value=datetime.now().time())
        end = st.date_input("End (Date)", value=min_data, min_value=min_data)
        #end_hora = st.time_input("end (Hora)", value=datetime.now().time())

        username = st.text_input("Username")
        email = st.text_input("E-mail")

        submitted = st.button("Agendar")
        if submitted:
            if not username or not n_cpu or not email:
                st.error("Por favor, preencha todos os campos.")
            elif min_data >= pd.to_datetime(start) and min_data >= pd.to_datetime(end):
                st.error("Por favor, indique uma data livre para o recurso desejado (GPU ou CPU).")
            else:
                try:
                    start_datetime = datetime.combine(start, datetime.now().time())
                    end_datetime = datetime.combine(end, time(23, 59, 0, 0))
                    queue.insert(
                        ip=maquina['ip'].iloc[0],
                        name=maquina['name'].iloc[0],
                        username=username,
                        start=start_datetime,
                        end=end_datetime,
                        n_cpu=n_cpu,
                        gpu_index=gpu_index,
                        gpu_name=gpu_name,
                        email=email, 
                        to_send=False
                    )
                    st.success(f"Agendamento feito com Sucesso '{username}' criado com sucesso.")
                    monitor_now()
                except Exception as e:
                    st.error(f"Erro ao agendar: {e}")
                    
def remover_agendamento() -> None:
    """ Remove a job from the queue

    Args:
    - None

    Returns:
    - None
    """

    global queue
    with st.container(border=True):
        st.subheader("Remove Schedule")
        try:
            agendamentos = queue.df[queue.df['status'] != 'Finished'].apply(
                                        lambda row: f"{row['name']} - {row['username']} - {row['start']} - {row['end']} - {row['n_cpu']} - {row['gpu_name']}",
                                        axis=1).tolist()
        except Exception as e:
            agendamentos = []

        agendamento = st.selectbox('Select user', agendamentos)
        
        email = st.text_input("E-mail")
        remove = st.button("Remove")

        if remove:
            nome_maquina, usuario, start, end, n_cpu, gpu_name = agendamento.split(' - ')

            index_remove = queue.df[(queue.df['name'] == nome_maquina) & (queue.df['username'] == usuario) & (queue.df['start'] == start) & (queue.df['end'] == end)].index[0]
            if not email:
                st.error("Por favor, preencha todos os campos.")
            elif email == queue.df.iloc[index_remove]['e-mail']:
                try:
                    queue.remove(index=index_remove)
                    st.success(f"Agendamento excluído com Sucesso.")
                except Exception as e:
                    st.error(f"Erro ao agendar: {e}")
            elif email != queue.df.iloc[index_remove]['e-mail']:
                st.error(f"E-mail não corresponde ao do agendamento.")

def lista_espera() -> None:
    """ List the machines in the queue

    Args:
    - None

    Returns:
    - None
    """

    global queue
    with st.container(border=True):
        st.subheader("Waiting list")
        maquinas_espera = queue.df[queue.df['status'] == "Waiting"]['name'].unique()
        print(maquinas_espera)
        for m in maquinas_espera:
            with st.expander(m):
                st.dataframe(queue.df[queue.df['name'] == m][queue.df['status'] == "Waiting"].drop(columns=['ip', 'e-mail', 'notification_last_day', 'notification_fist_day']),  hide_index=True, use_container_width=True)


# Main
############################################################################################################

st.markdown(
    """
    <div style="text-align: center;">
        <h1>Machine Scheduling</h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.sidebar.markdown("# Description")
st.sidebar.markdown("This section enables the logistical management of machines, allowing users to schedule and check their availability.")
st.sidebar.markdown("Information displayed here is captured and stored in \"queue.csv\" file.")
st.sidebar.markdown("If \"email.json\" is configured, you will receive emails with reminders, including the arrival of the scheduled time and the end of the scheduled time.")

data = Data(); data.read_machines(path=f"{sys.argv[1]}/machines.csv")
queue = Queue(data=data)

try:
    queue.update_status()
except:
    st.warning("Failed to update schedule status.")
    pass

def monitor_now() -> None:
    """ Monitor the queue now

    Args:
    - None
    
    Returns:
    - None
    """

    try:            
        queue.monitor(now=True)
    except Exception as e:
        st.warning(f"{e}")


st.subheader("Schedules")
st.dataframe(queue.df[queue.df['status'] == "Executando"].drop(columns=['ip', 'e-mail', 'notification_last_day', 'notification_fist_day']), use_container_width=True, hide_index=True)

def nenhum() -> None:
    """ Do nothing

    Args:
    - None

    Returns:
    - None
    """
    
    pass

action = st.selectbox("Select an action", ["Select", "Schedule", "Remove Schedule", "Waiting List"])
fun = {"Select": nenhum, "Schedule": agendar, "Remove Schedule": remover_agendamento, "Waiting List": lista_espera}

if "action_state" not in st.session_state: 
    st.session_state.action_state = action

try:
    fun[action]()
except Exception as e:
    st.error(f"Erro ao selecionar ação: {e}")

