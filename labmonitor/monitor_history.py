""" Monitor history module """

# Imports
############################################################################################################
import os
import time
import pandas as pd
from datetime import datetime
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
        print(f"Conectando a {ip}...", flush=True)
        results = {}
        c = Connection(ip, user, pw)
        m = Monitor(c)
    except Exception as e:
        print(f"Erro ao conectar a {ip}: {e}", flush=True)
        return name, None

    try: 
        results.update(m.get_usage_cpu())
    except Exception as e:
        results.update({"cpu_info": {"cpu_usage_percentage": -1}})
        print(f"Erro ao obter informações de CPU de {ip}: {e}", flush=True)
    try:
        results.update(m.get_usage_gpu())
    except Exception as e:
        results.update({"gpu_info": []})
        print(f"Erro ao obter informações de GPU de {ip}: {e}", flush=True)
    try:
        results.update(m.get_usage_ram())
    except Exception as e:
        {"ram_info": {"ram_used": -1,"ram_free": -1,"total_ram": -1}}
        print(f"Erro ao obter informações de RAM de {ip}: {e}", flush=True)
    try:
        results.update(m.get_usage_disk())
    except Exception as e:
        print(f"Erro ao obter informações de disco de {ip}: {e}", flush=True)

    return name, results

def save_to_csv(results: dict, filepath: str) -> None:
    """ Save the results to an csv file

    Args:
    - results (dict): Dictionary with the results of the monitor
    - filepath (str): Path to the csv file

    Returns:
    - None
    """

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = []

    for name, stats in results.items():
        row = {
            "Name": name,
            "Timestamp": timestamp,
            "CPU Usage (%)": stats["cpu_info"]["cpu_usage_percentage"],
            "RAM Used (GB)": stats["ram_info"]["ram_used"],
            "Total RAM (GB)": stats["ram_info"]["total_ram"],
        }

        for gpu in stats["gpu_info"]:
            gpu_index = gpu["gpu_index"]
            row[f"GPU_{gpu_index}_Utilization (%)"] = gpu["utilization_gpu"] if gpu["utilization_gpu"] != "[N/A]" else 0
            row[f"GPU_{gpu_index}_Memory Used (GB)"] = gpu["memory_used"]
            row[f"GPU_{gpu_index}_Memory Total (GB)"] = gpu["memory_total"]
            row[f"GPU_{gpu_index}_Name"] = gpu["name"]
            row[f"GPU_{gpu_index}_Process"] = gpu["process"]
            row[f"GPU_{gpu_index}_User"] = gpu["user"]

        data.append(row)

    df = pd.DataFrame(data)

    if os.path.exists(filepath):
        existing_data = pd.read_csv(filepath)
        df = pd.concat([existing_data, df], ignore_index=True)

    df.to_csv(filepath, index=False)
    print(f"Dados salvos em {filepath}", flush=True)


def exec_monitor_history(path: str) -> None:
    """ Execute the monitor history process

    Args:
    - path (str): Path to the csv file with the machines information

    Returns:
    - None
    """

    while True:
        data = Data()
        data.read_machines(path=f"{os.path.dirname(os.path.abspath(__file__))}/../machines.csv")

        ips = data.machines['ip'].to_list()
        names = data.machines['name'].to_list()
        usernames = data.machines['username'].to_list()
        passwords = data.machines['password'].to_list()
        print(data.machines, flush=True)

        results = {}
        history_file = f"{path}/history.csv"

        with ThreadPoolExecutor(max_workers=len(ips)) as executor:
            futures = [
                executor.submit(run, ip, name, user, pw)
                for ip, name, user, pw in zip(ips, names, usernames, passwords)
            ]
            for future in as_completed(futures):
                name, stats = future.result()
                if stats:
                    results[name] = stats
        try:
            save_to_csv(results, history_file)
        except Exception as e:
            print(e, flush=True)
            
        time.sleep(3600) 
