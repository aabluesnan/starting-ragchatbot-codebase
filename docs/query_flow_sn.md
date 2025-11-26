# Query Flow: From Frontend to Backend

This document traces the complete journey of a user query through the RAG chatbot system, from the frontend interface to the final AI-generated response.

---

## Complete Query Flow Diagram

```
User Input (Frontend)
    ↓
JavaScript Event Handler
    ↓
HTTP POST Request → /api/query
    ↓
FastAPI Backend Endpoint
    ↓
Session Manager (Create/Get Session)
    ↓
RAG System Query Handler
    ↓
AI Generator (Claude API)
    ↓
Tool Execution Loop (if needed)
    ├─→ CourseSearchTool
    │   ├─→ Vector Store Search
    │   │   ├─→ Resolve Course Name (optional)
    │   │   └─→ Query ChromaDB Content
    │   └─→ Format Results
    └─→ Return to AI for Synthesis
    ↓
Session Manager (Store History)
    ↓
HTTP Response (JSON)
    ↓
Frontend Display (Markdown Rendering)
```

---

## Detailed Step-by-Step Flow

### Phase 1: Frontend User Interaction

#### 1.1 User Input (frontend/script.js:45-55)
```javascript
// User types query and clicks send or presses Enter
async function sendMessage() {
    const query = chatInput.value.trim();

    // Disable input during processing
    chatInput.disabled = true;
    sendButton.disabled = true;

    // Display user message
    addMessage(query, 'user');

    // Show loading animation
    const loadingMessage = createLoadingMessage();
}
```

**Actions:**
- Capture user input from text field
- Disable input controls to prevent duplicate submissions
- Display user message in chat interface
- Show loading spinner

#### 1.2 HTTP Request (frontend/script.js:63-72)
```javascript
const response = await fetch(`${API_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        query: query,
        session_id: currentSessionId  // null for first query
    })
});
```

**Payload Structure:**
```json
{
    "query": "What is prompt caching?",
    "session_id": "session_1"  // or null
}
```

---

### Phase 2: Backend Request Handling

#### 2.1 FastAPI Endpoint (backend/app.py:56-74)
```python
@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    # Create session if not provided
    session_id = request.session_id
    if not session_id:
        session_id = rag_system.session_manager.create_session()

    # Process query using RAG system
    answer, sources = rag_system.query(request.query, session_id)

    return QueryResponse(
        answer=answer,
        sources=sources,
        session_id=session_id
    )
```

**Actions:**
- Validate request with Pydantic model
- Create new session if needed
- Delegate to RAG system
- Return structured JSON response

---

### Phase 3: Session Management

#### 3.1 Session Creation/Retrieval (backend/session_manager.py:18-23, 42-56)

**New Session:**
```python
def create_session(self) -> str:
    self.session_counter += 1
    session_id = f"session_{self.session_counter}"
    self.sessions[session_id] = []
    return session_id
```

**Get History:**
```python
def get_conversation_history(self, session_id: Optional[str]) -> Optional[str]:
    messages = self.sessions[session_id]
    formatted_messages = []
    for msg in messages:
        formatted_messages.append(f"{msg.role.title()}: {msg.content}")
    return "\n".join(formatted_messages)
```

**Purpose:**
- Maintain conversation context across multiple queries
- Format previous exchanges for AI context
- Limit history to `MAX_HISTORY` (default: 5 exchanges = 10 messages)

---

### Phase 4: RAG System Processing

#### 4.1 Query Handler (backend/rag_system.py:102-140)
```python
def query(self, query: str, session_id: Optional[str] = None) -> Tuple[str, List[str]]:
    # Create prompt
    prompt = f"Answer this question about course materials: {query}"

    # Get conversation history
    history = self.session_manager.get_conversation_history(session_id)

    # Generate response using AI with tools
    response = self.ai_generator.generate_response(
        query=prompt,
        conversation_history=history,
        tools=self.tool_manager.get_tool_definitions(),
        tool_manager=self.tool_manager
    )

    # Get sources from search tool
    sources = self.tool_manager.get_last_sources()

    # Update conversation history
    self.session_manager.add_exchange(session_id, query, response)

    return response, sources
```

**Flow:**
1. Wrap user query with instruction
2. Retrieve conversation history
3. Pass to AI generator with available tools
4. Extract sources from tool execution
5. Store query-response pair in session history

---

### Phase 5: AI Generation with Tool Use

#### 5.1 Initial AI Request (backend/ai_generator.py:43-87)
```python
def generate_response(self, query: str,
                     conversation_history: Optional[str] = None,
                     tools: Optional[List] = None,
                     tool_manager=None) -> str:

    # Build system prompt with history
    system_content = f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"

    # Prepare API call
    api_params = {
        "model": self.model,
        "temperature": 0,
        "max_tokens": 800,
        "messages": [{"role": "user", "content": query}],
        "system": system_content,
        "tools": tools,
        "tool_choice": {"type": "auto"}
    }

    # Get response from Claude
    response = self.client.messages.create(**api_params)
```

**System Prompt Instructs AI to:**
- Use search tool only for course-specific questions
- Maximum one search per query
- Answer general knowledge questions without searching
- Provide concise, educational responses
- No meta-commentary about the search process

#### 5.2 Tool Execution Decision
Claude analyzes the query and decides:
- **Course-specific question** → Use `search_course_content` tool
- **General knowledge** → Answer directly without tool use

---

### Phase 6: Tool Execution (If Needed)

#### 6.1 Tool Execution Handler (backend/ai_generator.py:89-135)
```python
def _handle_tool_execution(self, initial_response, base_params, tool_manager):
    # Add AI's tool use request to conversation
    messages.append({"role": "assistant", "content": initial_response.content})

    # Execute all tool calls
    for content_block in initial_response.content:
        if content_block.type == "tool_use":
            tool_result = tool_manager.execute_tool(
                content_block.name,  # "search_course_content"
                **content_block.input  # {query, course_name?, lesson_number?}
            )

    # Add tool results back to conversation
    messages.append({"role": "user", "content": tool_results})

    # Get final response from Claude
    final_response = self.client.messages.create(**final_params)
```

**Example Tool Call:**
```json
{
    "name": "search_course_content",
    "input": {
        "query": "prompt caching",
        "course_name": "Building Toward Computer Use"
    }
}
```

#### 6.2 CourseSearchTool Execution (backend/search_tools.py:52-86)
```python
def execute(self, query: str, course_name: Optional[str] = None,
            lesson_number: Optional[int] = None) -> str:

    # Use vector store's unified search
    results = self.store.search(
        query=query,
        course_name=course_name,
        lesson_number=lesson_number
    )

    # Handle errors or empty results
    if results.error or results.is_empty():
        return error_message

    # Format and return results
    return self._format_results(results)
```

---

### Phase 7: Vector Store Search

#### 7.1 Unified Search Interface (backend/vector_store.py:61-100)
```python
def search(self, query: str, course_name: Optional[str] = None,
           lesson_number: Optional[int] = None) -> SearchResults:

    # Step 1: Resolve course name if provided
    if course_name:
        course_title = self._resolve_course_name(course_name)
        if not course_title:
            return SearchResults.empty(f"No course found matching '{course_name}'")

    # Step 2: Build filter
    filter_dict = self._build_filter(course_title, lesson_number)

    # Step 3: Search course content with ChromaDB
    results = self.course_content.query(
        query_texts=[query],
        n_results=self.max_results,  # default: 5
        where=filter_dict
    )

    return SearchResults.from_chroma(results)
```

#### 7.2 Course Name Resolution (backend/vector_store.py:102-116)
**Handles fuzzy matching:**
- User input: "MCP" → Matches: "Building MCP Apps with Anthropic"
- User input: "computer use" → Matches: "Building Toward Computer Use with Anthropic"

```python
def _resolve_course_name(self, course_name: str) -> Optional[str]:
    # Semantic search in course catalog
    results = self.course_catalog.query(
        query_texts=[course_name],
        n_results=1
    )

    # Return best matching course title
    return results['metadatas'][0][0]['title']
```

#### 7.3 ChromaDB Vector Search
**Process:**
1. Convert query to embedding using SentenceTransformer
2. Calculate cosine similarity with stored chunk embeddings
3. Apply filters (course_title, lesson_number)
4. Return top N results by similarity

**Result Structure:**
```python
SearchResults(
    documents=["Chunk 1 content...", "Chunk 2 content..."],
    metadata=[
        {"course_title": "Course A", "lesson_number": 1, "chunk_index": 0},
        {"course_title": "Course A", "lesson_number": 2, "chunk_index": 5}
    ],
    distances=[0.15, 0.23]  # Lower = more similar
)
```

---

### Phase 8: Result Formatting

#### 8.1 Format Search Results (backend/search_tools.py:88-114)
```python
def _format_results(self, results: SearchResults) -> str:
    formatted = []
    sources = []

    for doc, meta in zip(results.documents, results.metadata):
        course_title = meta.get('course_title', 'unknown')
        lesson_num = meta.get('lesson_number')

        # Build context header
        header = f"[{course_title}"
        if lesson_num is not None:
            header += f" - Lesson {lesson_num}"
        header += "]"

        # Track source
        source = f"{course_title} - Lesson {lesson_num}"
        sources.append(source)

        formatted.append(f"{header}\n{doc}")

    # Store sources for API response
    self.last_sources = sources

    return "\n\n".join(formatted)
```

**Example Formatted Output:**
```
[Building Toward Computer Use with Anthropic - Lesson 1]
Prompt caching retains some of the results of processing prompts between
invocation to the model, which can be a large cost and latency saver.

[Building Toward Computer Use with Anthropic - Lesson 2]
With prompt caching, you can cache large contexts like documentation...
```

---

### Phase 9: Final AI Synthesis

#### 9.1 Second Claude API Call
**Conversation State:**
```
User: "Answer this question about course materials: What is prompt caching?"
Assistant: [tool_use: search_course_content with params]
User: [tool_result: formatted search results]
Assistant: [Final synthesized answer]
```

**AI Task:**
- Read search results
- Synthesize information into concise answer
- Follow system prompt guidelines (brief, educational, no meta-commentary)
- Generate response without mentioning "search results"

**Example Response:**
```
Prompt caching is a feature that retains the results of processing prompts
between model invocations, reducing both cost and latency. It's especially
useful for large contexts like documentation or long conversation histories,
as you don't need to reprocess the same content repeatedly.
```

---

### Phase 10: Response Assembly

#### 10.1 Update Session History (backend/session_manager.py:37-40)
```python
def add_exchange(self, session_id: str, user_message: str, assistant_message: str):
    self.add_message(session_id, "user", user_message)
    self.add_message(session_id, "assistant", assistant_message)
```

**Stored in Memory:**
```python
sessions["session_1"] = [
    Message(role="user", content="What is prompt caching?"),
    Message(role="assistant", content="Prompt caching is a feature...")
]
```

#### 10.2 Extract Sources (backend/rag_system.py:129-133)
```python
# Get sources from the search tool
sources = self.tool_manager.get_last_sources()

# Reset sources after retrieving them
self.tool_manager.reset_sources()
```

**Sources List:**
```python
[
    "Building Toward Computer Use with Anthropic - Lesson 1",
    "Building Toward Computer Use with Anthropic - Lesson 2"
]
```

#### 10.3 API Response (backend/app.py:68-72)
```python
return QueryResponse(
    answer=answer,
    sources=sources,
    session_id=session_id
)
```

**JSON Response:**
```json
{
    "answer": "Prompt caching is a feature that retains...",
    "sources": [
        "Building Toward Computer Use with Anthropic - Lesson 1",
        "Building Toward Computer Use with Anthropic - Lesson 2"
    ],
    "session_id": "session_1"
}
```

---

### Phase 11: Frontend Display

#### 11.1 Process Response (frontend/script.js:76-85)
```javascript
const data = await response.json();

// Update session ID if new
if (!currentSessionId) {
    currentSessionId = data.session_id;
}

// Replace loading message with response
loadingMessage.remove();
addMessage(data.answer, 'assistant', data.sources);
```

#### 11.2 Render Message (frontend/script.js:113-138)
```javascript
function addMessage(content, type, sources = null) {
    // Convert markdown to HTML for assistant messages
    const displayContent = type === 'assistant'
        ? marked.parse(content)  // Render markdown
        : escapeHtml(content);   // Escape HTML for user

    let html = `<div class="message-content">${displayContent}</div>`;

    // Add collapsible sources section
    if (sources && sources.length > 0) {
        html += `
            <details class="sources-collapsible">
                <summary class="sources-header">Sources</summary>
                <div class="sources-content">${sources.join(', ')}</div>
            </details>
        `;
    }

    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
}
```

#### 11.3 Final Display
**User sees:**
- AI response with markdown formatting (bold, lists, code blocks)
- Collapsible "Sources" section showing which courses/lessons were referenced
- Input field re-enabled for next query

---

## Performance Optimizations

### 1. Session Persistence
- Sessions stored in memory for fast access
- Limited history (5 exchanges) reduces token usage
- No database calls for conversation state

### 2. Vector Search Efficiency
- ChromaDB persistent storage avoids reloading embeddings
- SentenceTransformer embeddings cached in memory
- Configurable max_results limits computation

### 3. Tool Execution Strategy
- Maximum one search per query (enforced by system prompt)
- Automatic tool choice (Claude decides when to search)
- Direct answers for general knowledge (no search overhead)

### 4. Frontend Optimizations
- Single fetch request (no polling)
- Loading state prevents duplicate submissions
- Markdown rendering only for assistant messages

---

## Error Handling

### Frontend (frontend/script.js:87-95)
```javascript
catch (error) {
    loadingMessage.remove();
    addMessage(`Error: ${error.message}`, 'assistant');
} finally {
    chatInput.disabled = false;
    sendButton.disabled = false;
}
```

### Backend (backend/app.py:73-74)
```python
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

### Vector Store (backend/vector_store.py:92-100)
```python
try:
    results = self.course_content.query(...)
    return SearchResults.from_chroma(results)
except Exception as e:
    return SearchResults.empty(f"Search error: {str(e)}")
```

---

## Key Takeaways

1. **Two-Stage AI Interaction**: Initial request → Tool use decision → Tool execution → Final synthesis
2. **Smart Search**: Fuzzy course name matching + semantic content search
3. **Context Management**: Session history provides conversation continuity
4. **Source Tracking**: Sources flow from search tool → tool manager → API → frontend
5. **Separation of Concerns**: Clear boundaries between frontend, API, RAG logic, and AI generation
6. **Tool-Based RAG**: Claude decides when to search (vs. always searching)
7. **Semantic Everything**: Course resolution, content search, all use embeddings

---

## Example Complete Flow

**User Query:** "What does Colt say about tool use in lesson 2?"

1. **Frontend**: POST `/api/query` with query + session_id
2. **Backend**: Create/get session → Call RAG system
3. **Session**: Retrieve previous conversation context
4. **AI Generator**: Send to Claude with tools + history
5. **Claude Decision**: Detect course-specific question → Use search tool
6. **Tool Call**: `search_course_content(query="tool use", lesson_number=2)`
7. **Vector Store**:
   - No course name provided → Search all courses
   - Filter by lesson_number=2
   - Semantic search for "tool use"
   - Return top 5 chunks
8. **Format Results**: Add course/lesson headers, track sources
9. **Return to Claude**: Tool results with formatted content
10. **Claude Synthesis**: Generate concise answer from search results
11. **Session Update**: Store query + answer
12. **API Response**: JSON with answer + sources + session_id
13. **Frontend**: Render markdown response with collapsible sources

**Total Time**: ~2-4 seconds (depending on Claude API latency)
