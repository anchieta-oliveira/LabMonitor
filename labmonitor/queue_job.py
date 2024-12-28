

import os
import pandas as pd
from labmonitor.connection import Connection
from labmonitor.data import Data


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
    
    def copy_dir(self, ip_origin, username_origin, password_origin, ip_exc, username_exc, password_exc, path_origin:str, path_exc:str):
        cmd = f"""sshpass -p '{password_origin}' ssh {username_origin}@{ip_origin} "echo '{password_origin}' | sudo -S sshpass -p '{password_exc}' scp -r {path_origin} {username_exc}@{ip_exc}:{path_exc}" """
        os.system(cmd)
        