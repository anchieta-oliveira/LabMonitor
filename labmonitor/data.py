""" Data module """

# Imports
############################################################################################################
import os
import json
import shutil
import sqlite3
import pandas as pd


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

    def __init__(self, path: str = "database.db") -> None:
        """ Constructor method for the Data class

        Args:
        - None

        Returns:
        - None
        """

        self.machines = pd.DataFrame()
        self.machines_job = pd.DataFrame()
        self.path_data = path
        self.users = pd.DataFrame()
        self.email = pd.DataFrame()
        self.conn_sql = None
        self.connect_data(path)

    def read_machines(self) ->pd.DataFrame:
        """Read the machines information from a SQLite database file.
        
        Args:
        - path (str, optional): Path to the SQLite file with the machines information.

        Returns:
        - pd.DataFrame: DataFrame with the machines information.
        """

        try:
            self.machines = pd.read_sql_query("SELECT * FROM machines", self.conn_sql)

        except Exception as e:
            print(f"Error reading the database {e}", flush=True)

        return self.machines

    def save_machines(self) -> None:
        """Save the machines information to a SQLite database file.
        
        Args:
        - path (str, optional): Path to save the SQLite file. Defaults to `self.path_machines`.
        
        Returns:
        - None
        """

        try:            
            self.machines.to_sql("machines", self.conn_sql, if_exists='replace', index=False)

        except Exception as e:
            print("Error saving the database:", e, flush=True)
           

    def read_machines_job(self):
        """Read the machines information from a SQLite database file.
        
        Args:
        - path (str, optional): Path to the SQLite file with the machines information.

        Returns:
        - pd.DataFrame: DataFrame with the machines information.
        """

        try:
            self.machines_job = pd.read_sql_query("SELECT * FROM machines_job", self.conn_sql)

        except Exception as e:
            print(f"Error reading the database: {e}", flush=True)

        return self.machines_job
    
    def save_machines_job(self, path: str = "") -> None:
        """Save the machines information to a SQLite database file.
        
        Args:
        - path (str, optional): Path to save the SQLite file. Defaults to `self.path_machines`.
        
        Returns:
        - None
        """

        try:            
            self.machines_job.to_sql("machines_job", self.conn_sql, if_exists='replace', index=False)

        except Exception as e:
            print("Error saving the database:", e, flush=True)


    def read_users(self, path: str = "") -> pd.DataFrame:
        """ Read the users information from an csv file

        Args:
        - path (str, optional): Path.
        Returns:
        - pd.DataFrame: DataFrame with the users information
        """

        if path == "":
            path = self.path_data

        try:
            self.users = pd.read_sql_query("SELECT * FROM users", self.conn_sql)
            
        except Exception as e:
            print(f"Unable to load user information: {e}", flush=True)

        return self.users

    def save_users(self) -> pd.DataFrame:
        """ Svae the users information

        Args:
        - path (str, optional): Path.

        Returns:
        - pd.DataFrame: DataFrame with the users information
        """

        try:
            self.users.to_sql("users", self.conn_sql, if_exists='replace', index=False)
        
        except Exception as e:
            print(f"Unable to load user information: {e}", flush=True)

        return self.users


    def read_email(self):
        """ Read the email information from a JSON file

        Args:
        - path (str, optional): Path.

        Returns:
        - dict: Dictionary with the email information
        """

        try:                
            self.email = pd.read_sql_query("SELECT * FROM email", self.conn_sql)

        except Exception as e:
            print(f"The email information could not be uploaded: {e}", flush=True)
            return self.email


    def save_email(self):
        """

        Args:
        - path (str, optional): Path to the csv file with the users information.

        Returns:
        - pd.DataFrame: DataFrame with the users information
        """

        try:
            self.email.to_sql("email", self.conn_sql, if_exists='replace', index=False)        
        except Exception as e:
            print(f"Unable to load user information: {e}", flush=True)

        
    def connect_data(self, path: str = "") -> None:
        """

        Args:
        - path (str, optional): Path to the DB file.

        Returns:
        - None
        """
        if path == "":
            path = self.path_data

        self.conn_sql = sqlite3.connect(path, check_same_thread=False)