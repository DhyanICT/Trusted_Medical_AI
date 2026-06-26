# Evaluation Guide - TrustMed AI System

This guide explains what evaluations are currently available and how to run them.

## Available Evaluations

### ✅ 1. Retrieval Quality (`evaluate_retrieval.py`)

**What it measures:**
- **Precision@k**: Accuracy of retrieved chunks at different k values (5, 10, 15)
- **Latency**: Response time of FAISS index retrieval (mean, min, max, percentiles)

**What's automatable:**
- ✅ Latency measurement (fully automated)
- ✅ Retrieval statistics (chunk types, scores, counts)
- ⚠️ Precision@k (requires ground truth labels - template provided)

**How to run:**
```bash
cd evaluations
python evaluate_retrieval.py
```

**Output:**
- `evaluations/retrieval_quality_results.json`
- Metrics: average latency, precision scores (if ground truth provided)

---

### ✅ 2. Answer Accuracy - Citation Presence (`evaluate_citations.py`)

**What it measures:**
- **Citation Presence Rate**: Percentage of responses with citations (target ≥95%)
- **Citation Structure**: Presence of trusted/community sections
- **URL Presence**: Whether citations include clickable links
- **Inline Citations**: Whether citations appear in answer body

**What's automatable:**
- ✅ Citation presence detection (fully automated)
- ✅ URL detection (fully automated)
- ✅ Section structure validation (fully automated)
- ❌ Factuality (requires human evaluation)
- ❌ Clarity (requires human evaluation)

**How to run:**
```bash
cd evaluations
python evaluate_citations.py
```

**Output:**
- `evaluations/citation_presence_results.json`
- Metrics: citation presence rate, section counts, URL counts

---

### ✅ 3. Trust Evaluation (`evaluate_trust.py`)

**What it measures:**
- **Source Labeling Correctness**: Whether sources are correctly labeled as trusted vs community
- **Confidence Scores**: Analysis of similarity scores from retrieval

**What's automatable:**
- ✅ Source labeling validation (partially automated - checks structure)
- ✅ Confidence score analysis (fully automated)
- ⚠️ Full correctness check (requires ground truth for perfect accuracy)

**How to run:**
```bash
cd evaluations
python evaluate_trust.py
```

**Output:**
- `evaluations/trust_evaluation_results.json`
- Metrics: labeling accuracy, confidence score statistics

---

### ✅ 4. End-to-End Performance (`evaluate_end_to_end.py`)

**What it measures:**
- **Response Time**: Total time from query to answer
- **Completeness**: Presence of required sections (trusted info, community, safety, citations)
- **Consistency**: Variation across multiple runs of the same query

**What's automatable:**
- ✅ Response time measurement (fully automated)
- ✅ Completeness checking (fully automated)
- ✅ Consistency measurement (fully automated)

**How to run:**
```bash
cd evaluations
python evaluate_end_to_end.py
```

**Output:**
- `evaluations/end_to_end_performance_results.json`
- Metrics: average response time, completeness scores, consistency scores

---

## Running All Evaluations

### Recommended: Comprehensive Evaluation with Ground Truth

```bash
cd evaluations
python run_comprehensive_evaluation.py
```

This will:
1. Run evaluation with ground truth data (most thorough)
2. Calculate Precision, Recall, F1 scores
3. Generate all visualizations (charts and dashboard)
4. Create detailed JSON report

### Alternative: Run All Individual Evaluations

```bash
cd evaluations
python run_all_evaluations.py
```

This will:
1. Run all 4 evaluation scripts
2. Generate individual result files
3. Create a comprehensive report: `evaluations/comprehensive_report_TIMESTAMP.json`

---

## What Can Be Achieved Right Now

### ✅ Fully Automated (Ready to Use)

1. **Retrieval Latency**: ✅ Can measure FAISS retrieval speed
2. **Citation Presence**: ✅ Can verify if citations are present (target ≥95%)
3. **URL Presence**: ✅ Can check if citations have links
4. **Response Time**: ✅ Can measure end-to-end speed
5. **Completeness**: ✅ Can check if all sections are present
6. **Consistency**: ✅ Can measure variation across runs
7. **Confidence Scores**: ✅ Can analyze similarity scores
8. **Precision/Recall/F1**: ✅ Now available with ground truth data
9. **Visualizations**: ✅ Charts and dashboards automatically generated

### ✅ Ground Truth Evaluation (NEW)

1. **Precision@k**: ✅ Now fully automated with `ground_truth.json`
2. **Recall@k**: ✅ Calculated automatically
3. **F1 Score**: ✅ Calculated automatically
4. **Source Labeling Correctness**: ✅ Validated against ground truth

### ❌ Requires Human Evaluation

1. **Factuality**: Needs medical experts to verify accuracy
2. **Clarity**: Needs human raters to assess readability
3. **Answer Quality**: Subjective assessment required

---

## Ground Truth Data

Ground truth data is now included in `evaluations/ground_truth.json`!

The file contains:
- 7 curated test queries
- Expected relevant chunks for each query
- Evaluation criteria and thresholds

### Using Ground Truth

Simply run:
```bash
cd evaluations
python evaluate_with_ground_truth.py
```

Or use the comprehensive runner:
```bash
python run_comprehensive_evaluation.py
```

### Extending Ground Truth

To add more test queries, edit `evaluations/ground_truth.json`:

```json
{
  "test_queries": [
    {
      "question": "Your test question",
      "expected_disease": "Disease name",
      "expected_kinds": ["disease", "drug", "reddit"],
      "min_relevant_chunks": 5,
      "relevant_chunk_identifiers": [
        {
          "kind": "disease",
          "title_contains": "keyword",
          "required": true
        }
      ]
    }
  ]
}
```

---

## Human Evaluation Templates

For factuality and clarity evaluation, create a CSV/JSON file:

```json
{
  "evaluations": [
    {
      "question": "What medications are used for type 2 diabetes?",
      "answer": "...",
      "factuality_score": 5,  // 1-5 scale
      "clarity_score": 4,     // 1-5 scale
      "factuality_notes": "Accurate information about metformin...",
      "clarity_notes": "Clear and well-structured..."
    }
  ]
}
```

---

## Expected Results

Based on your proposal targets:

- **Citation Presence**: ≥95% of responses should have citations ✅ (automated)
- **Retrieval Latency**: Should be <100ms for FAISS search ✅ (automated)
- **Response Time**: Should be <5 seconds end-to-end ✅ (automated)
- **Completeness**: Should have all 4 sections (trusted, community, safety, citations) ✅ (automated)
- **Source Labeling**: Should correctly separate trusted vs community ✅ (partially automated)

---

## Next Steps

1. **Run automated evaluations** to get baseline metrics
2. **Create ground truth labels** for Precision@k if needed
3. **Set up human evaluation** for factuality and clarity
4. **Iterate** based on results

---

## Files Structure

```
evaluations/
├── evaluate_with_ground_truth.py    # ⭐ Main evaluation (with ground truth)
├── evaluate_retrieval.py            # Retrieval quality metrics
├── evaluate_citations.py             # Citation presence
├── evaluate_trust.py                # Trust evaluation
├── evaluate_end_to_end.py           # Performance metrics
├── visualize_results.py             # 📊 Generate charts and dashboards
├── run_comprehensive_evaluation.py  # ⭐ Recommended runner
├── run_all_evaluations.py           # Run all individual scripts
├── ground_truth.json                # 📋 Ground truth test data
├── README.md                        # Evaluation documentation
│
├── evaluation_with_ground_truth_TIMESTAMP.json  # Detailed results
├── evaluation_dashboard.png                     # Overall dashboard
├── retrieval_metrics.png                        # Precision/Recall/F1 charts
├── citation_metrics.png                         # Citation analysis
└── performance_metrics.png                      # Performance charts
```

## Visualizations

After running evaluations, visualizations are automatically generated:

- **`evaluation_dashboard.png`** - Overall system score and key metrics
- **`retrieval_metrics.png`** - Precision, Recall, F1 at different k values
- **`citation_metrics.png`** - Citation presence and distribution
- **`performance_metrics.png`** - Response time and completeness

To generate visualizations manually:
```bash
cd evaluations
python visualize_results.py --results evaluation_with_ground_truth_results.json
```

