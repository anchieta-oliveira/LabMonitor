import sys
sys.path.append(sys.argv[1])
import pandas as pd
import streamlit as st
from labmonitor.connection import Connection
from labmonitor.data import Data
from labmonitor.monitor import Monitor

def run(ip, username, password):
    results = {}
    c = Connection(ip, username, password)
    m = Monitor(c)
    results.update(m.get_usage_cpu())
    results.update(m.get_usage_gpu())
    results.update(m.get_usage_ram())
    results.update(m.get_usage_disk())
    return results

data = Data(); data.read_machines(path=f"{sys.argv[1]}/machines.xlsx")

ips = data.machines['ip'].to_list()
names = data.machines['name'].to_list()
usernames = data.machines['username'].to_list()
passwords = data.machines['password'].to_list()
print(data.machines)

results = {}
for ip, name, user, pw in zip(ips, names, usernames, passwords):
    print(f"Conectando a {ip}...")
    try:
        results[name] = run(ip, user, pw)
    except Exception as e:
        print(f"Erro: {e}")
        
print(results)
cpu_ram_data = []
for name, stats in results.items():
    row = {
        "Name": name,
        "CPU Usage (%)": stats["cpu_info"]["cpu_usage_percentage"],
        "RAM Used (GB)": stats["ram_info"]["ram_used"],
        "Total RAM (GB)": stats["ram_info"]["total_ram"],
    }
    cpu_ram_data.append(row)

cpu_ram_df = pd.DataFrame(cpu_ram_data)
# Tabela para GPU
gpu_data = []
for name, stats in results.items():
    for gpu in stats["gpu_info"]:
        row = {
            "Name": name,
            "GPU ID": gpu["name"],
            "GPU Utilization (%)": gpu["utilization_gpu"],
            "GPU Memory Used (GB)": gpu["memory_used"],
            "GPU Memory Total (GB)": gpu["memory_total"],
        }
        gpu_data.append(row)
gpu_df = pd.DataFrame(gpu_data)


disk_data = []
for name, stats in results.items():
    for disk in stats["disk_info"]:
        row = {
            "Name": name,
            "Ponto": disk["mount_point"],
            "Total": disk["total_size"],
            "Livre": disk["available"],
            "Usado (%)": disk["usage_percentage"],
            
        }
        disk_data.append(row)
disk_data = pd.DataFrame(disk_data)

# Exibir as tabelas no Streamlit

st.markdown("# Tempo Real")
st.sidebar.markdown("# Tempo Real")
st.subheader("Uso de CPU e RAM")
st.dataframe(cpu_ram_df, use_container_width=True, hide_index=True)
st.subheader("Uso de GPUs")
st.dataframe(gpu_df, use_container_width=True, hide_index=True)
st.subheader("Uso de Discos")
st.dataframe(disk_data, use_container_width=True, hide_index=True)