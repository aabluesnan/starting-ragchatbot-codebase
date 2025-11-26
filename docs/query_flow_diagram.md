# Query Flow Diagram

This document contains visual diagrams illustrating how user queries flow through the RAG chatbot system.

## Sequence Diagram: Complete Query Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(script.js)
    participant API as FastAPI<br/>(app.py)
    participant Session as SessionManager<br/>(session_manager.py)
    participant RAG as RAGSystem<br/>(rag_system.py)
    participant AI as AIGenerator<br/>(ai_generator.py)
    participant Claude as Claude API<br/>(Anthropic)
    participant Tools as ToolManager<br/>(search_tools.py)
    participant Vector as VectorStore<br/>(vector_store.py)
    participant Chroma as ChromaDB

    User->>Frontend: Types query & clicks Send
    Frontend->>Frontend: Disable input, show loading
    Frontend->>API: POST /api/query<br/>{query, session_id}

    API->>Session: Get or create session
    Session-->>API: session_id

    API->>RAG: query(user_query, session_id)

    RAG->>Session: get_conversation_history(session_id)
    Session-->>RAG: Previous messages (if any)

    RAG->>AI: generate_response()<br/>+ query<br/>+ history<br/>+ tools<br/>+ tool_manager

    AI->>Claude: messages.create()<br/>+ system prompt<br/>+ conversation history<br/>+ available tools<br/>+ user query

    Note over Claude: Analyzes query<br/>Decides if search needed

    alt Course-specific question
        Claude-->>AI: tool_use: search_course_content<br/>{query, course_name?, lesson_number?}

        AI->>Tools: execute_tool("search_course_content", kwargs)
        Tools->>Vector: search(query, course_name, lesson_number)

        opt Course name provided
            Vector->>Chroma: Query course_catalog<br/>(fuzzy match course name)
            Chroma-->>Vector: Resolved course title
        end

        Vector->>Vector: Build filter<br/>(course_title, lesson_number)
        Vector->>Chroma: Query course_content<br/>with embeddings + filters
        Chroma-->>Vector: Top N matching chunks<br/>+ metadata + distances

        Vector-->>Tools: SearchResults<br/>(documents, metadata, distances)
        Tools->>Tools: Format results with headers<br/>Track sources
        Tools-->>AI: Formatted search results

        AI->>Claude: messages.create()<br/>+ previous messages<br/>+ tool results
        Claude-->>AI: Synthesized answer
    else General knowledge question
        Claude-->>AI: Direct answer (no tool use)
    end

    AI-->>RAG: Final response text

    RAG->>Tools: get_last_sources()
    Tools-->>RAG: Source list

    RAG->>Session: add_exchange(session_id, query, response)
    Session->>Session: Store in memory<br/>Limit to MAX_HISTORY

    RAG-->>API: (answer, sources)

    API-->>Frontend: JSON Response<br/>{answer, sources, session_id}

    Frontend->>Frontend: Remove loading spinner
    Frontend->>Frontend: Render markdown answer<br/>Display sources (collapsible)
    Frontend->>Frontend: Re-enable input

    Frontend-->>User: Display response with sources
```

## Architecture Diagram: System Components

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[User Interface<br/>HTML/CSS/JS]
        B[Event Handlers]
        C[Fetch API]
    end

    subgraph "API Layer"
        D[FastAPI Server<br/>app.py]
        E[CORS Middleware]
        F[Endpoint Handlers]
    end

    subgraph "RAG System Core"
        G[RAG System<br/>rag_system.py]
        H[Session Manager<br/>session_manager.py]
        I[AI Generator<br/>ai_generator.py]
    end

    subgraph "Tool Execution Layer"
        J[Tool Manager<br/>search_tools.py]
        K[Course Search Tool]
    end

    subgraph "Storage Layer"
        L[Vector Store<br/>vector_store.py]
        M[ChromaDB<br/>Persistent Storage]
        N[SentenceTransformer<br/>Embeddings]
    end

    subgraph "External Services"
        O[Claude API<br/>Anthropic]
    end

    A --> B --> C
    C -->|HTTP POST| D
    D --> E --> F
    F --> G
    G --> H
    G --> I
    I -->|Tool definitions| J
    I -->|API calls| O
    J --> K
    K --> L
    L --> N
    L --> M
    O -->|Tool use decision| K
    O -->|Final response| I
    I --> G
    G --> F
    F -->|JSON| C
    C --> A

    style A fill:#e1f5ff
    style D fill:#ffe1f5
    style G fill:#fff5e1
    style J fill:#e1ffe1
    style L fill:#f5e1ff
    style O fill:#ffe1e1
```

## Data Flow Diagram: Query Processing

```mermaid
flowchart TD
    Start([User Submits Query]) --> Input[User Input: What is prompt caching?]

    Input --> FE[Frontend Processes]
    FE --> |POST Request|API[API Endpoint /api/query]

    API --> CheckSession{Session<br/>Exists?}
    CheckSession -->|No| CreateSession[Create New Session]
    CheckSession -->|Yes| GetHistory[Get Conversation History]
    CreateSession --> GetHistory

    GetHistory --> PreparePrompt[Prepare AI Request<br/>+ System Prompt<br/>+ History<br/>+ Tools<br/>+ Query]

    PreparePrompt --> Claude1[Claude API Call #1]

    Claude1 --> Decision{Tool Use<br/>Needed?}

    Decision -->|No| DirectAnswer[Claude Returns<br/>Direct Answer]

    Decision -->|Yes| ToolCall[Claude Requests:<br/>search_course_content<br/>query: prompt caching]

    ToolCall --> ResolveCourse{Course Name<br/>Provided?}

    ResolveCourse -->|Yes| FuzzyMatch[Vector Search in<br/>course_catalog<br/>for course name]
    ResolveCourse -->|No| BuildFilter[Build Filter<br/>lesson_number only]
    FuzzyMatch --> CourseTitle[Resolved Course Title]
    CourseTitle --> BuildFilter

    BuildFilter --> VectorSearch[Vector Search in<br/>course_content<br/>with filters]

    VectorSearch --> Embeddings[Generate Query Embedding<br/>SentenceTransformer]
    Embeddings --> ChromaQuery[ChromaDB Query<br/>Cosine Similarity<br/>Top 5 Results]

    ChromaQuery --> Results[Search Results:<br/>- Documents<br/>- Metadata<br/>- Distances]

    Results --> Format[Format Results<br/>Add Headers<br/>Track Sources]

    Format --> ToolResult[Return Formatted<br/>Results to Claude]

    ToolResult --> Claude2[Claude API Call #2<br/>with Tool Results]

    Claude2 --> Synthesize[Claude Synthesizes<br/>Answer from Results]

    Synthesize --> DirectAnswer

    DirectAnswer --> SaveHistory[Save to Session:<br/>User Query<br/>Assistant Response]

    SaveHistory --> ExtractSources[Extract Sources<br/>from Tool Manager]

    ExtractSources --> Response[Build API Response:<br/>answer<br/>sources<br/>session_id]

    Response --> RenderFE[Frontend Renders:<br/>- Markdown to HTML<br/>- Add Sources<br/>- Remove Loading]

    RenderFE --> Display([Display to User])

    style Start fill:#90EE90
    style Display fill:#90EE90
    style Claude1 fill:#FFB6C1
    style Claude2 fill:#FFB6C1
    style ChromaQuery fill:#DDA0DD
    style VectorSearch fill:#DDA0DD
    style Decision fill:#FFD700
    style ResolveCourse fill:#FFD700
```

## Component Interaction Diagram: Tool-Based Search

```mermaid
flowchart LR
    subgraph "AI Layer"
        A[Claude API]
    end

    subgraph "Tool Execution"
        B[ToolManager]
        C[CourseSearchTool]
    end

    subgraph "Vector Operations"
        D[VectorStore]
        E1[course_catalog<br/>Collection]
        E2[course_content<br/>Collection]
    end

    subgraph "Storage"
        F[ChromaDB<br/>Persistent]
    end

    A -->|1. tool_use decision| B
    B -->|2. execute_tool| C
    C -->|3a. resolve_course_name| D
    D -->|3b. query| E1
    E1 -->|3c. best match| D
    D -->|4a. search with filters| E2
    E2 -->|4b. vector query| F
    F -->|4c. top N results| E2
    E2 -->|4d. results| D
    D -->|5. SearchResults| C
    C -->|6. formatted text| B
    B -->|7. tool_result| A
    A -->|8. synthesized answer| B

    style A fill:#FFB6C1
    style B fill:#98FB98
    style C fill:#98FB98
    style D fill:#DDA0DD
    style E1 fill:#E6E6FA
    style E2 fill:#E6E6FA
    style F fill:#B0C4DE
```

## Session Management Diagram

```mermaid
stateDiagram-v2
    [*] --> NewSession: First Query
    NewSession --> Active: session_id created

    Active --> AddMessage: User Query
    AddMessage --> AddResponse: AI Response
    AddResponse --> Active: Exchange Stored

    Active --> GetHistory: Next Query
    GetHistory --> AddMessage: Include Context

    Active --> HistoryLimit: 10+ Messages
    HistoryLimit --> TrimHistory: Keep Last 10
    TrimHistory --> Active

    Active --> [*]: Session Ends

    note right of NewSession
        session_counter++
        session_id = f"session_{counter}"
        sessions[session_id] = []
    end note

    note right of AddMessage
        Store: Message(role="user", content=query)
    end note

    note right of AddResponse
        Store: Message(role="assistant", content=response)
    end note

    note right of GetHistory
        Format all messages:
        "User: query\nAssistant: response\n..."
        Pass to AI as context
    end note
```

## Vector Search Flow

```mermaid
flowchart TD
    Query[User Query:<br/>What is prompt caching?]

    Query --> Embed[Generate Embedding<br/>SentenceTransformer<br/>384-dim vector]

    Embed --> Compare[Compare with<br/>All Chunk Embeddings<br/>Cosine Similarity]

    Compare --> Filter{Filters<br/>Applied?}

    Filter -->|course_title| FilterCourse[Filter: course_title = X]
    Filter -->|lesson_number| FilterLesson[Filter: lesson_number = Y]
    Filter -->|both| FilterBoth[Filter: both conditions]
    Filter -->|none| NoFilter[No filtering]

    FilterCourse --> Rank
    FilterLesson --> Rank
    FilterBoth --> Rank
    NoFilter --> Rank

    Rank[Rank by Similarity<br/>Lower distance = Better]

    Rank --> TopN[Select Top 5 Results]

    TopN --> Results[Return:<br/>- Chunk content<br/>- Metadata<br/>- Distance scores]

    Results --> Format[Format with Context:<br/>[Course - Lesson N]<br/>chunk content...]

    style Query fill:#FFE4B5
    style Embed fill:#E0FFFF
    style Compare fill:#FFE4E1
    style Rank fill:#F0E68C
    style Results fill:#98FB98
```

## Document Processing vs Query Flow

```mermaid
graph LR
    subgraph "Indexing Phase (One-Time)"
        A1[Course Documents<br/>.txt files] --> B1[DocumentProcessor]
        B1 --> C1[Extract Metadata<br/>Parse Lessons]
        C1 --> D1[Chunk Text<br/>with Overlap]
        D1 --> E1[Generate Embeddings<br/>SentenceTransformer]
        E1 --> F1[Store in ChromaDB<br/>course_catalog<br/>course_content]
    end

    subgraph "Query Phase (Real-Time)"
        A2[User Query] --> B2[Generate Embedding]
        B2 --> C2[Vector Search<br/>in ChromaDB]
        F1 -.->|Uses indexed data| C2
        C2 --> D2[Retrieve Chunks]
        D2 --> E2[Send to Claude]
        E2 --> F2[Generate Answer]
    end

    style A1 fill:#FFE4B5
    style F1 fill:#DDA0DD
    style A2 fill:#98FB98
    style F2 fill:#98FB98
```

## Error Handling Flow

```mermaid
flowchart TD
    Start[User Query] --> Try1{Frontend<br/>Fetch OK?}

    Try1 -->|Error| FE_Error[Display Error in Chat<br/>Re-enable Input]
    Try1 -->|Success| Try2{API<br/>Response OK?}

    Try2 -->|500 Error| API_Error[HTTPException<br/>Return Error Detail]
    Try2 -->|Success| Try3{Session<br/>Valid?}

    Try3 -->|Invalid| Create[Create New Session]
    Try3 -->|Valid| Try4{Vector Search<br/>Successful?}
    Create --> Try4

    Try4 -->|Error| VectorError[Return SearchResults.empty<br/>with error message]
    Try4 -->|No Results| NoResults[Return: No relevant<br/>content found]
    Try4 -->|Success| Try5{Claude API<br/>Available?}

    Try5 -->|Error| AI_Error[Exception in<br/>generate_response]
    Try5 -->|Success| Success[Return Response<br/>with Sources]

    VectorError --> AI_Synthesize[Claude Synthesizes<br/>Error Context]
    NoResults --> AI_Synthesize
    AI_Synthesize --> Success

    API_Error --> FE_Error
    AI_Error --> API_Error

    Success --> Display[Display to User]
    FE_Error --> Display

    style FE_Error fill:#FFB6C1
    style API_Error fill:#FFB6C1
    style VectorError fill:#FFB6C1
    style AI_Error fill:#FFB6C1
    style Success fill:#90EE90
    style Display fill:#90EE90
```

---

## How to View These Diagrams

### Option 1: GitHub/GitLab
Push this file to a repository and view it on GitHub or GitLab - they render Mermaid diagrams automatically.

### Option 2: VS Code
Install the "Markdown Preview Mermaid Support" extension:
1. Open VS Code
2. Press `Ctrl+P` (Windows/Linux) or `Cmd+P` (Mac)
3. Type: `ext install bierner.markdown-mermaid`
4. Open this file and press `Ctrl+Shift+V` to preview

### Option 3: Online Mermaid Editor
1. Visit https://mermaid.live/
2. Copy any diagram code and paste it into the editor
3. See real-time rendering and export as PNG/SVG

### Option 4: Obsidian
Open this file in Obsidian - it has native Mermaid support.

---

## Diagram Descriptions

### 1. Sequence Diagram
Shows the chronological interaction between all components from user input to display. Best for understanding the order of operations.

### 2. Architecture Diagram
Shows the static structure of the system with all major components and their relationships. Best for understanding system organization.

### 3. Data Flow Diagram
Shows how data transforms as it moves through the query processing pipeline. Best for understanding data transformations.

### 4. Component Interaction Diagram
Focuses specifically on the tool-based search mechanism. Best for understanding RAG retrieval.

### 5. Session Management Diagram
Shows the state machine for conversation sessions. Best for understanding how history is maintained.

### 6. Vector Search Flow
Details the embedding and similarity search process. Best for understanding the core RAG retrieval mechanism.

### 7. Document Processing vs Query Flow
Compares the indexing phase with the query phase. Best for understanding the difference between setup and runtime.

### 8. Error Handling Flow
Shows all error paths and recovery mechanisms. Best for understanding system reliability.
