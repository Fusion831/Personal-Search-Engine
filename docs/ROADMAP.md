# 🔮 Future Features & Roadmap

This document outlines planned features and improvements ranked by importance. Features are organized by category, with implementation priority indicated.

---

## Conversational Intelligence

### Feature Ranking by Importance

1. **Multi-turn Conversation Memory** (Critical)
   - Maintain conversation context across multiple queries

2. **Context Window Management** (High)
   - Optimize chat history for token efficiency

3. **Conversation Summarization** (Medium)
   - Summarize long conversation threads for context

---

## Advanced Retrieval & Generation

### Feature Ranking by Importance

1. **Hybrid Search** (Critical)
   - Combine BM25 keyword search with vector similarity

2. **Re-ranking with Cross-Encoders** (High)
   - Improve ranking precision for top results

3. **Query Expansion** (High)
   - Multi-query generation and semantic expansion for better recall

4. **Multi-modal Support** (Medium)
   - Extract and process images and tables from PDFs

---

## RAG Evaluation Pipeline with RAGAS

### Feature Ranking by Importance

1. **Integrate RAGAS Framework** (Critical)
   - Core integration of Retrieval-Augmented Generation Assessment

2. **Comprehensive Evaluation Metrics** (Critical)
   - Retrieval metrics: Context Precision, Context Recall, Context Relevancy
   - Generation metrics: Faithfulness, Answer Relevancy, Answer Semantic Similarity
   - LLM-as-a-Judge scoring for end-to-end evaluation

3. **Deep RAG Component Analysis** (High)
   - Measure HyDe query transformation effectiveness
   - Evaluate intelligent routing accuracy
   - Analyze parent-child chunking impact on precision/recall trade-off
   - Track parent deduplication impact on token optimization

4. **Evaluation Dataset Management** (High)
   - System for benchmark queries and ground truth answers
   - Automated dataset generation tools

5. **Automated Regression Testing** (Medium)
   - Pipeline changes regression testing
   - Baseline retrieval method benchmarking

6. **Evaluation Dashboards** (Medium)
   - Metric visualization and reporting dashboards

---

## Production Hardening & Security

### Feature Ranking by Importance

1. **Authentication & Authorization** (Critical)
   - OAuth2 implementation for user authentication
   - Role-based access control (RBAC)

2. **Monitoring & Observability** (Critical)
   - Prometheus metrics and Grafana dashboards
   - Distributed tracing for request tracking

3. **Multi-tenancy Support** (High)
   - Tenant isolation and data segregation

4. **Rate Limiting & Quota Management** (High)
   - Per-user/tenant API rate limiting and token quotas

5. **Kubernetes Deployment** (Medium)
   - Kubernetes manifests for scalable deployment

---

## Autonomous Document Monitoring & CRON-based Ingestion

Use case: Students continuously add study materials to a folder, and the system automatically processes new documents in real-time without manual uploads.

### Feature Ranking by Importance

1. **Folder Monitoring System** (Critical)
   - Watches designated folders for new PDF files
   - Automatically triggers ingestion pipeline on file addition
   - Supports multiple monitored folders per workspace

2. **Automatic Chunk Generation** (Critical)
   - Seamlessly extends existing pipelines for new documents
   - Generates summaries, parent chunks, and child chunks automatically
   - Maintains vector embeddings in PostgreSQL

3. **CRON Scheduler Integration** (High)
   - Schedule batch processing at fixed intervals
   - Configurable scheduling for different folders
   - Handles large document batches efficiently

4. **Real-time Processing Notifications** (High)
   - Notify users when new documents are processed
   - Track processing status and completion times
   - Queue management for pending documents

5. **Document Versioning & Updates** (Medium)
   - Handle updated documents (re-index with versioning)
   - Maintain processing history and audit trails
   - Prevent duplicate ingestion

---

## Cohort-Based Question Engine

Use case: A cohort of students all receive the same set of questions about their study materials. The system optimizes for consistent, fast answers to these predefined questions across multiple student workspaces.

### Feature Ranking by Importance

1. **Predefined Question Sets** (Critical)
   - Create and manage cohort-specific question templates
   - Store questions with expected answer patterns and key concepts
   - Support question versioning and updates

2. **Cohort Workspace Management** (Critical)
   - Associate multiple students/workspaces to a cohort
   - Share common question sets across cohort members
   - Per-workspace document isolation with shared question context

3. **Optimized Answer Caching** (High)
   - Cache answers to predefined questions per document
   - Retrieve cached responses instantly for repeated questions
   - Invalidate cache on document updates

4. **Batch Question Processing** (High)
   - Process all cohort questions against new documents in parallel
   - Generate and cache answers during ingestion pipeline
   - Reduce inference overhead for common queries

5. **Answer Consistency Tracking** (High)
   - Track answer variations across cohort members
   - Detect inconsistencies in document quality or interpretation
   - Flag documents that produce outlier answers

6. **Performance Analytics Dashboard** (Medium)
   - View average response times per question across cohort
   - Identify slow-to-answer questions
   - Monitor cache hit rates and effectiveness

---

## Local Model Optimization (Planned)

Use case: Deploy faster, locally-hosted models to reduce API dependency, improve inference latency, and lower operational costs.

### Feature Ranking by Importance

1. **Local LLM Integration** (Critical)
   - Replace Gemini API with local LLM (Llama 2, Mistral, etc.)
   - Support multiple model options with configurable selection
   - Optimize for low-latency generation on consumer hardware

2. **Model Selection & Benchmarking** (Critical)
   - Benchmark available local models for quality vs. latency trade-off
   - Automatic model selection based on hardware constraints
   - Performance metrics: TTFT, token/s generation speed

3. **Inference Optimization** (High)
   - Quantization support (4-bit, 8-bit) for faster inference
   - Batch processing for improved throughput
   - KV-cache optimization for streaming responses

4. **Cost & Latency Reduction** (High)
   - Eliminate Gemini API dependency and associated costs
   - Reduce p99 latency from ~3-5s to <1s for generation
   - Local inference for HyDe query transformation

5. **Fallback & Hybrid Strategy** (High)
   - Graceful fallback to API when needed
   - Hybrid approach: local for fast queries, API for complex reasoning
   - Automatic routing based on query complexity

6. **Hardware Abstraction Layer** (Medium)
   - Support GPU (NVIDIA, AMD, Metal) and CPU inference
   - Docker containerization for local model deployment
   - Environment-specific model configuration

---

## Priority Implementation Order

**Immediate (Next 2-4 weeks):**
- Integrate RAGAS for evaluation
- Folder monitoring system
- Predefined question sets

**Short-term (Next 1-2 months):**
- Local LLM integration
- Cohort workspace management
- CRON scheduler integration

**Medium-term (Next 2-3 months):**
- Hybrid search implementation
- Authentication & authorization
- Monitoring & observability

**Long-term (3+ months):**
- Multi-tenancy
- Kubernetes deployment
- Multi-modal support

---

**Last Updated**: February 2, 2026
