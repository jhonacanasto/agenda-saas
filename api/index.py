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
class UsuarioCrear(BaseModel):
    username: str
    password: str
    nombre_completo: str
    rol: str

class UsuarioLogin(BaseModel):
    username: str
    password: str

class EjercicioDetalle(BaseModel):
    nombre_ejercicio: str
    peso: Optional[str] = "Sin peso"
    observaciones: Optional[str] = ""
    numero_repeticiones: int = 4

class RutinaHermanaCrear(BaseModel):
    cliente_id: str
    dia_semana: str
    titulo_rutina: Optional[str] = "Rutina General"
    ejercicios: List[EjercicioDetalle]

class RutinaJhonCrear(BaseModel):
    cliente_id: str
    dia_semana: str
    nombre_rutina: str
    enlace_video: Optional[str] = ""

class RutinaEditar(BaseModel):
    cliente_id: str
    dia_semana: str
    tipo: str
    nombre_rutina: Optional[str] = None
    enlace_video: Optional[str] = None
    titulo_rutina: Optional[str] = None
    ejercicios: Optional[List[EjercicioDetalle]] = []

# --- ENDPOINTS USUARIOS ---
@app.get("/")
def home():
    return {"status": "API activa"}

@app.post("/usuarios/crear/", status_code=status.HTTP_201_CREATED)
def crear_usuario(usuario: UsuarioCrear):
    if db["usuarios"].find_one({"username": usuario.username}):
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    db["usuarios"].insert_one(usuario.dict())
    return {"status": "success", "username": usuario.username}

@app.post("/login/")
def login(datos: UsuarioLogin):
    user = db["usuarios"].find_one({"username": datos.username, "password": datos.password})
    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    return {
        "status": "ok",
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

# --- ENDPOINTS RUTINAS (CON HORA COLOMBIA UTC-5) ---
@app.get("/rutinas/cliente/{cliente_id}")
def obtener_rutinas_cliente(cliente_id: str):
    rutinas = list(db["rutinas_asignadas"].find({"cliente_id": cliente_id}))
    for r in rutinas:
        r["_id"] = str(r["_id"])
    return rutinas

@app.get("/rutinas/cliente/{cliente_id}/hoy")
def obtener_rutina_cliente_hoy(cliente_id: str):
    dias_semana = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Ajuste explícito a la hora de Colombia (UTC-5)
    hora_colombia = datetime.utcnow() - timedelta(hours=5)
    dia_actual = dias_semana[hora_colombia.weekday()]
    
    rutinas = list(db["rutinas_asignadas"].find({"cliente_id": cliente_id, "dia_semana": dia_actual}))
    for r in rutinas:
        r["_id"] = str(r["_id"])
    return {"dia_actual": dia_actual, "rutinas": rutinas}

@app.get("/rutinas/todas/")
def listar_todas_rutinas():
    rutinas = list(db["rutinas_asignadas"].find({}))
    for r in rutinas:
        r["_id"] = str(r["_id"])
    return rutinas

@app.post("/rutinas/crear-tipo-jhon/", status_code=status.HTTP_201_CREATED)
def crear_rutina_jhon(rutina: RutinaJhonCrear):
    doc = {"tipo": "directa_video", **rutina.dict(), "fecha_creacion": datetime.now().isoformat()}
    res = db["rutinas_asignadas"].insert_one(doc)
    return {"status": "ok", "rutina_id": str(res.inserted_id)}

@app.post("/rutinas/crear-tipo-hermana/", status_code=status.HTTP_201_CREATED)
def crear_rutina_hermana(rutina: RutinaHermanaCrear):
    doc = {"tipo": "detallada", **rutina.dict(), "fecha_creacion": datetime.now().isoformat()}
    res = db["rutinas_asignadas"].insert_one(doc)
    return {"status": "ok", "rutina_id": str(res.inserted_id)}

@app.put("/rutinas/editar/{rutina_id}")
def editar_rutina(rutina_id: str, datos: RutinaEditar):
    actualizacion = datos.dict()
    if datos.tipo == "detallada":
        actualizacion["ejercicios"] = [e.dict() for e in datos.ejercicios]
    db["rutinas_asignadas"].update_one({"_id": ObjectId(rutina_id)}, {"$set": actualizacion})
    return {"status": "ok"}

@app.delete("/rutinas/eliminar/{rutina_id}")
def eliminar_rutina(rutina_id: str):
    db["rutinas_asignadas"].delete_one({"_id": ObjectId(rutina_id)})
    return {"status": "ok"}

@app.post("/guardar")
def guardar_cumplimiento(datos: Dict[str, Any]):
    db["registros_diarios"].update_one(
        {"usuario_id": datos.get("usuario_id"), "fecha": datos.get("fecha")},
        {"$set": datos},
        upsert=True
    )
    return {"status": "ok"}