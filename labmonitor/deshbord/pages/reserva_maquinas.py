import sys
import pandas as pd
import streamlit as st
from datetime import datetime, time
from labmonitor.connection import Connection
from labmonitor.data import Data
from labmonitor.monitor import Monitor
from labmonitor.queue import Queue


def agendar():
    global queue
    with st.container(border=True):
        st.subheader("Novo Agendamento")
        maquina_selecionada = st.selectbox('Escolha a máquina', data.machines['name'])
        maquina = data.machines.loc[data.machines["name"] == maquina_selecionada]

        lista_espera_maquina = queue.df[queue.df['name'] == maquina_selecionada][queue.df['status'] == "Em espera"].drop(columns=['ip', 'e-mail'])
        if lista_espera_maquina.size > 0:
            with st.expander(f"Lista de espera para {maquina_selecionada}"):
                st.dataframe(lista_espera_maquina,  hide_index=True, use_container_width=True)

        n_cpu = st.number_input("Número de CPUs", min_value=1, step=1)
        try:
            con = Connection(ip=maquina['ip'].iloc[0], username=maquina['username'].iloc[0], password=maquina['password'].iloc[0])
            mon = Monitor(con)
            gpu = st.selectbox('Selecione a GPU', ["-1 - Null"]+[f"{gpu['gpu_index']} - {gpu['name']}" for gpu in mon.get_usage_gpu()['gpu_info']])
            gpu_index, gpu_name = gpu.split(" - ")
        
        except Exception as e:
            gpu = st.selectbox('Selecione a GPU', ["-1 - Null"])
            gpu_index, gpu_name = gpu.split(" - ")
            st.error(f"Erro ao obeter informações de GPU. Provavelmente {maquina_selecionada} não tem GPU, está offline ou com falha.")

        min_data = pd.to_datetime(queue.df.loc[(queue.df['name'] == maquina_selecionada) & (queue.df['gpu_name'] == gpu_name.strip()) & (queue.df['gpu_index'] == int(gpu_index)), 'fim'].max())
        if str(min_data) == "NaT": min_data = datetime.now()

        inicio = st.date_input("Início (Data)", min_value=min_data)
        #inicio_hora = st.time_input("Início (Hora)", value=datetime.now().time())
        fim = st.date_input("Fim (Data)", value=min_data, min_value=min_data)
        #fim_hora = st.time_input("Fim (Hora)", value=datetime.now().time())

        username = st.text_input("Username")
        email = st.text_input("E-mail")

        submitted = st.button("Agendar")
        if submitted:
            if not username or not n_cpu or not email:
                st.error("Por favor, preencha todos os campos.")
            elif min_data >= pd.to_datetime(inicio) or min_data >= pd.to_datetime(fim):
                st.error("Por favor, indique uma data livre para o recurso desejado (GPU ou CPU).")
            else:
                try:
                    inicio_datetime = datetime.combine(inicio, datetime.now().time())
                    fim_datetime = datetime.combine(fim, time(23, 59, 0, 0))
                    queue.insert(
                        ip=maquina['ip'].iloc[0],
                        name=maquina['name'].iloc[0],
                        username=username,
                        inicio=inicio_datetime,
                        fim=fim_datetime,
                        n_cpu=n_cpu,
                        gpu_index=gpu_index,
                        gpu_name=gpu_name,
                        email=email, 
                        to_send=False
                    )
                    st.success(f"Agendamento feito com Sucesso '{username}' criado com sucesso.")

                except Exception as e:
                    st.error(f"Erro ao agendar: {e}")
                    
def remover_agendamento():
    global queue
    with st.container(border=True):
        st.subheader("Remover Agendamento")
        try:
            agendamentos = queue.df[queue.df['status'] != 'Finalizado'].apply(
                                        lambda row: f"{row['name']} - {row['username']} - {row['inicio']} - {row['fim']} - {row['n_cpu']} - {row['gpu_name']}",
                                        axis=1).tolist()
        except Exception as e:
            agendamentos = []

        agendamento = st.selectbox('Escolha usuário', agendamentos)
        
        email = st.text_input("E-mail")
        remove = st.button("Remover")

        if remove:
            nome_maquina, usuario, inicio, fim, n_cpu, gpu_name = agendamento.split(' - ')

            index_remove = queue.df[(queue.df['name'] == nome_maquina) & (queue.df['username'] == usuario) & (queue.df['inicio'] == inicio) & (queue.df['fim'] == fim)].index[0]
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

def lista_espera():
    global queue
    with st.container(border=True):
        st.subheader("Lista de espera")
        maquinas_espera = queue.df[queue.df['status'] == "Em espera"]['name'].unique()
        print(maquinas_espera)
        for m in maquinas_espera:
            with st.expander(m):
                st.dataframe(queue.df[queue.df['name'] == m][queue.df['status'] == "Em espera"].drop(columns=['ip', 'e-mail', 'notification_last_day']),  hide_index=True, use_container_width=True)


st.markdown("# Agendamento de Máquinas")
st.sidebar.markdown("# Agendamento de Máquinas")

data = Data(); data.read_machines(path=f"{sys.argv[1]}/machines.xlsx")
queue = Queue(data=data)

try:
    queue.update_status()
except:
    st.warning("Não foi possivel atualizar o status dos agendamentos.")
    pass


st.subheader("Agendamentos")
st.dataframe(queue.df[queue.df['status'] == "Executando"].drop(columns=['ip', 'e-mail', 'notification_last_day']), use_container_width=True, hide_index=True)

action = st.selectbox("Escolha uma ação", ["Selecione", "Agendar", "Remover Agendamento", "Lista de Espera"])
fun = {"Selecione": print, "Agendar": agendar, "Remover Agendamento": remover_agendamento, "Lista de Espera": lista_espera}

if "action_state" not in st.session_state: 
    st.session_state.action_state = action

try:
    fun[action]()
except Exception as e:
    st.error(f"Erro ao selecionar ação: {e}")


