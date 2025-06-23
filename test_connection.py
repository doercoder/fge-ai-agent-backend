import psycopg2

try:
    conn = psycopg2.connect(
        dbname="momostenango",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5435"
    )
    print("✅ Conexión exitosa con parámetros directos")
    conn.close()
except Exception as e:
    print("❌ Error:", e)
