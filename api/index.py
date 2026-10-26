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

# ==========================================
# MODELOS DE DATOS (PYDANTIC)
# ==========================================

class UsuarioCrear(BaseModel):
    username: str = Field(..., example="hermana_entrenadora")
    password: str = Field(..., example="Soraya92")
    nombre_completo: str = Field(..., example="Entrenadora Principal")
    rol: str = Field(..., example="entrenador")

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


# ==========================================
# ENDPOINTS DE USUARIOS
# ==========================================

@app.get("/")
def home():
    return {"status": "API activa y funcionando correctamente"}

@app.post("/usuarios/crear/", status_code=status.HTTP_201_CREATED)
def crear_usuario(usuario: UsuarioCrear):
    existe = db["usuarios"].find_one({"username": usuario.username})
    if existe:
        raise HTTPException(status_code=400, detail=f"El usuario '{usuario.username}' ya existe.")

    if usuario.rol.lower() not in ["entrenador", "cliente"]:
        raise HTTPException(status_code=400, detail="El rol debe ser 'entrenador' o 'cliente'.")

    nuevo_usuario = {
        "username": usuario.username,
        "password": usuario.password,
        "nombre_completo": usuario.nombre_completo,
        "rol": usuario.rol.lower(),
        "fecha_creacion": datetime.now().isoformat()
    }
    res = db["usuarios"].insert_one(nuevo_usuario)
    return {
        "mensaje": "Usuario creado exitosamente",
        "usuario_id": str(res.inserted_id),
        "username": usuario.username,
        "rol": usuario.rol
    }

@app.post("/login/")
def login(datos: UsuarioLogin):
    user = db["usuarios"].find_one({"username": datos.username, "password": datos.password})
    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    return {
        "status": "ok",
        "usuario_id": str(user["_id"]),
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


# ==========================================
# ENDPOINTS DE RUTINAS
# ==========================================

@app.post("/rutinas/crear-tipo-jhon/", status_code=status.HTTP_201_CREATED)
def crear_rutina_jhon(rutina: RutinaJhonCrear):
    documento = {
        "tipo": "directa_video",
        "cliente_id": rutina.cliente_id,
        "dia_semana": rutina.dia_semana,
        "nombre_rutina": rutina.nombre_rutina,
        "enlace_video": rutina.enlace_video,
        "fecha_creacion": datetime.now().isoformat()
    }
    res = db["rutinas_asignadas"].insert_one(documento)
    return {"status": "ok", "rutina_id": str(res.inserted_id)}

@app.post("/rutinas/crear-tipo-hermana/", status_code=status.HTTP_201_CREATED)
def crear_rutina_hermana(rutina: RutinaHermanaCrear):
    documento = {
        "tipo": "detallada",
        "cliente_id": rutina.cliente_id,
        "dia_semana": rutina.dia_semana,
        "titulo_rutina": rutina.titulo_rutina,
        "ejercicios": [e.dict() for e in rutina.ejercicios],
        "fecha_creacion": datetime.now().isoformat()
    }
    res = db["rutinas_asignadas"].insert_one(documento)
    return {"status": "ok", "rutina_id": str(res.inserted_id)}

@app.put("/rutinas/editar/{rutina_id}")
def editar_rutina(rutina_id: str, datos: RutinaEditar):
    actualizacion = {
        "cliente_id": datos.cliente_id,
        "dia_semana": datos.dia_semana,
        "ultima_modificacion": datetime.now().isoformat()
    }

    if datos.tipo == "directa_video":
        actualizacion["nombre_rutina"] = datos.nombre_rutina
        actualizacion["enlace_video"] = datos.enlace_video
    else:
        actualizacion["titulo_rutina"] = datos.titulo_rutina
        actualizacion["ejercicios"] = [e.dict() for e in datos.ejercicios]

    res = db["rutinas_asignadas"].update_one(
        {"_id": ObjectId(rutina_id)},
        {"$set": actualizacion}
    )

    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")

    return {"status": "ok", "mensaje": "Rutina actualizada correctamente"}

@app.get("/rutinas/cliente/{cliente_id}")
def obtener_rutinas_cliente(cliente_id: str):
    rutinas = list(db["rutinas_asignadas"].find({"cliente_id": cliente_id}))
    for r in rutinas:
        r["_id"] = str(r["_id"])
    return rutinas

@app.get("/rutinas/cliente/{cliente_id}/hoy")
def obtener_rutina_cliente_hoy(cliente_id: str):
    dias_semana = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # Ajuste explícito UTC-5 para horario Colombia
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

@app.delete("/rutinas/eliminar/{rutina_id}")
def eliminar_rutina(rutina_id: str):
    res = db["rutinas_asignadas"].delete_one({"_id": ObjectId(rutina_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")
    return {"status": "ok", "mensaje": "Rutina eliminada correctamente"}


# ==========================================
# ENDPOINTS DE CUMPLIMIENTO (EJERCICIOS)
# ==========================================

@app.post("/guardar")
def guardar_cumplimiento(datos: Dict[str, Any]):
    fecha = datos.get("fecha")
    usuario_id = datos.get("usuario_id", "jhoncanasto")
    tareas = datos.get("tareas", {})
    
    total = len(tareas)
    completadas = sum(1 for v in tareas.values() if v.get("completado", False))
    porcentaje = round((completadas / total) * 100, 2) if total > 0 else 0.0

    documento = {
        "usuario_id": usuario_id,
        "fecha": fecha,
        "dia_semana": datos.get("dia_semana"),
        "tareas": tareas,
        "porcentaje_cumplimiento": porcentaje,
        "ultima_actualizacion": datetime.now().isoformat()
    }

    db["registros_diarios"].update_one(
        {"usuario_id": usuario_id, "fecha": fecha},
        {"$set": documento},
        upsert=True
    )

    return {"status": "ok", "porcentaje_cumplimiento": porcentaje}


# ==========================================
# ENDPOINTS PROYECTOS, TAREAS Y PENSAMIENTOS
# ==========================================

# --- PROYECTOS ---
@app.get("/proyectos/{usuario_id}")
def obtener_proyectos(usuario_id: str):
    proyectos = list(db["proyectos"].find({"usuario_id": usuario_id}))
    for p in proyectos:
        p["_id"] = str(p["_id"])
    return proyectos

@app.post("/proyectos/crear/")
def crear_proyecto(data: Dict[str, Any]):
    data["fecha_creacion"] = datetime.now().isoformat()
    db["proyectos"].insert_one(data)
    return {"status": "ok"}

@app.put("/proyectos/actualizar-paso/")
def actualizar_paso_proyecto(data: Dict[str, Any]):
    db["proyectos"].update_one(
        {"_id": ObjectId(data["proyecto_id"]), "pasos.id": data["paso_id"]},
        {"$set": {"pasos.$.completado": data["completado"]}}
    )
    return {"status": "ok"}

@app.delete("/proyectos/eliminar/{proyecto_id}")
def eliminar_proyecto(proyecto_id: str):
    db["proyectos"].delete_one({"_id": ObjectId(proyecto_id)})
    return {"status": "ok"}


# --- TAREAS PERSONALES ---
@app.get("/tareas/{usuario_id}")
def obtener_tareas(usuario_id: str):
    tareas = list(db["tareas_personales"].find({"usuario_id": usuario_id}))
    for t in tareas:
        t["_id"] = str(t["_id"])
    return tareas

@app.post("/tareas/crear/")
def crear_tarea(data: Dict[str, Any]):
    data["fecha_creacion"] = datetime.now().isoformat()
    db["tareas_personales"].insert_one(data)
    return {"status": "ok"}

@app.put("/tareas/estado/{tarea_id}")
def cambiar_estado_tarea(tarea_id: str, data: Dict[str, Any]):
    db["tareas_personales"].update_one(
        {"_id": ObjectId(tarea_id)},
        {"$set": {"completado": data["completado"]}}
    )
    return {"status": "ok"}

@app.delete("/tareas/eliminar/{tarea_id}")
def eliminar_tarea(tarea_id: str):
    db["tareas_personales"].delete_one({"_id": ObjectId(tarea_id)})
    return {"status": "ok"}


# --- PENSAMIENTOS (JOURNALING) ---
@app.get("/pensamientos/{usuario_id}")
def obtener_pensamientos(usuario_id: str):
    pensamientos = list(db["pensamientos"].find({"usuario_id": usuario_id}).sort("fecha", -1))
    for p in pensamientos:
        p["_id"] = str(p["_id"])
    return pensamientos

@app.post("/pensamientos/crear/")
def crear_pensamiento(data: Dict[str, Any]):
    data["fecha"] = datetime.now().isoformat()
    db["pensamientos"].insert_one(data)
    return {"status": "ok"}

@app.delete("/pensamientos/eliminar/{pensamiento_id}")
def eliminar_pensamiento(pensamiento_id: str):
    db["pensamientos"].delete_one({"_id": ObjectId(pensamiento_id)})
    return {"status": "ok"}