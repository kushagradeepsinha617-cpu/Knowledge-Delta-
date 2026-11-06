"""Explicit offline build/fresh-install probe; all writes stay inside this repo."""
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.setup_ui import child_environment, PIP_NAME, PIP_SHA256


def main():
    run_id = uuid4().hex
    work = ROOT / ".tools/repro" / run_id
    work.mkdir(parents=True)
    env = child_environment(ROOT, work)
    env.update(PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1")
    report = {"kind": "offline_packaging_verification", "run_id": run_id,
              "commands": [], "downloads_performed": False, "global_installation": False,
              "model_calls": 0, "status": "running"}
    def command(name, arguments, cwd=work):
        result = subprocess.run(arguments, cwd=cwd, env=env, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=180)
        report["commands"].append({"name": name, "arguments": arguments,
            "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            raise RuntimeError(name + " failed; inspect command evidence")
        return result.stdout
    try:
        builder = ROOT / ".venv-ml/Scripts/python.exe"
        stage = work / "stage"
        stage.mkdir()
        shutil.copyfile(ROOT / "pyproject.toml", stage / "pyproject.toml")
        shutil.copytree(ROOT / "knowledge_delta", stage / "knowledge_delta",
                        ignore=shutil.ignore_patterns("__pycache__"))
        wheels = work / "wheels"
        wheels.mkdir()
        command("build_wheel", [str(builder), "-I", "-B", "-c",
            "import importlib.metadata as m;print('setuptools='+m.version('setuptools'));from setuptools.build_meta import build_wheel;print(build_wheel(" + repr(str(wheels)) + "))"], stage)
        found = list(wheels.glob("*.whl"))
        if len(found) != 1:
            raise RuntimeError("Expected exactly one built wheel")
        wheel = found[0]
        report["wheel"] = {"name": wheel.name, "bytes": wheel.stat().st_size,
                           "sha256": sha256(wheel.read_bytes()).hexdigest()}
        environment = work / "venv"
        command("fresh_environment", [str(builder), "-I", "-B", "-m", "venv", "--without-pip", str(environment)])
        python = environment / "Scripts/python.exe"
        pip = ROOT / ".tools/ui-setup" / PIP_NAME
        if sha256(pip.read_bytes()).hexdigest() != PIP_SHA256:
            raise RuntimeError("Previously verified pip wheel changed")
        installer = "import runpy,sys;sys.path.insert(0," + repr(str(pip)) + ");sys.argv=['pip','install','--no-index','--no-deps','--no-cache-dir'," + repr(str(wheel)) + "];runpy.run_module('pip',run_name='__main__')"
        command("offline_fresh_pip_install", [str(python), "-I", "-B", "-c", installer])
        command("installed_cli_help", [str(python), "-I", "-B", "-m", "knowledge_delta", "--help"])
        command("installed_doctor", [str(python), "-I", "-B", "-m", "knowledge_delta", "doctor"])
        command("installed_compare", [str(python), "-I", "-B", "-m", "knowledge_delta", "compare",
            str(ROOT / "examples/constructed/before/manifest.json"), str(ROOT / "examples/constructed/after/manifest.json")])
        probe = ("import importlib.resources as r,importlib.metadata as m,json,knowledge_delta;"
            "files=r.files('knowledge_delta')/'web_assets';names=['index.html','app.css','app.js'];"
            "assert all((files/n).is_file() for n in names);"
            "print(json.dumps({'package_version':m.version('knowledge-delta'),'module':knowledge_delta.__file__,'assets':names}))")
        command("installed_package_assets", [str(python), "-I", "-B", "-c", probe])
        ui_probe = """import json,threading,urllib.request
from knowledge_delta.web_app import create_server
server=create_server(PROJECT_ROOT,0)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
url='http://127.0.0.1:'+str(server.server_address[1])
try:
    page=urllib.request.urlopen(url+'/').read()
    assert b'/assets/app.css' in page and b'id="load-form"' in page
    state=json.load(urllib.request.urlopen(url+'/api/state'))
    request=urllib.request.Request(url+'/api/load',data=b'{}',headers={'Content-Type':'application/json','X-KnowledgeDelta-Token':state['csrf']})
    loaded=json.load(urllib.request.urlopen(request))['state']
    assert loaded['evaluation']['origin']=='fixture'
    assert loaded['evaluation']['counts']['planned_answer_records']==80
    print(json.dumps({'installed_ui_http_load':'passed','origin':'fixture','planned_answer_records':80,'model_calls':0}))
finally:
    server.shutdown();server.server_close();thread.join(5)
    assert not thread.is_alive()
""".replace("PROJECT_ROOT", repr(str(ROOT)))
        command("installed_ui_http_fixture", [str(python), "-I", "-B", "-c", ui_probe])
        report.update(status="passed", supported_runtime="Windows AMD64 / Python 3.14.10",
                      limits=["Offline wheel build and fresh pip install use already downloaded setuptools/pip.",
                              "No clean internet dependency resolution, ML dependency reinstall, POSIX or Python compatibility matrix is proven."])
    except Exception as exc:
        report.update(status="failed", error_type=type(exc).__name__, error=str(exc))
    output = ROOT / "docs/evidence/milestone5-packaging" / (run_id + ".json")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps({"status": report["status"], "report": str(output), "error": report.get("error")}))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
