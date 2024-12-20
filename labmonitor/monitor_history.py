import os
import time
import pandas as pd
from datetime import datetime
from labmonitor.data import Data
from labmonitor.monitor import Monitor
from labmonitor.connection import Connection
from concurrent.futures import ThreadPoolExecutor, as_completed

def run(ip, name, user, pw):
    try:
        print(f"Conectando a {ip}...")
        results = {}
        c = Connection(ip, user, pw)
        m = Monitor(c)
        results.update(m.get_usage_cpu())
        results.update(m.get_usage_gpu())
        results.update(m.get_usage_ram())
        return name, results
    except Exception as e:
        print(f"Erro ao conectar a {ip}: {e}")
        return name, None

def save_to_excel(results, filepath):
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

        data.append(row)

    df = pd.DataFrame(data)

    if os.path.exists(filepath):
        existing_data = pd.read_excel(filepath)
        df = pd.concat([existing_data, df], ignore_index=True)

    df.to_excel(filepath, index=False)
    print(f"Dados salvos em {filepath}")


def exec_monitor_history(path):
    while True:
        data = Data()
        data.read_machines(path=f"{os.path.dirname(os.path.abspath(__file__))}/../machines.xlsx")

        ips = data.machines['ip'].to_list()
        names = data.machines['name'].to_list()
        usernames = data.machines['username'].to_list()
        passwords = data.machines['password'].to_list()
        print(data.machines)

        results = {}
        history_file = f"{path}/history.xlsx"

        with ThreadPoolExecutor(max_workers=len(ips)) as executor:
            futures = [
                executor.submit(run, ip, name, user, pw)
                for ip, name, user, pw in zip(ips, names, usernames, passwords)
            ]
            for future in as_completed(futures):
                name, stats = future.result()
                if stats:
                    results[name] = stats

        save_to_excel(results, history_file)
        time.sleep(3600) 
