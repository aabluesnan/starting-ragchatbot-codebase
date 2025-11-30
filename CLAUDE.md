# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Workflow

**CRITICAL**: For any non-trivial change to this codebase:

1. First, explore the relevant files and produce a step-by-step plan.
2. Show me the plan and wait for my approval.
3. Only after I say "go ahead" should you start editing files.
4. Keep the plan concise and numbered.

This ensures all changes are reviewed before implementation.

## Project Overview

A Retrieval-Augmented Generation (RAG) chatbot system for semantic search and Q&A over course materials. Uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface.

**Key Architecture Pattern**: Tool-based RAG where Claude autonomously decides when to search (rather than always retrieving first). The AI receives tool definitions and determines whether to use the search tool based on query type.

## Commands

**IMPORTANT**: Always use `uv` to manage dependencies and run commands. Never use `pip` directly.

### Running the Application
```bash
# Start development server (auto-reload enabled)
./run.sh

# Or manually
cd backend
uv run uvicorn app:app --reload --port 8000
```

Access at http://localhost:8000 (web UI) and http://localhost:8000/docs (API docs)

### Dependency Management
```bash
# Install/sync dependencies
uv sync

# Add new dependency
uv add package-name

# Remove dependency
uv remove package-name
```

### Database Operations
```bash
# Clear and rebuild vector database (forces re-indexing)
rm -rf chroma_db/
./run.sh

# Windows
rmdir /s /q chroma_db
```

### Code Quality Tools
```bash
# Format code automatically (black + ruff)
./format.sh

# Run all quality checks (formatting, linting, type checking)
./check.sh

# Individual tools
uv run black backend/ main.py              # Auto-format code
uv run ruff check backend/ main.py         # Lint code
uv run ruff check --fix backend/ main.py   # Auto-fix linting issues
uv run mypy backend/ main.py               # Type check
```

**Quality Tools Configuration:**
- **Black**: Line length 100, Python 3.13+ (configured in pyproject.toml)
- **Ruff**: Fast linter with import sorting, replaces flake8/isort (pycodestyle, pyflakes, bugbear, etc.)
- **MyPy**: Type checker with balanced strictness settings

All quality tool configurations are in `pyproject.toml`. Run `./check.sh` before committing to ensure code quality standards are met.

## High-Level Architecture

### Two-Stage AI Interaction Flow

Unlike traditional RAG (retrieve → generate), this system uses:

1. **Initial Request**: Claude receives query + tool definitions + conversation history
2. **Tool Decision**: Claude analyzes whether query needs course-specific search
3. **Tool Execution** (if needed): `search_course_content` executes vector search
4. **Synthesis**: Claude receives results and generates answer

General knowledge questions skip retrieval entirely.

### Document Processing Pipeline

Documents in `docs/` must follow this format:
```
Course Title: [title]
Course Link: [url]
Course Instructor: [instructor]

Lesson N: [title]
Lesson Link: [url]
[content...]
```

Processing flow (backend/document_processor.py):
1. Extract metadata → Create `Course` object (title is unique ID)
2. Parse lessons by regex markers (`Lesson \d+:`)
3. Chunk text on sentence boundaries with overlap (`CHUNK_SIZE=800`, `CHUNK_OVERLAP=100`)
4. Add context prefix: `"Course {title} Lesson {N} content: {chunk}"`
5. Generate embeddings via SentenceTransformer (`all-MiniLM-L6-v2`, 384-dim)
6. Store in ChromaDB collections

### Vector Store Architecture

**Two ChromaDB Collections** (backend/vector_store.py):
- `course_catalog`: Course titles/instructors for fuzzy name matching
- `course_content`: Content chunks with metadata filters

**Search Flow**:
1. If `course_name` provided → semantic search `course_catalog` to resolve partial match (e.g., "MCP" → "Building MCP Apps with Anthropic")
2. Build filter dict with resolved `course_title` and/or `lesson_number`
3. Query `course_content` with embeddings + filters
4. Return top 5 results by cosine similarity

### Session Management (backend/session_manager.py)

In-memory only (not persisted):
- Session ID: `session_{counter}` auto-incremented
- Stores `List[Message]` with role + content
- Automatically truncates to last `MAX_HISTORY * 2` messages (default: 4)
- History formatted as `"User: ...\nAssistant: ..."` and injected into system prompt
- Sessions reset on server restart

### Tool Execution Pattern (backend/search_tools.py)

Registry pattern via `ToolManager`:
1. Tools implement `Tool` protocol: `get_tool_definition()` + `execute()`
2. `register_tool()` adds to registry
3. `get_tool_definitions()` returns list for Claude API
4. `execute_tool()` dispatches by name
5. Tools track state (`last_sources`) for response assembly

**Current tool**: `CourseSearchTool` wraps vector search with formatting.

### AI Generator Two-Call Pattern (backend/ai_generator.py)

```python
# Call 1: With tools
response = claude.create(messages, tools=tools)

if response.stop_reason == "tool_use":
    # Execute tools
    messages.append(assistant_tool_use)
    messages.append(user_tool_results)

    # Call 2: Without tools (forces answer)
    final = claude.create(messages)  # No tools
```

Second call deliberately omits tools to force final answer generation.

**System Prompt** (static class variable):
- One search maximum per query
- No meta-commentary about search process
- Direct answers for general knowledge
- Concise, educational responses

### Source Tracking Flow

Sources flow separately from AI response:
1. `CourseSearchTool.execute()` stores in `self.last_sources`
2. `ToolManager.get_last_sources()` retrieves from tools
3. `RAGSystem.query()` extracts after generation
4. `ToolManager.reset_sources()` clears for next query
5. API returns sources alongside answer (not in text)

### Frontend-Backend Contract (backend/app.py)

```
POST /api/query
  Request:  {query: string, session_id: string|null}
  Response: {answer: string, sources: [string], session_id: string}

GET /api/courses
  Response: {total_courses: int, course_titles: [string]}
```

Frontend uses `marked.parse()` for markdown rendering. Sources in collapsible `<details>`.

## Configuration (backend/config.py)

```python
CHUNK_SIZE: 800          # Characters per chunk
CHUNK_OVERLAP: 100       # Overlap for context
MAX_RESULTS: 5           # Vector search results
MAX_HISTORY: 2           # Exchanges remembered (4 messages)
ANTHROPIC_MODEL: "claude-sonnet-4-20250514"
EMBEDDING_MODEL: "all-MiniLM-L6-v2"
CHROMA_PATH: "./chroma_db"
```

## Key Implementation Details

### Chunk Context Enhancement (backend/document_processor.py:232-234)

Chunks prefixed with context during processing:
- `"Course {title} Lesson {N} content: {chunk}"`

This embeds lesson numbers, enabling semantic matching for queries like "lesson 2".

### Deduplication (backend/rag_system.py:75-96)

`add_course_folder()` checks existing titles before processing:
- Queries ChromaDB for existing course titles
- Skips if `course.title` already exists
- Enables idempotent folder loading

### Sentence-Based Chunking (backend/document_processor.py:34)

Regex splits on sentence boundaries:
```python
sentence_endings = re.compile(
    r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!|\?)\s+(?=[A-Z])'
)
```

Handles abbreviations to avoid mid-sentence splits.

## Adding New Course Documents

1. Create `.txt` file in `docs/` following format above
2. Restart server (auto-detects in `startup_event()`) OR delete `chroma_db/`
3. System processes files matching `.txt`, `.pdf`, `.docx` extensions

## Modifying Search Behavior

**Adjust results**: Change `MAX_RESULTS` in config.py

**Change chunking**: Edit `DocumentProcessor.chunk_text()` sentence regex

**Switch embedding model**: Update `EMBEDDING_MODEL`, then delete `chroma_db/` (embeddings incompatible)

**Custom filters**: Modify `VectorStore._build_filter()` for additional metadata

## Debugging

**Inspect vector store**:
```python
cd backend
uv run python
>>> from vector_store import VectorStore
>>> vs = VectorStore("./chroma_db", "all-MiniLM-L6-v2", 5)
>>> vs.course_catalog.count()
>>> vs.course_content.count()
```

**Test tool independently**:
```python
from search_tools import CourseSearchTool
from vector_store import VectorStore

vs = VectorStore("./chroma_db", "all-MiniLM-L6-v2", 5)
tool = CourseSearchTool(vs)
print(tool.execute(query="prompt caching", course_name="Computer Use"))
```

**View ChromaDB data**: Check `chroma_db/chroma.sqlite3` with SQLite browser

## Environment

- Python 3.13+ (required by pyproject.toml)
- `uv` package manager
- `.env` file with `ANTHROPIC_API_KEY`
- Windows: Use Git Bash for `run.sh`

## Known Limitations

- Sessions are in-memory (lost on restart)
- ChromaDB is local file-based (not distributed)
- First query is slow (~10-30s) due to model loading into memory
- One search per query enforced by system prompt only
- Course title is unique identifier (duplicates skipped)
- No authentication or multi-tenancy
