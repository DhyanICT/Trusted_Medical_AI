"""
Comprehensive Evaluation Runner
Runs all evaluations with ground truth and generates visualizations.
"""

import os
import sys
import json
from datetime import datetime

# Import evaluation modules
from evaluate_with_ground_truth import evaluate_with_ground_truth
from visualize_results import visualize_evaluation_results, load_evaluation_results


def create_comprehensive_results_file(result_file: str, output_file: str):
    """Create a comprehensive results file with all evaluation data"""
    
    # Load the evaluation results
    results = load_evaluation_results(result_file)
    
    # Create comprehensive structure
    comprehensive = {
        "evaluation_metadata": {
            "timestamp": datetime.now().isoformat(),
            "ground_truth_version": results.get("ground_truth_version", "1.0"),
            "total_queries": results.get("total_queries", 0),
        },
        "summary": results.get("summary", {}),
        "detailed_results": {
            "queries": results.get("queries", []),
        },
        "metrics_summary": {
            "retrieval_quality": {
                "precision_at_5": results.get("summary", {}).get("retrieval", {}).get("avg_precision_at_5", 0),
                "precision_at_10": results.get("summary", {}).get("retrieval", {}).get("avg_precision_at_10", 0),
                "precision_at_15": results.get("summary", {}).get("retrieval", {}).get("avg_precision_at_15", 0),
                "recall_at_5": results.get("summary", {}).get("retrieval", {}).get("avg_recall_at_5", 0),
                "recall_at_10": results.get("summary", {}).get("retrieval", {}).get("avg_recall_at_10", 0),
                "recall_at_15": results.get("summary", {}).get("retrieval", {}).get("avg_recall_at_15", 0),
                "f1_at_5": results.get("summary", {}).get("retrieval", {}).get("avg_f1_at_5", 0),
                "f1_at_10": results.get("summary", {}).get("retrieval", {}).get("avg_f1_at_10", 0),
                "f1_at_15": results.get("summary", {}).get("retrieval", {}).get("avg_f1_at_15", 0),
            },
            "overall_score": results.get("summary", {}).get("overall_score", 0),
        }
    }
    
    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(comprehensive, f, indent=2, ensure_ascii=False)
    
    return comprehensive


def main():
    """Run comprehensive evaluation with ground truth and generate visualizations"""
    
    eval_dir = os.path.dirname(__file__)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("="*70)
    print("COMPREHENSIVE EVALUATION WITH GROUND TRUTH")
    print("="*70)
    print(f"Timestamp: {timestamp}")
    print("="*70)
    
    # Step 1: Run evaluation with ground truth
    print("\n[Step 1/3] Running evaluation with ground truth...")
    result_file = os.path.join(eval_dir, f"evaluation_with_ground_truth_{timestamp}.json")
    
    try:
        results = evaluate_with_ground_truth(output_file=result_file)
        
        # Print summary
        print("\n" + "="*70)
        print("EVALUATION SUMMARY")
        print("="*70)
        
        summary = results.get("summary", {})
        
        if "retrieval" in summary:
            r = summary["retrieval"]
            print(f"\n📊 Retrieval Quality:")
            print(f"   Precision@5:  {r.get('avg_precision_at_5', 0):.3f} (Recall: {r.get('avg_recall_at_5', 0):.3f}, F1: {r.get('avg_f1_at_5', 0):.3f})")
            print(f"   Precision@10: {r.get('avg_precision_at_10', 0):.3f} (Recall: {r.get('avg_recall_at_10', 0):.3f}, F1: {r.get('avg_f1_at_10', 0):.3f})")
            print(f"   Precision@15: {r.get('avg_precision_at_15', 0):.3f} (Recall: {r.get('avg_recall_at_15', 0):.3f}, F1: {r.get('avg_f1_at_15', 0):.3f})")
        
        overall = summary.get("overall_score", 0)
        print(f"\n🎯 Overall Score (F1@15): {overall:.3f} ({overall*100:.1f}%)")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Generate visualizations
    print("\n[Step 2/3] Generating visualizations...")
    try:
        visualize_evaluation_results(result_file, eval_dir)
        print("\n✅ All visualizations generated successfully!")
    except Exception as e:
        print(f"⚠️ Visualization generation failed: {e}")
        import traceback
        traceback.print_exc()
        print("Continuing without visualizations...")
    
    # Step 3: Create comprehensive results file
    print("\n[Step 3/3] Creating comprehensive results file...")
    try:
        comprehensive_file = os.path.join(eval_dir, f"comprehensive_evaluation_results_{timestamp}.json")
        create_comprehensive_results_file(result_file, comprehensive_file)
        print(f"✅ Comprehensive results saved to: {comprehensive_file}")
    except Exception as e:
        print(f"⚠️ Comprehensive results file creation failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("EVALUATION COMPLETE")
    print("="*70)
    print(f"Results: {result_file}")
    print(f"Comprehensive Results: {comprehensive_file if 'comprehensive_file' in locals() else 'N/A'}")
    print(f"Visualizations: {eval_dir}/")
    print("="*70)


if __name__ == "__main__":
    main()

