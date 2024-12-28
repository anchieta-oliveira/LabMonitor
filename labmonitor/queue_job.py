

import os
import pandas as pd
from labmonitor.data import Data
from labmonitor.monitor import Monitor
from labmonitor.connection import Connection
from concurrent.futures import ThreadPoolExecutor, as_completed



class QueueJob:
    def __init__(self, data:Data, path:str="queue_job.xlsx"):
        self.df = self.read_excel(path)
        self.path = path
        self.data = data
        self.machines = data.machines

    def read_excel(self, path:str="queue_job.xlsx") -> pd.DataFrame:
        if os.path.exists(path):
            self.df = pd.read_excel(path)
            self.df['fim'] = self.df['fim'] = pd.to_datetime(self.df['fim'])
            self.df['inicio'] = self.df['inicio'] = pd.to_datetime(self.df['inicio'])
        else:
            self.reset()
        return self.df

    def save(self):
        self.df.to_excel(self.path, index=False)

    def reset(self) -> pd.DataFrame:
        columns = ["ip", "name", "username", "path_exc", "path_origin", "script_name", "inicio", "fim", "n_cpu", "gpu_name", "gpu_index", "e-mail", "notification_start", "notification_end"]
        self.df = pd.DataFrame(columns=columns)
        self.df.to_excel("queue_job.xlsx", index=False)
        return self.df
    
    def update_gpu(self):
        def run(ip, name, user, pw):
            try:
                print(f"Conectando a {ip}...")
                results = {}
                c = Connection(ip, user, pw)
                m = Monitor(c)
            except Exception as e:
                print(f"Erro ao conectar a {ip}: {e}")
                return name, None
            try:
                results.update(m.get_usage_gpu())
            except Exception as e:
                results.update({"gpu_info": []})
                print(f"Erro ao obter informações de GPU de {ip}: {e}")
            return name, results
        
        ips = self.data.machines['ip'].to_list()
        names = self.data.machines['name'].to_list()
        usernames = self.data.machines['username'].to_list()
        passwords = self.data.machines['password'].to_list()

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

        data_gpu = []
        for name, stats in results.items():
            row = {"name": name}
            for gpu in stats["gpu_info"]:
                gpu_index = gpu["gpu_index"]
                row[f"GPU_{gpu_index}_Name"] = gpu["name"]
                sts = ""
                if self.data.machines[self.data.machines['name'] == name][f"GPU_{gpu_index}_status"].iloc[0] != "": sts = self.data.machines[self.data.machines['name'] == name][f"GPU_{gpu_index}_status"].iloc[0]
                row[f"GPU_{gpu_index}_status"] = sts

            data_gpu.append(row)

        self.data.machines = pd.merge(self.machines[['ip','name', 'username', 'password', 'status', 'allowed_cpu', 'name_allowed_gpu', 'path_exc']], pd.DataFrame(data_gpu), on="name")
        self.data.save_machines()

    def copy_dir(self, ip_origin, username_origin, password_origin, ip_exc, username_exc, password_exc, path_origin:str, path_exc:str):
        cmd = f"""sshpass -p '{password_origin}' ssh {username_origin}@{ip_origin} "echo '{password_origin}' | sudo -S sshpass -p '{password_exc}' scp -r {path_origin} {username_exc}@{ip_exc}:{path_exc}" """
        os.system(cmd)
        