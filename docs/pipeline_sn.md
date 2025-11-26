# Document Processing Pipeline

This document explains how documents are processed in the RAG chatbot system.

## Document Processing Pipeline

### 1. **File Reading** (backend/document_processor.py:13-21)
Documents are read from the `docs/` folder using UTF-8 encoding with fallback error handling for encoding issues.

### 2. **Metadata Extraction** (backend/document_processor.py:97-146)
The system expects documents in a specific format:
```
Line 1: Course Title: [title]
Line 2: Course Link: [url]
Line 3: Course Instructor: [instructor]
```

The processor extracts this metadata using regex patterns and creates a `Course` object.

### 3. **Lesson Parsing** (backend/document_processor.py:162-218)
After metadata, the system looks for lesson markers like:
```
Lesson 0: Introduction
Lesson Link: [url]
[lesson content...]
```

Each lesson's content is collected separately with its number, title, and optional link.

### 4. **Text Chunking** (backend/document_processor.py:25-91)
The lesson content is split into smaller chunks with these characteristics:
- **Sentence-based splitting**: Uses regex to detect sentence boundaries (periods, exclamation marks, question marks)
- **Configurable chunk size**: Defined by `CHUNK_SIZE` config
- **Overlapping chunks**: `CHUNK_OVERLAP` ensures context continuity between chunks
- **Smart overlap calculation**: Counts backwards from chunk end to include overlapping sentences

### 5. **Context Enhancement** (backend/document_processor.py:184-188, 232-234)
Each chunk is enhanced with contextual information:
- First chunk of a lesson: `"Lesson {number} content: {chunk}"`
- Other chunks: `"Course {title} Lesson {number} content: {chunk}"`

This helps the AI understand context when retrieving chunks.

### 6. **Vector Storage** (backend/rag_system.py:38-46)
Processed chunks are stored in ChromaDB:
- **Course metadata** goes to `course_catalog` collection (titles, instructors, links)
- **Course content chunks** go to `course_content` collection with embeddings
- Uses **SentenceTransformer** for creating embeddings

### 7. **Deduplication** (backend/rag_system.py:75-96)
When adding courses from a folder, the system:
- Checks existing course titles
- Skips already-processed courses
- Only adds new courses to avoid duplicates

## Processing Flow Diagram
```
File (.txt/.pdf/.docx)
    ↓
Read File (UTF-8)
    ↓
Extract Metadata (Course Title, Link, Instructor)
    ↓
Parse Lessons (Lesson markers & content)
    ↓
Chunk Text (Sentence-based with overlap)
    ↓
Add Context (Course + Lesson info)
    ↓
Generate Embeddings (SentenceTransformer)
    ↓
Store in ChromaDB (Vector Store)
```

## Key Components

### DocumentProcessor
The `DocumentProcessor` class (backend/document_processor.py) handles:
- Reading files with proper encoding
- Extracting course and lesson metadata
- Chunking text with overlap
- Creating structured `Course` and `CourseChunk` objects

### RAGSystem
The `RAGSystem` class (backend/rag_system.py) orchestrates:
- Document processing workflow
- Vector store interactions
- Course catalog management
- Deduplication logic

### VectorStore
The `VectorStore` class (backend/vector_store.py) manages:
- ChromaDB collections for metadata and content
- Embedding generation using SentenceTransformer
- Semantic search capabilities
- Course and lesson filtering

## Usage

The entire pipeline is orchestrated by the `RAGSystem` class, which coordinates the document processor and vector store to transform course documents into searchable, semantically-indexed chunks.
