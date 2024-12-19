import paramiko


class Connection:
    def __init__(self, ip:str, username:str, password:str):
        self.ip = ip
        self.username = username
        self.password = password
        self.ssh = self.get_connection()


    def set_connection(self, ip:str, username:str, password:str):
        self.ip = ip
        self.username = username
        self.password = password

    def get_connection(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ip, username=self.username, password=self.password, timeout=10, look_for_keys=False, allow_agent=False)
            self.ssh = ssh
        except Exception as e:
            raise RuntimeError(f"Erro na conexão: {e}")
        
        return ssh
    
    def execute_ssh_command(self, command):
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            return stdout.read().decode().strip()
        except Exception as e:
            raise RuntimeError(f"Erro ao executar comando '{command}': {e}")