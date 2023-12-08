from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sqlite3

# Crea la base de datos
conn = sqlite3.connect("contactos.db")

app = FastAPI()

origins = [
    "https://contactos-api-frontend-heroku-f3a3001ed46a.herokuapp.com",
    "http://localhost:5000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Contacto(BaseModel):
    email: str
    nombre: str
    telefono: str

class ErrorRespuesta(BaseModel):
    mensaje: str

# Rutas para las operaciones CRUD

@app.get("/", status_code=200, description="Endpoint raíz de la API.", summary="Endpoint raíz.")
async def obtener_contactos():
    """Obtiene todos los contactos."""
    try:
        c = conn.cursor()
        c.execute('SELECT * FROM contactos')
        response = [{"email": row[0], "nombre": row[1], "telefono": row[2]} for row in c]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        c.close()
    
    return response

@app.post("/contactos", status_code=201, description="Endpoint para enviar datos a la API.", summary="Endpoint para enviar datos.")
async def crear_contacto(contacto: Contacto):
    """Crea un nuevo contacto."""
    try:
        c = conn.cursor()
        c.execute('INSERT INTO contactos (email, nombre, telefono) VALUES (?, ?, ?)',
                  (contacto.email, contacto.nombre, contacto.telefono))
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return contacto

@app.get("/contactos", status_code=200, description="Endpoint para consultar datos de la API.", summary="Endpoint para consulta.")
async def obtener_contacto(email: str):
    """Obtiene un contacto por su email."""
    c = conn.cursor()
    c.execute('SELECT * FROM contactos WHERE email = ?', (email,))
    contacto = None
    for row in c:
        contacto = {"email": row[0], "nombre": row[1], "telefono": row[2]}
    
    if not contacto:
        raise HTTPException(status_code=404, detail=f"No se encontró un contacto con el email {email}")

    return contacto

@app.put("/contactos/{email}", status_code=200, description="Endpoint para actualizar datos de la API.", summary="Endpoint para actualizar.")
async def actualizar_contacto(email: str, contacto: Contacto):
    """Actualiza un contacto."""
    try:
        c = conn.cursor()
        c.execute('UPDATE contactos SET nombre = ?, telefono = ?, email = ? WHERE email = ?',
                  (contacto.nombre, contacto.telefono, contacto.email, email))
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return contacto

@app.delete("/contactos/{email}", status_code=200, description="Endpoint para eliminar datos de la API.", summary="Endpoint para eliminar.")
async def eliminar_contacto(email: str):
    """Elimina un contacto."""
    try:
        c = conn.cursor()
        c.execute('DELETE FROM contactos WHERE email = ?', (email,))
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"mensaje": f"Contacto con email {email} eliminado con éxito."}
