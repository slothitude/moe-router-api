# NVIDIA NIM Models - Quick Reference Guide

## 🚀 Top Models for Comparison Benchmarking

Based on the 189 available NVIDIA models, here are the best ones for comparing against your local Ollama models:

### 🏆 Best for Factual/Complex Queries

1. **meta/llama-3.1-405b-instruct** (Currently configured)
   - **405B parameters** - Largest available
   - Best for: Complex reasoning, factual accuracy
   - Latency: ~500-2000ms
   - **Use for:** Quality benchmarking baseline

2. **meta/llama-3.1-70b-instruct**
   - **70B parameters** - Good balance
   - Best for: General tasks, factual queries
   - Latency: ~400-1500ms
   - **Use for:** Mid-range quality comparison

3. **mistralai/mistral-large-3-675b-instruct-2512**
   - **675B parameters** - Even larger!
   - Best for: Complex reasoning, enterprise tasks
   - Latency: ~800-2500ms
   - **Use for:** Ultimate quality comparison

### 💻 Best for Code

4. **deepseek-ai/deepseek-coder-6.7b-instruct**
   - **6.7B parameters** - Code specialist
   - Best for: Programming, code generation
   - Latency: ~300-800ms
   - **Use for:** Code quality comparison

5. **qwen/qwen2.5-coder-32b-instruct**
   - **32B parameters** - Large code model
   - Best for: Complex programming tasks
   - Latency: ~400-1000ms
   - **Use for:** Advanced code comparison

### 🧠 Best for Reasoning

6. **deepseek-ai/deepseek-v3.2**
   - Latest DeepSeek model
   - Best for: Math, logic, reasoning
   - **Use for:** Reasoning benchmarking

7. **microsoft/phi-4-mini-instruct**
   - Latest Phi-4 model
   - Best for: Efficient reasoning
   - Latency: Fast
   - **Use for:** Speed vs quality comparison

### 🌏 Multilingual

8. **qwen/qwen3.5-397b-a17b**
   - **397B parameters** - Massive Chinese model
   - Best for: Chinese, reasoning, factual
   - **Use for:** Non-English benchmarking

## 📊 Comparison Matrix

| Model | Size | Strength | Latency | Use Case |
|-------|------|----------|---------|----------|
| **Llama 3.1 405B** | 405B | Ultimate quality | 500-2000ms | Benchmark baseline |
| **Llama 3.1 70B** | 70B | Balance | 400-1500ms | Mid-range comparison |
| **Mistral Large 3** | 675B | Complex reasoning | 800-2500ms | Enterprise tasks |
| **DeepSeek Coder** | 6.7B | Code | 300-800ms | Code comparison |
| **Phi-4 Mini** | ~small | Speed + quality | Fast | Efficiency test |
| **Qwen 3.5** | 397B | Multilingual | 600-2000ms | Chinese/Asian |

## 🎯 Recommended Setup for Pi Agent Boss

### Option 1: Quality Focus (Current)
```yaml
- meta/llama-3.1-405b-instruct  # Ultimate quality comparison
```

### Option 2: Balanced Comparison
```yaml
- meta/llama-3.1-405b-instruct  # Large factual model
- deepseek-ai/deepseek-coder-6.7b-instruct  # Code specialist
```

### Option 3: Comprehensive Testing
```yaml
- meta/llama-3.1-405b-instruct  # Factual baseline
- deepseek-ai/deepseek-coder-6.7b-instruct  # Code baseline
- microsoft/phi-4-mini-instruct  # Efficient model
- qwen/qwen3.5-397b-a17b  # Multilingual
```

## 🔧 How to Add More Models

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
        specialization: "large-knowledge-model"
        priority: 90

      # Add more models:
      - name: "meta/llama-3.1-70b-instruct"
        display_name: "Llama 3.1 70B (NVIDIA)"
        categories: ["factual", "general"]
        specialization: "balanced-large-model"
        priority: 80

      - name: "deepseek-ai/deepseek-coder-6.7b-instruct"
        display_name: "DeepSeek Coder 6.7B"
        categories: ["code"]
        specialization: "code-generation"
        priority: 85
```

## 💡 Tips

1. **Start with one model** (current setup with 405B is perfect)
2. **Monitor costs** - External APIs charge per token
3. **Compare latency** - Note the speed difference (local ~100ms, external ~500-2000ms)
4. **Quality vs Speed** - Use external models to establish quality baseline
5. **Categorize queries** - Different models excel at different tasks

## 📝 Current Status

✅ **Configured:** 1 external model (Llama 3.1 405B)
✅ **Tested:** API connection successful
✅ **Discovery:** Working (10 total models found)
✅ **Ready:** To start benchmarking

## 🚀 Next Steps

1. Run benchmarks with current 405B model
2. Compare quality vs local models
3. Analyze when external model is worth the latency cost
4. Optionally add more specialized models for specific categories

---
**Total Available:** 189 models from NVIDIA NIM API
**Currently Configured:** 1 model (Llama 3.1 405B)
**Local Models:** 9 Ollama models
