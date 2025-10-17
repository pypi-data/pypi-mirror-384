from threading import Timer

from .run import run_task_process
from .__util_log import Log
from .__util_task import (
    ContainerStoppedException,
    extend_task_timeout,
    poll_task,
    FailedPollTaskException,
)

log = Log({})


def healtcheck_worker(run_state):
    run_state["healtcheck_timer"] = None
    task = run_state["task"]
    task_process = run_state["task_process"]

    if task and task_process:
        task_id = task.get("id")
        try:
            extend_task_timeout(task)
        except:
            log.log(f"Error during timeout extension -> killing task {task_id}")
            task_process.kill()

    healtcheck_timer = Timer(60.0, healtcheck_worker, [run_state])
    run_state["healtcheck_timer"] = healtcheck_timer
    healtcheck_timer.start()


def main():
    run_state = {"task_process": None, "task": None, "healtcheck_timer": None}
    healtcheck_worker(run_state)

    def set_task_process_run_state(task_process):
        run_state["task_process"] = task_process

    while True:
        try:
            task = poll_task()
        except ContainerStoppedException:
            log.log("Container is stopped - exiting...")
            break
        except FailedPollTaskException:
            log.log("Cannot poll task - exiting...")
            break

        if task:
            task_id = task.get("id")
            log.log({"level": "debug", "message": f"Got new task {task_id}"})
            run_state["task"] = task
            shared_dict = run_task_process(task, set_task_process_run_state)
            log.log({"level": "debug", "message": f"Task {task_id} process completed"})
            run_state["task_process"] = None
            run_state["task"] = None

    if run_state["healtcheck_timer"] and run_state["healtcheck_timer"].is_alive():
        run_state["healtcheck_timer"].cancel()

    return shared_dict


if __name__ == "__main__":
    main()
