from modal.volume import Volume
from modal.stream_type import StreamType


import modal
import uuid
import os
import shutil


from mixtrain import MixClient

# API_KEY = "mix-c213cf62f7ad75e50e4abc03ccd5176356851c32fd091f482934716581fa03ce" # local
# API_KEY = "mix-8c4d367cdcbafc2fbb9ca8a5ef325955249bd9603ee2db4abb0149ccee0dc067" # morphic-staging
API_KEY = (
    "mix-0ffca1a34c351bc3c3e9a19cfbd9e8f3bc72018fa5e8df5a0a295b12d3162187"  # test-prod
)
mix = MixClient(api_key=API_KEY)
app = modal.App.lookup("dk-app", create_if_missing=True)


secrets = {"MIXTRAIN_API_KEY": API_KEY}

for secret in mix.get_all_secrets():
    secrets[secret["name"]] = secret["value"]

uuid = str(uuid.uuid4())
print(uuid)
workdir = f"/workdir"
entrypoint = "/Users/dk/code/mixflow/mixtrain/compare_t2i.py"
files = [entrypoint]  # TODO add all files in the folder

local_folder = f"/tmp/mixtrain/{uuid}"
os.makedirs(local_folder, exist_ok=True)
for file in files:
    shutil.copy(file, local_folder)


workflow_id = 4
run_id = 9
overrides = {
    "limit": 5,
    "output_dataset_name": f"t2i_eval_{workflow_id}_{run_id}",
    "evaluation_name": f"t2i_eval_{workflow_id}_{run_id}",
}
entrypoint = "compare_t2i.py"
# log_file = f"/logs/stdout_{workflow_id}_{run_id}.txt"
# error_file = f"/logs/stderr_{workflow_id}_{run_id}.txt"
log_filename = f"/tmp/{run_id}.txt"
code = f"""
import os
import importlib
import inspect
from mixtrain import MixFlow
workflow_name = "whatever"
run_id = {run_id}
logs_url = "https://modal.com/api/volumes/morphic-staging/staging/logs/files/content?path={log_filename.removeprefix("/logs/")}"
print(logs_url)
def load_python_modules_from_folder(folder_path: str):
    modules = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".py") and not filename.startswith("__"):
            path = os.path.join(folder_path, filename)
            module_name = os.path.splitext(filename)[0]
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            modules.append(module)
    return modules

def find_workflow_classes_in_folder(folder_path: str):
    modules = load_python_modules_from_folder(folder_path)
    for module in modules:
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, MixFlow) and cls is not MixFlow:
                return cls

_c = find_workflow_classes_in_folder("{workdir + workdir}")
_inst_c = _c()

for key, value in {overrides}.items():
    setattr(_inst_c, key, value)

try:
    _inst_c.setup()
except Exception as e:
    print(e)
    _inst_c.mix.update_workflow_run_status(workflow_name=workflow_name, run_number=run_id, status="failed", logs_url="https://modal.com/api/volumes/morphic-staging/staging/logs/files/content?path={log_filename}")
    raise e
_inst_c.mix.update_workflow_run_status(workflow_name=workflow_name, run_number=run_id, status="running", logs_url=)
try:
    _inst_c.run()
except Exception as e:
    print(e)
    _inst_c.mix.update_workflow_run_status(workflow_name=workflow_name, run_number=run_id, status="failed", logs_url="https://modal.com/api/volumes/morphic-staging/staging/logs/files/content?path={log_filename}")
    raise e
try:
    _inst_c.cleanup()
except Exception as e:
    print(e)
    _inst_c.mix.update_workflow_run_status(workflow_name=workflow_name, run_number=run_id, status="failed", logs_url="https://modal.com/api/volumes/morphic-staging/staging/logs/files/content?path={log_filename}")
    raise e
_inst_c.mix.update_workflow_run_status(workflow_name=workflow_name, run_number=run_id, status="completed", logs_url="https://modal.com/api/volumes/morphic-staging/staging/logs/files/content?path={log_filename}")
print("done")
"""

with modal.Volume.ephemeral() as vol:
    with vol.batch_upload() as f:
        f.put_directory(local_folder, workdir)  # or dir

    sb = modal.Sandbox.create(
        app=app,
        image=modal.Image.debian_slim().uv_pip_install(
            "mixtrain==0.1.9", "pydantic<=2.11.10", "fal-client"
        ),
        volumes={
            workdir: vol,
            "/logs": modal.Volume.from_name("logs", create_if_missing=True),
        },
        timeout=600,
        idle_timeout=2,
        env=secrets,
    )

    # TODO: add overrides
    # TODO: api callbacks
    # p = sb.exec(
    #     "bash",
    #     "-lc",
    #     f"python -c '{code}' 2>&1 >/logs/logs.txt",
    #     workdir=workdir + workdir,
    # )
    p = sb.exec(
        "bash",
        "-lc",
        f"python - <<'PY' > {log_filename} 2>&1 \n{code}\nPY",
        workdir=workdir,
    )
    # p = sb.exec("ls", "-lR", workdir=workdir + workdir)
    # for line in p.stdout:
    #     print(line, end="")

    # for line in p.stderr:
    #     print(line, end="")
    # p.wait()
    # print(p.returncode)
    # p = sb.exec("python", "-c", "import fal_client; print(fal_client.__version__)")
    for line in p.stdout:
        print(line, end="")
    for line in p.stderr:
        print(line, end="")

    # sb.terminate()
