from labmonitor.connection import Connection

class Monitor:
    def __init__(self, connection:Connection):
        self.connection = connection
    
    def get_usage_cpu(self):
        cpu_usage = float(self.connection.execute_ssh_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}'").replace(',', '.'))
        return {"cpu_info": {"cpu_usage_percentage": cpu_usage}}

    def get_usage_gpu(self):
        gpu_info = []
        gpu_output = self.connection.execute_ssh_command("nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits")
        for line in gpu_output.split("\n"):
            gpu_index, name, mem_used, mem_total, gpu_util = line.split(", ")
            gpu_info.append({
                "gpu_index": int(gpu_index),
                "name": name,
                "memory_used": float(mem_used) / 1024,
                "memory_total": float(mem_total) / 1024,
                "utilization_gpu": gpu_util
            })
        return {"gpu_info": gpu_info}

    def get_usage_ram(self):
        ram_command = "top -bn1 -E g| grep 'Mem' | awk '{print $8, $4+$6}'"
        ram_data = self.connection.execute_ssh_command(ram_command).split()
        ram_free = float(ram_data[0].replace(',', '.')) 
        ram_used = float(ram_data[1].replace(',', '.')) - ram_free
        return {"ram_info": {
                            "ram_used": ram_used,
                            "ram_free": ram_free,
                            "total_ram": ram_used + ram_free}}
    

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
