# MoE Router API

Intelligent Mixture of Experts (MoE) routing API that automatically selects the best Ollama model for each query based on query type, hardware capabilities, and performance benchmarks. Features Pi Agent Boss for automated management and external API integration.

## Features

- **Automatic Query Routing**: Classifies queries and routes to optimal model
- **No API Timeouts**: Queries complete naturally based on Ollama's processing time
- **Pi Agent Boss**: Automated model management and benchmarking system
- **External API Integration**: Support for NVIDIA NIM, OpenAI, and other cloud models
- **Model Pool Management**: Intelligent GPU/RAM caching with LRU eviction
- **Circuit Breaker Pattern**: Automatic fallback on model failures
- **Response Caching**: LRU cache for improved performance
- **Concurrency Control**: Semaphore-based throttling per model
- **WebSocket Support**: Real-time streaming for chat sessions
- **Health Monitoring**: System health checks and metrics
- **API Key Authentication**: Secure API access with configurable keys
- **Rate Limiting**: Prevent abuse with per-client rate limits
- **Docker Support**: Containerized deployment with Docker & Docker Compose
- **CI/CD Pipeline**: Automated testing and deployment with GitHub Actions

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

## No Timeout Configuration

**Important**: This Router API has been configured with **NO API timeouts**. Queries will run as long as Ollama needs to complete them, naturally.

### Why No Timeouts?

- **Better cold load handling**: Models can take time to load from disk
- **No premature failures**: Queries won't timeout at arbitrary limits
- **Natural completion**: Only Ollama determines when a query finishes
- **Tested**: Queries successfully complete in 3+ minutes when needed

### Example

```bash
# This query will complete no matter how long it takes
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain quantum computing in detail"}'
```

Previously would have timed out at 120s. Now completes naturally!

## Pi Agent Boss

Pi Agent Boss is an autonomous management system for the MOE Router stack.

### Starting Pi Agent Boss

```bash
# ACTIVE mode - Auto-optimizing local assistant
python scripts/start_pi_assistant.py
```

### Features

- **Automatic Model Discovery**: Detects new Ollama models automatically
- **Mandatory Testing**: Ensures all models pass critical benchmarks
- **Auto-Optimization**: Updates routing based on performance data
- **Pool Management**: Automatically loads/unloads models for optimization
- **Disk Management**: Keeps Ollama models under 50GB with auto-cleanup
- **Health Monitoring**: Continuous system health checks every 60s

### Modes

- **ACTIVE**: Auto-optimize routing without heavy benchmarking (default)
- **BOSS**: Full control with mandatory benchmarks and optimization
- **ADVISORY**: Makes recommendations, waits for approval
- **PASSIVE**: Monitor only, no changes

### Pi Agent Status

```bash
# Check Pi Agent status
curl http://localhost:8000/api/v1/pi-agent/status

# Get routing recommendations
curl http://localhost:8000/api/v1/pi-agent/recommendations
```

## External API Integration

The Router API supports external cloud models alongside local Ollama models.

### Configuration

Edit `config/external_apis.yaml`:

```yaml
external_apis:
  nvidia_nim:
    enabled: true
    base_url: "https://integrate.api.nvidia.com/v1"
    api_key_env: "NVIDIA_API_KEY"
    models:
      - name: "meta/llama-3.1-405b-instruct"
        display_name: "Llama 3.1 405B (NVIDIA)"
        categories: ["factual", "document"]
        priority: 90
```

### Environment Variables

```bash
# Set your API keys
export NVIDIA_API_KEY="your-nvidia-api-key"
export OPENAI_API_KEY="your-openai-api-key"
```

### Benefits

- **Hybrid Routing**: Mix local and cloud models intelligently
- **Benchmarking**: Compare local vs external model performance
- **Fallback Chains**: Use external models when local models are busy
- **Cost Optimization**: Prefer local models, use cloud for complex queries

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

### Actual Test Results

| Query Type | Query | Model | Time | Result |
|------------|-------|-------|------|--------|
| speed_critical | "What is 2+2?" | qwen3:4b | 216s | ✅ "4" |
| code | "fibonacci function" | qwen2.5-coder | 109s | ✅ Working code |
| factual | "capital of France" | qwen3:4b | 321s | ✅ "Paris" (cached) |
| factual | "capital of Germany" | qwen3:4b | 180s | ✅ "Berlin" |

**No Timeout Configuration**: Queries complete naturally based on Ollama processing time.

### Expected Performance (Cached)

| Query Type | Model | Expected Time |
|------------|-------|---------------|
| Code/debugging | qwen2.5-coder | ~10-15s |
| Simple question | qwen3:4b | ~12-15s |
| Creative writing | llama3.2 | ~20-25s |
| General chat | llama3.1 | ~18-22s |
| Cache hit | N/A | <100ms |

### Capacity

- **Concurrent**: ~15 simultaneous queries
- **Effective (with caching)**: ~30+ queries/minute
- **No timeout limit**: Queries can run as long as needed

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

### Queries taking a long time
This is **expected behavior** - the Router API has no timeout limits. Queries will complete based on Ollama's processing time, which can be several minutes for:
- Cold model loads (first time using a model)
- Complex queries requiring large models
- External API calls

**Do not interrupt** - let the query complete naturally.

### Pi Agent Boss not discovering models
```bash
# Check Pi Agent status
curl http://localhost:8000/api/v1/pi-agent/status

# Verify Ollama is accessible
curl http://localhost:11434/api/tags

# Restart Pi Agent Boss
python scripts/start_pi_assistant.py
```

### External API not working
```bash
# Verify API key is set
echo $NVIDIA_API_KEY

# Check external API configuration
cat config/external_apis.yaml

# Test external API directly
curl -X POST https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "meta/llama-3.1-405b-instruct", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Deployment

### Docker Deployment

Build and run with Docker:

```bash
# Build the image
docker build -t moe-router-api .

# Run the container
docker run -p 8000:8000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e API_KEYS=your-secret-key \
  moe-router-api
```

### Docker Compose Deployment

Start all services (API + Ollama + Monitoring):

```bash
# Start with monitoring (Prometheus + Grafana)
docker-compose --profile monitoring up -d

# Start without monitoring
docker-compose up -d

# View logs
docker-compose logs -f moe-router

# Stop all services
docker-compose down
```

### Configuration

Environment variables for deployment:

```bash
# API Authentication (required for production)
API_KEYS=key1,key2,key3

# Rate Limiting
RATE_LIMIT_DISABLED=false

# Ollama Connection
OLLAMA_BASE_URL=http://ollama:11434
```

### Security Best Practices

1. **Always set API keys** in production:
   ```bash
   export API_KEYS="your-secure-key-1,your-secure-key-2"
   ```

2. **Use HTTPS** in production with a reverse proxy (nginx/traefik)

3. **Enable rate limiting** to prevent abuse:
   ```bash
   export RATE_LIMIT_DISABLED=false
   ```

4. **Monitor metrics** via Prometheus endpoint:
   ```
   http://your-server:8000/api/v1/metrics/prometheus
   ```

5. **Run behind a firewall** and restrict access to the API

### Monitoring

Access monitoring dashboards:

- **API Health**: http://localhost:8000/api/v1/health
- **Metrics**: http://localhost:8000/api/v1/metrics
- **Prometheus**: http://localhost:9090 (with `--profile monitoring`)
- **Grafana**: http://localhost:3000 (admin/admin, with `--profile monitoring`)

## License

MIT License
