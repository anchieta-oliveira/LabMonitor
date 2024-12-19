import os
import sys
import argparse as ap


parser = ap.ArgumentParser(description='Monitoramento de recurso de maquinas Linux em rede local e apresentação em Deshbord.',
                           formatter_class=ap.RawTextHelpFormatter )

parser.add_argument('-f','--file', help='Arquivo de configurações.')
parser.add_argument('-s', '--start', action='store_true', help='Start Deshbord.')
parser.add_argument('-sh', '--histoy', action='store_true', help='Salvar histórico das maquinas.')
args = parser.parse_args()

if args.start:
    try:
        script_path =  os.path.dirname(os.path.abspath(sys.argv[0]))
        os.system(f"streamlit run {script_path}/labmonitor/deshbord/main_page.py {script_path}")
        print("Streamlit iniciado. ")
    except Exception as e:
        print(f"Erro ao iniciar o Streamlit: {e}")