import sys
import streamlit as st

from labmonitor.data import Data
from labmonitor.queue_job import QueueJob

USERS = {
    "lmdm": "1mdm@b1of",
}

if len(sys.argv) > 1:
    path_labmonitor = sys.argv[1]

data = Data()

data.path_data = f"{path_labmonitor}/database.db"
data.connect_data()
q = QueueJob(data=data,  path=f"{path_labmonitor}/database.db")

def autenticar(usuario, senha):
    return USERS.get(usuario) == senha

def select_null():
    pass

def machines_job():
    data.read_machines_job()
    
    edited_mch_job = st.data_editor(data.machines_job, num_rows = "dynamic")
    save_mch_job = st.button("Save")

    if save_mch_job:
        data.machines_job = edited_mch_job.copy()

        data.save_machines_job()


def machine():
    data.read_machines()
    
    edited_mch = st.data_editor(data.machines, num_rows = "dynamic")
    save_mch = st.button("Save")

    if save_mch:
        data.machines = edited_mch.copy()

        data.save_machines()

def jobs():    
    edited_job = st.data_editor(q.df)

def users():
    data.read_users()
    
    edited_usr = st.data_editor(data.users, num_rows = "dynamic")
    save_usr = st.button("Save")

    if save_usr:
        data.users = edited_usr.copy()
        data.save_users()

def email():
    data.read_email()
    
    edited_email = st.data_editor(data.email)
    save_email = st.button("Save")

    if save_email:
        data.email = edited_email.copy()
        data.save_email()


# Página principal
def main_page():
    st.write("Selecione as funções que deseja utilizar:")

    action = st.selectbox("Select an action", ["Select", "Machines Job", "Machine", "Users", "e-mail", "Jobs"])
    fun = {"Select": select_null, "Machines Job": machines_job, "Machine": machine, "Users": users, "e-mail": email, "Jobs": jobs}

    if "action_state" not in st.session_state: 
        st.session_state.action_state = action

    try:
        fun[action]()
    except Exception as e:
        st.error(f"Erro ao selecionar ação: {e}")

def login_page():
    st.title("🔐 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    login = st.button("Entrar")

    if login:
        if autenticar(usuario, senha):
            st.session_state["logado"] = True
            st.session_state["usuario"] = usuario
            st.success("Login bem-sucedido!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")


# Controle de sessão
if "logado" not in st.session_state:
    st.session_state["logado"] = False
    

if st.session_state["logado"]:
    main_page()
else:
    login_page()

