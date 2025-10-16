r"""
Käivitamiseks (Windows)
cd Dev\pip-dapu\src\dapu
uvicorn main:app --port 17005 --host 0.0.0.0

API DOC: http://127.0.0.1:17005/openapi.json

Käivitamiseks (docker, linux)
cd /srv/dapu
export DAPU_PROFILES=.....Documents/profiles.yaml
uvicorn server:app --port 18905 --host 0.0.0.0 --forwarded-allow-ips '192.168.0.4'

"""

__version__ = '0.1.3' # peab olema enne import => saab olla ainult static/hardcoded

import os
import sys
# välised komponendid
from loguru import logger
from fastapi import FastAPI, Response, Request, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse, FileResponse, HTMLResponse
# omad
from dbpoint.hub import Hub
from dbpoint.datacapsule import DataCapsule, enname
#from prepare import prepare_context, AppContext
from dapu.context import DapuContext
from dapu.fileops import read_content_of_file, read_content_of_package_file, copy_from_package_to_file
from dapu.textops import generate_from_string
#from router_letter import router as router_letter # huvitav, kas selline dot-notation tegelikult ka toimib?
from dapu.versops import version_from_pyproject_file

name = "Dapu API"
version = version_from_pyproject_file("../../pyproject.toml") # 2 taset üles 
if version == "":
    version = version_from_pyproject_file("./pyproject.toml") # siitsamast
if version == "":
    version = __version__


work_dir = os.path.realpath(".")
alternative_profiles_filename = os.getenv("DAPU_PROFILES") or "./profiles.yaml"
profiles_text: str = read_content_of_file(work_dir + "/conf/profiles.yaml") or read_content_of_file(alternative_profiles_filename) or ""
if not profiles_text:
    logger.error("No profiles")
    sys.exit(1)

sql_drivers_text: str = read_content_of_package_file("dapu", "drivers.yaml") or "" # known SQL drivers
hub = Hub(profiles_text, sql_drivers_text)
context = DapuContext(work_dir, hub)

logger.info(f"{name} {version} is starting...")
app = FastAPI(title=name, version=version)

app.state.app_context = context # tüüpi DapuContext/AppContext (olemas ka pöörduste vahel, seal on nt AB ühendus) (mitte panna sinna pöörduse infot!)

@app.get("/status", include_in_schema=False, response_class=PlainTextResponse)
def read_root_status():
    return Response("server is running indeed")

@app.get("/favicon.ico", include_in_schema=False, response_class=FileResponse) 
def read_favicon(request: Request):
    """
    favicon is app.png in /static/
    """
    context: DapuContext = request.app.state.app_context  # app context teab kaustadest
    path = os.path.join(context.work_dir, "static", "app.png")
    if not os.path.exists(path):
        copy_from_package_to_file("dapu.static", "app.png", path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Item dapu.static.app.png not found")
    return FileResponse(path, media_type='image/png')

@app.get("/info", include_in_schema=False, response_class=HTMLResponse)
def read_root_info():
    html = f"""
    <h1>Resources</h1>
    <div>Just status: <a href="/status">status</a></div>
    <div>Definition (JSON): <a href="{app.openapi_url}">OpenAPI</a></div>
    <div>Services are mostly /api/letter </div>
    """
    return HTMLResponse(html)

@app.get("/signal/pause", response_class=HTMLResponse)
def web_signal_pause(request: Request):
    context: DapuContext = request.app.state.app_context
    context.signal_pause_switch(True)
    html = f"Pause demanded"
    return HTMLResponse(html)

@app.get("/signal/resume", response_class=HTMLResponse)
def web_signal_resume(request: Request):
    context: DapuContext = request.app.state.app_context
    context.signal_pause_switch(False)
    html = f"Allowed to run"
    return HTMLResponse(html)

@app.get("/signal/info", response_class=HTMLResponse)
def web_signal_info(request: Request):
    context: DapuContext = request.app.state.app_context
    data: dict = {}
    data["status"] = "ENABLED" if context.check_pause() else "PAUSED"
    jobs: list = []
    lastjobs: list = []
    waitjobs: list = []
    capsule: DataCapsule = context.running_jobs()
    if capsule.row_exists(0):
        for row in capsule:
            jobs.append(enname(row, ["id", "created_ts", "task_id", "worker", "last_start_ts", "commander", "failure_count"]))
        data["jobs"] = jobs
    capsule: DataCapsule = context.last_jobs(5)
    if capsule.row_exists(0):
        for row in capsule:
            lastjobs.append(enname(row, ["id", "created_ts", "task_id", "worker", "last_start_ts", "last_end_ts"]))
        data["lastjobs"] = lastjobs
    capsule: DataCapsule = context.waiting_jobs()
    if capsule.row_exists(0):
        for row in capsule:
            waitjobs.append(enname(row, ["id", "created_ts", "task_id", "commander", "failure_count"]))
        data["waitjobs"] = waitjobs
    template_str = read_content_of_package_file("dapu.templates", "running.html") or read_content_of_file("./templates/running.html") or "??"
    html = generate_from_string(template_str, template_data=data)
    return HTMLResponse(html)

@app.middleware("http")
async def midware_notify(request: Request, call_next):
    context: DapuContext = request.app.state.app_context
    context.notify(f"consumation of {request.url}")
    return await call_next(request)


context.notify(f"API is starting for {context.my_shift}")
