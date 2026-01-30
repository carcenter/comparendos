#!/bin/bash

# Script para ejecución mensual del procesamiento de comparendos
# Se ejecuta DIARIAMENTE para procesar lotes de clientes antiguos
# El día 1 del mes reinicia desde offset 0
# Los demás días continúa desde donde quedó hasta terminar todos los registros

cd .../comparendos
source venv/bin/activate

# Crear directorio de logs si no existe
mkdir -p logs

# Ejecutar el script mensual
python main.py monthly >> logs/cron_monthly_$(date +%Y-%m-%d_%H-%M-%S).log 2>&1