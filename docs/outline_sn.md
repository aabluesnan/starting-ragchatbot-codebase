# Codebase Overview: Course Materials RAG System

This is a **full-stack Retrieval-Augmented Generation (RAG) chatbot** built to answer questions about course materials using semantic search and AI-powered responses.

## Project Structure

```
starting-ragchatbot-codebase/
├── backend/              # Python FastAPI backend
│   ├── app.py           # Main API endpoints
│   ├── rag_system.py    # Core RAG orchestrator
│   ├── vector_store.py  # ChromaDB vector storage
│   ├── ai_generator.py  # Claude API integration
│   ├── document_processor.py  # Document parsing & chunking
│   ├── search_tools.py  # Search tool definitions
│   └── session_manager.py  # Conversation tracking
├── frontend/            # Web interface (HTML/CSS/JS)
│   ├── index.html
│   ├── script.js
│   └── style.css
├── docs/               # Course material documents (.txt)
└── run.sh             # Startup script
```

## Technology Stack

**Backend:**
- **FastAPI** (0.116.1) - REST API framework
- **ChromaDB** (1.0.15) - Vector database for semantic search
- **Anthropic** (0.58.2) - Claude AI integration
- **Sentence-Transformers** (5.0.0) - Text embeddings (all-MiniLM-L6-v2)
- **Python 3.13** with UV package manager

**Frontend:**
- Vanilla JavaScript with marked.js for Markdown rendering
- Modern dark-themed CSS

## How It Works

1. **Document Loading**: Parses course files from `docs/` folder on startup, extracts metadata (title, instructor, lessons) and chunks content
2. **Vector Storage**: Stores course metadata and content chunks in ChromaDB with embeddings
3. **User Query**: Frontend sends query to `/api/query` endpoint with session tracking
4. **RAG Pipeline**:
   - Claude decides whether to use the search tool based on the question
   - If needed, performs semantic search in vector database
   - Generates response using retrieved context
   - Maintains conversation history
5. **Response**: Returns answer with source attribution (course/lesson)

## Key Features

- Semantic search using embeddings
- Tool-based retrieval (Claude decides when to search)
- Multi-turn conversations with session management
- Course/lesson filtering in searches
- Source attribution showing which materials answered questions
- Responsive web UI with course statistics and suggested questions

## Running the Application

```bash
./run.sh  # Starts server on localhost:8000
```

Requires `.env` file with:
```
ANTHROPIC_API_KEY=your-key-here
```

The system automatically loads all `.txt`, `.pdf`, or `.docx` files from the `docs/` directory when it starts.

## Architecture Details

### Backend Components

**app.py** - FastAPI application entry point
- API endpoints: `/api/query` and `/api/courses`
- CORS middleware configuration
- Static file serving for frontend
- Automatic document loading on startup

**rag_system.py** - Core orchestrator that coordinates:
- Document processing
- Vector storage
- AI generation
- Session management
- Query processing with tool calling

**vector_store.py** - ChromaDB integration
- Two collections: `course_catalog` (metadata) and `course_content` (chunks)
- Semantic search with course/lesson filtering
- Sentence-Transformers for embeddings

**ai_generator.py** - Claude API integration
- System prompt for tool-based retrieval
- Multi-turn conversation handling
- Tool calling support for semantic search

**document_processor.py** - Course document parsing
- Intelligent text chunking (800 chars, 100 char overlap)
- Metadata extraction (title, instructor, lessons)
- Sentence-based splitting

**search_tools.py** - Tool framework
- CourseSearchTool for semantic search
- ToolManager for registration and execution
- Source tracking for UI display

**session_manager.py** - Conversation tracking
- Unique session IDs
- Message history management
- Context formatting for AI

### Frontend Components

**index.html** - Two-column layout
- Left sidebar: course statistics and suggested questions
- Main area: chat interface

**script.js** - Client-side logic
- Message sending and display
- Session management
- Course statistics loading
- Markdown rendering

**style.css** - Dark-themed responsive design
- Custom scrollbars and animations
- Mobile-friendly layout

## Data Flow

```
User Input
   ↓
Frontend (script.js)
   ↓
POST /api/query {query, session_id}
   ↓
Backend (app.py)
   ↓
RAGSystem.query()
   ├─ SessionManager: Get conversation history
   ├─ AIGenerator.generate_response()
   │   ├─ Claude receives prompt with tool definitions
   │   └─ Claude decides to use search_course_content tool
   ├─ ToolManager.execute_tool()
   │   └─ VectorStore.search() - semantic search
   ├─ Claude processes search results
   └─ SessionManager: Store exchange
   ↓
Response {answer, sources, session_id}
   ↓
Frontend: Display answer + sources
```

## Configuration

**config.py** - Centralized settings:
- `ANTHROPIC_API_KEY` - From .env (required)
- `ANTHROPIC_MODEL` - claude-sonnet-4-20250514
- `EMBEDDING_MODEL` - all-MiniLM-L6-v2
- `CHUNK_SIZE` - 800 characters
- `CHUNK_OVERLAP` - 100 characters
- `MAX_RESULTS` - 5 search results per query
- `MAX_HISTORY` - 2 messages to remember

## Course Document Format

Course files in `docs/` must follow this structure:
```
Course Title: [Title]
Course Link: [URL]
Course Instructor: [Name]

Lesson 0: [Lesson Title]
Lesson Link: [URL]
[Lesson content...]

Lesson 1: [Lesson Title]
Lesson Link: [URL]
[Lesson content...]
```

## Security Considerations

- CORS enabled with `allow_origins=["*"]` (development mode)
- Environment variables for API keys
- No authentication/authorization implemented
- Frontend escapes HTML to prevent XSS

## Deployment Notes

**Current State**: Development setup
- Hot reload enabled
- In-memory session storage (lost on restart)
- No database persistence for conversations

**For Production**: Would need:
- Persistent session storage (database)
- Authentication/authorization
- Rate limiting
- CORS restrictions
- Security headers
- Logging & monitoring
- Docker containerization
