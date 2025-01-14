""" Labmonitor

Linux monitoring tool for local network machines and presentation in Dashbord.
"""

# Imports
############################################################################################################

import os
import sys
import argparse as ap
import multiprocessing

from labmonitor.queue_job import QueueJob


# Parser
############################################################################################################

# Create the parser
parser = ap.ArgumentParser(description='Monitoramento de recurso de maquinas Linux em rede local e apresentação em Dashbord.',
                           formatter_class=ap.RawTextHelpFormatter )

# Add the arguments
parser.add_argument('-f','--file', help='Arquivo de configurações.')
parser.add_argument('-s', '--start', action='store_true', help='Start Dashbord.')
parser.add_argument('-sh', '--histoy', action='store_true', help='Salvar histórico das maquinas.')
parser.add_argument('-sq', '--queue', action='store_true', help='Monitorar fila. ')
parser.add_argument('-sqj', '--queue_job', action='store_true', help='Monitorar fila de trabalho. ')
parser.add_argument('-ph','--path_history', default=os.path.dirname(os.path.abspath(__file__)), help='Arquivo de configurações.')

# Execute the parse_args() method
args = parser.parse_args()

# If the history argument is passed
if args.histoy:
    from labmonitor.monitor_history import exec_monitor_history

    # Start the process
    p = multiprocessing.Process(target=exec_monitor_history, args=(args.path_history,))
    p.start()

# If the queue argument is passed
if args.queue:

    from labmonitor.queue import Queue
    from labmonitor.data import Data

    # Create the data object
    data = Data()

    # Set the queue 
    q = Queue(data=data)

    # Start the process
    pq = multiprocessing.Process(target=q.monitor)
    pq.start()

# If the queue_job argument is passed
if args.queue_job:
    from labmonitor.queue import Queue
    from labmonitor.data import Data

    # Create the data object
    data = Data()

    #Set the path of the machines xlsx file
    data.path_machines = "machines_job.xlsx"
    data.read_machines("machines_job.xlsx")
    q = QueueJob(data=data)
    pq = multiprocessing.Process(target=q.monitor)
    pq.start()

# If the start argument is passed
if args.start:
    try:
        # Get the path of the script
        script_path =  os.path.dirname(os.path.abspath(sys.argv[0]))

        # Start the streamlit
        os.system(f"streamlit run {script_path}/labmonitor/dashboard/main_page.py {script_path}")
        print("Streamlit iniciado. ")
    except Exception as e:
        print(f"Erro ao iniciar o Streamlit: {e}")