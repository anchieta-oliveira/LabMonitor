""" User management page """

# Imports
############################################################################################################
import os
import subprocess
import pandas as pd
import streamlit as st

from labmonitor.monitor import Monitor
from labmonitor.connection import Connection


# Functions
############################################################################################################

def adduser():
    """ [BUTTON] Add a new user to the machine
    
    Args:
    - None

    Returns:
    - None
    """

    with st.form("criar_usuario_form", clear_on_submit=True):
        username = st.text_input("Nome do Usuário", placeholder="Digite o nome do usuário")
        password = st.text_input("Senha do Usuário", type="password")
        is_sudo = st.checkbox("Adicionar ao grupo sudo")
        useradm = st.text_input("Usuário Administrador (sudo)")
        passadm = st.text_input("Senha Administrador (sudo)", type="password")
        
        criar = st.form_submit_button("Criar Usuário")

        if criar:
            if not username or not password or not useradm or not passadm:
                st.error("Por favor, preencha todos os campos.")
            else:
                try:
                    con_adm = Connection(ip=df_filtrado['ip'].iloc[0], username=useradm, password=passadm)
                    mon_adm = Monitor(con_adm)
                    mon_adm.add_new_user(username, password, passadm)
                    if is_sudo:
                        mon_adm.add_sudo_grup(username, passadm)
                    st.success(f"Usuário '{username}' criado com sucesso.")
                    
                except Exception as e:
                    st.error(f"Erro ao criar o usuário: {e}")
        
def removeuser():
    """ [BUTTON] Remove a user from the machine

    Args:
    - None

    Returns:
    - None
    """

    with st.form("excluir_usuario_form", clear_on_submit=True):
        selected_user = st.selectbox("Selecione o usuário para excluir:", users_df["Usuário"])
        useradm = st.text_input("Usuário Administrador (sudo)")
        passadm = st.text_input("Senha Administrador (sudo)", type="password")
        
        excluir = st.form_submit_button("Excluir Usuário")

        if excluir:
            if not useradm or not passadm:
                st.error("Por favor, preencha todos os campos.")
            else:
                try:
                    con_adm = Connection(ip=df_filtrado['ip'].iloc[0], username=useradm, password=passadm)
                    mon_adm = Monitor(con_adm)
                    mon_adm.remove_user(selected_user, passadm)
                    st.success(f"Usuário '{selected_user}' excluído com sucesso.")
                    
                except Exception as e:
                    print(e)
                    st.error(f"Erro ao criar o usuário: {e}")

def addsudo():
    """ [BUTTON] Add a user to the sudo group

    Args:
    - None

    Returns:
    - None
    """

    with st.form("addsudo_usuario_form", clear_on_submit=True):
        selected_user = st.selectbox("Selecione o usuário para tornar sudo:", users_df["Usuário"])
        useradm = st.text_input("Usuário Administrador (sudo)")
        passadm = st.text_input("Senha Administrador (sudo)", type="password")
        
        tornar_sudo = st.form_submit_button("Adicionar ao sudo")

        if tornar_sudo:
            if not useradm or not passadm:
                st.error("Por favor, preencha todos os campos.")
            else:
                try:
                    con_adm = Connection(ip=df_filtrado['ip'].iloc[0], username=useradm, password=passadm)
                    mon_adm = Monitor(con_adm)
                    mon_adm.add_sudo_grup(selected_user, passadm)
                    st.success(f"Usuário '{selected_user}' sudo com sucesso.")
                    
                except Exception as e:
                    st.error(f"Erro ao criar o usuário: {e}")


# Main
############################################################################################################

st.markdown("# Gerenciar usuários")
st.sidebar.markdown("# Gerenciar usuários.")

df = pd.read_csv(f"{os.path.dirname(os.path.abspath(__file__))}/../../../machines.csv")

maquina_selecionada = st.selectbox('Escolha a máquina', df['name'])
df_filtrado = df[df['name'] == maquina_selecionada].dropna(axis=1, how='all')
c = Connection(df_filtrado['ip'].iloc[0], df_filtrado['username'].iloc[0], df_filtrado['password'].iloc[0])
m = Monitor(c)

def run_get_user() -> None:
    """ Get the users from the machine

    Args:
    - None

    Returns:
    - None
    """

    global users_df 
    users_df = pd.DataFrame([
        {"Usuário": usuario, "Grupos": grupos}
        for usuario, grupos in m.get_users().items()
    ])
    

    st.subheader("Usuários")
    st.dataframe(users_df, use_container_width=True, hide_index=True)

run_get_user()

try: 
    st.subheader("Usuários logados")
    st.dataframe(m.logged_users()['logged_users'], use_container_width=True, hide_index=True)
except Exception as e:
    st.error(f"Erro ao carregar usuários logados: {e}")

action = st.selectbox("Escolha uma ação", ["Selecione", "Criar Novo Usuário", "Adicionar ao sudo", "Excluir Usuário"])
fun = {"Selecione": print, "Adicionar ao sudo": addsudo, "Criar Novo Usuário": adduser, "Excluir Usuário": removeuser}

if "action_state" not in st.session_state: 
    st.session_state.action_state = action

try:
    fun[action]()
except Exception as e:
    st.error(f"Erro ao selecionar ação: {e}")