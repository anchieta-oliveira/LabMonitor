from datetime import datetime
import os
import smtplib
import pandas as pd
from labmonitor.data import Data
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Queue:
    def __init__(self, data:Data, path:str="queue.xlsx"):
        self.df = self.read_excel(path)
        self.path = path
        self.data = data
        self.machines = data.machines

    def read_excel(self, path:str="queue.xlsx") -> pd.DataFrame:
        if os.path.exists(path):
            self.df = pd.read_excel(path)
            self.df['fim'] = self.df['fim'] = pd.to_datetime(self.df['fim'])
            self.df['inicio'] = self.df['inicio'] = pd.to_datetime(self.df['inicio'])
        else:
            self.reset()
        return self.df

    def reset(self) -> pd.DataFrame:
        columns = ["ip", "name", "username", "status", "inicio", "fim", "n_cpu", "gpu_name", "gpu_index", "e-mail", "notification_last_day"]
        self.df = pd.DataFrame(columns=columns)
        self.df.to_excel("queue.xlsx", index=False)
        return self.df

    def insert(self, ip:str, name:str, username:str, inicio:str, fim:str, n_cpu:int, gpu_index:int, gpu_name:str, email:str, to_send:bool=True) -> pd.DataFrame:
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
            "notification_last_day": "N"
        }
        self.df = pd.concat([self.df, pd.DataFrame([new_entry])], ignore_index=True)
        self.df.to_excel(self.path, index=False)
        if to_send: self.__send_mail(subject=f"Agendamento Máquinas LMDM - {username}", message=str(new_entry), to=email)
        
        return self.df


    def remove(self, index:int, to_send:bool=False):
        self.df = self.df.drop(index=index)
        self.df.to_excel(self.path, index=False)
        if to_send: self.__send_mail(subject=f"Agendamento Máquinas LMDM", message=str("new_entry"), to=self.df['e-mail'].iloc[index])


    def update_status(self):
        data_atual = datetime.now()
        self.df['status'] = self.df.apply(lambda row: 
                                "Executando" if row['inicio'] <= data_atual and row['fim'] >= data_atual else 
                                "Em espera" if row['inicio'] > data_atual else 
                                "Finalizado", axis=1)
        self.df.to_excel("queue.xlsx", index=False)
        return self.df
        

    def __send_mail(self, subject:str, message:str, to:str):
        msg = MIMEMultipart()
        # setup the parameters of the message
        self.data.read_email()
        password = self.data.email['password'] # a senha tem que ser gerada https://www.emailsupport.us/blog/gmail-smtp-not-working/
        msg['From'] = self.data.email['address'] 
        msg['To'] = to
        msg['Subject'] = subject
        
        # add in the message body
        msg.attach(MIMEText(message, 'plain'))
        
        #create server
        server = smtplib.SMTP('smtp.gmail.com: 587')
        
        server.starttls()
        
        # Login Credentials for sending the mail
        server.login(msg['From'], password)
    
        # send the message via the server.
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
        print ("successfully sent email")
