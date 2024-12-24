import os
import subprocess
import pandas as pd
import streamlit as st
import plotly.express as px

from labmonitor.connection import Connection
from labmonitor.monitor import Monitor

st.markdown("# Gerenciar usuários")
st.sidebar.markdown("# Gerenciar usuários.")

df = pd.read_excel(f"{os.path.dirname(os.path.abspath(__file__))}/../../../machines.xlsx")

maquina_selecionada = st.selectbox('Escolha a máquina', df['name'])
df_filtrado = df[df['name'] == maquina_selecionada].dropna(axis=1, how='all')
c = Connection(df_filtrado['ip'].iloc[0], df_filtrado['username'].iloc[0], df_filtrado['password'].iloc[0])
m = Monitor(c)

users_df = pd.DataFrame([
    {"Usuário": usuario, "Grupos": grupos}
    for usuario, grupos in m.get_users().items()
])

st.subheader("Usuários")
st.dataframe(users_df, use_container_width=True, hide_index=True)


# Botão para criar novo usuário
if st.button("Criar Novo Usuário"):
    with st.form("criar_usuario_form", clear_on_submit=True):
        nome_usuario = st.text_input("Nome do Usuário", placeholder="Digite o nome do usuário")
        senha_usuario = st.text_input("Senha do Usuário", type="password")
        is_sudo = st.checkbox("Adicionar ao grupo sudo")
        senha_sudo = st.text_input("Senha de Administrador (sudo)", type="password")
        
        # Botão de submissão
        criar = st.form_submit_button("Criar Usuário")
        
        if criar:
            if not nome_usuario or not senha_usuario or not senha_sudo:
                st.error("Por favor, preencha todos os campos.")
            else:
                # Comando para criar o usuário
                try:
                    # Adiciona o usuário
                    comando_add_user = f"echo {senha_sudo} | sudo -S useradd -m {nome_usuario}"
                    subprocess.run(comando_add_user, shell=True, check=True, text=True)
                    
                    # Configura a senha do usuário
                    comando_set_senha = f"echo '{nome_usuario}:{senha_usuario}' | sudo -S chpasswd"
                    subprocess.run(comando_set_senha, shell=True, check=True, text=True)
                    
                    # Adiciona ao grupo sudo se necessário
                    if is_sudo:
                        comando_add_sudo = f"echo {senha_sudo} | sudo -S usermod -aG sudo {nome_usuario}"
                        subprocess.run(comando_add_sudo, shell=True, check=True, text=True)
                    
                    st.success(f"Usuário '{nome_usuario}' criado com sucesso.")
                except subprocess.CalledProcessError as e:
                    st.error(f"Erro ao criar o usuário: {e}")