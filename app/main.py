import docker
client = docker.from_env()
from sqlalchemy.orm import Session
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, HTTPException
import asyncio
from app.services.docker_service import (
    get_docker_version,
    deploy_app_service,
    stop_and_remove_container,
    list_haab_containers,
    stream_container_logs
)
from .database import get_db, engine
from . import models, schemas
from typing import List

app = FastAPI(title="Haab PaaS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Haab Backend is running"}

@app.get("/system/check")
def check_system():
    version = get_docker_version()
    return {"system": "Haab PaaS", "docker": version}

@app.post("/deploy", response_model=schemas.ApplicationResponse)
def deploy_app(
    app_data: schemas.ApplicationCreate,
    db: Session = Depends(get_db) 
    ):

    port_check = db.query(models.Application).filter(models.Application.port == app_data.port).first()
    if port_check:
        raise HTTPException(
            status_code=400,
            detail = f"El puerto {app_data.port} ya está en uso por la app '{port_check.name}'."
        )

    name_check = db.query(models.Application).filter(models.Application.name == app_data.name).first()
    if name_check:
        raise HTTPException(
            status_code=400,
            detail = f"El nombre '{app_data.name}' ya está en uso. Por favor elige otro nombre."
        )
    result = deploy_app_service(app_data.image, app_data.name, app_data.port)

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    new_app = models.Application(
        name = app_data.name,
        image = app_data.image,
        port = app_data.port,
        status = "running"
    )
    
    db.add(new_app)
    db.commit()
    db.refresh(new_app)

    return new_app

@app.get("/apps", response_model=List[schemas.ApplicationResponse])
def get_apps(db: Session = Depends(get_db)):
    apps = db.query(models.Application).all()
    return apps

@app.delete("/apps/{app_id}")
def delete_app(app_id: int, db: Session = Depends(get_db)):
    # 1. Buscar en la DB
    app_record = db.query(models.Application).filter(models.Application.id == app_id).first()
    
    if not app_record:
        raise HTTPException(status_code=404, detail="La aplicación no existe en la base de datos")

    # 2. Usar el servicio que ya tienes (Músculo)
    # Importante: Pasa el nombre completo que usa Docker
    docker_name = f"haab-{app_record.name}"
    docker_result = stop_and_remove_container(docker_name)
    
    if docker_result.get("status") == "error":
        print(f"Nota: Docker avisó que {docker_result['message']}")

    # 3. Borrar de la DB (Cerebro)
    db.delete(app_record)
    db.commit()

    return {"message": f"Aplicación '{app_record.name}' eliminada correctamente"}

@app.websocket("/ws/logs/{container_name}")
async def websocket_logs(websocket: WebSocket, container_name: str):
    await websocket.accept()
    try:
        loop = asyncio.get_event_loop()

        def get_logs():
            return stream_container_logs(container_name)

        for line in get_logs():
            await websocket.send_text(line)
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for container: {container_name}")
    except Exception as e:
        await websocket.send_text(f"Error en websocket: {str(e)}")
    finally:
        await websocket.close()

@app.get("/apps", response_model=List[schemas.ApplicationResponse])
def get_apps(db: Session = Depends(get_db)):
    apps = db.query(models.Application).all()
    return apps

@app.get("/apps/{app_id}/logs")
def get_app_logs(app_id: int, db: Session = Depends(get_db)):
    app_record = db.query(models.Application).filter(models.Application.id == app_id).first()
    
    if not app_record:
        raise HTTPException(status_code=404, detail="La aplicación no existe en la base de datos")
    
    try:
        container = client.containers.get(f"haab-{app_record.name}")
        logs = container.logs(tail=100).decode('utf-8')
        return {"name": app_record.name, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los logs: {str(e)}")

models.Base.metadata.create_all(bind=engine)