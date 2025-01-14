""" Data module """

# Imports
############################################################################################################
import os
import json
import pandas as pd
current_dirname_path = os.path.dirname(os.path.abspath(__file__))


# Class
############################################################################################################
class Data:
    """ Data class to handle the data of the machines and users 
    
    Attributes:
    - machines (pd.DataFrame): DataFrame with the machines information
    - path_machines (str): Path to the machines Excel file
    - path_users (str): Path to the users Excel file
    - users (pd.DataFrame): DataFrame with the users information
    - email (dict): Dictionary with the email information
    """

    def __init__(self) -> None:
        """ Constructor method for the Data class

        Args:
        - None

        Returns:
        - None
        """

        self.machines = pd.DataFrame()
        self.path_machines = ""
        self.path_users = ""
        self.users = pd.DataFrame()
        self.email = {}

    def read_machines(self, path: str = f"{current_dirname_path}/../machines.xlsx"):
        """ Read the machines information from an Excel file
        
        Args:
        - path (str, optional): Path to the Excel file with the machines information. Defaults to f"{current_dirname_path}/../machines.xlsx".

        Returns:
        - pd.DataFrame: DataFrame with the machines information
        """

        self.path_machines = path
        self.machines = pd.read_excel(path)
        
        return self.machines

    def save_machines(self, path: str = f"") -> None:
        """ Save the machines information to an Excel file

        Args:
        - path (str, optional): Path to save the Excel file with the machines information. Defaults to "".

        Returns:
        - None
        """

        if path == "":
            path = self.path_machines
        backup_path = f"{os.path.splitext(path)[0]}_old{os.path.splitext(path)[1]}"
    
        try:
            if os.path.exists(path): os.rename(path, backup_path)
            self.machines.to_excel(path, index=False)
            
        except Exception as e:
            print("Erro ao salvar o arquivo:", e)

    def read_users(self, path: str = f"{current_dirname_path}/../users.xlsx") -> pd.DataFrame:
        """ Read the users information from an Excel file

        Args:
        - path (str, optional): Path to the Excel file with the users information. Defaults to f"{current_dirname_path}/../users.xlsx".

        Returns:
        - pd.DataFrame: DataFrame with the users information
        """

        try:
            self.path_users = path
            self.users = pd.read_excel(path)
        
        except Exception as e:
            print(f"Não foi possivel carregar as informações de usuários: {e}")

        return self.users


    def read_email(self, path: str = f"{current_dirname_path}/../email.json"):
        """ Read the email information from a JSON file

        Args:
        - path (str, optional): Path to the JSON file with the email information. Defaults to f"{current_dirname_path}/../email.json".

        Returns:
        - dict: Dictionary with the email information
        """

        try:
            with open(path, 'r') as config_file:
                self.email = json.load(config_file)
                return self.email
            
        except Exception as e:
            print(f"Não foi possivel carregar as informações de e-mial: {e}")
            return self.email
    