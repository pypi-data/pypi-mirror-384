import argparse
import base64
import json
import multiprocessing
import os
import shutil
import sys
import tempfile
import traceback
from .__util_log import Log
from .__util_task import update_task_status
from .__task_script_runner import run

log = Log({})


def get_run_params(task):
    return {
        "input": task.get("input"),
        "context_from_arg": task.get("context"),
        "func": task.get("func"),
        "correlation_id": task.get("correlation_id"),
        "func_dir": task.get("func_dir"),
        "store_output": False,
        "storage_type": os.environ.get("TASK_STORAGE_TYPE"),
        "storage_bucket": os.environ.get("TASK_STORAGE_S3FILE_BUCKET"),
        "storage_file_key": os.environ.get("TASK_STORAGE_S3FILE_FILE_KEY"),
        "storage_endpoint": os.environ.get("TASK_STORAGE_S3FILE_ENDPOINT"),
        "artifact_bucket": os.environ.get("ARTIFACT_S3FILE_BUCKET"),
        "artifact_prefix": os.environ.get("ARTIFACT_S3FILE_PREFIX"),
        "artifact_endpoint": os.environ.get("ARTIFACT_S3FILE_ENDPOINT"),
        "artifact_file_key": os.environ.get("ARTIFACT_IDS_SCHEMA_S3FILE_FILE_KEY"),
        "artifact_bucket_private": os.environ.get("ARTIFACT_S3FILE_BUCKET_PRIVATE"),
        "artifact_prefix_private": os.environ.get("ARTIFACT_S3FILE_PREFIX_PRIVATE"),
        "artifact_endpoint_private": os.environ.get("ARTIFACT_S3FILE_ENDPOINT_PRIVATE"),
    }


def task_process_fn(task, shared_dict):
    task_tmp_dir = tempfile.mkdtemp()
    os.environ.update({"TMPDIR": task_tmp_dir})

    run_params = get_run_params(task)
    sys.path.append(run_params.get("func_dir"))
    try:
        shared_dict["result"] = run(**run_params)
    except:
        e = sys.exc_info()[1]
        log.log(log.generate_error(e))
        shared_dict["error"] = traceback.format_exc()
    finally:
        sys.path.remove(run_params.get("func_dir"))
        shutil.rmtree(task_tmp_dir, ignore_errors=True)


def run_task_process(task, task_process_cb=None):
    manager = multiprocessing.Manager()
    shared_dict = manager.dict({"result": None, "error": None})
    task_id = task.get("id")
    task_process = multiprocessing.Process(
        name=f"task-{task_id}", target=task_process_fn, args=(task, shared_dict)
    )
    if task_process_cb:
        task_process_cb(task_process)
    task_process.start()
    task_process.join()
    exitcode = task_process.exitcode
    if exitcode != 0:
        if exitcode == -9 or exitcode == 137:
            exitcode = 137
            update_status_payload = {
                "status": "failed",
                "exitCode": exitcode,
                "result": {
                    "error": {
                        "message": {
                            "text": f"Invalid exit code {exitcode}",
                            "oomError": True,
                        }
                    }
                },
            }
        else:
            update_status_payload = {
                "status": "failed",
                "exitCode": exitcode,
                "result": {"error": f"Invalid exit code {exitcode}"},
            }
    else:
        if not (shared_dict["result"] is None):
            update_status_payload = {"exitCode": 0, **shared_dict["result"]}
        else:
            update_status_payload = {
                "status": "failed",
                "exitCode": 0,
                "result": {
                    "error": (
                        shared_dict["error"]
                        if shared_dict["error"]
                        else "No content returned by worker"
                    )
                },
            }
    update_task_status(task, update_status_payload)
    return shared_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--func", help="function slug", required=True)
    parser.add_argument("--correlation-id", help="correlation id")
    parser.add_argument("--input", help="input string", default="")
    parser.add_argument("--context", help="context", default="")
    parser.add_argument("--func-dir", help="function dir", default="./func")
    args = parser.parse_args()
    params = {
        "input": json.loads(base64.standard_b64decode(args.input)),
        "context_from_arg": json.loads(base64.standard_b64decode(args.context)),
        "func": args.func,
        "correlation_id": args.correlation_id,
        "func_dir": args.func_dir,
        "storage_type": os.environ.get("TASK_STORAGE_TYPE"),
        "storage_bucket": os.environ.get("TASK_STORAGE_S3FILE_BUCKET"),
        "storage_file_key": os.environ.get("TASK_STORAGE_S3FILE_FILE_KEY"),
        "storage_endpoint": os.environ.get("TASK_STORAGE_S3FILE_ENDPOINT"),
        "artifact_bucket": os.environ.get("ARTIFACT_S3FILE_BUCKET"),
        "artifact_prefix": os.environ.get("ARTIFACT_S3FILE_PREFIX"),
        "artifact_endpoint": os.environ.get("ARTIFACT_S3FILE_ENDPOINT"),
        "artifact_file_key": os.environ.get("ARTIFACT_IDS_SCHEMA_S3FILE_FILE_KEY"),
        "artifact_bucket_private": os.environ.get("ARTIFACT_S3FILE_BUCKET_PRIVATE"),
        "artifact_prefix_private": os.environ.get("ARTIFACT_S3FILE_PREFIX_PRIVATE"),
        "artifact_endpoint_private": os.environ.get("ARTIFACT_S3FILE_ENDPOINT_PRIVATE"),
    }
    sys.path.append(params["func_dir"])

    run(**params)
