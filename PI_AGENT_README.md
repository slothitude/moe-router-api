# Pi Agent Boss - Manager of the MoE Router Stack

The **Pi Agent Boss** is the autonomous manager of the entire MoE Router API system. It discovers new models, runs mandatory benchmarks, and optimizes routing decisions.

## What It Does

### 1. Model Discovery
- Automatically discovers new models from Ollama
- Registers models in the system
- Tracks model availability

### 2. Mandatory Benchmarking
- Runs required tests on all models
- Tests 4 mandatory categories: agentic, code, factual, document
- Generates performance scores

### 3. Routing Management
- Updates routing recommendations based on benchmarks
- Optimizes fallback chains
- Manages model pool (load/unload)

### 4. Continuous Monitoring
- Health checks every 60 seconds
- Model discovery every 5 minutes
- Real-time performance tracking

## Installation

```bash
# Ensure dependencies are installed
pip install -r requirements.txt

# Start Ollama
ollama serve

# Start the MoE Router API
python main.py
```

## Usage

### Start Pi Agent Boss

```bash
# Start in boss mode (default - full control)
python scripts/pi_agent.py start

# Start in passive mode (monitor only)
python scripts/pi_agent.py start --mode passive

# Start in active mode (auto-optimize routing)
python scripts/pi_agent.py start --mode active
```

### Command Reference

```bash
# Start the agent
python scripts/pi_agent.py start [options]

Options:
  --mode {passive,advisory,active,boss}
                        Agent operating mode (default: boss)
  --ollama-url TEXT     Ollama API URL (default: http://localhost:11434)
  --router-url TEXT     Router API URL (default: http://localhost:8000)
  --state-dir TEXT      State directory (default: pi_agent_state)
  --categories TEXT     Mandatory benchmark categories (comma-separated)
  --discovery-interval INT
                        Model discovery interval in seconds (default: 300)
  --health-interval INT
                        Health check interval in seconds (default: 60)
  --no-auto-optimize    Disable auto routing optimization
  --no-auto-manage      Disable auto pool management

# Show dashboard
python scripts/pi_agent.py dashboard

# Benchmark a specific model
python scripts/pi_agent.py benchmark <model_name>

# List all known models
python scripts/pi_agent.py list

# Run model discovery
python scripts/pi_agent.py discover
```

## Agent Modes

### PASSIVE Mode
- Monitors system only
- Makes no changes
- Useful for observation

### ADVISORY Mode
- Makes recommendations
- Waits for approval
- Logs suggestions

### ACTIVE Mode
- Automatically optimizes routing
- Updates recommendations
- Does not manage pool

### BOSS Mode (Default)
- Full system control
- Manages models and routing
- Runs benchmarks automatically
- Optimizes pool

## Architecture

```
┌─────────────────────────────────────────────────┐
│              PI AGENT BOSS                      │
│  ┌───────────────────────────────────────────┐ │
│  │ Model Discovery (Ollama API)              │ │
│  └───────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────┐ │
│  │ Benchmark System (130 tests)              │ │
│  └───────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────┐ │
│  │ Routing Manager (Admin API)               │ │
│  └───────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────┐ │
│  │ Pool Manager (Load/Unload)                │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│           MoE Router API                        │
│  /api/v1/query  |  /api/v1/admin/*             │
└─────────────────────────────────────────────────┘
```

## State Management

Pi Agent persists its state in `pi_agent_state/`:

- `agent_state.json` - Known models, benchmark results, recommendations
- `benchmark_*.json` - Detailed benchmark results per model

## Example Workflow

1. **Start Pi Agent Boss**
   ```bash
   python scripts/pi_agent.py start
   ```

2. **Automatic Discovery**
   - Agent discovers all Ollama models
   - Registers new models automatically

3. **Mandatory Benchmarking**
   - Agent runs tests on unbenchmarked models
   - Tests: agentic, code, factual, document
   - Generates performance scores

4. **Routing Optimization**
   - Updates fallback chains based on results
   - Recommends best model per category
   - Loads high-performing models

5. **Continuous Monitoring**
   - Health checks every 60s
   - Performance tracking
   - Auto-recovery

## Dashboard

View real-time status:

```bash
python scripts/pi_agent.py dashboard
```

Output:
```
======================================================================
 PI AGENT BOSS - DASHBOARD
======================================================================

📊 MODE: BOSS

🤖 Models:
   Total: 7
   Benchmarked: 5
   In Pool: 3
   Loaded: 2

📈 Model Performance:
   qwen3:4b                   | Score: 87.50%  | Queries: 1523 | Latency: 245ms
   llama3.1                   | Score: 82.30%  | Queries: 2341 | Latency: 312ms
   qwen2.5-coder              | Score: 91.20%  | Queries:  892 | Latency: 278ms

🎯 Routing Recommendations:
   agentic          → llama3.1
   code             → qwen2.5-coder
   factual          → qwen3:4b
   document         → llama3.1

======================================================================
```

## Integration with Router API

Pi Agent uses the Admin API endpoints:

- `GET /api/v1/admin/routing` - Get routing config
- `POST /api/v1/admin/routing/recommendations` - Update recommendations
- `POST /api/v1/admin/routing/update-fallback` - Update fallback chains
- `POST /api/v1/admin/model/benchmark-score` - Update benchmark scores
- `GET /api/v1/admin/pi-status` - Get Pi Agent status

## Troubleshooting

### Agent won't start
```bash
# Check if Router API is running
curl http://localhost:8000/api/v1/health

# Check if Ollama is running
curl http://localhost:11434/api/tags
```

### Models not discovered
```bash
# Run manual discovery
python scripts/pi_agent.py discover

# Check Ollama models
ollama list
```

### Benchmark failures
```bash
# Check Router API logs
# Increase timeout
python scripts/pi_agent.py start --health-interval 120
```

## Advanced Usage

### Custom mandatory categories
```bash
python scripts/pi_agent.py start --categories code,creative
```

### Adjust discovery frequency
```bash
python scripts/pi_agent.py start --discovery-interval 600
```

### Passive monitoring
```bash
python scripts/pi_agent.py start --mode passive --auto-optimize false
```

## Production Deployment

```bash
# Run as background service
nohup python scripts/pi_agent.py start > pi_agent.log 2>&1 &

# Or use systemd/supervisord
```

## Configuration

Edit environment variables:

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export ROUTER_API_URL="http://localhost:8000"
export PI_AGENT_MODE="boss"
export AUTO_OPTIMIZE="true"
```

## License

Same as the MoE Router API project.
