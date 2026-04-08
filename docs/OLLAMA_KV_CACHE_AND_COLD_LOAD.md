# Ollama KV Cache, Cold Load & Hot Swapping Guide

## 🎯 What You Need to Know

### 1. Ollama KV Cache Settings

**Current Configuration:**
```
OLLAMA_NUM_GPUS: (not set - auto-detect)
OLLAMA_GPU_OVERHEAD: (not set - default 4GB)
OLLAMA_LOAD_TIMEOUT: (not set - default 5 minutes)
OLLAMA_MAX_QUEUE: (not set - default unlimited)
```

**Default KV Cache Behavior:**
- **Automatic sizing** - Ollama automatically calculates KV cache size based on:
  - Available GPU VRAM
  - Model size
  - Context window requested
  - `OLLAMA_GPU_OVERHEAD` (default 4GB reserved)

- **No manual KV cache setting** - Unlike some systems, Ollama doesn't expose direct KV cache size configuration
- **Dynamic allocation** - KV cache grows/shrinks based on context window

**How to check your KV cache usage:**
```bash
# Check currently loaded models and their VRAM usage
curl http://localhost:11434/api/ps

# Example output shows:
# - size_vram: 5533622912 (5.3GB VRAM used)
# - context_length: 32768 (max context)
```

---

### 2. Cold Load Performance

**What is Cold Load Time?**
- Time to load model from disk → GPU/RAM
- Includes: File reading, model initialization, KV cache allocation
- Measured from start of load request until model responds to first query

**Why It Matters:**
- **Hot Swapping** - How long to switch between models
- **Pool Management** - When to load/unload models
- **User Experience** - First query latency after model switch

**What Affects Cold Load Time:**
1. **Model Size** - Larger models take longer
2. **Storage Speed** - SSD vs HDD (you have SSD)
3. **GPU Bandwidth** - PCIe speed, GPU memory bandwidth
4. **System Load** - Other processes competing for resources
5. **Ollama Cache** - Previous runs may have cached some data

**Expected Cold Load Times (Estimates):**
| Model | Size | Est. Load Time | Actual Time |
|-------|------|----------------|-------------|
| phi3:mini | 2.0GB | 5-10s | To be measured |
| llama3.2 | 1.9GB | 5-10s | To be measured |
| qwen3:4b | 2.3GB | 8-15s | To be measured |
| nemotron-3-nano:4b | 2.6GB | 10-20s | To be measured |
| llama3.1 | 4.6GB | 15-30s | To be measured |
| qwen2.5-coder | 4.4GB | 15-30s | To be measured |
| gemma4:e4b | 9.0GB | 30-60s | To be measured |
| ministral-3 | 5.6GB | 20-40s | To be measured |

---

### 3. Warm Performance (Tokens Per Second)

**What is TPS?**
- **Tokens Per Second** = Generation speed after model is loaded
- **Prompt TPS** = How fast model processes input (embedding)
- **Generation TPS** = How fast model generates output

**Metrics Tracked:**
```python
# From benchmark results:
{
  "prompt_speed_tps": 653,    # Input processing speed
  "gen_speed_tps": 73,        # Output generation speed
  "total_time_s": 12.5        # Total query time
}
```

**Expected TPS by Model Size:**
| Model | Params | Gen TPS | Prompt TPS |
|-------|--------|---------|------------|
| phi3:mini | 3.8B | ~99 t/s | ~2 t/s |
| llama3.2 | 3.2B | ~107 t/s | ~3 t/s |
| qwen3:4b | 4B | ~73 t/s | ~653 t/s |
| gemma4:e4b | 8B | ~55 t/s | ~450 t/s |
| llama3.1 | 8B | ~15 t/s | ~77 t/s |

**Key Insight:** Faster prompt processing (embeddings) = Better for large contexts

---

### 4. Hot Swapping

**What is Hot Swapping?**
- Dynamically loading/unloading models while system is running
- **Goal:** Keep frequently-used models loaded, unload unused ones
- **Challenge:** GPU memory is limited (your GPU: ~8-12GB effective)

**How Pi Agent Boss Handles Hot Swapping:**

1. **Model Pool Management**
   ```
   GPU Capacity: 3500MB (config)
   RAM Capacity: 20000MB (config)

   Models in GPU: High-priority, frequently-used
   Models in RAM: Medium priority
   Models on Disk: Low priority (unloaded)
   ```

2. **Load Time Tracking**
   ```python
   # Pi Agent tracks cold load times:
   "load_time": 12.5  # Seconds to load from cold
   ```

3. **Swap Decisions**
   - When GPU is full → unload least recently used model
   - When query needs different model → load it (takes load_time seconds)
   - External models → No swap needed (always available)

**Hot Swap Sequence:**
```
1. Router selects Model B (not loaded)
2. Pi Agent checks GPU capacity
3. If full → unload Model A
4. Load Model B (takes load_time seconds)
5. Process query
6. Model B stays loaded (next queries faster)
```

**Swap Penalty:**
- First query after swap: Cold load time (5-60s)
- Subsequent queries: Normal latency (100-500ms)
- **Strategy:** Keep popular models loaded, accept swap penalty for rarely-used ones

---

### 5. Current Status & Next Steps

**Currently Loaded Model:**
```
Model: ministral-3:latest (8.9B parameters)
VRAM Usage: 5.3GB
Context: 32768 tokens
Status: Actively loaded
```

**Available Models:**
- 9 local Ollama models
- 1 external NVIDIA model (always available)

**All models have:** `load_time: null` (not yet benchmarked)

**Next Steps:**

1. **Run Cold Load Benchmark**
   ```bash
   python scripts/benchmark_cold_load.py
   ```

   This will:
   - Unload each model
   - Measure cold load time
   - Measure warm TPS
   - Save results to `pi_agent_state/cold_load_benchmark_results.json`

2. **Analyze Results**
   - Identify fastest/slowest loading models
   - Determine optimal model pool configuration
   - Plan hot swap strategy

3. **Optimize Model Pool**
   - Keep fastest-loading models for frequent swapping
   - Keep popular models permanently loaded
   - Use external model for complex queries (no load time)

---

### 6. Optimization Strategies

**Strategy A: Small Model Pool (Fast Swapping)**
```
Keep loaded: qwen3:4b (fastest)
Swap: All other models as needed
Benefit: Fast queries, low VRAM usage
Cost: Frequent cold loads (5-30s penalty)
```

**Strategy B: Balanced Pool**
```
Keep loaded: qwen3:4b + llama3.2 (fast + fast generation)
Swap: Other models as needed
Benefit: Good speed, moderate VRAM
Cost: Medium swap penalty
```

**Strategy C: Large Pool (Minimal Swapping)**
```
Keep loaded: 3-4 medium models
Swap: Only large models (gemma4, ministral-3)
Benefit: Minimal swap penalty
Cost: High VRAM usage
```

**Strategy D: Hybrid (Recommended)**
```
Local: qwen3:4b + llama3.2 (always loaded)
External: NVIDIA 405B (no load time)
Swap: Other local models as needed
Benefit: Best of both worlds
```

---

### 7. Measuring Words Per Second

**Note:** LLMs measure **tokens** per second, not words.

**Why?**
- Tokenization varies (1 word ≈ 0.75-1.5 tokens)
- Accurate metric across languages
- Consistent with industry standards

**Rough Conversion:**
```
1 word ≈ 1.33 tokens (average)
100 tokens/sec ≈ 75 words/sec
```

**To measure actual WPS:**
```python
# Count words in response
word_count = len(response.split())
tokens_per_second = 73  # From benchmark
words_per_second = word_count / (tokens / tokens_per_second)
```

---

## 🚀 Run the Cold Load Benchmark

```bash
cd C:\Users\aaron\OneDrive\Desktop\moe-router-api
python scripts\benchmark_cold_load.py
```

This will:
1. ✅ Measure cold load time for each model
2. ✅ Measure warm TPS (tokens per second)
3. ✅ Track memory footprint
4. ✅ Save comprehensive results
5. ✅ Generate summary table

**Expected Duration:** ~15-30 minutes (depends on models)

---

## 📊 What You'll Get

**For Each Model:**
- Cold load time (seconds)
- Warm performance (tokens/second)
- Parameter count
- Quantization level
- Memory footprint

**Summary Table:**
```
Model              Load Time    Tokens/sec    Parameters
--------------------------------------------------------
qwen3:4b          8.5s         73 tps       4B
llama3.2           6.2s        107 tps       3.2B
phi3:mini          5.1s         99 tps       3.8B
...
```

**Use This Data To:**
- Plan optimal model pool configuration
- Predict hot swap performance
- Choose models for different use cases
- Balance speed vs quality

---

## 🔍 Quick Check: Current Ollama Settings

```bash
# Check loaded models
curl http://localhost:11434/api/ps

# Check all models
curl http://localhost:11434/api/tags

# Check model details (replace with your model)
curl -X POST http://localhost:11434/api/show -d '{"name":"qwen3:4b"}'
```

---

## 💡 Key Takeaways

1. **Ollama auto-manages KV cache** - No manual setting needed
2. **Cold load time varies** - 5-60s depending on model size
3. **Hot swapping has penalty** - First query pays load time
4. **External models have no load time** - Always available
5. **Tokens/second > Words/second** - Use industry standard metric
6. **Optimize based on usage patterns** - Keep popular models loaded

---

**Ready to benchmark?** Run `python scripts\benchmark_cold_load.py` now!
