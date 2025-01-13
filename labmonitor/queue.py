from datetime import datetime
import os
import smtplib
import time
import pandas as pd
from labmonitor.data import Data
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Queue:
    """
    A class to manage a queue of scheduled tasks for machines, including reading from and writing to
    an Excel file, updating task statuses, and sending email notifications.

    Attributes:
    df (pd.DataFrame): DataFrame holding the schedule of tasks with machine and user details.
    path (str): The file path for the Excel file storing the queue data.
    data (Data): An instance of the Data class that holds machine and email information.
    machines (list): List of machines available, fetched from the `data` instance.

    Methods:
        __init__(self, data: Data, path: str = "queue.xlsx"): 
            Initializes the Queue object, reads the Excel file, and stores the data.

        read_excel(self, path: str = "queue.xlsx") -> pd.DataFrame: 
            Reads the Excel file and returns the schedule data as a DataFrame.

        save(self): 
            Saves the current queue data (DataFrame) back to the Excel file.

        reset(self) -> pd.DataFrame: 
            Resets the queue to an empty DataFrame with predefined columns.

        insert(self, ip: str, name: str, username: str, inicio: str, fim: str, n_cpu: int, gpu_index: int, gpu_name: str, email: str, to_send: bool = True) -> pd.DataFrame: 
            Adds a new task to the queue and sends an email notification.

        remove(self, index: int, to_send: bool = True): 
            Removes a task from the queue by index and sends an email notification.

        update_status(self): 
            Updates the status of tasks based on their start and end times (e.g., "Executing", "Waiting", "Finished").
            
        __last_day(self) -> pd.DataFrame: 
            Filters the tasks that have an end date matching today's date.

        __fist_day(self) -> pd.DataFrame: 
            Filters the tasks that have a start date matching today's date.

        __not_notified_last_day(self, df) -> pd.DataFrame: 
            Filters the tasks that have not been notified for the last day.

        __not_notified_fist_day(self, df) -> pd.DataFrame: 
            Filters the tasks that have not been notified for the first day.

        __monitor_now(self, fist_day: bool = True, last_day: bool = True, send_email: bool = True): 
            Monitors tasks for the first or last day, and sends email notifications.

        monitor(self, fist_day: bool = True, last_day: bool = True, send_email: bool = True, feq_time: int = 43200, now: bool = False): 
            Periodically monitors tasks and sends email notifications based on user-defined frequency.

        __send_mail(self, subject: str, message: str, to: str, subtype: str = "plain") -> bool: 
            Sends an email with the provided subject, message, and recipient.
        """
    def __init__(self, data:Data, path:str="queue.xlsx"):
        self.df = self.read_excel(path)
        self.path = path
        self.data = data
        self.machines = data.machines

    def read_excel(self, path:str="queue.xlsx") -> pd.DataFrame:
        """
        Reads an Excel file and loads it into a pandas DataFrame.

        This method checks if the specified Excel file exists at the given `path`. If the file exists, 
        it reads the file into a pandas DataFrame, converts the 'fim' and 'inicio' columns to datetime objects, 
        and stores the result in the instance attribute `self.df`. If the file doesn't exist, it resets the DataFrame.

        Args:
        path (str): The file path of the Excel file to read. Defaults to 'queue.xlsx'.

        Returns:
        pd.DataFrame: The DataFrame containing the data from the Excel file.
        """
        if os.path.exists(path):
            self.df = pd.read_excel(path)
            self.df['fim'] = self.df['fim'] = pd.to_datetime(self.df['fim'])
            self.df['inicio'] = self.df['inicio'] = pd.to_datetime(self.df['inicio'])
        else:
            self.reset()
        return self.df

    def save(self):
        """
        Saves the current DataFrame to an Excel file.

        This method writes the DataFrame stored in `self.df` to an Excel file at the location specified by `self.path`.
        The index is not saved in the Excel file.

        Args:
        None

        Returns:
        None
        """
        self.df.to_excel(self.path, index=False)

    def reset(self) -> pd.DataFrame:
        """
        Resets the DataFrame to its initial structure and saves it to an Excel file.

        This method creates a new empty DataFrame with predefined column names and stores it in the instance attribute `self.df`.
        The DataFrame is then saved to an Excel file called 'queue.xlsx', with no index included in the file.

        Args:
        None

        Returns:
        pd.DataFrame: The newly created empty DataFrame with predefined columns.
        """
        columns = ["ip", "name", "username", "status", "inicio", "fim", "n_cpu", "gpu_name", "gpu_index", "e-mail", "notification_last_day", "notification_fist_day"]
        self.df = pd.DataFrame(columns=columns)
        self.df.to_excel("queue.xlsx", index=False)
        return self.df

    def insert(self, ip:str, name:str, username:str, inicio:str, fim:str, n_cpu:int, gpu_index:int, gpu_name:str, email:str, to_send:bool=True) -> pd.DataFrame:
        """
        Inserts a new entry into the DataFrame and saves it to an Excel file.

        This method creates a new entry with the provided information and appends it to the DataFrame (`self.df`). 
        After adding the new entry, the DataFrame is saved to an Excel file. If `to_send` is `True`, an email notification is sent 
        to the provided email address regarding the new entry.

        Args:
        ip (str): The IP address associated with the entry.
        name (str): The name associated with the entry.
        username (str): The username associated with the entry.
        inicio (str): The start time of the entry.
        fim (str): The end time of the entry.
        n_cpu (int): The number of CPUs for the entry.
        gpu_index (int): The GPU index for the entry.
        gpu_name (str): The name of the GPU for the entry.
        email (str): The email address to notify.
        to_send (bool): A flag indicating whether to send an email notification. Defaults to `True`.

        Returns:
        pd.DataFrame: The updated DataFrame with the new entry added.
        """
        new_entry = {
            "ip": ip,
            "name": name,
            "username": username,
            "inicio": inicio,
            "fim": fim,
            "n_cpu": n_cpu,
            "gpu_index": gpu_index,
            "gpu_name": gpu_name,
            "e-mail": email,
            "notification_last_day": "N",
            "notification_fist_day": "N",
        }
        self.df = pd.concat([self.df, pd.DataFrame([new_entry])], ignore_index=True)
        self.df.to_excel(self.path, index=False)
        if to_send: self.__send_mail(subject=f"Seu agendamento foi removido - {new_entry['name']}", message=self.__make_email_html(df_row=new_entry), to=new_entry['e-mail'], subtype="html")
        
        return self.df


    def remove(self, index:int, to_send:bool=True):
        """
        Removes an entry from the DataFrame and sends a notification email.

        This method removes the entry at the specified index from the DataFrame (`self.df`). After removing the entry, 
        the updated DataFrame is saved to an Excel file. If `to_send` is `True`, an email notification is sent 
        to the user regarding the removal of the entry.

        Args:
        index (int): The index of the entry to be removed from the DataFrame.
        to_send (bool): A flag indicating whether to send an email notification after removal. Defaults to `True`.

        Returns:
        None
        """
        e = self.df.iloc[index]
        self.df = self.df.drop(index=index)
        self.df.to_excel(self.path, index=False)
        if to_send: self.__send_mail(subject=f"Seu agendamento foi removido - {e['name']}", message=self.__make_email_html(df_row=e), to=e['e-mail'], subtype="html")


    def update_status(self):
        """
        Updates the status of each entry based on the current date and time.

        This method checks the 'inicio' (start time) and 'fim' (end time) of each entry in the DataFrame (`self.df`) 
        and updates the 'status' column. The status is set to:
        - "Executando" if the current date and time is between 'inicio' and 'fim'.
        - "Em espera" if the current date and time is before 'inicio'.
        - "Finalizado" if the current date and time is after 'fim'.
        
        After updating the status, the DataFrame is saved to an Excel file ("queue.xlsx").

        Args:
        None

        Returns:
        pd.DataFrame: The updated DataFrame with the new status for each entry.
        """
        data_atual = datetime.now()
        self.df['status'] = self.df.apply(lambda row: 
                                "Executando" if row['inicio'] <= data_atual and row['fim'] >= data_atual else 
                                "Em espera" if row['inicio'] > data_atual else 
                                "Finalizado", axis=1)
        self.df.to_excel("queue.xlsx", index=False)
        return self.df
        
    def __last_day(self) -> pd.DataFrame:
        """
        Retrieves entries that have the same 'fim' (end time) date as the current date.

        This method filters the DataFrame (`self.df`) and returns only the rows where the 'fim' (end time) 
        corresponds to the current date. It compares the date part of 'fim' with the current date.

        Args:
        None

        Returns:
        pd.DataFrame: A DataFrame containing only the entries where 'fim' matches the current date.
        """
        data_atual = datetime.now().date()
        return self.df[self.df['fim'].dt.date == data_atual]

    def __fist_day(self) -> pd.DataFrame:
        """
        Retrieves entries that have the same 'inicio' (start time) date as the current date.

        This method filters the DataFrame (`self.df`) and returns only the rows where the 'inicio' (start time) 
        corresponds to the current date. It compares the date part of 'inicio' with the current date.

        Args:
        None

        Returns:
        pd.DataFrame: A DataFrame containing only the entries where 'inicio' matches the current date.
        """
        data_atual = datetime.now().date()
        return self.df[self.df['inicio'].dt.date == data_atual]

    def __not_notified_last_day(self, df) -> pd.DataFrame:
        """
        Filters entries that have not been notified on the last day.

        This method filters the DataFrame (`df`) and returns only the rows where the 'notification_last_day' 
        column is equal to "N", indicating that the user has not been notified for the last day.

        Args:
        df (pd.DataFrame): The DataFrame to filter.

        Returns:
        pd.DataFrame: A DataFrame containing only the entries where 'notification_last_day' is "N".
        """
        return df[df['notification_last_day'] == "N"]

    def __not_notified_fist_day(self, df) -> pd.DataFrame:
        """
        Filters entries that have not been notified on the first day.

        This method filters the DataFrame (`df`) and returns only the rows where the 'notification_fist_day' 
        column is equal to "N", indicating that the user has not been notified for the first day.

        Args:
        df (pd.DataFrame): The DataFrame to filter.

        Returns:
        pd.DataFrame: A DataFrame containing only the entries where 'notification_fist_day' is "N".
        """
        return df[df['notification_fist_day'] == "N"]


    def __monitor_now(self, fist_day:bool=True, last_day:bool=True, send_email:bool=True):
        """
        Monitors and sends email notifications for users whose scheduling is starting or ending on the current day.

        This method performs the following actions:
        - Reads the Excel file containing scheduling information.
        - Updates the status of each entry based on the current date.
        - If `last_day` is True, it checks for entries where the 'fim' (end time) is the current date and sends a notification email to those users who have not been notified yet.
        - If `fist_day` is True, it checks for entries where the 'inicio' (start time) is the current date and sends a notification email to those users who have not been notified yet.
        - After sending the emails, the method updates the 'notification_last_day' and 'notification_fist_day' columns accordingly to mark that the notifications have been sent.

        Args:
        fist_day (bool): A flag indicating whether to send emails for entries starting today. Defaults to True.
        last_day (bool): A flag indicating whether to send emails for entries ending today. Defaults to True.
        send_email (bool): A flag indicating whether to send the emails. Defaults to True.

        Returns:
        None
        """
        self.read_excel(self.path)
        self.update_status()
        if last_day: df_last = self.__last_day()
        if fist_day: df_fist = self.__fist_day()

        if send_email and last_day: 
            send_last_day = self.__not_notified_last_day(df_last)
            r_email = [self.__send_mail(subject=f"Útlimo dia do seu agendamento - {e['name']}.", 
                                        message=self.__make_email_html(e, title="Agendamento Máquinas LMDM",
                                                                       observation="Caso deseje continuar usando os recursos da máquina, lembre de agendar no sistema. Muito obrigado."), 
                                        to=e['e-mail'], 
                                        subtype="html") 
                                        for i, e in send_last_day.iterrows()]
            
            for (_, e), r in zip(send_last_day.iterrows(), r_email): 
                if r: self.df.loc[(self.df == e).all(axis=1), 'notification_last_day'] = "Y"

        if send_email and fist_day: 
                send_fist_day = self.__not_notified_fist_day(df_fist)
                r_email = [self.__send_mail(subject=f"Seu agendamento começa hoje - {e['name']}.", 
                                            message=self.__make_email_html(e, title="Agendamento Máquinas LMDM", 
                                                                           observation="Em caso de desistência lembre de cancelar no sistema. Muito obrigado."), 
                                            to=e['e-mail'], 
                                            subtype="html") 
                                            for i, e in send_fist_day.iterrows()]
                
                for (_, e), r in zip(send_fist_day.iterrows(), r_email): 
                    if r: self.df.loc[(self.df == e).all(axis=1), 'notification_fist_day'] = "Y"
        self.save()


    def monitor(self, fist_day:bool=True, last_day:bool=True, send_email:bool=True, feq_time:int=43200, now:bool=False):
        """
        Monitors and sends notifications about scheduling events, checking at regular intervals.

        This method monitors scheduling data and sends notifications for users whose schedules are starting 
        or ending on the current day. It can run continuously, checking at specified intervals, or execute only 
        once based on the `now` parameter.

        - If `now` is False, it will repeatedly check and send notifications at the specified frequency (`feq_time`).
        - If `now` is True, it will run a single check and notification process.

        Args:
        fist_day (bool): A flag indicating whether to send notifications for entries starting today. Defaults to True.
        last_day (bool): A flag indicating whether to send notifications for entries ending today. Defaults to True.
        send_email (bool): A flag indicating whether to send the notifications via email. Defaults to True.
        feq_time (int): The time interval (in seconds) between checks when `now` is False. Defaults to 43200 (12 hours).
        now (bool): A flag to specify whether to run the check once or continuously. Defaults to False (continuous check).

        Returns:
        None
        """
        while not now:
            self.__monitor_now(fist_day=fist_day, last_day=last_day, send_email=send_email)
            time.sleep(feq_time)
        else:
            self.__monitor_now(fist_day=fist_day, last_day=last_day, send_email=send_email)


    def __head_mail(self) -> str:
        return """<head>
            <style>
                body { font-family: Arial, sans-serif; }
                .header {
                    background-color: #A8D08D; /* verde claro */
                    color: white;
                    padding: 10px 0;
                    text-align: center;
                }
                .container {
                    margin: 20px;
                }
                .table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }
                .table th, .table td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }
                .table th {
                    background-color: #f2f2f2;
                }
                .footer {
                    margin-top: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                }
            </style>
            <div class="header">
                <span style="font-size: 24px; font-weight: bold; margin-left: 10px;">Laboratório de Modelagem e Dinâmica Molecular</span>
            </div>
        </head>"""

    def __footer_mail(self) -> str:
        return """<div class="footer">
            <p>Este é um e-mail automático. Por favor, não responda.</p>
        </div>"""

    def __make_email_html(self, df_row: pd.Series, title: str = "Agendamento", observation:str=""):
        return f"""<html>
        {self.__head_mail()}
        <body>
            <div class="container">
                <h2>{title}</h2>
                <table class="table">
                    <tr>
                        <th>Nome</th>
                        <td>{df_row['name']}</td>
                    </tr>
                    <tr>
                        <th>Usuário</th>
                        <td>{df_row['username']}</td>
                    </tr>
                    <tr>
                        <th>Status</th>
                        <td>{df_row['status']}</td>
                    </tr>
                    <tr>
                        <th>Início</th>
                        <td>{df_row['inicio']}</td>
                    </tr>
                    <tr>
                        <th>Fim</th>
                        <td>{df_row['fim']}</td>
                    </tr>
                    <tr>
                        <th>CPU</th>
                        <td>{df_row['n_cpu']}</td>
                    </tr>
                    <tr>
                        <th>GPU</th>
                        <td>{df_row['gpu_name']} (Índice {df_row['gpu_index']})</td>
                    </tr>
                </table>
                {f'''
                <div class="observation">
                    <h3>Observações</h3>
                    <p>{observation}</p>
                </div>
                ''' if observation else ''}
            </div>
        {self.__footer_mail()}
        </body>
    </html>"""

    def __send_mail(self, subject:str, message:str, to:str, subtype:str="plain") -> bool:
        """
        Sends an email with the specified subject and message to a recipient.

        This method sends an email using Gmail's SMTP server. It requires an email address and password 
        (which should be an app-specific password generated for Gmail). The method creates a multipart 
        email message with the provided subject and body and then sends it to the specified recipient.

        Args:
        subject (str): The subject of the email.
        message (str): The body content of the email.
        to (str): The recipient's email address.
        subtype (str): The subtype of the email (either 'plain' or 'html'). Defaults to 'plain'.

        Returns:
        bool: True if the email was successfully sent, False otherwise.
        """
        try:
            msg = MIMEMultipart()
            # setup the parameters of the message
            self.data.read_email()
            password = self.data.email['password'] # a senha tem que ser gerada https://www.emailsupport.us/blog/gmail-smtp-not-working/
            msg['From'] = self.data.email['address'] 
            msg['To'] = to
            msg['Subject'] = subject
            
            # add in the message body
            msg.attach(MIMEText(message, subtype))
            
            #create server
            server = smtplib.SMTP('smtp.gmail.com: 587')
            
            server.starttls()
            
            # Login Credentials for sending the mail
            server.login(msg['From'], password)
        
            # send the message via the server.
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.quit()
            print (f"Successfully sent email {to}")
            return True
        except Exception as e: 
            print(f"Erro a enviar e-mail: {e}")
            return False
