from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
import logging
import uuid
import hashlib

# Crea la base de datos
conn = sqlite3.connect("contactos.db")

app = FastAPI()

security = HTTPBearer()
security_basic = HTTPBasic()

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
    email : str
    nombre : str
    telefono : str


#  ------------------------ Login y Registro de usuarios ------------------------

@app.post("/registrar/")
def registrar(credentials: HTTPBasicCredentials = Depends(security_basic)):

    if not credentials.username or not credentials.password:
        raise HTTPException(status_code=401, detail="Acceso denegado: Faltan Credenciales")

    username = credentials.username
    password = credentials.password

    password_cifrada = hashlib.sha256(password.encode()).hexdigest()

    with sqlite3.connect("contactos.db") as conn:
        c = conn.cursor()
        # Verificar que el nombre de usuario no se encuentre ya registrado, si no, mostrar un error
        c.execute('SELECT username FROM users WHERE username=?', (username,))
        existing_user = c.fetchone()

        if existing_user:
            return {"Error":"Este usuario ya existe"}

        # Si no está registrado todavía, registrarlo
        c.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            (username, password_cifrada)
        )
        conn.commit()

    return {"message": "El usuario se ha registrado correctamente."}

@app.get("/login")
def login(credentials: HTTPBearer = Depends(security)):
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Error: No se encontró el token")

    token = credentials.credentials

    current_timestamp = datetime.utcnow().timestamp()

    with sqlite3.connect("contactos.db") as conn:
        c = conn.cursor()

        # Obtener el nombre de usuario y la fecha de expiración de token para comprobar la validez del token
        c.execute('SELECT username, expiration_timestamp FROM users WHERE token=?', (token,))
        datos_usuario = c.fetchone() 

        # Comprobar si los datos del usuario existen/se obtuvieron y el token aún es válido, según la fecha de expiración
        if datos_usuario and current_timestamp < datos_usuario[1]:  
            return {"message": "Acceso permitido"}
        else:
            raise HTTPException(status_code=401, detail="Error: Token no válido o ha expirado")

@app.get("/token/")
def generar_token(credentials: HTTPBasicCredentials = Depends(security_basic)):

    # Verificar que se obtuvo el nombre y contraseña en las credenciales
    if not credentials.username or not credentials.password:
        raise HTTPException(status_code=401, detail="Error: Faltan Credenciales")

    username = credentials.username
    password = credentials.password

    password_cifrada = hashlib.sha256(password.encode()).hexdigest()

    with sqlite3.connect("contactos.db") as conn:
        c = conn.cursor()
        # Se obtienen los datos que coincidan con el nombre de usuario
        c.execute('SELECT username, password FROM users WHERE username=?', (username,))
        user = c.fetchone()

        if user and user[1] == password_cifrada:  # Verifica que los datos se hayan conseguido y que la contraseña encontrada sea igual a la contraseña cifrada anteriormente
            timestamp = conn.execute('SELECT strftime("%s", "now")').fetchone()[0]  # Se consiguen la fecha y hora actuales
            token = hashlib.sha256((username + str(uuid.uuid4())).encode()).hexdigest()  # Se consigue el token haciendo uso del nombre de usuario y algoritmos de cifrado
            expiration_time = timedelta(minutes=120)  # Establecer el tiempo de expiración
            expiration_timestamp = (datetime.utcnow() + expiration_time).timestamp()  # Se establece la hora de expiración
            
            # Una vez conseguido el token y fecha de expiración, actualizar el registro correspondiente para que cuente con estos datos
            c.execute(
                'UPDATE users SET token=?, timestamp=?, expiration_timestamp=? WHERE username=?',
                (token, timestamp, expiration_timestamp, username)
            )
            conn.commit()
            
            response_data = {
                "token": token
            }
            return JSONResponse(content=response_data)
        else:
            raise HTTPException(status_code=401, detail="Error: Credenciales no válidas")


#  ----------------------------------  ----------------------------------

# Rutas para las operaciones CRUD

@app.get("/", status_code=200, description="Endpoint raíz de la API.", summary="Endpoint raíz.")
async def obtener_contactos(token: str = Depends(login)):
    """Obtiene todos los contactos."""
    # DONE Consulta todos los contactos de la base de datos y los envia en un JSON  

    with sqlite3.connect("contactos.db") as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM contactos')
        response = []
        for row in c:
            contacto = {"email": row[0], "nombre": row[1], "telefono": row[2]}
            response.append(contacto)

    return response

@app.post("/contactos", status_code=201, description="Endpoint para enviar datos a la API.", summary="Endpoint para enviar datos.")
async def crear_contacto(contacto: Contacto, token: str = Depends(login)):
    """Crea un nuevo contacto."""
    # DONE Inserta el contacto en la base de datos y responde con un mensaje
    try:
        c = conn.cursor()
        c.execute('INSERT INTO contactos (email, nombre, telefono) VALUES (?, ?, ?)',
                (contacto.email, contacto.nombre, contacto.telefono))
        conn.commit()
        return contacto
    
    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=500, detail="Error de servidor")


@app.get("/contactos", status_code=200, description="Endpoint para consultar datos de la API.", summary="Endpoint para consulta.")
async def obtener_contacto(email: str, token: str = Depends(login)):
    """Obtiene un contacto por su email."""
    # DONE Consulta el contacto por su email
    c = conn.cursor()
    c.execute('SELECT * FROM contactos WHERE email = ?', (email,))
    contacto = None
    for row in c:
        contacto = {"email":row[0], "nombre":row[1], "telefono":row[2]}
    
    if contacto is None:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")

    return contacto

@app.put("/contactos/{email}", status_code=200, description="Endpoint para actualizar datos de la API.", summary="Endpoint para actualizar.")
async def actualizar_contacto(email: str, contacto: Contacto, token: str = Depends(login)):
    """Actualiza un contacto."""
    # DONE Actualiza el contacto en la base de datos
    c = conn.cursor()
    c.execute('UPDATE contactos SET nombre = ?, telefono = ?, email = ? WHERE email = ?',
              (contacto.nombre, contacto.telefono, contacto.email, email))
    conn.commit()
    return contacto


@app.delete("/contactos/{email}", status_code=200, description="Endpoint para eliminar datos de la API.", summary="Endpoint para eliminar.")
async def eliminar_contacto(email: str, token: str = Depends(login)):
    """Elimina un contacto."""
    # DONE Elimina el contacto de la base de datos
    c = conn.cursor()
    c.execute('DELETE FROM contactos WHERE email = ?', (email,))
    conn.commit()
    return {"message": "Contacto eliminado con éxito."}
    
