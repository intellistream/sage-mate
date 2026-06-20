# Knowledge Base Storage

<cite>
**Referenced Files in This Document**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)
- [models.py](file://src/sage_faculty_twin/models.py)
- [config.py](file://src/sage_faculty_twin/config.py)
- [knowledge_import.py](file://src/sage_faculty_twin/knowledge_import.py)
- [test_knowledge_base.py](file://tests/test_knowledge_base.py)
- [test_sagevdb_knowledge_store.py](file://tests/test_sagevdb_knowledge_store.py)
- [test_bm25_backend_config.py](file://tests/test_bm25_backend_config.py)
- [conftest.py](file://tests/conftest.py)
</cite>

## Update Summary
**Changes Made**
- Enhanced backend selection system with improved model caching detection and automatic backend validation
- Added comprehensive knowledge backend plugins documentation covering new features
- Improved automatic backend validation with enhanced model availability checking
- Updated backend selection logic to prioritize FAISS over BM25 based on model caching detection
- Enhanced knowledge backend plugins documentation with new automatic validation features

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document explains the knowledge base storage system that powers multi-backend retrieval and persistence for the digital twin. The system has evolved to support an enhanced hybrid search approach that combines sagevdb candidate recall with sophisticated token-overlap plus tag-boost scoring. Recent enhancements include:

- Multi-backend architecture supporting Local (in-memory), SageVDB with SageANNs, and Neuromem backends
- Enhanced backend selection system with improved model caching detection and automatic backend validation
- Hybrid search approach: sagevdb provides candidate recall, followed by precise lexical scoring
- Advanced tokenization and span overlap scoring for improved technical query accuracy
- Profile-based scoring that considers visitor profiles, course contexts, and document intents
- Unlimited search operations without k-limit caps for comprehensive retrieval
- Enhanced embedding strategies: HashingTextEmbedder, SentenceTransformerTextEmbedder, and NeuromemBgeEmbedder
- Automatic backend migration from BM25 to SageVDB/SageANNs system with intelligent index type detection
- Practical ingestion and search workflows with improved accuracy and performance

## Project Structure
The knowledge base module centers around a single class that orchestrates document lifecycle and retrieval across multiple backends. Supporting modules define data models, configuration, and ingestion utilities.

```mermaid
graph TB
subgraph "Knowledge Base Module"
KB["LocalKnowledgeStore<br/>Enhanced Hybrid Search"]
E1["HashingTextEmbedder"]
E2["SentenceTransformerTextEmbedder"]
E3["NeuromemBgeEmbedder"]
end
subgraph "Models and Config"
M["Models<br/>Enhanced Scoring Algorithms"]
C["AppSettings<br/>retrieval_top_k Setting"]
end
subgraph "Ingestion"
I["Knowledge Import<br/>Advanced Processing"]
end
subgraph "Testing and Validation"
T1["test_knowledge_base.py<br/>Hybrid Search Tests"]
T2["test_sagevdb_knowledge_store.py"]
T3["test_bm25_backend_config.py"]
T4["conftest.py<br/>Model Caching Detection"]
end
KB --> E1
KB --> E2
KB --> E3
KB --> M
KB --> C
I --> KB
I --> M
T1 --> KB
T2 --> KB
T3 --> KB
T4 --> KB
```

**Diagram sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)
- [models.py](file://src/sage_faculty_twin/models.py)
- [config.py](file://src/sage_faculty_twin/config.py)
- [knowledge_import.py](file://src/sage_faculty_twin/knowledge_import.py)
- [test_knowledge_base.py](file://tests/test_knowledge_base.py)
- [test_sagevdb_knowledge_store.py](file://tests/test_sagevdb_knowledge_store.py)
- [test_bm25_backend_config.py](file://tests/test_bm25_backend_config.py)
- [conftest.py](file://tests/conftest.py)

**Section sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)
- [models.py](file://src/sage_faculty_twin/models.py)
- [config.py](file://src/sage_faculty_twin/config.py)
- [knowledge_import.py](file://src/sage_faculty_twin/knowledge_import.py)
- [test_knowledge_base.py](file://tests/test_knowledge_base.py)
- [test_sagevdb_knowledge_store.py](file://tests/test_sagevdb_knowledge_store.py)
- [test_bm25_backend_config.py](file://tests/test_bm25_backend_config.py)
- [conftest.py](file://tests/conftest.py)

## Core Components
- LocalKnowledgeStore: Orchestrates document lifecycle, backend selection, indexing, and search across Local, SageVDB, and Neuromem backends with enhanced hybrid search capabilities
- Enhanced Backend Selection System: Improved model caching detection with automatic backend validation and intelligent index type selection
- Enhanced Scoring System: Custom token-overlap plus tag-boost scoring with profile-based relevance calculation
- Advanced Tokenization: Comprehensive text tokenization supporting both English and Chinese characters with maximal span deduplication
- Embedding Strategies: Hashing-based and sentence-transformer-based embedders for dense retrieval; Neuromem-specific embedder for FAISS index
- Query Profiling: Intelligent query analysis that extracts document types, topics, courses, and named entities
- Unlimited Search Operations: Removed k-limit caps for comprehensive retrieval without artificial constraints
- Automatic Backend Migration: Automatically migrates from BM25 to SageVDB/SageANNs system with FAISS preference

Key responsibilities:
- Persistence: Documents are stored as JSON under a configured directory and kept in-memory for fast iteration
- Deduplication: Removes duplicates by source_name and normalizes metadata during load and upsert
- Visibility: Enforces audience-based visibility using visitor/admin roles
- Indexing: Builds and rebuilds indexes for selected backends with intelligent index type selection
- Enhanced Search: Implements hybrid approach with sagevdb candidate recall and precise lexical scoring
- Backend Migration: Automatically migrates from BM25 to SageVDB/SageANNs system with FAISS preference
- Model Caching Detection: Validates embedding model availability before enabling FAISS backend

**Section sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)
- [models.py](file://src/sage_faculty_twin/models.py)
- [config.py](file://src/sage_faculty_twin/config.py)
- [knowledge_import.py](file://src/sage_faculty_twin/knowledge_import.py)
- [conftest.py](file://tests/conftest.py)

## Architecture Overview
The system supports three backends with enhanced hybrid search capabilities and improved backend validation:

- Local: Pure Python lexical scoring with advanced token overlap and tag-boost algorithms
- SageVDB: Vector database with SageANNs integration and automatic FAISS preference
- Neuromem: Unified collection with automatic index type detection preferring FAISS over BM25 based on model caching validation

```mermaid
graph TB
Client["Client"]
Store["LocalKnowledgeStore<br/>Enhanced Hybrid Search"]
Local["Local Backend<br/>Advanced Lexical Scoring"]
SageVDB["SageVDB Backend<br/>Vector Index with SageANNs<br/>Candidate Recall"]
Neuromem["Neuromem Backend<br/>Unified Collection<br/>Auto Index Detection<br/>Model Caching Validation"]
Client --> Store
Store --> Local
Store --> SageVDB
Store --> Neuromem
SageVDB --> Local
Neuromem --> Local
Neuromem --> Validation["Model Caching Detection<br/>Automatic Backend Validation"]
Validation --> FAISS["FAISS Index<br/>Dense Retrieval"]
Validation --> BM25["BM25 Index<br/>Sparse Retrieval"]
```

**Diagram sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)
- [conftest.py](file://tests/conftest.py)

## Detailed Component Analysis

### Enhanced Backend Selection System
The LocalKnowledgeStore now implements an enhanced backend selection system with improved model caching detection and automatic backend validation:

**Enhanced Backend Selection Features:**
- Automatic model caching detection using `_embedding_model_is_cached()` function
- Intelligent backend validation before enabling FAISS vs BM25 selection
- Improved error handling with descriptive runtime errors for missing dependencies
- Enhanced configuration validation for embedding models and dimensions

**Enhanced Backend Selection Logic:**
- Auto-detection of sentence-transformers availability for FAISS backend
- Fallback to BM25 sparse retrieval when models are not cached
- Runtime validation of embedding model dimensions and compatibility
- Automatic backend switching based on model availability

**Enhanced Backend-specific Behaviors:**
- Local: Uses advanced token-overlap scoring with maximal span deduplication and tag-boost algorithms
- SageVDB: Provides candidate recall using dense vectors, then applies precise lexical re-ranking
- Neuromem: Automatic index type detection preferring FAISS (dense retrieval) when sentence-transformers is available, falls back to BM25 otherwise

```mermaid
classDiagram
class LocalKnowledgeStore {
+add_document(payload, rebuild_indexes)
+upsert_document(payload, rebuild_indexes)
+update_document(document_id, payload, rebuild_indexes)
+list_documents()
+get_document(document_id)
+delete_documents(document_ids, rebuild_indexes)
+rebuild_indexes()
+search(query, top_k, visitor_profile, admin_role)
+count_documents()
+backend_name()
+embedding_backend_name()
+_initialize_sagevdb()
+_initialize_neuromem()
+_rebuild_backend_indexes()
+_score_document(document, query_tokens, query_profile)
+_finalize_hits(hits, query_profile, limit)
+_expand_retrieval_text(text)
+_tokenize(text)
+_compose_retrieval_text(document)
+_normalize_sagevdb_backend()
+_uses_sagevdb_anns_backend()
+_build_text_embedder(np_module)
}
class HashingTextEmbedder {
+encode(text)
+dimension
}
class SentenceTransformerTextEmbedder {
+encode(text)
+dimension
}
class NeuromemBgeEmbedder {
+encode(text)
+dimension
}
class BackendSelectionSystem {
+_embedding_model_is_cached(model_name)
+_validate_backend_availability()
+_select_optimal_backend()
}
LocalKnowledgeStore --> HashingTextEmbedder : "uses"
LocalKnowledgeStore --> SentenceTransformerTextEmbedder : "uses"
LocalKnowledgeStore --> NeuromemBgeEmbedder : "uses"
LocalKnowledgeStore --> BackendSelectionSystem : "uses"
```

**Diagram sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)
- [conftest.py](file://tests/conftest.py)

**Section sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)
- [conftest.py](file://tests/conftest.py)

### LocalKnowledgeStore
The LocalKnowledgeStore now implements an enhanced hybrid search approach that combines the strengths of vector-based candidate recall with precise lexical scoring:

**Enhanced Responsibilities:**
- Initialize backend based on settings with automatic migration support
- Manage document lifecycle: add, upsert, update, list, delete
- Persist documents to disk and maintain in-memory registry
- Build and rebuild indexes for selected backends with intelligent index type detection
- **Enhanced Search**: Hybrid approach with sagevdb candidate recall and custom token-overlap scoring
- **Removed K-Limit Caps**: Unlimited search operations for comprehensive retrieval
- **Profile-Based Scoring**: Advanced query profiling with visitor profiles, course contexts, and document intents
- Deduplicate documents by source_name and normalize metadata

**Enhanced Lifecycle Highlights:**
- Initialization loads persisted documents, infers missing metadata, and removes duplicates
- Add/upsert/update write JSON files and update in-memory registry
- Rebuild triggers backend-specific index initialization with automatic migration
- **Enhanced Search**: Routes to backend-specific handlers, collects candidates, then applies precise lexical scoring

**Enhanced Backend-specific Behaviors:**
- Local: Uses advanced token-overlap scoring with maximal span deduplication and tag-boost algorithms
- SageVDB: Provides candidate recall using dense vectors, then applies precise lexical re-ranking
- Neuromem: Automatic index type detection preferring FAISS (dense retrieval) when sentence-transformers is available, falls back to BM25 otherwise

```mermaid
classDiagram
class LocalKnowledgeStore {
+add_document(payload, rebuild_indexes)
+upsert_document(payload, rebuild_indexes)
+update_document(document_id, payload, rebuild_indexes)
+list_documents()
+get_document(document_id)
+delete_documents(document_ids, rebuild_indexes)
+rebuild_indexes()
+search(query, top_k, visitor_profile, admin_role)
+count_documents()
+backend_name()
+embedding_backend_name()
+_initialize_sagevdb()
+_initialize_neuromem()
+_rebuild_backend_indexes()
+_score_document(document, query_tokens, query_profile)
+_finalize_hits(hits, query_profile, limit)
+_expand_retrieval_text(text)
+_tokenize(text)
+_compose_retrieval_text(document)
}
class HashingTextEmbedder {
+encode(text)
+dimension
}
class SentenceTransformerTextEmbedder {
+encode(text)
+dimension
}
class NeuromemBgeEmbedder {
+encode(text)
+dimension
}
LocalKnowledgeStore --> HashingTextEmbedder : "uses"
LocalKnowledgeStore --> SentenceTransformerTextEmbedder : "uses"
LocalKnowledgeStore --> NeuromemBgeEmbedder : "uses"
```

**Diagram sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

**Section sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

### Enhanced Scoring Algorithms
The system now implements sophisticated scoring algorithms that combine vector-based candidate recall with precise lexical scoring:

**Token Overlap Scoring:**
- Maximal span deduplication to reward longer, more specific matches over short, generic ones
- Advanced Chinese character processing with n-gram extraction (2-grams, 3-grams)
- Length-squared scoring to penalize overlapping spans appropriately

**Tag-Boost Scoring:**
- Semantic tag matching with weighted scoring (title: 3x, content: 1x, tags: 2x)
- Intent-based boosting based on document types, research focus, and meeting domains
- Course scope matching with positive/negative scoring based on course alignment

**Profile-Based Scoring:**
- Visitor profile adaptation: hust_undergraduate, paper_writing_student, lab_member, general_visitor
- Course context awareness with positive/negative scoring for course-specific queries
- Named entity recognition for technical queries with specialized boosting
- Feedback signal integration for web review status

**Query Profiling:**
- Automatic extraction of document types (tutorial, lecture, experiment)
- Topic domain identification (teaching, research, meeting)
- Course ID inference from query text
- Named entity extraction for technical terminology
- Ordinal number detection for lecture/experiment references

```mermaid
classDiagram
class ScoringSystem {
+token_overlap_score(text, query_tokens)
+tag_boost_score(document, query_profile)
+intent_boost(document, query_profile)
+profile_boost(document, query_profile)
+course_scope_boost(document, query_profile)
+feedback_boost(document, query_profile)
+final_score(document, query_profile)
}
class QueryProfile {
+document_types : frozenset[str]
+ordinal_numbers : frozenset[str]
+topic_domains : frozenset[str]
+course_ids : frozenset[str]
+research_focus : str
+prefers_intro_parts : bool
+named_entities : frozenset[str]
+visitor_profile : str
+admin_role : str
}
ScoringSystem --> QueryProfile : "analyzes"
```

**Diagram sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

**Section sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

### Enhanced Search and Ranking
The search functionality now implements a sophisticated hybrid approach:

**Hybrid Search Pipeline:**
1. **SageVDB Candidate Recall**: Dense vector search provides initial candidate documents
2. **Neuromem Hybrid Approach**: Combines FAISS dense recall with lexical scoring
3. **Local Advanced Scoring**: Precise token-overlap plus tag-boost scoring
4. **Profile-Based Re-ranking**: Context-aware re-ranking based on visitor profiles and query intent

**Enhanced Ranking Algorithm:**
- **Base Score**: Token overlap (title: 3x, content: 1x, tags: 2x) plus tag overlap
- **Intent Boost**: Document type matching, ordinal number detection, research focus
- **Profile Boost**: Visitor profile adaptation with domain-specific preferences
- **Course Scope**: Positive/negative scoring based on course alignment
- **Feedback Signals**: Integration of web review status and document freshness

**Removed K-Limit Caps:**
- Unlimited search operations for comprehensive retrieval
- Dynamic limit calculation based on query complexity and backend capabilities
- Intelligent candidate filtering to maintain performance while maximizing recall

```mermaid
sequenceDiagram
participant Client as "Client"
participant Store as "LocalKnowledgeStore"
participant Backend as "Backend"
participant Scorer as "Scoring Engine"
participant Final as "Finalizer"
Client->>Store : search(query, top_k=None)
alt backend=sagevdb
Store->>Backend : dense search (no k-limit)
Backend-->>Store : candidate documents
Store->>Scorer : re-rank with token-overlap + tag-boost
Scorer-->>Store : precise scores
else backend=neuromem
Store->>Backend : hybrid recall (faiss + lexical)
Backend-->>Store : mixed candidates
Store->>Scorer : profile-based re-ranking
Scorer-->>Store : enhanced scores
else local
Store->>Store : advanced lexical scoring
Store->>Scorer : token-overlap + tag-boost
Scorer-->>Store : final scores
end
Store->>Final : deduplicate by source group
Final-->>Client : ranked results
```

**Diagram sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

**Section sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

### Enhanced Tokenization and Text Processing
The system implements comprehensive text processing for improved search accuracy:

**Advanced Tokenization:**
- English word tokenization with alphanumeric and underscore handling
- Chinese character processing with maximal span extraction (1-char, 2-char, 3-char n-grams)
- Unicode range support for Chinese characters (U+4E00-U+9FFF)
- Lowercase normalization and token deduplication

**Span Overlap Scoring:**
- Maximal span selection to avoid overlapping matches
- Length-squared scoring to reward longer, more specific matches
- Greedy algorithm for optimal span selection
- Support for both English tokens and Chinese character spans

**Query Expansion:**
- Automatic retrieval text expansion with tokenized versions
- Enhanced text composition combining title, tags, aliases, and content
- Metadata integration for comprehensive search coverage

```mermaid
flowchart TD
Start(["Input Text"]) --> Tokenize["Tokenize Text"]
Tokenize --> EnglishTokens["Extract English Tokens"]
Tokenize --> ChineseChars["Extract Chinese Characters"]
EnglishTokens --> Normalize["Normalize & Deduplicate"]
ChineseChars --> Ngrams["Generate N-grams (1,2,3)"]
Ngrams --> Combine["Combine All Tokens"]
Normalize --> Combine
Combine --> Output["Query Tokens"]
```

**Diagram sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

**Section sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

### Document Lifecycle and Persistence
- Add: Creates a new record with UUID, persists JSON, updates in-memory registry, and optionally rebuilds backend index
- Upsert: Finds existing by source_name, compares fields, updates if changed, removes duplicates, rebuilds indexes if requested
- Update: Modifies existing record, persists JSON, removes duplicates, rebuilds indexes if requested
- Delete: Removes records by IDs, deletes JSON files, clears vector ID mapping, rebuilds indexes if requested
- Load: On startup, reads all JSON files, infers missing metadata, and deduplicates by source_name

```mermaid
sequenceDiagram
participant Client as "Client"
participant Store as "LocalKnowledgeStore"
participant FS as "Filesystem"
participant Backend as "Backend"
Client->>Store : add_document(payload)
Store->>FS : write JSON
Store->>Store : update in-memory registry
alt backend=sagevdb or neuromem
Store->>Backend : add_to_index
end
Store-->>Client : KnowledgeDocumentRecord
```

**Diagram sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

**Section sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

### Enhanced Metadata Handling and Deduplication
- Metadata inference: Extracts identity, domain, course_id, material_type, ordinal_type/number from tags and source_name
- Backfill: Legacy records without metadata have inferred metadata populated on load
- Deduplication: Removes older duplicates for the same source_name; preserves newest by creation time
- Audience visibility: Filters results by allowed audiences derived from visitor/admin roles
- **Enhanced Source Grouping**: Improved deduplication by canonical source groups with knowledge gap handling

```mermaid
flowchart TD
Start(["Load Documents"]) --> ReadJSON["Read JSON files"]
ReadJSON --> InferMeta["Infer missing metadata"]
InferMeta --> GroupBySource["Group by source_name"]
GroupBySource --> RemoveOlder["Remove older duplicates"]
RemoveOlder --> EnhanceGroups["Enhance source groups"]
EnhanceGroups --> Persist["Persist cleaned registry"]
Persist --> End(["Ready"])
```

**Diagram sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

**Section sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

### Ingestion Pipeline
- Homepage ingestion: Parses markdown pages, extracts sections, builds payloads with tags and source_name, upserts into store, prunes stale documents, and rebuilds indexes
- Chunking: Long content split into parts with ::part-N suffix for source grouping
- Attachments: PDFs and office docs parsed and ingested as separate documents

```mermaid
flowchart TD
A["Scan Homepage Directory"] --> B["Parse Markdown Sections"]
B --> C["Build Payloads (title, content, tags, source_name)"]
C --> D["Upsert into LocalKnowledgeStore"]
D --> E{"Stale documents?"}
E -- Yes --> F["Delete stale by source_name"]
E -- No --> G["Skip deletion"]
F --> H["Rebuild indexes"]
G --> H
H --> I["Done"]
```

**Diagram sources**
- [knowledge_import.py](file://src/sage_faculty_twin/knowledge_import.py)
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

**Section sources**
- [knowledge_import.py](file://src/sage_faculty_twin/knowledge_import.py)
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)

## Dependency Analysis
- LocalKnowledgeStore depends on:
  - AppSettings for backend and embedding configuration with automatic migration support
  - Models for typed payloads and records with enhanced scoring data structures
  - Backend libraries (sagevdb, isage-neuromem) when enabled
  - Enhanced model caching detection system for automatic backend validation
- Embedding strategies depend on external packages (numpy, sentence-transformers)
- Ingestion utilities depend on LocalKnowledgeStore and models

```mermaid
graph LR
Settings["AppSettings<br/>retrieval_top_k=3"] --> Store["LocalKnowledgeStore<br/>Enhanced Hybrid Search"]
Models["Models<br/>Enhanced Scoring"] --> Store
Store --> SageVDB["sagevdb"]
Store --> Neuromem["isage-neuromem"]
Store --> Embed1["HashingTextEmbedder"]
Store --> Embed2["SentenceTransformerTextEmbedder"]
Store --> Embed3["NeuromemBgeEmbedder"]
Store --> Validation["Model Caching Detection<br/>Automatic Backend Validation"]
Import["knowledge_import.py"] --> Store
```

**Diagram sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)
- [models.py](file://src/sage_faculty_twin/models.py)
- [config.py](file://src/sage_faculty_twin/config.py)
- [knowledge_import.py](file://src/sage_faculty_twin/knowledge_import.py)
- [conftest.py](file://tests/conftest.py)

**Section sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)
- [models.py](file://src/sage_faculty_twin/models.py)
- [config.py](file://src/sage_faculty_twin/config.py)
- [knowledge_import.py](file://src/sage_faculty_twin/knowledge_import.py)
- [conftest.py](file://tests/conftest.py)

## Performance Considerations
- **Enhanced SageVDB ANN Performance:**
  - Prefer ANN backends (e.g., FAISS HNSW) for large-scale dense retrieval
  - Use INNER_PRODUCT metric for ANN backends; COSINE otherwise
  - Batch-build index with stacked vectors for speed
  - **Removed K-Limit Caps**: SageVDB now provides unlimited candidate recall for comprehensive retrieval

- **SageVDB Hash Embeddings:**
  - Deterministic hashing avoids model overhead; suitable for CPU-only environments
  - Enhanced scoring algorithms work effectively with hash embeddings

- **Neuromem FAISS Performance:**
  - Batch-encode all documents to minimize latency
  - Use FAISS index with cosine metric for BGE embeddings
  - Automatic index type detection prefers FAISS over BM25 for better performance
  - **Hybrid Approach**: Combines dense recall with lexical scoring for optimal accuracy
  - **Enhanced Model Caching**: Automatic validation ensures FAISS backend only activates when models are cached

- **Local Backend Optimizations:**
  - Efficient for small to medium corpora; leverage advanced tokenization and scoring heuristics
  - **Maximal Span Deduplication**: Prevents inflated scores from overlapping matches
  - **Profile-Based Filtering**: Early filtering reduces computational overhead

- **Memory Management:**
  - Keep only necessary documents in memory; rely on persistent JSON for durability
  - Defer index rebuilds to batch operations (e.g., after ingestion)
  - **Enhanced Deduplication**: Improved source group handling reduces memory footprint

- **Index Rebuilding:**
  - Rebuild indexes after bulk operations to maintain accuracy and performance
  - **Dynamic Limit Calculation**: Backend-specific optimization based on document counts

- **Backend Migration Benefits:**
  - Automatic migration from BM25 to SageVDB/SageANNs system improves retrieval quality and performance
  - **Hybrid Search Advantages**: Combining vector recall with lexical precision

- **Enhanced Model Caching Benefits:**
  - Prevents runtime model downloads during backend initialization
  - Ensures consistent performance by avoiding network-dependent model loading
  - Automatic fallback to BM25 when models are not available

**Updated** Enhanced performance considerations now include hybrid search benefits, removed k-limit caps, advanced scoring optimizations, and model caching validation

**Section sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)
- [config.py](file://src/sage_faculty_twin/config.py)
- [conftest.py](file://tests/conftest.py)

## Troubleshooting Guide
Common issues and resolutions:
- **Missing backend dependencies:**
  - SageVDB: Install via package or expose checkout on PYTHONPATH
  - Neuromem: Install isage-neuromem
  - sentence-transformers: Install for dense embeddings
  - **Enhanced Dependencies**: Additional requirements for hybrid search (numpy, advanced tokenizers)

- **Dimension mismatches:**
  - Verify embedding model reports a dimension; ensure settings match
  - **Enhanced Verification**: Additional checks for hybrid scoring algorithms

- **SageVDB ANN configuration:**
  - Provide algorithm name for sage-anns backend
  - **Enhanced Configuration**: Additional parameters for hybrid search optimization

- **Visibility filtering:**
  - Ensure audience tags or metadata align with visitor/admin roles
  - **Enhanced Profile Matching**: Improved visitor profile handling

- **Duplicate documents:**
  - Use upsert with source_name to deduplicate automatically
  - **Enhanced Deduplication**: Improved source group canonicalization

- **Index rebuild failures:**
  - Trigger rebuild_indexes after ingestion or configuration changes
  - **Enhanced Rebuild Logic**: Better handling of hybrid search indexes

- **Backend migration issues:**
  - Automatic migration handles BM25 to SageVDB/SageANNs transition seamlessly
  - **Enhanced Migration**: Improved hybrid search integration

- **Search Performance Issues:**
  - **Check retrieval_top_k setting**: Default is 3, adjust based on query complexity
  - **Monitor hybrid search performance**: SageVDB candidate recall combined with lexical scoring
  - **Verify tokenization**: Ensure proper English/Chinese text processing

- **Model Caching Issues:**
  - **Check embedding model availability**: Use `_embedding_model_is_cached()` to validate model presence
  - **Network download prevention**: Tests automatically set offline mode to prevent model downloads
  - **Automatic backend fallback**: FAISS backend automatically falls back to BM25 when models are not cached

- **Backend Selection Problems:**
  - **Verify backend configuration**: Check `neuromem_index_type` setting and model availability
  - **Runtime validation errors**: Enhanced error messages for missing dependencies or invalid configurations

**Updated** Added troubleshooting guidance for enhanced hybrid search, removed k-limit caps, advanced scoring algorithms, and model caching validation

**Section sources**
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)
- [test_sagevdb_knowledge_store.py](file://tests/test_sagevdb_knowledge_store.py)
- [test_knowledge_base.py](file://tests/test_knowledge_base.py)
- [test_bm25_backend_config.py](file://tests/test_bm25_backend_config.py)
- [conftest.py](file://tests/conftest.py)

## Conclusion
The knowledge base storage system now offers a sophisticated, multi-backend architecture with enhanced hybrid search capabilities and improved backend validation. The recent enhancements include advanced token-overlap plus tag-boost scoring, profile-based relevance calculation, unlimited search operations without k-limit caps, and an enhanced backend selection system with model caching detection. The hybrid approach combining sagevdb candidate recall with precise lexical scoring provides superior accuracy for technical queries while maintaining excellent performance. By leveraging local advanced scoring, dense retrieval with SageVDB, and hybrid FAISS/BM25 with Neuromem, it scales from small deployments to large knowledge bases while delivering exceptional search quality and user experience. The enhanced model caching detection system ensures reliable backend selection and prevents runtime model downloads, making the system more robust and production-ready.

**Updated** Enhanced conclusion reflecting the successful implementation of hybrid search, advanced scoring algorithms, performance optimizations, and improved backend validation with model caching detection

## Appendices

### Practical Examples

**Enhanced Document ingestion from homepage:**
- Use the ingestion pipeline to parse markdown sections and attachments, upsert payloads, prune stale documents, and rebuild indexes with improved hybrid search capabilities.

**Upsert with source_name tracking:**
- Upsert preserves created_at and avoids unnecessary writes when content is unchanged; duplicates are removed and indexes rebuilt if requested with enhanced deduplication logic.

**Enhanced Index rebuilding:**
- Call rebuild_indexes after bulk add/update/delete operations to refresh backend indices with hybrid search optimizations.

**Advanced Search with visitor/admin roles:**
- Use visitor_profile and admin_role to enforce audience visibility and tailor ranking with sophisticated profile-based scoring algorithms.

**Hybrid Backend migration:**
- Automatic migration from BM25 to SageVDB/SageANNs system with FAISS preference for optimal performance and enhanced hybrid search capabilities.

**Technical Query Processing:**
- Leverage advanced tokenization for Chinese text processing, maximal span overlap scoring, and named entity recognition for improved technical query accuracy.

**Unlimited Search Operations:**
- Utilize the enhanced search functionality that removes k-limit caps while maintaining performance through intelligent candidate filtering and profile-based re-ranking.

**Enhanced Model Caching Validation:**
- Use `_embedding_model_is_cached()` to validate model availability before enabling FAISS backend, ensuring reliable operation without network dependencies.

**Automatic Backend Selection:**
- Configure `neuromem_index_type` to "auto" for automatic FAISS vs BM25 selection based on model caching detection and availability.

**Section sources**
- [knowledge_import.py](file://src/sage_faculty_twin/knowledge_import.py)
- [knowledge_base.py](file://src/sage_faculty_twin/knowledge_base.py)
- [test_knowledge_base.py](file://tests/test_knowledge_base.py)
- [test_sagevdb_knowledge_store.py](file://tests/test_sagevdb_knowledge_store.py)
- [test_bm25_backend_config.py](file://tests/test_bm25_backend_config.py)
- [conftest.py](file://tests/conftest.py)