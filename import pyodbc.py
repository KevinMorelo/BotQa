import os
from sshtunnel import SSHTunnelForwarder
import pymysql
import pandas as pd
from openai import OpenAI

# --- CONFIGURACIÓN GENERAL ---
# 💡 Recomendación: exporta la API key como variable de entorno:
# En Windows (PowerShell):  setx OPENAI_API_KEY "tu_api_key"
# En Linux/macOS:           export OPENAI_API_KEY="tu_api_key"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "TWYaQ17Nj0esMEpGqJWC4g"))

# --- CONFIGURACIÓN SSH ---
ssh_host = '54.175.217.96'
ssh_port = 2222
ssh_user = 'ec2-user'
ssh_key = r'C:\Users\kmorelo\OneDrive - TPZ INFORMATICA LTDA\Documents\pem-dev1\us-east-1.dev1.us-east-1.COB.681989517074.pem'

# --- CONFIGURACIÓN MYSQL ---
mysql_host = 'master.database.general.cob.cobiscloud.int'
mysql_port = 3333
mysql_user = 'userregulatorios'
mysql_pass = 'U53r3gul4t0r105'
mysql_db   = 'cob_conta_super'

# --- QUERY PRINCIPAL ---
query = """
SELECT 
    rc_tabla_dic,
    rc_orden_dic,
    rc_campo_dic,
    rc_tipo_dic,
    rc_tabla_inst,
    rc_orden_inst,
    rc_campo_inst,
    rc_tipo_inst
FROM sb_resultado_comparacion_orden_campos
ORDER BY rc_tabla_dic, rc_orden_dic;
"""

# --- FUNCIÓN PRINCIPAL ---
def generar_reporte():
    try:
        # --- Establecer túnel SSH ---
        with SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_private_key=ssh_key,
            remote_bind_address=(mysql_host, mysql_port),
            local_bind_address=('127.0.0.1', 3307)
        ) as tunnel:
            print("✅ Túnel SSH establecido correctamente")

            # --- Conexión MySQL ---
            conn = pymysql.connect(
                host='127.0.0.1',
                port=3307,
                user=mysql_user,
                password=mysql_pass,
                database=mysql_db
            )
            print("✅ Conectado a la base de datos MySQL correctamente")

            # --- Ejecutar consulta ---
            df = pd.read_sql(query, conn)
            print(f"✅ Datos cargados correctamente. Registros: {len(df)}")

            # --- Cerrar conexión ---
            conn.close()

            # --- Preparar prompt para la IA ---
            muestra = df.head(50).to_markdown()
            prompt = f"""
            Tienes el resultado de una comparación entre el diccionario de datos (DDD)
            y las tablas instaladas en la base de datos.
            Tu tarea:
            1. Identifica los campos fuera de orden por tabla.
            2. Marca los que existen en DDD pero no en BD, y viceversa.
            3. Señala diferencias de tipo de dato.
            4. Sugiere comandos ALTER TABLE o CREATE TABLE según el caso.
            Aquí está una muestra de los datos:
            {muestra}
            """

            # --- Llamada al modelo ---
            response = client.chat.completions.create(
                model="gpt-4o-nano",
                messages=[
                    {"role": "system", "content": "Eres un experto DBA especializado en MySQL y auditoría de estructuras."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            reporte = response.choices[0].message.content

            # --- Guardar reporte ---
            output_file = "reporte_comparacion_campos.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(reporte)

            print(f"✅ Reporte generado correctamente: {output_file}")
            print("\n📄 Vista previa del reporte:\n")
            print(reporte[:1500])  # mostrar primeros caracteres

    except Exception as e:
        print(f"❌ Error durante la ejecución: {e}")

# --- EJECUCIÓN ---
if __name__ == "__main__":
    generar_reporte()
