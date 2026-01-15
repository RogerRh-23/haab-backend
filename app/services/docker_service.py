import docker

try:
    client = docker.from_env()
except Exception as e:
    print(f"Failed to connect to Docker daemon: {e}")
    client = None

def get_docker_version():
    if client:
        return client.version()
    return {"error": "Docker client not initialized"}

def create_container(image: str, name: str, ports: dict):
    if not client:
        return {"error": "Docker client not initialized"}
    try:
        container = client.continers.run(image, name=name, ports=ports, detach=True)
        return {"id": container.id, "status": "deployed"}
    except Exception as e:
        return {"error": str(e)}


def deploy_app_service(image_name: str, app_name: str, external_port: int):
    if not client:
        return {"error": "Docker client not initialized"}
    try:
        print(f"Descargando imagen: {image_name}...")
        client.images.pull(image_name)


        container = client.containers.run(
            image_name,
            name=f"Haab-app_name",
            ports={'80/tcp': external_port},
            detach=True
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
def stop_and_remove_container(container_id_or_name: str):
    if not client:
        return {"error": "Docker client not initialized"}
    try:
        container = client.containers.get(container_id_or_name)

        container.stop()
        container.remove()

        return {"status": "success", "message": f"Container {container_id_or_name} stopped and removed."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
def list_haab_containers():
    if not client:
        return []
    
    containers = client.containers.list(all=True)
    return [
        {
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "image": c.image.tags[0] if c.image.tags else "unknown"
        }
        for c in containers if c.name.startswith("haab-")
    ]