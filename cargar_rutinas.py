from pymongo import MongoClient

# Cadena de conexión
MONGO_URI = "mongodb+srv://jhon_user:Soraya92@cluster0.nuj9phg.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client["agenda_db"]

# 1. Definición de la matriz de rutinas basada en tu Excel 'Horarios.xlsx'
rutinas_data = [
    {
        "dia": "Monday",
        "workout": {"titulo": "GLUTES & HAMSTRINGS", "link": "https://www.youtube.com/watch?v=pehjrNhQSZQ&t=1949s"},
        "household_chores": "BARRER",
        "learn": "INGLES",
        "proyecto": "Articulo Filosofico",
        "journaling_num": 1
    },
    {
        "dia": "Tuesday",
        "workout": {"titulo": "RUNNING & ABS", "link": "https://www.youtube.com/watch?v=3U_TXBVnW2A"},
        "household_chores": "BAÑO",
        "learn": "INGLES",
        "proyecto": "Articulo de Escalabilidad",
        "journaling_num": 2
    },
    {
        "dia": "Wednesday",
        "workout": {"titulo": "ARMS & SHOULDERS", "link": "https://www.youtube.com/watch?v=rQBO5_cDUwg"},
        "household_chores": "TAREAS OTRAS",
        "learn": "INGLES",
        "proyecto": "Articulo Filosofico",
        "journaling_num": 3
    },
    {
        "dia": "Thursday",
        "workout": {"titulo": "RUNNING AND YOGA", "link": "https://www.youtube.com/watch?v=wCUI1bwlJqA"},
        "household_chores": "BARRER",
        "learn": "INGLES",
        "proyecto": "Publicar en LinkedIn",
        "journaling_num": 4
    },
    {
        "dia": "Friday",
        "workout": {"titulo": "BACK & BICEPS", "link": "https://www.youtube.com/watch?v=qD9lPRPe-Yy"},
        "household_chores": "REGAR MATAS",
        "learn": "INGLES",
        "proyecto": "Articulo de Escalabilidad",
        "journaling_num": 5
    },
    {
        "dia": "Saturday",
        "workout": {"titulo": "RUNNING AND STRETCHES", "link": "https://www.youtube.com/watch?v=8lkJi4ldZ90"},
        "household_chores": "GENERAL",
        "learn": "REST",
        "proyecto": "Generación de Contenido",
        "journaling_num": 6
    },
    {
        "dia": "Sunday",
        "workout": {"titulo": "REST", "link": ""},
        "household_chores": "REST",
        "learn": "REST",
        "proyecto": "REST",
        "journaling_num": 7
    }
]

# 2. Preguntas de Journaling
journaling_preguntas = {
    1: "☀️ Morning Routine: What is one small thing that made you smile today?",
    2: "🎯 Personal Goals: What is one goal you want to achieve this week, and why is it important to you?",
    3: "🧘 Mindfulness: How are you feeling right now in three words?",
    4: "💡 Self-Reflection: What is a recent mistake you made, and what did you learn from it?",
    5: "🍫 Simple Pleasures: What is your favorite treat or comfort food, and how does it make you feel?",
    6: "🌿 Habits: What is one healthy habit you want to build in your daily routine?",
    7: "🤝 Gratitude: Who is someone you are thankful for today, and why?",
    8: "🔮 Future Self: Where do you see yourself one year from now?",
    9: "🎨 Creativity: If you had a completely free day with no responsibilities, how would you spend it?",
    10: "💬 Self-Care: What is one nice thing you can say to yourself today?"
}

def inicializar_colecciones():
    # Insertar/Actualizar rutinas semanales
    rutinas_col = db["rutinas_semanales"]
    rutinas_col.delete_many({})  # Limpiar previo
    rutinas_col.insert_many(rutinas_data)
    print("✅ Colección 'rutinas_semanales' cargada exitosamente.")

    # Insertar/Actualizar preguntas de Journaling
    journaling_col = db["preguntas_journaling"]
    journaling_col.delete_many({})
    journaling_docs = [{"num": k, "pregunta": v} for k, v in journaling_preguntas.items()]
    journaling_col.insert_many(journaling_docs)
    print("✅ Colección 'preguntas_journaling' cargada exitosamente.")

if __name__ == "__main__":
    inicializar_colecciones()
    client.close()