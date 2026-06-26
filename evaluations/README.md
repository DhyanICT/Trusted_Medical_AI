# Evaluation Framework

This directory contains comprehensive evaluation tools for the TrustMed AI system.

## Files

### Evaluation Scripts

- **`evaluate_with_ground_truth.py`** - Main evaluation script using ground truth data
  - Calculates Precision, Recall, F1 at different k values
  - Evaluates citations, performance, and trust metrics
  - Uses ground truth labels for accurate assessment

- **`evaluate_retrieval.py`** - Retrieval quality metrics (latency, precision)
- **`evaluate_citations.py`** - Citation presence validation
- **`evaluate_end_to_end.py`** - End-to-end performance metrics
- **`evaluate_trust.py`** - Trust evaluation (source labeling, confidence)

### Ground Truth Data

- **`ground_truth.json`** - Manually curated test queries with expected results
  - Contains 7 test queries with expected relevant chunks
  - Defines evaluation criteria and thresholds
  - Can be extended with more queries

### Visualization

- **`visualize_results.py`** - Generates charts and graphs from evaluation results
  - Retrieval metrics (Precision, Recall, F1)
  - Citation metrics
  - Performance metrics
  - Overall dashboard

### Runners

- **`run_comprehensive_evaluation.py`** - Main runner (recommended)
  - Runs evaluation with ground truth
  - Generates all visualizations
  - Creates comprehensive report

- **`run_all_evaluations.py`** - Runs all individual evaluation scripts

## Quick Start

### 1. Run Comprehensive Evaluation (Recommended)

```bash
cd evaluations
python run_comprehensive_evaluation.py
```

This will:
- Run evaluation with ground truth data
- Generate all visualizations
- Create detailed JSON report

### 2. Run Individual Evaluations

```bash
cd evaluations

# With ground truth (most thorough)
python evaluate_with_ground_truth.py

# Individual metrics
python evaluate_retrieval.py
python evaluate_citations.py
python evaluate_end_to_end.py
python evaluate_trust.py
```

### 3. Generate Visualizations

```bash
cd evaluations
python visualize_results.py --results evaluation_with_ground_truth_results.json
```

## Output Files

After running evaluations, you'll find:

- **`evaluation_with_ground_truth_TIMESTAMP.json`** - Detailed results
- **`evaluation_dashboard.png`** - Overall metrics dashboard
- **`retrieval_metrics.png`** - Precision/Recall/F1 charts
- **`citation_metrics.png`** - Citation analysis charts
- **`performance_metrics.png`** - Response time and completeness charts

## Ground Truth Format

The `ground_truth.json` file contains:

```json
{
  "test_queries": [
    {
      "question": "What medications are used for type 2 diabetes?",
      "expected_disease": "Type 2 diabetes",
      "expected_kinds": ["disease", "drug", "reddit"],
      "min_relevant_chunks": 5,
      "relevant_chunk_identifiers": [
        {
          "kind": "disease",
          "title_contains": "type 2 diabetes",
          "required": true
        }
      ],
      "expected_sections": ["trusted_info", "community", "safety", "citations"],
      "expected_citation_count": {
        "min_trusted": 2,
        "min_community": 0,
        "min_total": 3
      }
    }
  ],
  "evaluation_criteria": {
    "retrieval": {
      "precision_at_5_threshold": 0.6,
      "precision_at_10_threshold": 0.7,
      "precision_at_15_threshold": 0.75
    },
    "citations": {
      "presence_rate_threshold": 0.95
    }
  }
}
```

## Metrics Explained

### Retrieval Quality
- **Precision@k**: Fraction of retrieved chunks that are relevant
- **Recall@k**: Fraction of relevant chunks that were retrieved
- **F1@k**: Harmonic mean of Precision and Recall
- **Latency**: Time to retrieve chunks from FAISS

### Citation Presence
- **Citation Presence Rate**: Percentage of queries with citations
- **Trusted vs Community**: Separation of source types
- **URL Presence**: Whether citations include links

### Performance
- **Response Time**: End-to-end time to generate answer
- **Completeness**: Presence of required sections
- **Consistency**: Variation across multiple runs

### Trust
- **Labeling Accuracy**: Correct separation of trusted vs community sources
- **Confidence Scores**: Analysis of similarity scores

## Extending Ground Truth

To add more test queries:

1. Edit `ground_truth.json`
2. Add a new entry to `test_queries` array
3. Specify expected disease, chunk kinds, and citation counts
4. Run evaluation again

## Requirements

Make sure you have:
- `matplotlib` and `seaborn` for visualizations
- All dependencies from `code/requirements.txt`

Install with:
```bash
pip install matplotlib seaborn
```

## Troubleshooting

**No citations found**: Check that the system is generating citations properly. The evaluation checks for "Sources / Citations" section.

**Low precision scores**: Verify ground truth labels match actual data in your database. Update `ground_truth.json` if needed.

**Visualization errors**: Ensure matplotlib is installed and using a non-interactive backend (handled automatically).

