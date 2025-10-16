import os
import sys
import dxpy
import subprocess
from datetime import datetime
import random

from dxpy import api, DXFile, DXApplet, DXJob
from dxpy.utils.job_log_client import DXJobLogStreamClient
from dxpy.utils.printing import RED, set_colors

DX_PROJECT_ID = "project-GQ8KZq009z7ZP56xfPy9qzzf"
DEFAULT_REQUIREMENTS_FILE = "file-GXbz1B809z7qZGzkYq1Gkqf3"
TEST_FOLDER_PATH = "/test_fsspec"


def get_xvjupyter_input(req_dxfile: DXFile,
                        jupyter_dxfile: DXFile, 
                        jupyter_output_file: str, 
                        output_folder: str):
    cmd = f"papermill {DXFile(jupyter_dxfile.get_id(), jupyter_dxfile.get_proj_id()).name} {jupyter_output_file} -p output_folder {output_folder}"
    return {
        "requirements": {"$dnanexus_link": {"id": req_dxfile.get_id(), "project": req_dxfile.get_proj_id()}},
        "cmd": cmd,
        "in": [{"$dnanexus_link": {"id": jupyter_dxfile.get_id(), "project": jupyter_dxfile.get_proj_id()}}],
        "keep_cluster_running_with_jupyterlab": False
    }

def get_dxjupyter_input(req_dxfile: DXFile,
                        jupyter_dxfile: DXFile, 
                        jupyter_output_file: str, 
                        output_folder: str):
    dxtoken = os.environ.get("TOKEN") 
    if not dxtoken:
        dxctx = os.environ.get("DX_SECURITY_CONTEXT")
        if not dxctx:
            raise ValueError('There is no token to login DNAnexus platform.')
        import json
        dxtoken =  json.loads(dxctx)['auth_token']

    cmd = f"dx select $DX_PROJECT_CONTEXT_ID && source ~/.dnanexus_config/unsetenv && dx login --token {dxtoken} --noprojects && "
    cmd += f"pip install -r {DXFile(req_dxfile.get_id(), req_dxfile.get_proj_id()).name} && "
    cmd += f"papermill {DXFile(jupyter_dxfile.get_id(), jupyter_dxfile.get_proj_id()).name} {jupyter_output_file} -p output_folder {output_folder}"
    return {
        "cmd": cmd,
        "in": [{"$dnanexus_link": {"id": jupyter_dxfile.get_id(), "project": jupyter_dxfile.get_proj_id()}},
               {"$dnanexus_link": {"id": req_dxfile.get_id(), "project": req_dxfile.get_proj_id()}}],
    }

def stream_stderr(job_id: str):
    def msg_callback(message):
        message = str(message)
        if "AssertionError" in message:
            print(RED(message=message))
            
    input_params = {"levels": ['STDERR']}
        
    log_client = DXJobLogStreamClient(job_id, 
                                    input_params=input_params, 
                                    msg_callback=msg_callback,
                                    msg_output_format="{msg}",
                                    print_job_info=False)

    try:
        log_client.connect()
    except Exception as details:
        print(str(details))

def run_notebook(app_or_applet_id: str, project_id: str, test_folder_path: str,
                jupyter_filepath: str, requirement_fileid: str,
                instance_count: int = 2):
    now = int(datetime.now().timestamp()) + random.random()
    job_name = f"test_fsspec-{now}"

    # create the test folder
    output_folder = os.path.join(test_folder_path, job_name)
    api.project_new_folder(project_id, input_params={"folder": output_folder, "parents": True})

    # build package
    subprocess.call("python3 setup.py sdist", shell=True)
    
    from fsspec_dnanexus import __version__
    package_filepath = os.path.join("dist", f"fsspec-dnanexus-{__version__}.tar.gz")
    # upload package to test folder on platform
    dxfile: DXFile = dxpy.upload_local_file(package_filepath, folder=output_folder, project=project_id)
    dxfile.wait_on_close()
    dl_url, _ = dxfile.get_download_url(preauthenticated=True)

    requirements = None
    if requirement_fileid:
        # download default requirements file
        requirements = DXFile(requirement_fileid, project=project_id).read()
    else:
        requirements = 'modin~=0.23.0\npyarrow\n'
   
   # add `npapermill` package
    requirements += f"{dl_url}\npapermill\npytest\n"
    # upload requirement file to test folder on platform
    requirement_file = dxpy.upload_string(to_upload=requirements, 
                                          name="requirements.txt", 
                                          folder=output_folder, 
                                          project=project_id)
    
    # upload jupyter input file on local to test folder
    jupyter_input_dxfile: DXFile = dxpy.upload_local_file(jupyter_filepath, folder=output_folder, project=project_id)
    jupyter_input_dxfile.wait_on_close()

    jupyter_filename = jupyter_input_dxfile.describe(fields={"name": True})["name"]
    jupyter_output_name = f"output_{jupyter_filename}"

    app_or_applet = None
    kwargs = {}
    app_input = None
    try:
        dxpy.verify_string_dxid(app_or_applet_id, expected_classes='app')
        app_or_applet = dxpy.DXApp(app_or_applet_id)
        # app_or_applet.access = {'network': ['*'], 'project': 'CONTRIBUTE'}
        app_input = get_dxjupyter_input(req_dxfile=requirement_file, jupyter_dxfile=jupyter_input_dxfile,
                            jupyter_output_file=jupyter_output_name, 
                            output_folder=output_folder)
    except dxpy.exceptions.DXError:
        app_or_applet = DXApplet(app_or_applet_id, project_id)
        app_input = get_xvjupyter_input(req_dxfile=requirement_file, jupyter_dxfile=jupyter_input_dxfile,
                            jupyter_output_file=jupyter_output_name, 
                            output_folder=output_folder)
        # get `clusterSpec` info
        desc = app_or_applet.describe(fields={"runSpec": True})
        systemRequirements = desc["runSpec"]["systemRequirements"]
        clusterSpec = systemRequirements["*"]["clusterSpec"]
        # update `initialInstanceCount`
        clusterSpec["initialInstanceCount"] = instance_count
        kwargs["cluster_spec"] = {
            "*": {
                "clusterSpec": clusterSpec
            }
        }

    # run job
    job: DXJob = app_or_applet.run(
        app_input,
        name=job_name,
        project=project_id,
        folder=output_folder,
        instance_type="mem2_ssd1_v2_x4",
        # debug={
        #     "debugOn": ["AppError", "AppInternalError", "ExecutionError"]
        # },
        delay_workspace_destruction=False,
        **kwargs
    )

    try:
        job.wait_on_done(timeout=1200)
    except dxpy.exceptions.DXJobFailureError as e:
        set_colors()
        stream_stderr(job_id=job.get_id())
        raise(e)

    output_file = dxpy.find_one_data_object(name=jupyter_output_name, 
                                            folder=output_folder, 
                                            project=project_id, 
                                            recurse=False,
                                            zero_ok=True)
    assert output_file is not None, "Jupyter output file does not exist!"
