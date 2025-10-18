"""Background jobs using dbbasic-queue (TSV-based, no Redis/Celery needed)"""
from dbbasic.queue import Queue
from .settings import DATA_DIR

# Job queue stored in flat TSV files
job_queue = Queue(str(DATA_DIR / "jobs.tsv"))


def enqueue(task_name: str, **kwargs) -> str:
    """Enqueue a background job"""
    return job_queue.push({"task": task_name, "args": kwargs})


def process_jobs():
    """Process pending jobs (run this in a worker process)"""
    while True:
        job = job_queue.pop()
        if not job:
            break

        task_name = job.get("task")
        args = job.get("args", {})

        # Dispatch to handlers
        if task_name == "write_flatfile":
            _write_flatfile(**args)
        elif task_name == "process_upload":
            _process_upload(**args)
        else:
            print(f"Unknown task: {task_name}")


def _write_flatfile(relpath: str, content: str) -> str:
    """Write content to a flat file"""
    from .storage import write_text

    return write_text(relpath, content)


def _process_upload(filename: str, data: bytes) -> dict:
    """Process an uploaded file"""
    from .storage import write_bytes

    path = write_bytes(f"uploads/{filename}", data)
    return {"status": "processed", "path": path, "size": len(data)}
