from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo import MongoClient
from bson import ObjectId

app = FastAPI(title="Agenda Personal & Sistema de Rutinas API", root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = "mongodb+srv://jhon_user:Soraya92@cluster0.nuj9phg.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["agenda_db"]

# --- MODELOS ---
class LoginRequest(BaseModel):
    username: str
    password: str

class UsuarioCreate(BaseModel):
    username: str
    password: str
    nombre_completo: str
    rol: str

class SubTarea(BaseModel):
    id: str
    nombre: str
    fecha_limite: Optional[str] = None
    completado: bool = False

class ProyectoCreate(BaseModel):
    usuario_id: str
    nombre_proyecto: str
    descripcion: Optional[str] = ""
    fecha_limite: Optional[str] = None
    tareas: List[SubTarea] = []

class TareaPersonalCreate(BaseModel):
    usuario_id: str
    tipo: str  # "recurrente" o "unica"
    titulo: str
    dia_recurrente: Optional[str] = None
    fecha_limite: Optional[str] = None
    completado: bool = False

# --- RUTAS DE AUTENTICACIÓN Y USUARIOS ---
@app.post("/login/")
def login(data: LoginRequest):
    user = db["usuarios"].find_one({"username": data.username, "password": data.password})
    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    return {
        "username": user["username"],
        "nombre_completo": user.get("nombre_completo", user["username"]),
        "rol": user.get("rol", "cliente")
    }

@app.get("/usuarios/")
def listar_usuarios():
    usuarios = list(db["usuarios"].find({}, {"password": 0}))
    for u in usuarios:
        u["_id"] = str(u["_id"])
    return usuarios

@app.post("/usuarios/crear/")
def crear_usuario(data: UsuarioCreate):
    if db["usuarios"].find_one({"username": data.username}):
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    db["usuarios"].insert_one(data.dict())
    return {"status": "success", "mensaje": "Usuario creado con éxito"}

# --- RUTAS DE RUTINAS CON HORARIO COLOMBIA (UTC-5) ---
@app.get("/rutinas/cliente/{cliente_id}")
def obtener_rutinas_cliente(cliente_id: str):
    rutinas = list(db["rutinas_asignadas"].find({"cliente_id": cliente_id}))
    for r in rutinas:
        r["_id"] = str(r["_id"])
    return rutinas

@app.get("/rutinas/cliente/{cliente_id}/hoy")
def obtener_rutina_cliente_hoy(cliente_id: str):
    dias_semana = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Hora de Colombia (UTC-5) exacta para evitar desfase horario
    hora_colombia = datetime.utcnow() - timedelta(hours=5)
    dia_actual = dias_semana[hora_colombia.weekday()]
    
    rutinas = list(db["rutinas_asignadas"].find({"cliente_id": cliente_id, "dia_semana": dia_actual}))
    for r in rutinas:
        r["_id"] = str(r["_id"])
    return {"dia_actual": dia_actual, "rutinas": rutinas}

@app.get("/rutinas/todas/")
def obtener_todas_rutinas():
    rutinas = list(db["rutinas_asignadas"].find({}))
    for r in rutinas:
        r["_id"] = str(r["_id"])
    return rutinas

@app.post("/rutinas/crear-tipo-jhon/")
def crear_rutina_video(data: Dict[str, Any]):
    data["tipo"] = "directa_video"
    db["rutinas_asignadas"].insert_one(data)
    return {"status": "success"}

@app.post("/rutinas/crear-tipo-hermana/")
def crear_rutina_detallada(data: Dict[str, Any]):
    data["tipo"] = "detallada"
    db["rutinas_asignadas"].insert_one(data)
    return {"status": "success"}

@app.delete("/rutinas/eliminar/{rutina_id}")
def eliminar_rutina(rutina_id: str):
    db["rutinas_asignadas"].delete_one({"_id": ObjectId(rutina_id)})
    return {"status": "success"}

# --- RUTAS PROYECTOS Y TAREAS ---
@app.get("/proyectos/{usuario_id}")
def obtener_proyectos(usuario_id: str):
    proyectos = list(db["proyectos"].find({"usuario_id": usuario_id}))
    for p in proyectos:
        p["_id"] = str(p["_id"])
    return proyectos

@app.post("/proyectos/crear/")
def crear_proyecto(data: ProyectoCreate):
    db["proyectos"].insert_one(data.dict())
    return {"status": "success"}

@app.get("/tareas/{usuario_id}")
def obtener_tareas(usuario_id: str):
    tareas = list(db["tareas_personales"].find({"usuario_id": usuario_id}))
    for t in tareas:
        t["_id"] = str(t["_id"])
    return tareas

@app.post("/tareas/crear/")
def crear_tarea(data: TareaPersonalCreate):
    db["tareas_personales"].insert_one(data.dict())
    return {"status": "success"}