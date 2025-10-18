"""CLI entry point for dbbasic-web command"""
import sys
import os


def main():
    """Main CLI entry point (installed as 'dbbasic-web' command)"""
    if len(sys.argv) < 2:
        print("Usage: dbbasic-web [command]")
        print("\nCommands:")
        print("  init <name>  - Create a new dbbasic-web project")
        print("  serve        - Run the development server")
        print("  worker       - Run the background job worker")
        print("  shell        - Start interactive shell")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        init_project()
    elif command == "serve":
        serve()
    elif command == "worker":
        worker()
    elif command == "shell":
        shell()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


def init_project():
    """Create a new dbbasic-web project"""
    if len(sys.argv) < 3:
        print("Usage: dbbasic-web init <project_name>")
        sys.exit(1)

    project_name = sys.argv[2]
    print(f"Creating new dbbasic-web project: {project_name}")

    # TODO: Scaffold project structure
    print("Project scaffolding not yet implemented")
    print(f"Manually create: {project_name}/")
    print("  - {project_name}_web/")
    print("    - api/")
    print("    - templates/")
    print("    - public/")
    print("  - manage.py")
    print("  - pyproject.toml")


def serve():
    """Run the development server"""
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    # Try to import from current project
    try:
        # Look for app in current directory
        sys.path.insert(0, os.getcwd())
        print(f"Starting dbbasic-web on http://{host}:{port}")

        # Try common module names
        for module_name in ["app.asgi:app", "dbbasic_web.asgi:app"]:
            try:
                uvicorn.run(
                    module_name,
                    host=host,
                    port=port,
                    reload=True,
                    log_level="info",
                )
                return
            except (ImportError, ModuleNotFoundError):
                continue

        print("Error: Could not find ASGI application")
        print("Expected: app.asgi:app or dbbasic_web.asgi:app")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


def worker():
    """Run background job worker"""
    import time

    sys.path.insert(0, os.getcwd())

    try:
        from dbbasic_web.jobs import process_jobs
    except ImportError:
        print("Error: Could not import jobs module")
        sys.exit(1)

    print("Starting job worker...")
    while True:
        try:
            process_jobs()
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nWorker stopped")
            break
        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(5)


def shell():
    """Start interactive shell with app context"""
    import code

    sys.path.insert(0, os.getcwd())

    try:
        from dbbasic_web import settings
        from dbbasic_web.storage import write_text, read_text
        from dbbasic_web.jobs import enqueue
        from dbbasic_web.bus import EventBus

        context = {
            "settings": settings,
            "write_text": write_text,
            "read_text": read_text,
            "enqueue": enqueue,
            "EventBus": EventBus,
        }

        banner = "dbbasic-web interactive shell\nAvailable: settings, write_text, read_text, enqueue, EventBus"
        code.interact(banner=banner, local=context)
    except ImportError as e:
        print(f"Error importing modules: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
