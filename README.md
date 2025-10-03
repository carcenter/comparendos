# Comparendos

Sistema de procesamiento y notificación de comparendos de tránsito.

## Descripción

Este proyecto automatiza la consulta, registro y notificación de comparendos usando Python, MariaDB y la API de HolaAmigo. Permite procesar lotes, deduplicar registros y enviar mensajes personalizados a los usuarios.

## Estructura

- `main.py`: Lógica principal de procesamiento y envío (diario/mensual).
- `db.py`: Funciones de acceso y manipulación de la base de datos.
- `comparendos_api.py`: Integración con APIs de municipios.
- `holaamigo.py`: Integración con la API de HolaAmigo.
- `cron_daily.sh`: Script para ejecución diaria automática.
- `cron_monthly.sh`: Script para ejecución mensual automática.
- `cron_config.txt`: Configuración de cron jobs.
- `docker-compose.yml`: Configuración de contenedores MariaDB.
- `README_CRON.md`: Guía detallada de configuración de cron jobs.
- `.env`: Variables de entorno (no se sube al repositorio).
- `logs/`: Directorio de logs automáticos.
- `certificados/`: Certificados SSL para APIs de municipios.

## Instalación

1. Clona el repositorio.
2. Crea y activa un entorno virtual:
	```
	python -m venv venv
	venv\Scripts\activate
	```
3. Instala dependencias:
	```
	pip install -r requirements.txt
	```
4. Configura el archivo `.env` con tus credenciales y parámetros.

## Uso

### Configuración inicial:
1. Crea el archivo `.env` con tus credenciales y parámetros
2. Inicia la base de datos:
   ```bash
   docker-compose up -d
   ```
3. Da permisos a los scripts:
   ```bash
   chmod +x cron_daily.sh cron_monthly.sh
   ```

### Ejecución manual:
```bash
# Procesar clientes del día actual
python main.py daily

# Procesar fecha específica
python main.py daily 2025-10-01

# Barrido mensual completo
python main.py monthly

# Reprocesar process_template_id
python main.py ABC123XYZ
```

### Automatización con cron:
Ver `README_CRON.md` para configuración detallada de cron jobs.

## Funcionalidades

- **Procesamiento diario**: Solo clientes registrados en el día
- **Procesamiento mensual**: Barrido completo por lotes con offset
- **Deduplicación**: Evita notificar el mismo comparendo múltiples veces  
- **Logs automáticos**: Registro detallado con limpieza automática
- **Filtrado inteligente**: Solo procesa clientes con Whatsapp = 2
- **Manejo de errores SSL**: Configuración específica por municipio

## Notas

- No subas `.env`, `venv/` ni `__pycache__/` al repositorio
- Los logs se guardan automáticamente en `logs/`
- Certificados SSL en `certificados/` para APIs municipales
- Revisa y ajusta los parámetros de conexión según tu entorno

## Licencia

MIT
