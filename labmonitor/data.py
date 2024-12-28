import os
import json
import pandas as pd
current_dirname_path = os.path.dirname(os.path.abspath(__file__))


class Data:
    def __init__(self):
        self.machines = pd.DataFrame()
        self.path_machines = ""
        self.email = {}

    def read_machines(self, path:str=f"{current_dirname_path}/../machines.xlsx"):
        self.path_machines = path
        self.machines = pd.read_excel(path)
        return self.machines

    def save_machines(self, path:str=f""):
        if path == "": path = self.path_machines
        self.machines.to_excel(path, index=False)

    def read_email(self, path:str=f"{current_dirname_path}/../email.json"):
        try:
            with open(path, 'r') as config_file:
                self.email = json.load(config_file)
                return self.email
            
        except Exception as e:
            print(f"Não foi possivel carregar as informações de e-mial: {e}")
            return self.email


    