from datetime import datetime
import os
import smtplib
import time
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

    def save(self):
        self.df.to_excel(self.path, index=False)

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
        
    def __last_day(self) -> pd.DataFrame:
        data_atual = datetime.now().date()
        return self.df[self.df['fim'].dt.date == data_atual]

    def __not_notified_last_day(self, df) -> pd.DataFrame:
        return df[df['notification_last_day'] == "N"]

    def monitor(self, last_day:bool=True, send_email:bool=True, feq_time:int=43200):
        while True:
            self.read_excel(self.path)
            self.update_status()
            if last_day: df_last = self.__last_day()
            if send_email: 
                send_last_day = self.__not_notified_last_day(df_last)
                r_email = [self.__send_mail(subject=f"Útlimo dia do seu agendamento - {e['name']}.", 
                                            message=self.__make_email_html(e, title="Agendamento"), 
                                            to=e['e-mail'], 
                                            subtype="html") 
                                            for i, e in send_last_day.iterrows()]
                
                for (_, e), r in zip(df_last.iterrows(), r_email): 
                    if r: self.df.loc[(self.df == e).all(axis=1), 'notification_last_day'] = "Y"
                    
            self.save()
            time.sleep(feq_time) 


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

    def __make_email_html(self, df_row: pd.Series, title: str = "Relatório"):
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
            </div>
        {self.__footer_mail()}
        </body>
    </html>"""

    def __send_mail(self, subject:str, message:str, to:str, subtype:str="plain") -> bool:
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
