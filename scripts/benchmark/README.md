# Router's Matrix - MoE Router Benchmark System

A comprehensive benchmark test system for the MoE Router API that creates a "router's matrix" - a detailed performance comparison across all models and query categories.

## Features

- **130 Test Cases** across 5 categories:
  - 30 Agentic assistant tasks (planning, multi-step reasoning, tool use)
  - 25 Document writing/editing tasks
  - 30 Code generation/debugging tasks
  - 20 Creative writing tasks
  - 25 Quick factual questions

- **Multiple Metrics**:
  - Speed: Total latency, first token time, prompt speed, generation speed
  - Accuracy: Semantic similarity, keyword matching, code validity, completeness
  - Routing: Query type classification, model selection, confidence

- **Visual Outputs**:
  - Interactive HTML heatmaps
  - JSON summary with matrices
  - CSV export for analysis
  - Routing recommendations

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure Ollama is running
ollama serve
```

## Usage

### Quick Start

```bash
# Run quick benchmark (20 tests)
python scripts/router_matrix.py --quick

# Run full benchmark (130 tests)
python scripts/router_matrix.py --full
```

### Advanced Usage

```bash
# Benchmark specific category
python scripts/router_matrix.py --category code

# Benchmark specific models
python scripts/router_matrix.py --models qwen3:4b,llama3.1

# Custom API URL
python scripts/router_matrix.py --api-url http://localhost:9000

# Adjust concurrency and timeout
python scripts/router_matrix.py --concurrent 10 --timeout 180

# Verbose output
python scripts/router_matrix.py --quick -v
```

### CLI Options

```
--full              Run full benchmark (130 tests)
--quick             Run quick benchmark (20 tests)
--category CATEGORY Test specific category only
--models MODELS     Comma-separated list of models
--api-url URL       MoE Router API base URL
--output-dir DIR    Output directory for results
--concurrent N      Number of concurrent tests (default: 5)
--timeout N         Timeout per test in seconds (default: 120)
--format FORMAT     Output format: json, html, csv, all (default: all)
--verbose, -v       Verbose output
```

## Output

The benchmark generates the following files in `benchmark_output/matrix_YYYYMMDD_HHMMSS/`:

- `summary.json` - JSON summary with speed and accuracy matrices
- `speed_matrix.html` - Interactive heatmap of response times
- `accuracy_matrix.html` - Interactive heatmap of quality scores
- `recommendations.json` - Routing recommendations per category
- `detailed_metrics.csv` - Raw metrics for all test runs

## Understanding the Output

### Speed Matrix
- **Green cells** = Faster response times (better)
- **Red cells** = Slower response times (worse)
- Values show average latency in seconds

### Accuracy Matrix
- **Green cells** = Higher accuracy scores (better)
- **Red cells** = Lower accuracy scores (worse)
- Values show accuracy as percentage

### Recommendations
Based on combined speed and accuracy performance:
- Agentic tasks → Best model for multi-step reasoning
- Document tasks → Best model for writing/editing
- Code tasks → Best model for programming
- Creative tasks → Best model for creative content
- Factual tasks → Best model for quick answers

## Test Categories

### 1. Agentic Assistant Tasks (30 tests)
Multi-step reasoning, planning, and tool use simulation.

**Subcategories:**
- Planning (10 tests): Trip planning, project planning, meal prep, etc.
- Reasoning (10 tests): Business analysis, troubleshooting, calculations
- Tool Use (10 tests): API integration, debugging workflows, automation

### 2. Document Writing/Editing (25 tests)
Document creation, revision, and summarization.

**Subcategories:**
- Writing (10 tests): Emails, press releases, documentation
- Editing (8 tests): Grammar, clarity, tone adjustments
- Summarization (7 tests): TL;DRs, executive summaries

### 3. Code Generation/Debugging (30 tests)
Programming tasks across multiple languages.

**Subcategories:**
- Generation (12 tests): Functions, classes, APIs, SQL
- Debugging (10 tests): Fix bugs, resolve errors, optimize
- Optimization (8 tests): Improve performance, refactor code

### 4. Creative Writing (20 tests)
Imaginative content creation.

**Subcategories:**
- Stories (8 tests): Science fiction, mystery, romance, horror
- Poetry (5 tests): Haiku, sonnet, free verse, limerick
- Dialogue (4 tests): Conversations with distinct voices
- Content (3 tests): Trailers, menus, podcast intros

### 5. Quick Factual Questions (25 tests)
Simple lookups and definitions.

**Subcategories:**
- Definitions (7 tests): Technical concepts and terminology
- Facts (8 tests): Historical facts, versions, creators
- Comparisons (5 tests): Technology comparisons
- Quick Answers (5 tests): Commands, shortcuts, how-tos

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Benchmark Orchestrator (Python)         │
│  scripts/router_matrix.py                        │
└──────────────┬──────────────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
┌──────────────┐    ┌─────────────┐
│ Test Suite   │    │ Metrics     │
│ Generator    │◄───┤ Collector   │
│ (130 tests)  │    │ (Speed)     │
└──────┬───────┘    └─────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│          MoE Router API (Existing)              │
│  /api/v1/query endpoint                         │
└──────────────┬──────────────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
┌──────────────┐    ┌─────────────┐
│ Quality      │    │ Matrix      │
│ Analyzer     │    │ Generator   │
│ (Accuracy)   │    │ (HTML/JSON) │
└──────────────┘    └─────────────┘
```

## Performance Tips

1. **Preload models**: Run `python scripts/preload_models.py` before benchmarking
2. **Adjust concurrency**: Higher values (10-20) for faster benchmarks
3. **Use --quick**: For rapid testing during development
4. **Monitor resources**: Watch GPU/RAM usage during benchmarks

## Troubleshooting

### "No models available"
- Ensure Ollama is running: `ollama serve`
- Check models are installed: `ollama list`
- Verify API URL is correct: `--api-url http://localhost:8000`

### "Timeout errors"
- Increase timeout: `--timeout 180`
- Reduce concurrency: `--concurrent 3`
- Check system resources

### "Import errors"
- Install dependencies: `pip install -r requirements.txt`
- Ensure Python 3.8+ is installed

## Contributing

To add new test cases:

1. Edit the appropriate file in `scripts/benchmark/test_suites/`
2. Follow the test case format:
```python
{
    "id": "category_XXX",
    "category": "category",
    "subcategory": "type",
    "query": "Your test query here",
    "expected_elements": ["keyword1", "keyword2"],
    "complexity": "low|medium|high"
}
```
3. Re-run the benchmark

## License

Same as the MoE Router API project.
