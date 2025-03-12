from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import pyodbc
import io
import os

app = FastAPI()

# Leer la conexión desde las variables de entorno
DB_CONNECTION = os.getenv("DB_CONNECTION")

# Función de inserción a la BD
def insert_data(table_name: str, df: pd.DataFrame):
    if df.empty:
        raise ValueError("El archivo está vacío o tiene formato incorrecto.")

    try:
        conn = pyodbc.connect(DB_CONNECTION)
        cursor = conn.cursor()

        # Identificar qué columnas son numéricas y cuáles son de texto
        numeric_columns = df.select_dtypes(include=['number']).columns
        text_columns = df.select_dtypes(exclude=['number']).columns

        # Reemplazar valores vacíos: 'NA' para texto y 0 para números
        df[text_columns] = df[text_columns].fillna("NA")
        df[numeric_columns] = df[numeric_columns].fillna(0)

        # Valores a insertar
        data_tuples = [tuple(row) for row in df.itertuples(index=False, name=None)]

        # Placeholder para los valores de inserción
        placeholders = ",".join(["?" for _ in df.columns])

        # Query de inserción
        query = f"INSERT INTO {table_name} VALUES ({placeholders})"

        # Definición batch de carga (1000 registros)
        for i in range(0, len(data_tuples), 1000):
            batch = data_tuples[i:i+1000]
            cursor.executemany(query, batch)
            conn.commit()

        cursor.close()
        conn.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/{table_name}")
async def upload_csv(table_name: str, file: UploadFile = File(...)):
    if table_name not in ["departments", "jobs", "hired_employees"]:
        raise HTTPException(status_code=400, detail="Tabla no válida")

    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Tipo de archivo no válido. Se espera un archivo CSV.")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="La extensión del archivo no es .csv")

    max_file_size = 10 * 1024 * 1024  # 10 MB
    contents = await file.read()
    if len(contents) > max_file_size:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande")

    try:
        # Carga df con datos del archivo
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")),header=None,sep=",")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="Error al analizar el archivo CSV. Verifique el formato.")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Error de codificación del archivo. Asegúrese de que sea UTF-8.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado al leer el archivo: {str(e)}")


    try:
        # Llamado a la función de inserción
        insert_data(table_name, df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al insertar datos en la base de datos: {str(e)}")

    return {"message": f"Datos insertados en {table_name} correctamente"}

# 1. Endpoint para obtener el número de empleados contratados en 2021 por Q
@app.get("/hired_employees/quarterly")
def get_hired_employees_by_quarter():
    try:
        conn = pyodbc.connect(DB_CONNECTION)
        query = """
        SELECT 
            d.department,
            j.job,
            SUM(CASE WHEN MONTH(case when try_cast(he.datetime as date) is not null then cast(he.datetime as date) else cast('2999-12-31' as datetime) end) BETWEEN 1 AND 3 THEN 1 ELSE 0 END) AS Q1,
            SUM(CASE WHEN MONTH(case when try_cast(he.datetime as date) is not null then cast(he.datetime as date) else cast('2999-12-31' as datetime) end) BETWEEN 4 AND 6 THEN 1 ELSE 0 END) AS Q2,
            SUM(CASE WHEN MONTH(case when try_cast(he.datetime as date) is not null then cast(he.datetime as date) else cast('2999-12-31' as datetime) end) BETWEEN 7 AND 9 THEN 1 ELSE 0 END) AS Q3,
            SUM(CASE WHEN MONTH(case when try_cast(he.datetime as date) is not null then cast(he.datetime as date) else cast('2999-12-31' as datetime) end) BETWEEN 10 AND 12 THEN 1 ELSE 0 END) AS Q4
        FROM hired_employees he
        JOIN jobs j ON 
            he.job_id = j.id
        JOIN departments d ON 
            he.department_id = d.id
        WHERE year(case when try_cast(he.datetime as date) is not null then cast(he.datetime as date) else cast('2999-12-31' as datetime) end) = 2021
        GROUP BY d.department, j.job
        ORDER BY d.department, j.job;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df.to_dict(orient="records")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar la consulta: {str(e)}")


# 2. Endpoint para obtener los departamentos que contrataron más empleados que la media
@app.get("/hired_employees/above_average")
def get_departments_above_mean():
    try:
        conn = pyodbc.connect(DB_CONNECTION)
        query = """
            WITH DepartmentHires AS (
                SELECT 
                    d.id,
                    d.department,
                    COUNT(*) AS hired
                FROM hired_employees he
                JOIN departments d ON 
                    he.department_id = d.id
                WHERE year(case when try_cast(he.datetime as date) is not null then cast(he.datetime as date) else cast('2999-12-31' as datetime) end) = 2021
                GROUP BY d.id, d.department
            ),
            AvgHires AS (
                SELECT AVG(hired) AS avg_hired FROM DepartmentHires
            )
            SELECT dh.id, dh.department, dh.hired
            FROM DepartmentHires dh
            CROSS JOIN AvgHires
            WHERE dh.hired > AvgHires.avg_hired
            ORDER BY dh.hired DESC;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df.to_dict(orient="records")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar la consulta: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "API de Migración en ejecución"}
