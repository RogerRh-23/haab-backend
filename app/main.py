from fastapi import FastAPI
from app.services.docker_service import (
    get_docker_version,
    deploy_app_service,
    stop_and_remove_container,
    list_haab_containers
)
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Haab Backend is running"}

@app.get("/system/check")
def check_system():
    version = get_docker_version()
    return {"system": "Haab PaaS", "docker": version}

@app.post("/deploy")
def deploy(image_name: str, app_name: str, external_port: int):
    result = deploy_app_service(image_name, app_name, external_port)
    return result

@app.get("/apps")
def get_apps():
    return {"apps": list_haab_containers()}

@app.delete("/apps/{name_or_id}")
def delete_app(name_or_id: str):
    return stop_and_remove_container(name_or_id)
