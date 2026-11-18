
# AutoAgent – Autonomous AI Agent Framework

AutoAgent is a modular autonomous agent framework built with Python and FastAPI. It uses a tool-based architecture, a state machine, and an LLM decision layer to interpret user requests, select tools, execute tasks, and observe results.

The project also includes semantic memory, persistent conversation history, role-based access control, API-key authentication, rate limiting, and human approval for sensitive tool operations.

## Features

- **Agent Controller:** Coordinates the agent's decision-making and tool execution.
- **State Machine:** Manages the THINK, VALIDATE, AUTHORIZE, EXECUTE, OBSERVE, DONE, and FAILED states.
- **Tool Registry:** Supports registering tools with argument validation using Pydantic.
- **Mock LLM:** Provides a local decision-making implementation for testing without an external LLM API.
- **Web Search:** Retrieves web search results through DuckDuckGo.
- **Python Executor:** Executes Python code in a separate process with timeout and output limits.
- **SQL Executor:** Supports controlled SQLite database operations.
- **File I/O:** Supports reading, writing, and appending files within the configured data directory.
- **Semantic Memory:** Uses Sentence Transformers and FAISS for similarity-based memory retrieval.
- **Conversation History:** Persists conversations using SQLite.
- **Human Approval:** Requires approval before executing sensitive tool operations.
- **Authentication:** Uses API keys with salted PBKDF2 hashing.
- **RBAC:** Provides admin, developer, analyst, and guest roles.
- **Rate Limiting:** Limits API requests to help prevent excessive usage.

## Architecture

```text
User
 |
 v
FastAPI Application
 |
 v
Authentication and RBAC
 |
 v
Agent Controller
 |
 +------> Semantic Memory
 |
 v
Mock LLM / Decision Layer
 |
 v
State Machine
 |
 +------> Validate Tool Arguments
 |
 +------> Check Permissions
 |
 +------> Request Human Approval
 |
 v
Tool Registry
 |
 +------> Web Search
 +------> Python Executor
 +------> SQL Executor
 +------> File I/O
 +------> Basic Mathematical Tools
 |
 v
Observation and Final Response
```

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.10 |
| API Framework | FastAPI |
| Data Validation | Pydantic |
| Semantic Embeddings | Sentence Transformers |
| Vector Search | FAISS |
| Database | SQLite |
| Web Search | DuckDuckGo Search |
| Testing | Pytest |

## Project Structure

```text
AutoAgent/
|
├── app/
│   ├── agent/
│   │   ├── state_machine.py
│   │   ├── mock_llm.py
│   │   └── controller.py
│   |
│   ├── tools/
│   │   ├── registry.py
│   │   ├── basic_tools.py
│   │   ├── web_search.py
│   │   ├── python_executor.py
│   │   ├── sql_tool.py
│   │   └── file_tool.py
│   |
│   ├── memory/
│   │   ├── semantic_memory.py
│   │   └── conversation_store.py
│   |
│   └── api/
│       ├── main.py
│       ├── schemas.py
│       ├── security.py
│       ├── roles.py
│       ├── user_store.py
│       └── approval_store.py
|
├── data/
├── tests/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd AutoAgent
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

Start the FastAPI server:

```bash
uvicorn app.api.main:app --reload
```

The application will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## API Usage

### Run the Agent

Endpoint:

```http
POST /agent/run
```

Headers:

```http
X-API-Key: YOUR_API_KEY
Content-Type: application/json
```

Request:

```json
{
  "message": "Calculate 25 multiplied by 4"
}
```

Example response:

```json
{
  "success": true,
  "result": {
    "answer": "The final answer is 100"
  }
}
```

The actual response can include additional fields depending on the execution result.

## User Roles and Permissions

| Role | Permissions |
|---|---|
| Admin | All seven registered tools |
| Developer | Basic tools, web search, Python execution, file I/O |
| Analyst | Basic tools, web search, SQL execution |
| Guest | Basic mathematical tools only |

## Testing

Run the complete test suite:

```bash
pytest -v
```

The current test suite contains **69 passing tests**.

Test coverage includes:

- Agent controller and state machine
- Tool registration and validation
- Python execution and timeout handling
- SQL and file operations
- Semantic memory and persistence
- API authentication
- Role-based access control
- Web search

## Security Considerations

- API keys are stored as salted PBKDF2 hashes.
- Tool arguments are validated using Pydantic.
- Tool access is restricted according to user roles.
- Sensitive tools require human approval.
- SQL operations use parameterized queries and SQLite authorizer restrictions.
- Python execution uses a separate process, timeout handling, a temporary working directory, and output limits.
- File operations are restricted to the configured data directory.

**Important:** The Python executor is not a complete security sandbox. Running arbitrary untrusted code requires stronger isolation, such as a restricted operating-system account or container.

## Current Limitations

- The current decision layer uses a Mock LLM rather than a production LLM API.
- Python execution does not provide complete operating-system-level isolation.
- SQLite is used for persistence and is intended for this project's current scope.
- Rate limiting currently uses in-memory storage.

## Future Improvements

- Integrate a production LLM provider.
- Add stronger execution isolation.
- Improve distributed memory and persistence.
- Add more tools and advanced agent planning.

## Author

**Kishan Kumar**

B.Tech – Computer Science and Engineering  
Indian Institute of Technology (BHU), Varanasi
