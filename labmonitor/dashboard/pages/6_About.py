""" More information page """

# Imports
############################################################################################################

import streamlit as st
import os

# Main
############################################################################################################

st.markdown(
    """
    <div style="text-align: center;">
        <h1>About</h1>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("## LabMonitor")
st.markdown("LabMonitor is a Python application designed to simplify the management of computing resources in decentralized networks of Linux machines.")


st.markdown("## Official Publication")
st.markdown("Please cite the following article if you use this tool in your work: [Insert Article Title, Authors, Journal, Year, DOI].")


st.markdown("## Meet Our Group")
st.image("http://lmdm.biof.ufrj.br/images/logo.png",
         width=900,
         use_container_width=False)
st.markdown("LabMonitor was developed by members of the Molecular Modelling and Dynamics Laboratory (LMDM) at the Carlos Chagas Filho Biophysics Institute (IBCCF) of the Federal University of Rio de Janeiro (UFRJ). LMDM is a research group focused on studying molecular aspects of life using computational approaches. For more information about the group, visit http://lmdm.biof.ufrj.br.")
st.sidebar.markdown("# Description")
st.markdown("### Meet LabMonitor Colaborators")
team_members = [
    {
        "url": "http://lmdm.biof.ufrj.br/images/team/Pedro_Pascutti.jpg",
        "caption": "Professor PhD. Pedro Geraldo Pascutti",
    },
    {
        "url": "http://lmdm.biof.ufrj.br/images/team/Pedro_Torres.png",
        "caption": "Professor PhD. Pedro Henrique Monteiro Torres",
    },
    {
        "url": "http://lmdm.biof.ufrj.br/images/team/Anchieta_Oliveira.jpg",
        "caption": "MSc. José de Anchieta De Oliveira Filho",
    },
    {
        "url": "http://lmdm.biof.ufrj.br/images/team/Artur_Rossi.jpg",
        "caption": "MSc. Artur Duque Rossi",
    },
    {
        "url": "http://servicosweb.cnpq.br/wspessoa/servletrecuperafoto?tipo=1&id=K4900986H3",
        "caption": "MSc. Mariana Simões Ferreira",
    },
    {
        "url": "http://lmdm.biof.ufrj.br/images/team/Guilherme_Ian.jpg",
        "caption": "BSc. Guilherme Ian Spelta",
    },
]

cols = st.columns(3)
for i, member in enumerate(team_members):
    with cols[i % 3]:
        st.image(member["url"], caption=member["caption"], width=150)

st.markdown("## Check Out Our Github!")
st.markdown("Check out more of our software, utility packages, and tutorials focused on computational biology analysis at: https://github.com/LMDM")

st.markdown("## Contact Us")
st.markdown("To address any douts or suggestions, please contact the corresponding author: anchieta.oliveira@biof.ufrj.br")

st.sidebar.markdown("This section provides useful information about LabMonitor developers and publications.")
