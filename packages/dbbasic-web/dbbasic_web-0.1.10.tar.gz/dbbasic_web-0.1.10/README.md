# dbbasic-web

<img src="https://dbbasic.com/static/images/web_coyote.png" alt="Web Coyote Mascot" width="300">

A Unix-philosophy micro-framework that restores the simplicity of CGI while delivering modern performance (~4000 req/s vs 100 req/s for traditional CGI).

## Philosophy

Modern web frameworks moved away from Unix principles and lost key capabilities:
- ❌ Message passing → bolted-on queue systems
- ❌ Cron jobs → separate background job libraries
- ❌ Filesystem routing → giant route tables
- ❌ Flat files → everything forced into SQL
- ❌ Streams → poor SSE/WebSocket support

**dbbasic-web restores these capabilities** using:
- ✅ Filesystem routing (like CGI, but async)
- ✅ TSV-based storage, queues, and streams (no Redis/SQL required)
- ✅ First-class WebSockets and Server-Sent Events
- ✅ Background jobs with dbbasic-queue
- ✅ Message bus with dbbasic-pipe
- ✅ Flat files alongside databases

## Features

### 1. Filesystem Routing
No route tables. No decorators. Just files:

```
api/hello.py         → handles /hello
api/tasks.py         → handles /tasks (collection)
api/tasks/[id].py    → handles /tasks/123 (item with pattern matching)
api/users/[username].py → handles /users/alice
templates/about.html → renders /about
public/css/app.css   → serves /css/app.css
```

Use method-specific functions (GET, POST, PUT, DELETE) or generic `handle()` function.

### 2. Hierarchical API Handlers
Each handler can manage its own sub-routes:

```python
# api/user.py
def handle(request):
    path_parts = request['path_parts']  # ['user', '123', 'edit']

    if len(path_parts) == 1:
        return list_users()
    elif len(path_parts) == 2:
        return get_user(path_parts[1])
    elif len(path_parts) == 3:
        return edit_user(path_parts[1], path_parts[2])
```

### 3. TSV-Based Storage (No SQL Required)
```python
from dbbasic_web.storage import write_text, read_text

# Flat files with automatic directory creation
write_text("notes/2024-01-15.txt", "Meeting notes...")
content = read_text("notes/2024-01-15.txt")
```

### 4. Background Jobs (No Celery/Redis)
```python
from dbbasic_web.jobs import enqueue

# Jobs stored in TSV files
enqueue("write_flatfile", relpath="exports/data.csv", content=csv_data)
```

Run worker:
```bash
python manage.py worker
```

### 5. Message Bus (No Kafka/Redis)
```python
from dbbasic_web.bus import EventBus

bus = EventBus()
await bus.publish("notifications", {"user_id": 123, "event": "login"})

async for message in bus.consume("notifications", group="processors", consumer="worker-1"):
    print(message['data'])
```

### 6. WebSockets & Server-Sent Events
Built-in, no configuration needed:

**WebSocket:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/room-name');
ws.send(JSON.stringify({message: 'Hello!'}));
```

**SSE:**
```javascript
const events = new EventSource('/sse/counter');
events.addEventListener('tick', (e) => console.log(e.data));
```

## Quick Start

### Installation

```bash
pip install dbbasic-web
```

Or install from source:
```bash
git clone https://github.com/askrobots/dbbasic-web.git
cd dbbasic-web
pip install -e .
```

### Run the Server

```bash
python manage.py serve
```

Visit: http://localhost:8000

### Project Structure

```
dbbasic-web/
├── dbbasic_web/
│   ├── api/              # API handlers (filesystem routing)
│   │   ├── hello.py      # /hello
│   │   └── user.py       # /user, /user/*, /user/*/posts
│   ├── templates/        # Jinja2 templates
│   │   ├── base.html
│   │   └── index.html
│   ├── public/           # Static files
│   │   ├── css/app.css
│   │   └── js/app.js
│   ├── asgi.py           # ASGI application
│   ├── router.py         # Filesystem router
│   ├── jobs.py           # Background jobs
│   ├── bus.py            # Message bus
│   ├── storage.py        # Flat-file storage
│   ├── websocket.py      # WebSocket hub
│   └── sse.py            # Server-Sent Events
├── _data/                # Auto-created data directory
│   ├── jobs.tsv          # Job queue
│   └── streams/          # Message bus streams
├── manage.py             # CLI
└── pyproject.toml
```

## Creating API Endpoints

### Simple Endpoint

```python
# api/status.py
import json
from dbbasic_web.responses import json as json_response

def handle(request):
    return json_response(json.dumps({"status": "ok"}))
```

Access: `GET /status`

### REST Resource with Sub-Routes (Classic Pattern)

```python
# api/posts.py
def handle(request):
    parts = request['path_parts']
    method = request['method']

    # /posts
    if len(parts) == 1:
        if method == 'GET':
            return list_posts()
        elif method == 'POST':
            return create_post(request)

    # /posts/123
    elif len(parts) == 2:
        post_id = parts[1]
        if method == 'GET':
            return get_post(post_id)
        elif method == 'PUT':
            return update_post(post_id, request)

    # /posts/123/comments
    elif len(parts) == 3 and parts[2] == 'comments':
        return get_comments(parts[1])
```

### Pattern Routing with Method Functions (New in 0.1.7)

Split routes by file structure and HTTP method for cleaner code:

**Collection endpoints:**
```python
# api/tasks.py
def GET(request):
    """List all tasks"""
    return json(json.dumps({"tasks": [...]}))

def POST(request):
    """Create new task"""
    data = json.loads(request.body)
    return json(json.dumps({"task": data}), status=201)
```

**Item endpoints with pattern matching:**
```python
# api/tasks/[id].py - matches /tasks/123
def GET(request, id):
    """Get single task - id is automatically extracted"""
    task = tasks.query_one(id=id)
    return json(json.dumps({"task": task}))

def PUT(request, id):
    """Update task"""
    data = json.loads(request.body)
    tasks.update({'id': id}, data)
    return json(json.dumps({"success": True}))

def DELETE(request, id):
    """Delete task"""
    tasks.delete(id=id)
    return json(json.dumps({"success": True}))
```

**Pattern routing works with any parameter name:**
```
api/users/[username].py  → /users/alice   → GET(request, username)
api/posts/[slug].py      → /posts/hello   → GET(request, slug)
api/@[handle].py         → /@alice        → GET(request, handle)
```

**Benefits:**
- File structure mirrors URL structure (`ls api/tasks/` shows available routes)
- HTTP method = function name (no nested IFs)
- Parameters extracted from URL and passed as function arguments
- Backward compatible (old `handle()` pattern still works)

## Performance

| Implementation | Requests/sec |
|---------------|--------------|
| Traditional CGI | ~100 |
| dbbasic-web | ~4000 |

Achieved by combining:
- Async I/O (ASGI/uvicorn)
- Filesystem routing (no regex matching)
- Direct module imports (no middleware chains)
- TSV files instead of database round-trips

## Dependencies

Minimal and purposeful:
- `uvicorn` - ASGI server
- `jinja2` - Templates
- `dbbasic-tsv` - TSV database
- `dbbasic-queue` - Job queue
- `dbbasic-pipe` - Message streams
- `dbbasic-sessions` - Authentication
- `websockets` - WebSocket support

**No Redis. No Celery. No PostgreSQL required.**

## Commands

```bash
# Run development server
python manage.py serve

# Run background job worker
python manage.py worker

# Interactive shell
python manage.py shell
```

## Examples

See complete working examples at [dbbasic-examples](https://github.com/askrobots/dbbasic-examples):
- **blog** - Simple blog with posts
- **microblog** - Twitter-like microblog with follows
- **api** - REST API with Bearer token auth, demonstrating pattern routing

## Philosophy in Action

This framework proves that:
1. **Simplicity scales** - Filesystem routing is faster than route tables
2. **Flat files work** - TSV beats Redis for many use cases
3. **Unix was right** - Pipes, files, and processes are enough
4. **Less is more** - 8000 lines total vs 200k+ for Django

## License

MIT

## Contributing

Built for clarity and hackability. Every module is under 500 lines. Read the source.
