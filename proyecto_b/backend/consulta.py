import sqlite3

conexion = sqlite3.connect("pipeline.db")
cursor = conexion.cursor()

cursor.execute("SELECT SUM(monto) FROM  articles")

resultado = cursor.fetchone()

print("Total de ingresos:", resultado[0])

conexion.close()