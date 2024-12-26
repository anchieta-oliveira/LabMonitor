import os
import sys
import argparse as ap
import multiprocessing




parser = ap.ArgumentParser(description='Monitoramento de recurso de maquinas Linux em rede local e apresentação em Deshbord.',
                           formatter_class=ap.RawTextHelpFormatter )

parser.add_argument('-f','--file', help='Arquivo de configurações.')
parser.add_argument('-s', '--start', action='store_true', help='Start Deshbord.')
parser.add_argument('-sh', '--histoy', action='store_true', help='Salvar histórico das maquinas.')
parser.add_argument('-sq', '--queue', action='store_true', help='Monitorar fila. ')
parser.add_argument('-ph','--path_history', default=os.path.dirname(os.path.abspath(__file__)), help='Arquivo de configurações.')
args = parser.parse_args()

if args.histoy:
    from labmonitor.monitor_history import exec_monitor_history
    p = multiprocessing.Process(target=exec_monitor_history, args=(args.path_history,))
    p.start()

if args.queue:
    from labmonitor.queue import Queue
    from labmonitor.data import Data
    data = Data()
    q = Queue(data=data)
    pq = multiprocessing.Process(target=q.monitor)
    pq.start()


if args.start:
    try:
        script_path =  os.path.dirname(os.path.abspath(sys.argv[0]))
        os.system(f"streamlit run {script_path}/labmonitor/deshbord/main_page.py {script_path}")
        print("Streamlit iniciado. ")
    except Exception as e:
        print(f"Erro ao iniciar o Streamlit: {e}")