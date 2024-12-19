import pandas as pd


class Data:
    def __init__(self):
        self.machines = pd.DataFrame()

    def read_machines(self, path:str="machines.xlsx"):
        self.machines = pd.read_excel(path)
        return self.machines



    