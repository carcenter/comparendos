#!/bin/bash

# Script para ejecución diaria del procesamiento de comparendos
# Se ejecuta para procesar solo los clientes registrados en el día
# Uso: ./cron_daily.sh [fecha_opcional]

cd .../comparendos
source venv/bin/activate

# Crear directorio de logs si no existe
mkdir -p logs

# Si se pasa una fecha como parámetro, usarla; sino procesar el día actual
if [ $# -eq 1 ]; then
    FECHA=$1
    echo "Procesando fecha específica: $FECHA"
    python main.py daily $FECHA >> logs/cron_daily_${FECHA}_$(date +%H-%M-%S).log 2>&1
else
    echo "Procesando día actual: $(date +%Y-%m-%d)"
    python main.py daily >> logs/cron_daily_$(date +%Y-%m-%d_%H-%M-%S).log 2>&1
fi