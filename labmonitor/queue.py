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
        else:
            self.reset()
        return self.df

    def reset(self) -> pd.DataFrame:
        columns = ["ip", "name", "username", "inicio", "fim", "n_cpu", "gpu_index", "gpu_name", "e-mail"]
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
            "e-mail": email
        }
        self.df = pd.concat([self.df, pd.DataFrame([new_entry])], ignore_index=True)
        self.df.to_excel(self.path, index=False)
        if to_send: self.__send_mail(subject=f"Agendamento Máquinas LMDM - {username}", message=str(new_entry), to=email)
        
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
