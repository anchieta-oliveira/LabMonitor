echo "Executando a etapa de minimização..."
/opt/NAMD_2.14_Linux-x86_64-multicore-CUDA/namd2 mini.conf +p 6 +devices 0 > mini.log &&

echo "Executando a etapa de aquecimento..."
/opt/NAMD_2.14_Linux-x86_64-multicore-CUDA/namd2 ann.conf +p 6 +devices 0 > ann.log &&

echo "Executando a etapa de equilibração..."
/opt/NAMD_3.0alpha13_Linux-x86_64-multicore-CUDA/namd3 equi.conf +p 4 +devices 0 > equi.log &&

echo "Executando a etapa de produção..."
/opt/NAMD_3.0alpha13_Linux-x86_64-multicore-CUDA/namd3 md.conf +p 4 +devices 0 > md.log &&
