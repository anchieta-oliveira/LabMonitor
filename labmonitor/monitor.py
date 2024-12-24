from labmonitor.connection import Connection

class Monitor:
    def __init__(self, connection:Connection):
        self.connection = connection
    
    def get_usage_cpu(self):
        cpu_usage = float(self.connection.execute_ssh_command("top -bn1 | grep -i 'Cpu(s)' | awk '{print $2+$4}'").replace(',', '.'))
        return {"cpu_info": {"cpu_usage_percentage": cpu_usage}}

    def get_usage_gpu(self):
        gpu_info = []
        gpu_output = self.connection.execute_ssh_command("nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits")
        gpu_lines = gpu_output.split("\n")
        gpu_process_output = self.connection.execute_ssh_command("nvidia-smi --query-compute-apps=pid,name,gpu_name --format=csv,noheader,nounits").split("\n")

        if gpu_process_output[0] != "": 
            pids, process, gnames = zip(*[p.split(",") for p in gpu_process_output])
            gpu_users = [self.connection.execute_ssh_command(f"ps -p {pid} -o user --no-headers") if pid != "[N/A]" else "null" for pid in pids]
        else: 
            gpu_users =  ["null"] * len(gpu_lines);  process = ["null"] * len(gpu_lines)

        if len(gpu_lines) != len(gpu_users):
            name_to_user_process = {gnames[i]: (gpu_users[i], process[i]) for i in range(len(gnames))}
            gpu_users_new = ["null"] * len(gpu_lines)
            process_new = ["null"] * len(gpu_lines)
            for l, gpu in enumerate(gpu_lines):
                gpu_name = gpu.split(",")[1]
                if gpu_name in name_to_user_process:
                    gpu_users_new[l], process_new[l] = name_to_user_process[gpu_name]

            gpu_users, process = gpu_users_new, process_new

        for i, line in enumerate(gpu_lines):
            try:
                gpu_index, name, mem_used, mem_total, gpu_util = line.split(", ")
                gpu_info.append({
                    "gpu_index": int(gpu_index),
                    "name": name,
                    "memory_used": float(mem_used) / 1024,
                    "memory_total": float(mem_total) / 1024,
                    "utilization_gpu": gpu_util,
                    "process": process[i],
                    'user': gpu_users[i],
                })
            except Exception as e:
                print(f"Erro GPU {line}\n{e}")
                
        return {"gpu_info": gpu_info}

    def get_usage_ram(self):
        ram_command = "free -g | awk '/^Mem/ {print $3, $4, $2}'"
        ram_data = self.connection.execute_ssh_command(ram_command).split()
        ram_used = float(ram_data[0])
        ram_free = float(ram_data[1])
        total_ram = float(ram_data[2])

        return {
            "ram_info": {
                "ram_used": ram_used,
                "ram_free": ram_free,
                "total_ram": total_ram
            }
        }
    

    def get_usage_disk(self):
        disk_command = "df -h --output=target,size,used,avail,pcent"
        disk_output = self.connection.execute_ssh_command(disk_command)
        lines = disk_output.split("\n")
        disk_info = []
        for line in lines[1:]:
            values = line.split()
            if len(values) >= 5 and not "snap" in values[0] and not "run" in values[0] and not "dev" in values[0] and not "tmp" in values[0] and not "boot" in values[0] and not "var" in values[0] and not "sys" in values[0]:
                disk_info.append({
                    "mount_point": values[0],
                    "total_size": values[1],
                    "used": values[2],
                    "available": values[3],
                    "usage_percentage": values[4]
                })
                
        return {"disk_info": disk_info}


    def get_users(self):
        result = {}
        users_command = "awk -F: '$3 >= 1000 && $3 < 65534 {print $1}' /etc/passwd"
        users_output = self.connection.execute_ssh_command(users_command)
        users = users_output.split()
        grups = list(map(lambda u: self.connection.execute_ssh_command(f"groups {u}").split()[2:], users))
        for u, g in zip(users, grups): result[u]=g
        return result

    def add_new_user(self, username, password, sudo_password):
        new_user_cmd = f"""
                        echo '{sudo_password}' | sudo -S useradd -m {username} && \
                        echo '{password}:{password}' | sudo -S chpasswd"""
        useradd_output = self.connection.execute_ssh_command(new_user_cmd)
        return useradd_output

    def add_sudo_grup(self, username, sudo_password):
        sudo_user_cmd = f"""echo '{sudo_password}' | sudo -S usermod -aG sudo {username}"""
        addsudo_output = self.connection.execute_ssh_command(sudo_user_cmd)
        return addsudo_output

    def remove_sudo_grup(self, username, sudo_password):
        sudo_user_cmd = f"echo '{sudo_password}' | sudo -S deluser {username} sudo"
        removesudo_output = self.connection.execute_ssh_command(sudo_user_cmd)
        return removesudo_output

    def remove_user(self, username, sudo_password):
        remove_cmd = f"echo '{sudo_password}' | sudo -S userdel -r {username}"
        remove_output = self.connection.execute_ssh_command(remove_cmd)
        return remove_output

    def logged_users(self):
        res = []
        w_cmd = f"w -h"
        w_output = self.connection.execute_ssh_command(w_cmd)
        line = w_output.split("\n")
        try: 
            for usr in line:
                info = usr.split()
                res.append(
                        {
                            'user': info[0],
                            'TTY': info[1],
                            'from': info[2],
                            'login_time': info[3],
                            'jcpu': info[5],
                        })
        except Exception as e:
            res.append({'user': "", 'TTY': "", 'from': "", 'login_time':"", 'jcpu': "",})
            print(f"Erro: {e}")
            return {'logged_users': res}
        
        return {'logged_users': res}
        

