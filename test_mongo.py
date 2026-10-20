from pymongo import MongoClient

# Cadena de conexión con credenciales completadas
MONGO_URI = "mongodb+srv://jhon_user:Soraya92@cluster0.nuj9phg.mongodb.net/?appName=Cluster0"

def probar_conexion():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Probar respuesta del servidor
        client.admin.command('ping')
        print("✅ ¡Conexión exitosa a MongoDB Atlas!")
        
        # Listar bases de datos disponibles
        dbs = client.list_database_names()
        print("Bases de datos encontradas:", dbs)
        
        client.close()
    except Exception as e:
        print("❌ Error de conexión:", e)

if __name__ == "__main__":
    probar_conexion()