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
    - path_machines (str): Path to the machines csv file
    - path_users (str): Path to the users csv file
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

    def read_machines(self, path: str = f"{current_dirname_path}/../machines.csv"):
        """ Read the machines information from an csv file
        
        Args:
        - path (str, optional): Path to the csv file with the machines information. Defaults to f"{current_dirname_path}/../machines.csv".

        Returns:
        - pd.DataFrame: DataFrame with the machines information
        """

        self.path_machines = path
        try:
            self.machines = pd.read_csv(path)
        except Exception as e:
            print(f"Error reading the file {path}: {e}", flush=True)
            backup_path = f"{os.path.splitext(path)[0]}_old{os.path.splitext(path)[1]}"
            try:
                self.machines = pd.read_csv(backup_path)
                print(f"Backup file {backup_path} uploaded successfully.", flush=True)
            except Exception as e_backup:
                print(f"Error reading the backup file {backup_path}: {e_backup}", flush=True)
            
        return self.machines

    def save_machines(self, path: str = f"") -> None:
        """ Save the machines information to an CSV file

        Args:
        - path (str, optional): Path to save the csv file with the machines information. Defaults to "".

        Returns:
        - None
        """

        if path == "":
            path = self.path_machines
        backup_path = f"{os.path.splitext(path)[0]}_old{os.path.splitext(path)[1]}"
    
        try:
            if os.path.exists(path): os.rename(path, backup_path)
            self.machines.to_csv(path, index=False)
            
        except Exception as e:
            print("Error saving the file:", e, flush=True)
            try:
                if os.path.exists(path): os.rename(path, backup_path)
                self.machines.to_csv(path, index=False)
            except Exception as e:
                print("Error saving the file 2:", e, flush=True)


    def read_users(self, path: str = f"{current_dirname_path}/../users.csv") -> pd.DataFrame:
        """ Read the users information from an csv file

        Args:
        - path (str, optional): Path to the csv file with the users information. Defaults to f"{current_dirname_path}/../users.csv".

        Returns:
        - pd.DataFrame: DataFrame with the users information
        """

        try:
            self.path_users = path
            self.users = pd.read_csv(path)
        
        except Exception as e:
            print(f"Unable to load user information: {e}", flush=True)

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
            print(f"The email information could not be uploaded: {e}", flush=True)
            return self.email
    