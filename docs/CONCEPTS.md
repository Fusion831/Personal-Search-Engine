# Core Concepts & Design Philosophy

Understanding the three key concepts that make this RAG system effective.

---

## Parent-Child Chunking

### The Problem

Traditional RAG faces a fundamental trade-off:

| Approach | Pros | Cons |
|----------|------|------|
| **Small Chunks** (100-200 chars) | Precise vector similarity | Limited context for LLM |
| **Large Chunks** (1000+ chars) | Rich context for generation | Poor retrieval accuracy |

You can't have both with a single chunk size.

### The Solution

Store and search with **small chunks**, retrieve and generate with **large chunks**.

```python
# Child Chunk (stored with embedding, used for search)
"The accuracy of the model was 94.2% on the test set."

# Parent Chunk (retrieved for LLM context)
"We evaluated our proposed diabetes prediction model on a held-out 
test set of 5,000 patients. The accuracy of the model was 94.2% on 
the test set, with a precision of 91.3% and recall of 96.7%. This 
represents a 5.3% improvement over the baseline approach."
```

### How It Works

1. **Indexing Phase:**
   - Split documents into natural paragraphs (parents)
   - Further split parents into 500-char chunks with 100-char overlap (children)
   - Generate embeddings only for child chunks
   - Store both in separate database tables with FK relationship

2. **Retrieval Phase:**
   - Vector search returns top-10 most similar **child** chunks
   - For each child, retrieve its corresponding **parent** chunk
   - Deduplicate parent IDs to avoid redundant context
   - Combine all child chunks + unique parent paragraphs as context

### Benefits

✅ **Precision:** Child chunks are granular enough for semantic search
✅ **Context:** Parent chunks provide full paragraph context to LLM
✅ **Efficiency:** Parent deduplication reduces input tokens by ~30%
✅ **Natural:** Works with document structure (paragraphs exist naturally)

---

## HyDe: Hypothetical Document Embeddings

### The Problem

Queries and documents use fundamentally different language:

**User Query:**  
"What is diabetes?"

**Document Text:**  
"Diabetes mellitus is a chronic metabolic disorder characterized by elevated blood glucose levels resulting from dysfunction in insulin production..."

When you embed these directly and compare vectors, they're surprisingly **dissimilar** despite being on the same topic. This is the **semantic gap**.

### The Solution

Transform the query into a hypothetical answer that mimics how documents describe the topic.

```python
# Original Query
query = "What is diabetes?"

# Gemini API generates hypothetical answer
hypothetical = """Diabetes is a chronic condition where the body 
cannot properly regulate blood sugar levels due to insulin resistance 
or insufficient insulin production. There are two main types: Type 1 
(autoimmune) and Type 2 (insulin resistance)..."""

# Embed the hypothetical answer instead
query_vector = embed(hypothetical)  # Much more similar to document language!
```

### How It Works

1. **Generation:** Gemini API generates a 100-200 word hypothetical answer to the user's query
2. **Encoding:** This hypothetical text is embedded to a vector
3. **Retrieval:** Vector search uses this "mock document" representation
4. **Result:** Much higher semantic alignment with actual documents

### Why It Works

- Transforms query language into document language
- Hypothetical answer contains keywords and phrasing from actual documents
- Bridges vocabulary gap (synonyms, terminology)
- Provides broader context than the original query

### Trade-offs

✅ **Pros:**
- Significantly improves retrieval for ambiguous queries
- Handles semantic mismatches well
- No additional training required

⚠️ **Cons:**
- Adds ~800ms latency (Gemini API call)
- Requires API access
- Hallucination risk if generation is poor (mitigated with careful prompting)

---

## Intelligent Query Routing

### The Problem

Not all questions need the same retrieval strategy:

**Broad Question:** "Summarize this research paper"
- Best answered by document summary
- Needs high-level overview context
- Child chunks provide too granular a view

**Specific Question:** "What was the F1 score reported in section 4?"
- Needs precise fact retrieval
- Document summary may lack specific metrics
- Child chunks with exact numbers work better

A single retrieval strategy fails at one or both.

### The Solution

**Automatically detect query type and route accordingly.**

```python
# Parallel Search
summary_distance = similarity_search(query_vector, document_summaries, top=1)
chunk_distance = similarity_search(query_vector, child_chunks, top=10)

# Routing Decision
if summary_distance < (chunk_distance * 0.8):
    # Broad question: summary is much closer
    context = get_full_summary()
    route = SUMMARY
else:
    # Specific question: chunks are closer or more relevant
    parents = get_parent_chunks(chunks)
    context = combine(chunks, deduplicate(parents))
    route = PARENT_CHILD
```

### How It Works

1. **Parallel Retrieval:**
   - Search for best summary match
   - Search for best child chunk matches
   - Compute L2 distances for both

2. **Distance Comparison:**
   - If summary is significantly closer → Broad question
   - If chunks are closer → Specific question
   - Threshold (0.8) is configurable and empirically tuned

3. **Context Assembly:**
   - **Summary route:** Return full document summary
   - **Parent-child route:** Combine chunks + deduplicated parents

### Why It Works

- Leverages natural document structure (summaries + details)
- Threshold automatically adapts to query specificity
- No additional training or labeled data needed
- Empirically tuned on actual usage patterns

### Benefits

✅ **Adaptability:** Handles both broad and specific questions well
✅ **No Training:** Threshold-based logic requires no ML training
✅ **Interpretability:** Easy to understand why routing decision was made
✅ **Flexibility:** Threshold can be adjusted per use case

---

## How They Work Together

### Example: Technical Paper Query

**User Query:** "What were the main results?"

1. **HyDe Transformation (800ms)**
   ```
   Hypothetical Answer:
   "The study achieved significant improvements over baseline methods. 
    The proposed model obtained state-of-the-art results on standard 
    benchmarks with 94.2% accuracy on the test set and an F1 score 
    of 0.96. The improvements represent a 5.3% increase over the 
    previous best approach..."
   ```

2. **Parallel Search**
   ```
   Summary Search:    distance = 0.65 (good match with overview)
   Chunk Search:      distance = 1.20 (chunks are about methodology)
   
   0.65 < (1.20 * 0.8) = 0.96  ✓ TRUE
   → Route: SUMMARY
   ```

3. **Context & Generation**
   ```
   Context: Full document summary (100-300 words)
   Gemini: Generates summary of main results from full summary
   Response: Streamed to user with markdown formatting
   ```

**Benefits of the combination:**
- HyDe found the right document despite query using different language
- Routing correctly identified this as a broad question
- Summary provided complete context without overwhelming detail
- Result: Fast, accurate, well-scoped answer

---

## Design Philosophy

This system embodies three principles:

1. **Precision + Context:** Don't sacrifice one for the other
2. **Semantic Intelligence:** Understand intent, not just keywords
3. **Adaptive Behavior:** Adjust retrieval strategy to query type

The three core concepts work together to achieve these principles without requiring massive fine-tuning or training datasets.

