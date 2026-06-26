"""
Visualization of Evaluation Results
Generates charts and graphs from evaluation data.
"""

import json
import os
import sys
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import numpy as np
from datetime import datetime

# Try to import seaborn for better styling
try:
    import seaborn as sns
    sns.set_style("whitegrid")
    USE_SEABORN = True
except ImportError:
    USE_SEABORN = False


def load_evaluation_results(result_file: str) -> Dict[str, Any]:
    """Load evaluation results from JSON file"""
    with open(result_file, "r", encoding="utf-8") as f:
        return json.load(f)


def create_retrieval_metrics_chart(results: Dict[str, Any], output_dir: str):
    """Create improved charts for retrieval metrics (Precision, Recall, F1)"""
    
    if "summary" not in results or "retrieval" not in results["summary"]:
        print("⚠️ No retrieval metrics found in results")
        return
    
    retrieval = results["summary"]["retrieval"]
    
    # Create figure with better styling and spacing
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.suptitle('Retrieval Quality Metrics', fontsize=18, fontweight='bold', y=1.02)
    plt.subplots_adjust(wspace=0.4, top=0.92)  # Add spacing between subplots
    
    k_values = [5, 10, 15]
    precision_values = [
        retrieval.get("avg_precision_at_5", 0),
        retrieval.get("avg_precision_at_10", 0),
        retrieval.get("avg_precision_at_15", 0),
    ]
    recall_values = [
        retrieval.get("avg_recall_at_5", 0),
        retrieval.get("avg_recall_at_10", 0),
        retrieval.get("avg_recall_at_15", 0),
    ]
    f1_values = [
        retrieval.get("avg_f1_at_5", 0),
        retrieval.get("avg_f1_at_10", 0),
        retrieval.get("avg_f1_at_15", 0),
    ]
    
    # Define colors with better contrast
    colors = {
        'precision': '#27ae60',  # Green
        'recall': '#3498db',     # Blue
        'f1': '#e74c3c'           # Red
    }
    
    # Precision chart
    bars1 = axes[0].bar(k_values, precision_values, color=colors['precision'], alpha=0.8, 
                        edgecolor='white', linewidth=2, width=2.5)
    axes[0].set_title('Precision@K', fontsize=14, fontweight='bold', pad=15)
    axes[0].set_xlabel('K (Number of Results)', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Precision', fontsize=12, fontweight='bold')
    axes[0].set_ylim([0, 1.1])
    axes[0].set_xticks(k_values)
    axes[0].grid(True, alpha=0.3, linestyle='--', axis='y')
    axes[0].set_facecolor('#f8f9fa')
    
    # Add value labels on bars
    for bar, val in zip(bars1, precision_values):
        height = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2., height + 0.03,
                    f'{val:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # Add threshold line if available
    if precision_values:
        avg_precision = sum(precision_values) / len(precision_values)
        axes[0].axhline(y=avg_precision, color='gray', linestyle=':', linewidth=1.5, alpha=0.7, label=f'Avg: {avg_precision:.3f}')
        axes[0].legend(loc='lower right', fontsize=9)
    
    # Recall chart
    bars2 = axes[1].bar(k_values, recall_values, color=colors['recall'], alpha=0.8,
                        edgecolor='white', linewidth=2, width=2.5)
    axes[1].set_title('Recall@K', fontsize=14, fontweight='bold', pad=15)
    axes[1].set_xlabel('K (Number of Results)', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Recall', fontsize=12, fontweight='bold')
    axes[1].set_ylim([0, 1.1])
    axes[1].set_xticks(k_values)
    axes[1].grid(True, alpha=0.3, linestyle='--', axis='y')
    axes[1].set_facecolor('#f8f9fa')
    
    for bar, val in zip(bars2, recall_values):
        height = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2., height + 0.03,
                    f'{val:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    if recall_values:
        avg_recall = sum(recall_values) / len(recall_values)
        axes[1].axhline(y=avg_recall, color='gray', linestyle=':', linewidth=1.5, alpha=0.7, label=f'Avg: {avg_recall:.3f}')
        axes[1].legend(loc='lower right', fontsize=9)
    
    # F1 chart
    bars3 = axes[2].bar(k_values, f1_values, color=colors['f1'], alpha=0.8,
                        edgecolor='white', linewidth=2, width=2.5)
    axes[2].set_title('F1 Score@K', fontsize=14, fontweight='bold', pad=15)
    axes[2].set_xlabel('K (Number of Results)', fontsize=12, fontweight='bold')
    axes[2].set_ylabel('F1 Score', fontsize=12, fontweight='bold')
    axes[2].set_ylim([0, 1.1])
    axes[2].set_xticks(k_values)
    axes[2].grid(True, alpha=0.3, linestyle='--', axis='y')
    axes[2].set_facecolor('#f8f9fa')
    
    for bar, val in zip(bars3, f1_values):
        height = bar.get_height()
        axes[2].text(bar.get_x() + bar.get_width()/2., height + 0.03,
                    f'{val:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    if f1_values:
        avg_f1 = sum(f1_values) / len(f1_values)
        axes[2].axhline(y=avg_f1, color='gray', linestyle=':', linewidth=1.5, alpha=0.7, label=f'Avg: {avg_f1:.3f}')
        axes[2].legend(loc='lower right', fontsize=9)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, "retrieval_metrics.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"✅ Saved: {output_path}")


def create_citation_metrics_chart(results: Dict[str, Any], output_dir: str):
    """Create charts for citation metrics"""
    
    if "queries" not in results:
        print("⚠️ No query-level data found")
        return
    
    queries = results["queries"]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Citation presence per query
    query_numbers = list(range(1, len(queries) + 1))
    has_citations = [1 if q.get("citations", {}).get("has_citations", False) else 0 for q in queries]
    trusted_counts = [q.get("citations", {}).get("trusted_citations", 0) for q in queries]
    community_counts = [q.get("citations", {}).get("community_citations", 0) for q in queries]
    
    axes[0, 0].bar(query_numbers, has_citations, color='#27ae60', alpha=0.7)
    axes[0, 0].set_title('Citation Presence per Query', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Query Number')
    axes[0, 0].set_ylabel('Has Citations (1=Yes, 0=No)')
    axes[0, 0].set_xticks(query_numbers)
    axes[0, 0].grid(True, alpha=0.3)
    
    # Citation counts stacked
    x = np.arange(len(query_numbers))
    width = 0.6
    axes[0, 1].bar(x, trusted_counts, width, label='Trusted', color='#3498db', alpha=0.7)
    axes[0, 1].bar(x, community_counts, width, bottom=trusted_counts, label='Community', color='#e74c3c', alpha=0.7)
    axes[0, 1].set_title('Citation Counts by Type', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('Query Number')
    axes[0, 1].set_ylabel('Number of Citations')
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(query_numbers)
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Citation presence rate (if available)
    if "summary" in results and "citations" in results["summary"]:
        citation_rate = results["summary"]["citations"].get("citation_presence_rate", 0) * 100
        axes[1, 0].barh([0], [citation_rate], color='#2ecc71', alpha=0.7, height=0.3)
        axes[1, 0].axvline(x=95, color='r', linestyle='--', label='Target (95%)')
        axes[1, 0].set_title('Citation Presence Rate', fontsize=12, fontweight='bold')
        axes[1, 0].set_xlabel('Percentage (%)')
        axes[1, 0].set_xlim([0, 100])
        axes[1, 0].set_yticks([])
        axes[1, 0].text(citation_rate + 2, 0, f'{citation_rate:.1f}%', va='center', fontweight='bold')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
    
    # Citation distribution pie chart
    total_trusted = sum(trusted_counts)
    total_community = sum(community_counts)
    if total_trusted + total_community > 0:
        axes[1, 1].pie([total_trusted, total_community], 
                       labels=['Trusted Sources', 'Community Sources'],
                       colors=['#3498db', '#e74c3c'],
                       autopct='%1.1f%%',
                       startangle=90)
        axes[1, 1].set_title('Citation Distribution', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, "citation_metrics.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: {output_path}")


def create_performance_chart(results: Dict[str, Any], output_dir: str):
    """Create charts for performance metrics"""
    
    if "queries" not in results:
        return
    
    queries = results["queries"]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    query_numbers = list(range(1, len(queries) + 1))
    response_times = [q.get("performance", {}).get("response_time_seconds", 0) for q in queries]
    completeness_scores = [q.get("performance", {}).get("completeness_score", 0) for q in queries]
    
    # Response time
    axes[0].bar(query_numbers, response_times, color='#9b59b6', alpha=0.7)
    if "summary" in results and "performance" in results["summary"]:
        avg_time = results["summary"]["performance"].get("avg_response_time_seconds", 0)
        axes[0].axhline(y=avg_time, color='r', linestyle='--', label=f'Average: {avg_time:.2f}s')
    axes[0].set_title('Response Time per Query', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Query Number')
    axes[0].set_ylabel('Time (seconds)')
    axes[0].set_xticks(query_numbers)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Completeness
    axes[1].bar(query_numbers, completeness_scores, color='#f39c12', alpha=0.7)
    axes[1].axhline(y=0.75, color='r', linestyle='--', label='Target (0.75)')
    axes[1].set_title('Completeness Score per Query', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Query Number')
    axes[1].set_ylabel('Completeness Score')
    axes[1].set_ylim([0, 1])
    axes[1].set_xticks(query_numbers)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, "performance_metrics.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: {output_path}")


def create_overall_dashboard(results: Dict[str, Any], output_dir: str):
    """Create an overall dashboard with all key metrics for @5, @10, and @15"""
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    fig.suptitle('TrustMed AI - Retrieval Quality Dashboard', fontsize=20, fontweight='bold', y=0.98)
    
    # Get metrics
    summary = results.get("summary", {}).get("retrieval", {})
    overall_score = min(results.get("summary", {}).get("overall_score", 0), 1.0) * 100
    
    # Data for each K value
    k_configs = [
        {
            "k": 5,
            "ax": axes[0],
            "precision": min(summary.get("avg_precision_at_5", 0), 1.0) * 100,
            "f1": min(summary.get("avg_f1_at_5", 0), 1.0) * 100,
        },
        {
            "k": 10,
            "ax": axes[1],
            "precision": min(summary.get("avg_precision_at_10", 0), 1.0) * 100,
            "f1": min(summary.get("avg_f1_at_10", 0), 1.0) * 100,
        },
        {
            "k": 15,
            "ax": axes[2],
            "precision": min(summary.get("avg_precision_at_15", 0), 1.0) * 100,
            "f1": min(summary.get("avg_f1_at_15", 0), 1.0) * 100,
        }
    ]
    
    # Create bar charts for each K value
    for config in k_configs:
        ax = config["ax"]
        k = config["k"]
        precision = config["precision"]
        f1 = config["f1"]
        
        # For K=15, include overall score; for others, just precision and F1
        if k == 15:
            metrics = ['Overall Score\n(F1@15)', 'Precision@15', 'F1 Score@15']
            values = [overall_score, precision, f1]
            colors = ['#2ecc71', '#3498db', '#16a085']
        else:
            metrics = ['Precision@' + str(k), 'F1 Score@' + str(k)]
            values = [precision, f1]
            colors = ['#3498db', '#16a085']
        
        bars = ax.bar(metrics, values, color=colors, alpha=0.8, edgecolor='white', linewidth=2.5, width=0.6)
        
        # Add value labels on top of bars
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                    f'{val:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        # Styling
        ax.set_ylabel('Score (%)', fontsize=12, fontweight='bold')
        ax.set_ylim([0, 110])  # Extra space at top for labels
        ax.set_title(f'Metrics @{k}', fontsize=14, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, linestyle='--', axis='y', zorder=0)
        ax.set_facecolor('#f8f9fa')
    
    # Adjust layout to prevent overlap - add padding
    plt.tight_layout(rect=[0, 0, 1, 0.96], pad=2.0, wspace=0.3)  # Leave space for suptitle and add padding
    
    output_path = os.path.join(output_dir, "evaluation_dashboard.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.2)
    plt.close()
    print(f"✅ Saved: {output_path}")


def visualize_evaluation_results(
    result_file: str = None,
    output_dir: str = None
):
    """
    Main function to generate all visualizations from evaluation results.
    """
    if result_file is None:
        # Try to find the most recent evaluation result
        eval_dir = os.path.dirname(__file__)
        result_files = [f for f in os.listdir(eval_dir) if f.endswith('_results.json') or f.startswith('comprehensive_report_')]
        if result_files:
            result_file = os.path.join(eval_dir, sorted(result_files)[-1])
        else:
            result_file = os.path.join(eval_dir, "evaluation_with_ground_truth_results.json")
    
    if output_dir is None:
        output_dir = os.path.dirname(result_file)
    
    print(f"Loading results from: {result_file}")
    results = load_evaluation_results(result_file)
    
    print("\nGenerating visualizations...")
    
    # Create retrieval quality charts only
    create_retrieval_metrics_chart(results, output_dir)
    create_overall_dashboard(results, output_dir)
    
    print(f"\n✅ All visualizations saved to: {output_dir}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize evaluation results')
    parser.add_argument('--results', type=str, help='Path to evaluation results JSON file')
    parser.add_argument('--output', type=str, help='Output directory for charts')
    
    args = parser.parse_args()
    
    visualize_evaluation_results(args.results, args.output)


if __name__ == "__main__":
    main()

