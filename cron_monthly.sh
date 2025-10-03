#!/bin/bash

# Script para ejecución mensual del procesamiento de comparendos
# Se ejecuta para hacer el barrido completo de la base de datos por lotes

cd .../comparendos
source venv/bin/activate

# Crear directorio de logs si no existe
mkdir -p logs

# Ejecutar el script mensual
python main.py monthly >> logs/cron_monthly_$(date +%Y-%m-%d_%H-%M-%S).log 2>&1