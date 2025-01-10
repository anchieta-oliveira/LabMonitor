# Verifique a versão. Seu script python podem chamar outros programas, verifique os requisitos.
conda create -n seu_ambiente python=3.12 numpy pandas tensorflow

# ative seu ambiente 
conda activate seu_ambiente

# Execute seus comandos. Exemplo, script em python. 
python3.12 pca.py

# Desative seu ambiente conda. 
conda deactivate
