# Python 3.9
FROM python:3.9

# Dependencias generales
RUN apt-get update && apt-get install -y \
    unixodbc unixodbc-dev \
    odbcinst odbcinst1debian2 \
    libodbc1 \
    curl

# Driver ODBC para SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18

# directorio de trabajo
WORKDIR /app

# Copiar archivos al contenedor
COPY ./app /app
COPY requirements.txt /app/

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto 8000 para FastAPI
EXPOSE 8000

# Comando para ejecutar la API con Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]