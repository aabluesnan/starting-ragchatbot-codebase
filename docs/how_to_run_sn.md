# How to Run This Application

This guide provides step-by-step instructions for setting up and running the Course Materials RAG chatbot application.

---

## Prerequisites

Before you begin, ensure you have the following:

1. **Python 3.13 or higher** - [Download Python](https://www.python.org/downloads/)
2. **uv** (Python package manager) - Fast, modern package manager
3. **Anthropic API key** - [Get your API key](https://console.anthropic.com/)
4. **For Windows users**: Git Bash - [Download Git for Windows](https://git-scm.com/downloads/win)

---

## Setup Steps

### 1. Install uv (if not already installed)

**Windows (Git Bash):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, restart your terminal or run:
```bash
source $HOME/.cargo/env
```

### 2. Install Dependencies

Navigate to the project directory and install all required packages:

```bash
uv sync
```

This command will install:
- **chromadb** (1.0.15) - Vector database for semantic search
- **anthropic** (0.58.2) - Claude API client
- **sentence-transformers** (5.0.0) - Embedding models
- **fastapi** (0.116.1) - Web framework
- **uvicorn** (0.35.0) - ASGI web server
- **python-multipart** (0.0.20) - File upload support
- **python-dotenv** (1.1.1) - Environment variable management

### 3. Set Up Environment Variables

Create a `.env` file in the root directory with your Anthropic API key:

**Method 1: Copy from example**
```bash
cp .env.example .env
```

Then edit `.env` and replace the placeholder with your actual API key:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

**Method 2: Create manually**

Create a new file named `.env` in the root directory:
```bash
echo "ANTHROPIC_API_KEY=your_actual_api_key_here" > .env
```

**Getting an Anthropic API Key:**
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and paste it into your `.env` file

---

## Running the Application

### Option 1: Using the Shell Script (Recommended)

The easiest way to run the application is using the provided shell script.

**In Git Bash (Windows) or Terminal (macOS/Linux):**
```bash
chmod +x run.sh
./run.sh
```

This script will:
- Create necessary directories
- Check for the backend directory
- Remind you about the API key
- Start the uvicorn server with auto-reload enabled

### Option 2: Manual Start

If you prefer to start the server manually or the script doesn't work:

```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

**Explanation:**
- `cd backend` - Navigate to the backend directory
- `uv run` - Run using uv's environment
- `uvicorn app:app` - Start uvicorn with the FastAPI app
- `--reload` - Enable auto-reload on code changes (development mode)
- `--port 8000` - Run on port 8000

### Option 3: Windows Command Prompt/PowerShell

If you're using Windows without Git Bash:

```cmd
cd backend
uv run uvicorn app:app --reload --port 8000
```

Or with PowerShell:
```powershell
cd backend
uv run uvicorn app:app --reload --port 8000
```

---

## Accessing the Application

Once the server is running, you can access:

### Web Interface
**URL:** http://localhost:8000

This is the main chat interface where you can:
- Ask questions about course materials
- View conversation history
- See sources for each answer
- Browse available courses

### API Documentation
**URL:** http://localhost:8000/docs

Interactive Swagger UI providing:
- API endpoint documentation
- Request/response schemas
- Try-it-out functionality
- Example payloads

### Alternative API Documentation
**URL:** http://localhost:8000/redoc

ReDoc interface with:
- Clean, readable documentation
- Downloadable OpenAPI spec
- Code samples

---

## What Happens on Startup

When you start the application, the following sequence occurs:

### 1. Initialization
```
Starting Course Materials RAG System...
Make sure you have set your ANTHROPIC_API_KEY in .env
```

### 2. Component Startup
- FastAPI application initializes
- CORS middleware configured
- RAG system components loaded:
  - DocumentProcessor
  - VectorStore (ChromaDB)
  - AIGenerator (Claude API client)
  - SessionManager
  - ToolManager with CourseSearchTool

### 3. Document Loading
```
Loading initial documents...
```

The system scans the `docs/` folder for course documents:
- Checks existing courses in ChromaDB
- Processes new course documents
- Extracts metadata (title, instructor, link)
- Chunks content with overlap
- Generates embeddings
- Stores in vector database

**Example output:**
```
Added new course: Building Toward Computer Use with Anthropic (45 chunks)
Added new course: Introduction to MCP (32 chunks)
Added new course: Prompt Engineering (38 chunks)
Added new course: Tool Use Fundamentals (41 chunks)
Loaded 4 courses with 156 chunks
```

### 4. Server Ready
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

The application is now ready to accept queries!

---

## Current Course Documents

The system comes with 4 pre-loaded course documents in the `docs/` folder:

1. **course1_script.txt** - Building Toward Computer Use with Anthropic
   - Instructor: Colt Steele
   - Topics: Computer use, vision, tool use, agentic workflows

2. **course2_script.txt** - Course 2 content

3. **course3_script.txt** - Course 3 content

4. **course4_script.txt** - Course 4 content

### Document Format

Each course document follows this structure:
```
Course Title: [Course Name]
Course Link: [URL]
Course Instructor: [Instructor Name]

Lesson 0: [Lesson Title]
Lesson Link: [URL]
[Lesson content...]

Lesson 1: [Lesson Title]
Lesson Link: [URL]
[Lesson content...]
```

---

## Using the Application

### Chat Interface

1. **Open the web interface** at http://localhost:8000
2. **Type your question** in the input field
3. **Press Enter** or click **Send**
4. **View the response** with markdown formatting
5. **Click "Sources"** to see which courses/lessons were referenced

**Example Questions:**
- "What is prompt caching?"
- "How does tool use work in lesson 2?"
- "Explain computer use capabilities"
- "What does Colt Steele say about agentic workflows?"

### Conversation Context

The system maintains conversation history:
- Stores last 5 exchanges (10 messages) per session
- Provides context to AI for follow-up questions
- Session persists until page reload or server restart

**Example conversation:**
```
You: What is prompt caching?
AI: Prompt caching is a feature that retains...

You: How does it save costs?
AI: Based on our previous discussion about prompt caching, it saves costs by...
```

### Course Statistics

The sidebar shows:
- **Total Courses**: Number of indexed courses
- **Course Titles**: List of available courses

---

## Stopping the Application

To stop the server:

1. **In the terminal where the server is running**, press:
   ```
   Ctrl + C
   ```

2. **Wait for graceful shutdown:**
   ```
   INFO:     Shutting down
   INFO:     Waiting for application shutdown.
   INFO:     Application shutdown complete.
   INFO:     Finished server process [12346]
   ```

3. **The terminal will return to the command prompt**

---

## Troubleshooting

### Issue: "ModuleNotFoundError" or "No module named 'X'"

**Problem:** Dependencies not installed

**Solution:**
```bash
uv sync
```

If that doesn't work, try:
```bash
rm -rf .venv
uv sync
```

---

### Issue: "ANTHROPIC_API_KEY not found"

**Problem:** Environment variable not set

**Solution:**
1. Check that `.env` file exists in the root directory:
   ```bash
   ls -la .env
   ```

2. Verify the content:
   ```bash
   cat .env
   ```

3. Ensure the key is set correctly:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

4. Restart the server after updating `.env`

---

### Issue: "Port 8000 is already in use"

**Problem:** Another application is using port 8000

**Solution 1 - Use a different port:**
```bash
cd backend
uv run uvicorn app:app --reload --port 8001
```

Then access at: http://localhost:8001

**Solution 2 - Find and kill the process:**

**Windows:**
```cmd
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

**macOS/Linux:**
```bash
lsof -ti:8000 | xargs kill -9
```

---

### Issue: ChromaDB Errors

**Problem:** Corrupted or incompatible ChromaDB data

**Symptoms:**
- "Chroma collection not found"
- "Embedding function mismatch"
- Segmentation faults

**Solution:**

1. **Stop the server** (Ctrl+C)

2. **Delete the ChromaDB directory:**
   ```bash
   rm -rf chroma_db/
   ```

   On Windows:
   ```cmd
   rmdir /s /q chroma_db
   ```

3. **Restart the server** - it will re-index all documents

---

### Issue: "No documents loaded" or "0 courses"

**Problem:** Documents not found or not processed

**Solution:**

1. **Check that docs folder exists:**
   ```bash
   ls docs/
   ```

2. **Verify course files are present:**
   ```bash
   ls docs/*.txt
   ```

3. **Check file permissions** (macOS/Linux):
   ```bash
   chmod 644 docs/*.txt
   ```

4. **Look at server logs** for error messages

5. **Manually trigger indexing** by deleting ChromaDB and restarting:
   ```bash
   rm -rf chroma_db/
   ./run.sh
   ```

---

### Issue: Windows Can't Run `run.sh`

**Problem:** Shell script not executable on Windows

**Solutions:**

**Option 1 - Use Git Bash:**
- Install Git for Windows (includes Git Bash)
- Open Git Bash
- Run `./run.sh`

**Option 2 - Use WSL (Windows Subsystem for Linux):**
```bash
wsl
./run.sh
```

**Option 3 - Run manually:**
```cmd
cd backend
uv run uvicorn app:app --reload --port 8000
```

---

### Issue: Slow First Query

**Problem:** First query takes 10-30 seconds

**Explanation:** This is normal! The first query loads the sentence-transformer model into memory.

**Subsequent queries:** Much faster (2-4 seconds)

---

### Issue: "Connection Refused" or Can't Access Web Interface

**Problem:** Server not running or wrong URL

**Solution:**

1. **Check server is running** - look for:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```

2. **Try alternative URLs:**
   - http://localhost:8000
   - http://127.0.0.1:8000
   - http://0.0.0.0:8000

3. **Check firewall settings** - ensure port 8000 is not blocked

4. **Restart the server**

---

### Issue: Claude API Errors

**Problem:** "Authentication error" or "Rate limit exceeded"

**Solutions:**

**Authentication Error:**
1. Verify your API key is valid
2. Check for extra spaces in `.env` file
3. Ensure API key starts with `sk-ant-api03-`

**Rate Limit:**
1. Wait a few minutes and try again
2. Check your Anthropic Console for usage limits
3. Consider upgrading your plan if needed

**Insufficient Credits:**
1. Add credits to your Anthropic account
2. Check billing settings in Anthropic Console

---

## Advanced Configuration

### Changing Server Host/Port

Edit the command in `run.sh` or run manually:

```bash
uv run uvicorn app:app --reload --host 0.0.0.0 --port 8080
```

- `--host 0.0.0.0` - Allow external connections
- `--port 8080` - Use port 8080

### Disabling Auto-Reload

For production, remove `--reload`:

```bash
uv run uvicorn app:app --host 0.0.0.0 --port 8000
```

### Configuring RAG Settings

Edit `backend/config.py` to adjust:

- `CHUNK_SIZE` - Size of text chunks (default: varies)
- `CHUNK_OVERLAP` - Overlap between chunks
- `MAX_RESULTS` - Number of search results
- `EMBEDDING_MODEL` - SentenceTransformer model
- `ANTHROPIC_MODEL` - Claude model version
- `MAX_HISTORY` - Conversation history length

### Adding New Course Documents

1. **Create a new `.txt` file** in `docs/` folder
2. **Follow the format:**
   ```
   Course Title: Your Course Name
   Course Link: https://example.com
   Course Instructor: Instructor Name

   Lesson 0: Introduction
   Lesson Link: https://example.com/lesson0
   [Content...]
   ```

3. **Restart the server** - it will auto-index new courses

4. **Or manually clear and rebuild:**
   ```bash
   rm -rf chroma_db/
   ./run.sh
   ```

---

## Project Structure

```
starting-ragchatbot-codebase/
├── backend/                    # Backend Python code
│   ├── app.py                 # FastAPI application
│   ├── rag_system.py          # RAG orchestration
│   ├── document_processor.py  # Document parsing/chunking
│   ├── vector_store.py        # ChromaDB interface
│   ├── ai_generator.py        # Claude API client
│   ├── search_tools.py        # Tool definitions
│   ├── session_manager.py     # Conversation history
│   ├── models.py              # Data models
│   └── config.py              # Configuration
├── frontend/                   # Frontend web interface
│   ├── index.html             # Main page
│   ├── script.js              # JavaScript logic
│   └── style.css              # Styling
├── docs/                       # Course documents
│   ├── course1_script.txt
│   ├── course2_script.txt
│   ├── course3_script.txt
│   └── course4_script.txt
├── chroma_db/                  # Vector database (auto-generated)
├── .env                        # Environment variables (you create)
├── .env.example                # Environment template
├── pyproject.toml              # Python dependencies
├── uv.lock                     # Dependency lock file
├── run.sh                      # Startup script
└── README.md                   # Project documentation
```

---

## Next Steps

After successfully running the application:

1. **Explore the chat interface** - Try different questions
2. **Check the API docs** - Visit http://localhost:8000/docs
3. **Add your own courses** - Create new `.txt` files in `docs/`
4. **Review the architecture** - See `docs/query_flow_sn.md`
5. **Understand document processing** - See `docs/pipeline_sn.md`
6. **View system diagrams** - See `docs/query_flow_diagram.md`

---

## Getting Help

If you encounter issues not covered in this guide:

1. **Check server logs** - Look for error messages in terminal
2. **Review API logs** - Check http://localhost:8000/docs for request details
3. **Check ChromaDB logs** - Look in `chroma_db/` directory
4. **Verify environment** - Run `uv run python --version`
5. **Test API key** - Make a simple request to Anthropic API

---

## Summary

**Quick Start (if everything is installed):**
```bash
# 1. Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 2. Install dependencies
uv sync

# 3. Run the application
./run.sh

# 4. Open browser
# Visit http://localhost:8000
```

That's it! You're ready to start querying your course materials.
