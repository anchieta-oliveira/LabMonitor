""" Main page of the dashboard """

# Imports
############################################################################################################
import sys
sys.path.append(sys.argv[1])
import pandas as pd
import streamlit as st

from labmonitor.data import Data
from labmonitor.monitor import Monitor
from labmonitor.connection import Connection
from concurrent.futures import ThreadPoolExecutor, as_completed

# Functions
############################################################################################################

def run(ip: str, name: str, user: str, pw: str) -> tuple[str, dict]:
    """ Run the monitor for a given machine

    Args:
    - ip (str): IP address of the machine
    - name (str): Name of the machine
    - user (str): Username to connect to the machine
    - pw (str): Password to connect to the machine

    Returns:
    - name (str): Name of the machine
    - results (dict): Dictionary with the results of the monitor
    """

    try:
        print(f"Connecting to {ip}...")
        results = {}
        c = Connection(ip, user, pw)
        m = Monitor(c)
    except Exception as e:
        print(f"Error connecting to {ip}: {e}")
        return name, None

    try: 
        results.update(m.get_usage_cpu())
    except Exception as e:
        results.update({"cpu_info": {"cpu_usage_percentage": -1}})
        print(f"Error getting CPU information from {ip}: {e}")
    try:
        results.update(m.get_usage_gpu())
    except Exception as e:
        results.update({"gpu_info": []})
        print(f"Error getting GPU information from {ip}: {e}")
    try:
        results.update(m.get_usage_ram())
    except Exception as e:
        {"ram_info": {"ram_used": -1,"ram_free": -1,"total_ram": -1}}
        print(f"Error getting RAM information from{ip}: {e}")
    try:
        results.update(m.get_usage_disk())
    except Exception as e:
        print(f"Error getting disk information from {ip}: {e}")

    return name, results

# Main
############################################################################################################

data = Data(); data.read_machines(path=f"{sys.argv[1]}/machines.csv")

ips = data.machines['ip'].to_list()
names = data.machines['name'].to_list()
usernames = data.machines['username'].to_list()
passwords = data.machines['password'].to_list()
print(data.machines)

results = {}

with ThreadPoolExecutor(max_workers=len(ips)) as executor:
    futures = [
        executor.submit(run, ip, name, user, pw)
        for ip, name, user, pw in zip(ips, names, usernames, passwords)
    ]
    for future in as_completed(futures):
        name, stats = future.result()
        if stats:
            results[name] = stats
        
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

gpu_data = []
for name, stats in results.items():
    for gpu in stats["gpu_info"]:
        row = {
            "Name": name,
            "ID": gpu["name"],
            "User": gpu["user"],
            "Utilization (%)": gpu["utilization_gpu"],
            "Memory Used (GB)": gpu["memory_used"],
            "Memory Total (GB)": gpu["memory_total"],
            "Process": gpu["process"],
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

st.markdown("# Real Time")
st.sidebar.markdown("# Real Time")
st.subheader("CPU and RAM")
st.dataframe(cpu_ram_df.sort_values(by='CPU Usage (%)', ascending=False), use_container_width=True, hide_index=True)
st.subheader("GPUs")
st.dataframe(gpu_df.sort_values(by='ID', ascending=False), use_container_width=True, hide_index=True)
st.subheader("Disks")
st.dataframe(disk_data, use_container_width=True, hide_index=True)