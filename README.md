# **API de Migración de Datos a Azure SQL**

## 📌 Descripción
Esta API permite recibir archivos de migración (.csv) y cargarlos en una base de datos en **Azure SQL**. Está encapsulada en un **contenedor Docker**.

Los archivos con los datos a migrar son:

- jobs.csv
- departments.csv
- hired_employees.csv

## 🚀 Instalación
1. Clonar el repositorio.
2. Ejecutar:
```bash
docker-compose up -d
```
La estructura del proyecto debe ser la siguiente:

```bash
api_mig/
│── app/
│   │── main.py         # Código de la API
│   │── requirements.txt # Dependencias
│── Dockerfile          # Configuración de Docker
│── docker-compose.yml  # Orquestación de Docker
│── README.md           # Documentación
```

## 📡 Endpoints
### `POST /upload/{table_name}`
Sube un archivo CSV y lo inserta en la tabla correspondiente.

Ejemplo:
```bash
curl -X POST -F "file=@departments.csv" http://127.0.0.1:8000/upload/departments
```

## 🔑 Cadena de Conexión Azure SQL

DB_CONNECTION=Driver={ODBC Driver 18 for SQL Server};Server=tcp:your_az_sql_server,1433;Database=db_name;Uid=user_name;Pwd=password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;

## 💾 Creación de tablas

### 📅 Tabla departments
```sql
CREATE TABLE [dbo].[departments](
	[id] [int] NOT NULL,
	[department] [varchar](100) NULL
) ON [PRIMARY]
GO
```
### 📅 Tabla jobs
```sql
CREATE TABLE [dbo].[jobs](
	[id] [int] NOT NULL,
	[job] [varchar](100) NULL
) ON [PRIMARY]
GO
```
### 📅 Tabla hired_employees
```sql
CREATE TABLE [dbo].[hired_employees](
	[id] [int] NOT NULL,
	[name] [varchar](100) NULL,
	[datetime] [varchar](50) NULL,
	[department_id] [int] NOT NULL,
	[job_id] [int] NOT NULL
) ON [PRIMARY]
GO
```