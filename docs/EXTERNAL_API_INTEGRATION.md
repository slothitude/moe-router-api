# External API Integration for Pi Agent Boss

## Overview

This feature allows Pi Agent Boss to connect to external AI model APIs (NVIDIA NIM, OpenAI, MiniMax) to benchmark and test the internal MOE router system. External models become part of the model pool and are used alongside local Ollama models for comparison and validation.

## Purpose

The external API integration is designed for **testing and benchmarking**, not for production routing. It enables you to:

1. **Compare Performance**: Benchmark local small models vs external large models
2. **Validate Routing**: Verify routing decisions make sense
3. **Test Quality**: Can external models handle queries local models struggle with?
4. **Cost-Benefit Analysis**: When is it worth paying for external vs using local?

## Architecture

```
Pi Agent Boss
    ├─ Local Ollama Models (VRAM)
    │   ├─ phi3:mini (3.8B)
    │   ├─ llama3.2:latest (3.2B)
    │   └─ qwen3:4b (4B)
    │
    └─ External API Models (Cloud)
        └─ NVIDIA Llama 3.1 405B (comparison only)

Router selects best model based on:
- Query type
- Model capabilities
- Current load
- Performance benchmarks
```

## Setup

### 1. Configure External APIs

Edit `config/external_apis.yaml`:

```yaml
external_apis:
  nvidia_nim:
    enabled: true
    base_url: "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key_env: "NVIDIA_API_KEY"
    models:
      - name: "nvapi-meta/llama-3.1-405b-instruct"
        display_name: "Llama 3.1 405B (NVIDIA)"
        categories: ["factual", "document"]
        specialization: "large-knowledge-model"
        priority: 90
```

### 2. Set Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# Get your key at: https://build.nvidia.com/
NVIDIA_API_KEY=nvapi-your-key-here
```

### 3. Start Pi Agent Boss

```bash
python scripts/pi_agent.py start \
  --external-api-config config/external_apis.yaml
```

## Expected Output

```
Running initial discovery...
✓ External API client initialized with 1 models
✓ Discovered external model: Llama 3.1 405B (NVIDIA)
Initial discovery complete: 10 models known (9 Ollama + 1 external)

⚠️  Model external/nvidia_nim/nvapi-meta/llama-3.1-405b-instruct needs benchmarking
🚀 Starting mandatory benchmark for external/nvidia_nim/nvapi-meta/llama-3.1-405b-instruct
  Benchmarking factual...
  Testing query: What is the capital of France?
    Response: Paris is the capital of France... (2341ms)
  ...
✓ Benchmark complete: 85.2%

🔄 BENCHMARKING AUTO-ROUTING
Testing factual with auto-routing...
  Query: Explain quantum computing
  Router selected: llama3.2:latest (local)
  Confidence: 0.82
  Latency: 127ms
```

## Usage Examples

### View All Models (Local + External)

```bash
python scripts/pi_agent.py list
```

Output:
```
📦 qwen3:4b
   In Pool: True
   Loaded: True
   Location: gpu
   Benchmark Score: 78.5%

📦 external/nvidia_nim/nvapi-meta/llama-3.1-405b-instruct
   In Pool: True
   Loaded: True
   Location: external
   Benchmark Score: 92.1%
```

### Force Benchmark External Model

```bash
python scripts/pi_agent.py benchmark external/nvidia_nim/nvapi-meta/llama-3.1-405b-instruct
```

### View Routing Comparison

```bash
python scripts/pi_agent.py routing-report
```

Output:
```
📊 ROUTING COMPARISON REPORT

FACTUAL:
  Auto-Routing:
    Score: 82.5%
    Latency: 145ms
    Models: {'llama3.2:latest': 15, 'external/nvidia_nim/...': 5}

  External Model (NVIDIA):
    Score: 92.1%
    Latency: 2341ms

  Comparison:
    External model has 9.6% better quality but 16x slower
    Local model preferred for speed-critical queries
```

## Configuration Options

### Model Categories

External models can be configured for specific query types:

- `factual`: Knowledge-intensive questions
- `code`: Programming and code generation
- `document`: Long-form content creation
- `agentic`: Complex reasoning tasks
- `creative`: Creative writing

### Priority Levels

Higher priority values (0-100) indicate preference for certain query types:

```yaml
priority: 90  # High priority for factual queries
```

### Enabling/Disabling APIs

Set `enabled: false` to temporarily disable an API:

```yaml
external_apis:
  nvidia_nim:
    enabled: false  # Disabled
```

## Benchmarking Behavior

### Local Models

- Warmup time measured (cold load)
- Categories: agentic, code, factual, document
- 5 queries per category
- Metrics: latency, quality, success rate

### External Models

- No warmup (always available)
- Categories based on model configuration
- 5 queries per category
- Metrics: latency, quality, API response time

## Use Cases

### 1. Simple Queries

**Query**: "What's 2+2?"

**Routing**: Local model (qwen3:4b)

**Reason**: Fast, free, accurate for simple math

**Latency**: ~50ms

### 2. Complex Factual Queries

**Query**: "Explain quantum entanglement theory"

**Routing**: External model (NVIDIA 405B) or local (llama3.2)

**Reason**: External has more knowledge, but local is faster

**Latency**: External ~2000ms, Local ~150ms

### 3. Code Generation

**Query**: "Write a Python function to sort a list"

**Routing**: Local code model (qwen2.5-coder)

**Reason**: Specialized, fast, free

**Latency**: ~200ms

### 4. Hot-Swapping

**Scenario**: External API rate limit reached

**Behavior**: Router automatically falls back to local models

**Result**: Seamless user experience, no errors

## Limitations

1. **No Rate Limiting**: External APIs may have rate limits (handle manually)
2. **No Cost Tracking**: Monitor API usage separately
3. **Basic Error Handling**: API failures fall back to local models
4. **Single Model**: Currently configured for one external model (NVIDIA)

## Troubleshooting

### API Key Not Found

```
Warning: No API key for nvidia_nim (NVIDIA_API_KEY)
```

**Solution**: Set environment variable:
```bash
export NVIDIA_API_KEY="nvapi-your-key"
```

### External Model Not Discovered

```
External API client initialized with 0 models
```

**Solution**: Check `config/external_apis.yaml`:
- Verify `enabled: true`
- Verify API key environment variable name matches
- Check YAML syntax

### Benchmark Fails

```
External API error: 401 Unauthorized
```

**Solution**: Verify API key is valid and has credits

### Slow External Responses

External APIs typically have 1-3 second latency. This is normal.

## Future Enhancements

Potential additions (not yet implemented):

1. **Rate Limiting**: Automatic throttling of external API calls
2. **Cost Tracking**: Token usage and cost estimation
3. **Multiple APIs**: OpenAI, Anthropic, Google, etc.
4. **Smart Caching**: Cache external responses to reduce API calls
5. **A/B Testing**: Compare local vs external on same queries
6. **Quality Scoring**: Automated quality comparison

## Security Notes

1. **Never commit `.env` file** with real API keys
2. **Use `.env.example`** as template
3. **Rotate keys regularly** for production use
4. **Monitor usage** to detect unauthorized access
5. **Set budgets** on external API accounts

## Cost Considerations

External APIs charge per token. Example costs:

- **NVIDIA NIM**: ~$0.10 per 1M tokens (varies by model)
- **Local Ollama**: Free after initial model download

**Recommendation**: Use external models for benchmarking and testing, not production routing.

## Support

For issues or questions:

1. Check logs: `pi_agent_state/`
2. Verify configuration: `config/external_apis.yaml`
3. Test API key manually (curl or Postman)
4. Check external API status pages

## License

This integration is part of the MoE Router API project. See main LICENSE file.
