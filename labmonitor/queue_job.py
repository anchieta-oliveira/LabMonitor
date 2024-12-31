import os
import time
import threading
import pandas as pd
from datetime import datetime
from labmonitor.data import Data
from labmonitor.monitor import Monitor
from labmonitor.connection import Connection
from concurrent.futures import ThreadPoolExecutor, as_completed



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
        columns = ["ip", "name", "username", "job_name", "status", "pid", "path_exc", "path_origin", "machine_origin", "script_name", "submit", "inicio", "fim", "n_cpu", "cpu_start", "cpu_end", "gpu_requested", "gpu_name", "gpu_index", "e-mail", "notification_start", "notification_end"]
        self.df = pd.DataFrame(columns=columns)
        self.df.to_excel("queue_job.xlsx", index=False)
        return self.df
    

    def submit(self, username:str, job_name:str, machine_origin:str, script_name:str, path_origin:str, n_cpu:int, email:str, gpus:list=['all']):
        new_job = {
            "username": username,
            "machine_origin": machine_origin,
            "job_name": job_name,
            "script_name": script_name,
            "path_origin": path_origin,
            "n_cpu": n_cpu,
            "e-mail": email,
            "gpu_requested": ",".join(gpus),
            "submit": datetime.now(),
            "notification_start": "N",
            "notification_end": "N",
        }

        self.df = pd.concat([self.df, pd.DataFrame([new_job])], ignore_index=True)
        self.save()
        print(self.df)

    

    def update_gpu(self):
        def run(ip, name, user, pw):
            try:
                print(f"Conectando a {ip}...")
                results = {}
                c = Connection(ip, user, pw)
                m = Monitor(c)
            except Exception as e:
                print(f"Erro ao conectar a {ip}: {e}")
                return name, None
            try:
                results.update(m.get_usage_gpu())
            except Exception as e:
                results.update({"gpu_info": []})
                print(f"Erro ao obter informações de GPU de {ip}: {e}")
            return name, results
        
        ips = self.data.machines['ip'].to_list()
        names = self.data.machines['name'].to_list()
        usernames = self.data.machines['username'].to_list()
        passwords = self.data.machines['password'].to_list()

        results = {}

        with ThreadPoolExecutor(max_workers=len(ips)) as executor:
            futures = [
                executor.submit(run, ip, name, user, pw)
                for ip, name, user, pw in zip(ips, names, usernames, passwords)
            ]
            for future in as_completed(futures):
                name, stats = future.result()
                if stats:
                    results[name] = stats

        data_gpu = []
        for name, stats in results.items():
            row = {"name": name}
            for gpu in stats["gpu_info"]:
                gpu_index = gpu["gpu_index"]
                row[f"GPU_{gpu_index}_Name"] = gpu["name"]
                sts = ""
                if f"GPU_{gpu_index}_status" in self.data.machines.columns: 
                    if self.data.machines[self.data.machines['name'] == name][f"GPU_{gpu_index}_status"].iloc[0] != "": sts = self.data.machines[self.data.machines['name'] == name][f"GPU_{gpu_index}_status"].iloc[0]
                row[f"GPU_{gpu_index}_status"] = sts

            data_gpu.append(row)

        self.data.machines = pd.merge(self.machines[['ip','name', 'username', 'password', 'status', 'allowed_cpu','cpu_used', 'name_allowed_gpu', 'path_exc']], pd.DataFrame(data_gpu), on="name")
        self.data.save_machines()

    def __allowed_gpu(self):
        g_names = [e.split(",") for e in self.data.machines['name_allowed_gpu'].to_list()]
        col = self.data.machines.loc[:, self.data.machines.columns.str.contains(r"gpu_.*_name", case=False, regex=True)]

        for i, row in self.data.machines.iterrows():
            for c in col:
                for name in g_names[i]:
                    if name == self.data.machines[c].iloc[i]:
                        self.data.machines.loc[i, c.replace("Name", "status")] = "disponivel"
                    elif name != self.data.machines[c].iloc[i] and pd.isna(self.data.machines[c].iloc[i]): 
                        self.data.machines.loc[i, c.replace("Name", "status")] = "bloqueada"


    def __status_in_queue(self):
        v = self.df[self.df['status'] == "executando"]
        for i, maq in v.iterrows():
            self.data.machines.loc[
                    (self.data.machines['name'] == maq['name']) & 
                    (self.data.machines['ip'] == maq['ip']) & 
                    (self.data.machines[f"GPU_{int(maq['gpu_index'])}_Name"] == maq['gpu_name']),
                    f"GPU_{int(maq['gpu_index'])}_status"
                ] = "executando"
     

    def __update_cpu_used(self):
        v = self.df[self.df['status'] == "executando"]
        self.data.machines.loc[:,'cpu_used'] = 0
        for i, maq in v.iterrows():
            self.data.machines.loc[
                    (self.data.machines['name'] == maq['name']) & 
                    (self.data.machines['ip'] == maq['ip']),
                    "cpu_used"
                ] += maq['n_cpu']


    def update_status_machines(self):
        self.update_gpu()
        self.__allowed_gpu()
        self.__update_cpu_used()
        self.__status_in_queue()
        self.data.save_machines()


    def search_available_machine(self, n_cpu:int, gpu:bool = False, gpu_name:list = ["all"]):
        self.data.read_machines(self.data.path_machines)
    
        available_cpu = self.data.machines.loc[((self.data.machines['allowed_cpu'] - self.data.machines['cpu_used']) >= n_cpu)]
        
        if gpu:
            gpu_status_cols = self.data.machines.loc[:,self.data.machines.columns.str.contains(r"gpu.*status", case=False, regex=True)].columns
            gpu_name_cols = self.data.machines.loc[:,self.data.machines.columns.str.contains(r"gpu.*name", case=False, regex=True)].columns
            
            gpu_status_available = self.data.machines[gpu_status_cols].eq("disponivel").any(axis=1)

            if gpu_name[0] != "all": gpu_name_match = self.data.machines[gpu_name_cols].isin(gpu_name).any(axis=1) 
            else: gpu_name_match = self.data.machines[gpu_name_cols].any(axis=1) 
            
            filtered_machines = self.data.machines.loc[self.data.machines['name'].isin(available_cpu['name'].to_list()) &
                                                       gpu_status_available & 
                                                       gpu_name_match]
            return filtered_machines
        
        else:
            return available_cpu



    def update_status_jobs(self):
        for i, job in self.df.iterrows():
            if job['status'] == 'executando': self.df.loc[i, ['status', 'pid']] = self.get_status_job(job['name'], job['path_exc'])
            if pd.isna(job['status']): self.df.loc[i, ['status']] = 'esperando'
        self.save()


    def copy_dir(self, ip_origin, username_origin, password_origin, ip_exc, username_exc, password_exc, path_origin:str, path_exc:str, inverse:bool = False):
        try:
            print(f"Conectando a {ip_origin}...")
            c = Connection(ip_origin, username_origin, password_origin)
            if inverse: cmd = f""" dpkg -l | grep -qw sshpass || echo '{password_origin}' | sudo -S apt install -y sshpass & echo '{password_origin}' | sudo -S  sshpass -p '{password_exc}' scp -o StrictHostKeyChecking=no -r {username_exc}@{ip_exc}:{path_exc}/ {path_origin}/ && echo '{password_origin}' | sudo -S chmod 777 {path_origin}/{os.path.basename(os.path.normpath(path_exc))}"""
            else: cmd = f""" dpkg -l | grep -qw sshpass || echo '{password_origin}' | sudo -S apt install -y sshpass & echo '{password_origin}' | sudo -S  sshpass -p '{password_exc}' scp -o StrictHostKeyChecking=no -r {path_origin}/ {username_exc}@{ip_exc}:{path_exc} """
                
            c.execute_ssh_command(cmd)
            #if inverse: c.execute_ssh_command(f"echo '{password_origin}' | sudo -S chmod 777 {path_origin}/{os.path.basename(os.path.normpath(path_exc))}")
            c.ssh.close()
        except Exception as e:
            print(f"Erro ao conectar a {ip_origin}: {e}")

        
        
    def __make_script_exc(self, cpu_start:int, cpu_end:int, script:str, gpu_id:int=-1):
        return f"""
import os
import subprocess
with open("labmonitor.status", "w") as log: log.write("iniciado  - "+ str(os.getpid()))
if {gpu_id} == -1:
    pcs = subprocess.Popen(f"CUDA_VISIBLE_DEVICES= taskset -c {int(cpu_start)}-{int(cpu_end)} sh {script} > {script.split(".")[0]}.log", shell=True)
else:
    pcs = subprocess.Popen(f"CUDA_VISIBLE_DEVICES={gpu_id} taskset -c {int(cpu_start)}-{int(cpu_end)} sh {script} > {script.split(".")[0]}.log", shell=True)
with open("labmonitor.status", "w") as log: log.write("executando - "+ str(os.getpid()))
pcs.wait()
with open("labmonitor.status", "w") as log: log.write("finalizado_copiar - "+ str(os.getpid()))"""
    

    def prepare_job(self, machine_name:str, cpu_start:int, cpu_end:int, script:str, path_exc:str, gpu_id:int=-1):
        row = self.machines[self.machines['name'] == machine_name].iloc[0]
        try:
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            con.execute_ssh_command(f"echo '{self.__make_script_exc(cpu_start, cpu_end, script, gpu_id)}' > {path_exc}/run_labmonitor.py")
            print(f"Preparação concluída em {row['ip']} - {path_exc}")
        except Exception as e:
            print(f"Erro na conexão ao preparar trabalho (srcipt run_labmonitor.py): {e}")


    def get_status_job(self, machine_name:str, path_exc:str):
        row = self.machines[self.machines['name'] == machine_name].iloc[0]
        try:
            print(f"Verificando status do job em {row['ip']}")
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            status, pid = con.execute_ssh_command(f"cat {path_exc}/labmonitor.status").split('-')
            if (not pid in con.execute_ssh_command(f"ps -p {pid}")) and (status.strip() == 'executando'): status = "nao_finalizado_corretamente"; con.execute_ssh_command(f"echo '{status} - {pid}' > {path_exc}/labmonitor.status")
            con.ssh.close()
            return status.strip(), int(pid)
        except Exception as e:
            print(f"Erro ao verificar status do job: {e}")
            return "", -1


    def star_job(self, machine_name:str, path_exc:str)  -> int:
        row = self.machines[self.machines['name'] == machine_name].iloc[0]
        try:
            print(f"Iniciando trabalho em {row['ip']}")
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            ch = con.ssh.get_transport().open_session()
            ch.exec_command(f"cd {path_exc} && nohup python3 run_labmonitor.py >  run_labmonitor.log &")
            time.sleep(0.1)
            _, pid = con.execute_ssh_command(f"cat {path_exc}/labmonitor.status").split("-")
            ch.close()
            con.ssh.close()
            return int(pid)
        except Exception as e:
            print(f"Erro a iniciar trabalho {row['ip']} {path_exc}: {e}")
            return -1
    

    def __make_dir_exc(self, machine_exc:str, dir_exc:str):
        row = self.machines[self.machines['name'] == machine_exc].iloc[0]
        try:
            print(f"Conectando a {row['ip']}...")
            con = Connection(ip=row['ip'], username=row['username'], password=row['password'])
            con.execute_ssh_command(f"mkdir {dir_exc}")
            print(f"mkdir {dir_exc}")
            return True
        except Exception as e:
            print(f"Erro ao conectar a para criar dir_exec {row['ip']}: {e}")
            return False
    

    def __esperando(self, index:int):
        n_cpu=self.df.loc[index, 'n_cpu']
        gpu = not pd.isna(self.df.loc[index, 'gpu_requested'])
        if gpu: gpu_name = self.df.loc[index, 'gpu_requested'].split(",")
        else: gpu_name = ["all"]

        machines = self.search_available_machine(n_cpu=n_cpu,
                                      gpu=gpu,
                                      gpu_name=gpu_name
                                      )
        
        if machines.shape[0] > 0:
            machine = machines.iloc[0]
            self.df.loc[index, ['status']] = 'executando'
            self.df.loc[index, ['ip', 'name']] = machine[['ip', 'name']]

            # pegar start e and CPU e colocar na fila
            max_cpu_end = self.df.loc[(self.df['name'] == machine['name']) & (self.df['status'] == 'executando'), 'cpu_end'].max()
            self.df.loc[index, ['cpu_start', 'cpu_end']] = (max_cpu_end+1, n_cpu-1)
            if pd.isna(self.df.loc[index, 'cpu_start']): self.df.loc[index, 'cpu_start'] = 0

            # Atualziar CPUs ocupadas nas maquinas 
            self.data.machines.loc[self.data.machines['name'] == machine['name'], 'cpu_used'] += n_cpu

            if gpu:
                # Pegar GPU e Index na fila de trabalho
                gpu_status_cols = machines.loc[0:,machines.columns.str.contains(r"gpu.*status", case=False, regex=True)].columns
                gpu_name_cols = machines.loc[0:,machines.columns.str.contains(r"gpu.*name", case=False, regex=True)].columns
                for n, s in zip(gpu_name_cols, gpu_status_cols):
                    gpu_index = n.split('_')[1]
                    if "disponivel" == machine[s] and (machine[n] in gpu_name or "all" in gpu_name):
                        self.df.loc[index, ['gpu_name', 'gpu_index']] = (machine[n], gpu_index)
                        # Atualizar status da GPU nas maquinas
                        self.data.machines.loc[self.data.machines['name'] == machine['name'], s] = "executando"
            
            # Criar pasta na maquina exc com username_datasubmit
            self.__make_dir_exc(machine_exc=machine['name'], dir_exc=f"{machine['path_exc']}/{self.df.loc[index, 'username']}_{self.df.loc[index, 'submit'].strftime('%m_%d_%Y_%I-%M-%S')}/")

            # Atualizar diretorio exc 
            self.df.loc[index, ['path_exc']] = f"{machine['path_exc']}/{self.df.loc[index, 'username']}_{self.df.loc[index, 'submit'].strftime('%m_%d_%Y_%I-%M-%S')}/{os.path.basename(os.path.normpath(self.df.loc[index, 'path_origin']))}/"
    
            # Copiar arquivos 
            data_machines_origin = Data(); data_machines_origin.read_machines()
            
            self.copy_dir(ip_origin=data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'ip'].iloc[0],
                          username_origin=data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'username'].iloc[0],
                          password_origin=data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'password'].iloc[0],
                          path_origin=self.df.loc[index, 'path_origin'],
                          
                          ip_exc=self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'ip'].iloc[0],
                          username_exc=self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'username'].iloc[0],
                          password_exc=self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'password'].iloc[0],
                          path_exc=self.df.loc[index, 'path_exc']
                          )

            # Iniciar trabalho
            self.prepare_job(machine_name=machine['name'], 
                            cpu_start=self.df.loc[index, 'cpu_start'], 
                            cpu_end=self.df.loc[index, 'cpu_end'], 
                            script=self.df.loc[index, 'script_name'],
                            path_exc=self.df.loc[index, 'path_exc'],
                            gpu_id=self.df.loc[index, 'gpu_index']
                            )

            pid = self.star_job(machine_name=machine['name'], path_exc=self.df.loc[index, 'path_exc'])
            self.df.loc[index, ['pid']] = pid

            self.data.save_machines() 
            self.save()
            

    def __finalizado_copiar(self, index:int):
        def subp_copy():
            data_machines_origin = Data(); data_machines_origin.read_machines()
            ip_exc = self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'ip'].iloc[0]
            username_exc = self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'username'].iloc[0]
            password_exc = self.data.machines.loc[self.data.machines['name'] == self.df.loc[index, 'name'], 'password'].iloc[0]
            path_exc = self.df.loc[index, 'path_exc']
            copiar = False
            copiado = False

            try:
                print(f"Atualziando status copiando {ip_exc}")
                con = Connection(ip=ip_exc,
                                username=username_exc, 
                                password=password_exc)
                
                _, pid = con.execute_ssh_command(f"cat {path_exc}/labmonitor.status").split('-')
                con.execute_ssh_command(f"echo 'copiando - {pid}' > {path_exc}/labmonitor.status")
                con.ssh.close()
                self.df.loc[index, ['status']] = 'copiando'; self.save()
                copiar = True
            except Exception as e:
                print(f"Erro ao atualizar status do job p/ copiando: {e}")

            if copiar:
                try:
                    self.copy_dir(ip_origin=data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'ip'].iloc[0],
                        username_origin=data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'username'].iloc[0],
                        password_origin=data_machines_origin.machines.loc[data_machines_origin.machines['name'] == self.df.loc[index, 'machine_origin'], 'password'].iloc[0],
                        path_origin=self.df.loc[index, 'path_origin'],
                        
                        ip_exc=ip_exc,
                        username_exc=username_exc,
                        password_exc=password_exc,
                        path_exc=path_exc,
                        inverse=True
                        )
                    copiado = True
                    
                except Exception as e:
                    print(f'Erro ao copiar arquivos de exc para origin {ip_exc}: {e}')
            
            if copiado:
                cmd = f"echo 'finalizado - {pid}' > {path_exc}/labmonitor.status"
                self.df.loc[index, ['status']] = 'finalizado'; self.save()
                
            else:
                cmd = f"echo 'falha_ao_copiar - {pid}' > {path_exc}/labmonitor.status"
                self.df.loc[index, ['status']] = 'falha_ao_copiar'; self.save()
            try:
                print(f"Atualziando status final de copia (falha_ao_copiar ou finalizado - {copiado}) {ip_exc}")
                con = Connection(ip=ip_exc,
                                username=username_exc, 
                                password=password_exc)
                con.execute_ssh_command(cmd)
                con.ssh.close()
            except Exception as e:
                print(f"Erro ao atualizar status do job p/ finalizado: {e}")
                

        proc = threading.Thread(target=subp_copy)
        proc.start()
        
        



    def __executando(self, index:int):
        pass

    def __finalizado(self, index:int):
        pass

    def __nao_finalizado_corretamente(self, index):
        pass

    def __monitor_now(self):
        action = {'esperando': self.__esperando, "finalizado_copiar": self.__finalizado_copiar,"executando": self.__executando, "finalizado": self.__finalizado, "nao_finalizado_corretamente": self.__nao_finalizado_corretamente}
        self.read_excel()
        self.update_status_machines()
        self.update_status_jobs()
        print(self.df)
        
        for i, row in self.df.iterrows():
            action[row['status']](index=i)



    def monitor(self, fist_day:bool=True, last_day:bool=True, send_email:bool=True, feq_time:int=20, now:bool=False):
        while not now:
            print(f"Monitorando inicio: {datetime.now()}")

            self.__monitor_now()
            
            print(f"Monitorando fim: {datetime.now()}")
            time.sleep(feq_time)
        else:
            self.__monitor_now()