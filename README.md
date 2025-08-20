# Comparendos

Sistema de procesamiento y notificación de comparendos de tránsito.

## Descripción

Este proyecto automatiza la consulta, registro y notificación de comparendos usando Python, MariaDB y la API de HolaAmigo. Permite procesar lotes, deduplicar registros y enviar mensajes personalizados a los usuarios.

## Estructura

- `main.py`: Lógica principal de procesamiento y envío.
- `db.py`: Funciones de acceso y manipulación de la base de datos.
- `auth.py`: Autenticación y manejo de tokens.
- `holaamigo.py`: Integración con la API de HolaAmigo.
- `logger.py`: Registro de eventos y errores.
- `docker-compose.yml`: Configuración de contenedores MariaDB.
- `.env`: Variables de entorno (no se sube al repositorio).
- `venv/`, `__pycache__/`: Archivos generados automáticamente (ignorados por git).

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

1. Crea el archivo .env con base en .env.example y cambia las credenciales correspondientes
	```
	docker-compose up -d
	```
2. Ejecuta el script principal:
	```
	python main.py
	```

## Notas

- No subas `.env`, `venv/`, `main.py` ni `__pycache__/` al repositorio.
- Revisa y ajusta los parámetros de conexión y API según tu entorno.

## Licencia

MIT
