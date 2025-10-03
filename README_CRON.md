# Guía de Configuración de Cron Jobs

## Scripts Creados

### 1. Ejecución Diaria (`cron_daily.sh`)
- **Propósito**: Procesa solo los clientes registrados en el día actual o fecha específica
- **Comando**: `python main.py daily [fecha_opcional]`
- **Logs**: `logs/cron_daily_YYYY-MM-DD_HH-MM-SS.log`
- **Uso**: `./cron_daily.sh` o `./cron_daily.sh 2025-10-01`

### 2. Ejecución Mensual (`cron_monthly.sh`)
- **Propósito**: Hace el barrido completo de la base de datos por lotes
- **Comando**: `python main.py monthly`
- **Logs**: `logs/cron_monthly_YYYY-MM-DD_HH-MM-SS.log`

## Instalación de Cron Jobs

1. **Instalar los cron jobs**:
   ```bash
   crontab cron_config.txt
   ```

2. **Verificar instalación**:
   ```bash
   crontab -l
   ```

3. **Ver logs del cron**:
   ```bash
   sudo tail -f /var/log/syslog | grep cron
   ```

## Horarios Configurados

- **Diario**: 8:00 AM todos los días (procesa clientes del día)
- **Mensual**: 5:00 AM del día 1 al 15 de cada mes (barrido completo por lotes)
- **Opcional**: 6:00 PM para reprocesar fechas específicas

## Ejecución Manual

### Usando Python directamente:
```bash
# Procesar clientes del día actual
python main.py daily

# Procesar clientes de una fecha específica
python main.py daily 2025-10-01

# Ejecución mensual (barrido completo)
python main.py monthly

# Reprocesar un process_template_id específico
python main.py ABC123XYZ
```

### Usando scripts de cron:
```bash
# Procesar día actual
./cron_daily.sh

# Procesar fecha específica
./cron_daily.sh 2025-10-01

# Ejecución mensual
./cron_monthly.sh
```

## Monitoreo

### Estructura de Logs:
- **Diarios**: `logs/cron_daily_YYYY-MM-DD_HH-MM-SS.log`
- **Diarios con fecha específica**: `logs/cron_daily_YYYY-MM-DD_HH-MM-SS.log`
- **Mensuales**: `logs/cron_monthly_YYYY-MM-DD_HH-MM-SS.log`

### Limpieza Automática:
- Los logs antiguos se limpian automáticamente (30 días para diarios, 90 días para mensuales)
- Cada ejecución registra inicio y fin del proceso
- Los errores se capturan en los mismos archivos de log

### Ver logs en tiempo real:
```bash
# Último log diario
tail -f logs/cron_daily_*.log

# Último log mensual  
tail -f logs/cron_monthly_*.log
```

## Modificar Horarios

Para cambiar los horarios, edita `cron_config.txt` y vuelve a ejecutar:
```bash
crontab cron_config.txt
```

## Desinstalar Cron Jobs

```bash
crontab -r
```