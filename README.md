# MoE Router API

Intelligent Mixture of Experts (MoE) routing API that automatically selects the best Ollama model for each query based on query type, hardware capabilities, and performance benchmarks.

## Features

- **Automatic Query Routing**: Classifies queries and routes to optimal model
- **Model Pool Management**: Intelligent GPU/RAM caching with LRU eviction
- **Circuit Breaker Pattern**: Automatic fallback on model failures
- **Response Caching**: LRU cache for improved performance
- **Concurrency Control**: Semaphore-based throttling per model
- **WebSocket Support**: Real-time streaming for chat sessions
- **Health Monitoring**: System health checks and metrics

## Quick Start

### Prerequisites

- Python 3.8+
- Ollama running locally (http://localhost:11434)
- At least one Ollama model installed

### Installation

```bash
# Clone or navigate to project directory
cd moe-router-api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Edit `config.yaml` to customize settings:

```yaml
server:
  host: "0.0.0.0"
  port: 8000

models:
  ollama_base_url: "http://localhost:11434"
  pool:
    gpu_capacity_mb: 3500
    ram_capacity_mb: 20000
  preload:
    - "qwen3:4b"
    - "llama3.1"
```

### Starting the Server

**Windows:**
```bash
scripts\start.bat
```

**Linux/Mac:**
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

Or manually:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at http://localhost:8000

API documentation: http://localhost:8000/docs

## API Endpoints

### Query Endpoints

#### POST /api/v1/query
Execute a single query with automatic routing.

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of France?"}'
```

Response:
```json
{
  "response": "The capital of France is Paris.",
  "model_used": "qwen3:4b",
  "routing_decision": {
    "query_type": "speed_critical",
    "selected_model": "qwen3:4b",
    "confidence": 0.9
  },
  "tokens_generated": 25,
  "processing_time": 12.5,
  "from_cache": false
}
```

#### POST /api/v1/query/stream
Execute a query with streaming response (Server-Sent Events).

```bash
curl -X POST http://localhost:8000/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Write a short story"}'
```

#### POST /api/v1/batch
Execute multiple queries concurrently.

```bash
curl -X POST http://localhost:8000/api/v1/batch \
  -H "Content-Type: application/json" \
  -d '{"queries": [{"query": "Hello"}, {"query": "World"}]}'
```

### Model Management

#### GET /api/v1/models
List all available models with specifications.

#### GET /api/v1/models/pool
Get current model pool status (GPU/RAM usage).

#### GET /api/v1/models/{model_name}
Get status of a specific model.

#### POST /api/v1/models/{model_name}/load
Preload a model into the pool.

#### POST /api/v1/models/{model_name}/unload
Unload a model from the pool.

### Monitoring

#### GET /api/v1/health
Health check endpoint.

#### GET /api/v1/metrics
Performance metrics (cache stats, query counts, etc.).

#### GET /api/v1/metrics/prometheus
Prometheus metrics for scraping.

#### GET /api/v1/cache/stats
Detailed cache statistics.

#### POST /api/v1/cache/clear
Clear all cached responses.

### WebSocket

#### WS /ws/chat
Persistent chat session with context management.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.send(JSON.stringify({
  type: 'query',
  query: 'Hello, how are you?'
}));
```

#### WS /ws/batch
Batch processing over WebSocket.

## Query Types

The system automatically classifies queries into types:

1. **CODE**: Programming, debugging, code review
   - Routes to: qwen2.5-coder → qwen3:4b → llama3.1

2. **SPEED_CRITICAL**: Simple questions, quick answers
   - Routes to: qwen3:4b → nemotron → llama3.1

3. **GENERATION_HEAVY**: Creative writing, long-form
   - Routes to: llama3.2 → phi3:mini → llama3.1

4. **PROMPT_HEAVY**: Document analysis, large context
   - Routes to: ministral-3 → qwen3:4b → nemotron

5. **BALANCED**: General conversation, analysis
   - Routes to: llama3.1 → qwen3:4b → llama3.2

## Architecture

```
FastAPI Gateway
    ↓
Query Classifier (embeddings + heuristics)
    ↓
Model Selection Engine (scoring + load balancing)
    ↓
Model Pool (GPU/RAM caching with LRU)
    ↓
Query Executor (semaphores + circuit breakers)
    ↓
Response Cache (LRU with TTL)
```

## Utilities

### Preload Models
```bash
python scripts/preload_models.py
```

### Benchmark Models
```bash
python scripts/benchmark_models.py
```

## Performance

Based on benchmark data:

| Query Type | Model | Expected Time |
|------------|-------|---------------|
| Code/debugging | qwen2.5-coder | ~10-15s |
| Simple question | qwen3:4b | ~12-15s |
| Creative writing | llama3.2 | ~20-25s |
| General chat | llama3.1 | ~18-22s |
| Cache hit | N/A | <100ms |

Concurrent capacity: ~15 simultaneous queries
Effective capacity (with caching): ~30+ queries/minute

## Hardware Optimization

Optimized for Acer Nitro AN515-55:
- CPU: Intel i5-10300H
- GPU: NVIDIA RTX 3060 Laptop (4GB VRAM)
- RAM: 40GB

Memory allocation:
- GPU Pool (3.5GB): qwen3:4b (resident) + 1 on-demand
- RAM Pool (20GB): 5-6 models with LRU eviction

## Troubleshooting

### Ollama not responding
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

### Model not found
```bash
# Pull the model
ollama pull qwen3:4b
```

### Out of memory
Reduce `gpu_capacity_mb` and `ram_capacity_mb` in `config.yaml`

## License

MIT License
