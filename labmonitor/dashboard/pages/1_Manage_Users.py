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
        username = st.text_input("User Name", placeholder="Enter the user name")
        password = st.text_input("User Password", type="password")
        is_sudo = st.checkbox("AAdd to sudo group")
        useradm = st.text_input("Administrator user (sudo)")
        passadm = st.text_input("Password Administrator (sudo)", type="password")
        
        criar = st.form_submit_button("Create User")

        if criar:
            if not username or not password or not useradm or not passadm:
                st.error("Please fill in all the fields.")
            else:
                try:
                    con_adm = Connection(ip=df_filtrado['ip'].iloc[0], username=useradm, password=passadm)
                    mon_adm = Monitor(con_adm)
                    mon_adm.add_new_user(username, password, passadm)
                    if is_sudo:
                        mon_adm.add_sudo_grup(username, passadm)
                    st.success(f"User '{username}' created successfully.")
                    
                except Exception as e:
                    st.error(f"Error creating the user: {e}")
        
def removeuser():
    """ [BUTTON] Remove a user from the machine

    Args:
    - None

    Returns:
    - None
    """

    with st.form("excluir_usuario_form", clear_on_submit=True):
        selected_user = st.selectbox("Select the user to delete:  ", users_df["User"])
        useradm = st.text_input("Administrator user (sudo)")
        passadm = st.text_input("Password Administrator (sudo)", type="password")
        
        excluir = st.form_submit_button("Delete User")

        if excluir:
            if not useradm or not passadm:
                st.error("Please fill in all the fields.")
            else:
                try:
                    con_adm = Connection(ip=df_filtrado['ip'].iloc[0], username=useradm, password=passadm)
                    mon_adm = Monitor(con_adm)
                    mon_adm.remove_user(selected_user, passadm)
                    st.success(f"User '{selected_user}' successfully deleted.")
                    
                except Exception as e:
                    print(e)
                    st.error(f"Error creating user: {e}")

def addsudo():
    """ [BUTTON] Add a user to the sudo group

    Args:
    - None

    Returns:
    - None
    """

    with st.form("addsudo_usuario_form", clear_on_submit=True):
        selected_user = st.selectbox("Select the user to make sudo:  ", users_df["User"])
        useradm = st.text_input("Administrator user (sudo)")
        passadm = st.text_input("Password Administrator (sudo)", type="password")
        
        tornar_sudo = st.form_submit_button("Add to sudo")

        if tornar_sudo:
            if not useradm or not passadm:
                st.error("Please fill in all the fields.")
            else:
                try:
                    con_adm = Connection(ip=df_filtrado['ip'].iloc[0], username=useradm, password=passadm)
                    mon_adm = Monitor(con_adm)
                    mon_adm.add_sudo_grup(selected_user, passadm)
                    st.success(f"User '{selected_user}' sudo successful.")
                    
                except Exception as e:
                    st.error(f"Error creating user: {e}")


# Main
############################################################################################################

st.markdown(
    """
    <div style="text-align: center;">
        <h1>Manage Users</h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.sidebar.markdown("# Description")
st.sidebar.markdown("This section lists users of the machines listed in the \"machines.csv\" and the groups they belong to, shows which ones are currently online, and allows actions such as creating and deleting users.")
st.sidebar.markdown("Note that in order to create and delete users in a specific computer you must include one of its sudo users in the \"machines.csv\" file")

df = pd.read_csv(f"{os.path.dirname(os.path.abspath(__file__))}/../../../machines.csv")

maquina_selecionada = st.selectbox('Choose a machine', df['name'])
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
        {"User": usuario, "Groups": grupos}
        for usuario, grupos in m.get_users().items()
    ])
    

    st.subheader("Users")
    st.dataframe(users_df, use_container_width=True, hide_index=True)

run_get_user()

try: 
    st.subheader("Users logged")
    st.dataframe(m.logged_users()['logged_users'], use_container_width=True, hide_index=True)
except Exception as e:
    st.error(f"Error loading logged-in users: {e}")

action = st.selectbox("Action", ["Select", "Create New User", "Add to sudo", "Delete User"])
fun = {"Select": print, "Add to sudo": addsudo, "Create New User": adduser, "Delete User": removeuser}

if "action_state" not in st.session_state: 
    st.session_state.action_state = action

try:
    fun[action]()
except Exception as e:
    st.error(f"Error selecting action: {e}")

#    