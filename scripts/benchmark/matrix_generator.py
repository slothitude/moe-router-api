"""Matrix generator for Router's Matrix benchmark system.

Generates visual outputs:
- JSON summary with speed and accuracy matrices
- HTML heatmap with color-coded performance
- CSV export of raw metrics
- Routing recommendations
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class MatrixGenerator:
    """Generate performance matrix outputs."""

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize matrix generator.

        Args:
            output_dir: Directory to save outputs (default: benchmark_output/)
        """
        if output_dir is None:
            output_dir = "benchmark_output"

        self.output_dir = Path(output_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.output_dir / f"matrix_{self.timestamp}"
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(
        self,
        speed_matrix: Dict[str, Dict[str, float]],
        accuracy_matrix: Dict[str, Dict[str, float]],
        recommendations: Dict[str, str],
        raw_metrics: List[Dict[str, Any]]
    ) -> str:
        """
        Generate all output formats.

        Args:
            speed_matrix: Model -> Category -> Avg latency
            accuracy_matrix: Model -> Category -> Accuracy score
            recommendations: Category -> Best model
            raw_metrics: List of all metric records

        Returns:
            Path to output directory
        """
        # Generate JSON summary
        json_path = self._generate_json(
            speed_matrix,
            accuracy_matrix,
            recommendations
        )

        # Generate HTML heatmap
        html_speed_path = self._generate_html_heatmap(
            speed_matrix,
            "speed",
            title="Speed Matrix (Average Latency in seconds)",
            metric_name="Latency (s)"
        )
        html_accuracy_path = self._generate_html_heatmap(
            accuracy_matrix,
            "accuracy",
            title="Accuracy Matrix (Semantic Similarity & Quality)",
            metric_name="Accuracy Score"
        )

        # Generate CSV export
        csv_path = self._generate_csv(raw_metrics)

        # Generate recommendations JSON
        rec_path = self._generate_recommendations(recommendations)

        return str(self.run_dir)

    def _generate_json(
        self,
        speed_matrix: Dict[str, Dict[str, float]],
        accuracy_matrix: Dict[str, Dict[str, float]],
        recommendations: Dict[str, str]
    ) -> Path:
        """Generate JSON summary file."""
        summary = {
            "timestamp": self.timestamp,
            "speed_matrix": speed_matrix,
            "accuracy_matrix": accuracy_matrix,
            "recommendations": recommendations,
        }

        path = self.run_dir / "summary.json"
        with open(path, 'w') as f:
            json.dump(summary, f, indent=2)

        return path

    def _generate_html_heatmap(
        self,
        matrix: Dict[str, Dict[str, float]],
        matrix_type: str,
        title: str,
        metric_name: str
    ) -> Path:
        """Generate interactive HTML heatmap."""

        # Get all models and categories
        models = sorted(matrix.keys())
        categories = sorted(set(
            cat for model_data in matrix.values()
            for cat in model_data.keys()
        ))

        # Determine value ranges for color coding
        all_values = []
        for model_data in matrix.values():
            all_values.extend(model_data.values())

        if not all_values:
            min_val, max_val = 0, 1
        else:
            min_val, max_val = min(all_values), max(all_values)

        # Generate HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .info {{
            text-align: center;
            color: #666;
            margin-bottom: 20px;
        }}
        table {{
            border-collapse: collapse;
            margin: 20px auto;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px 16px;
            text-align: center;
            border: 1px solid #ddd;
        }}
        th {{
            background: #444;
            color: white;
            font-weight: 600;
        }}
        th:first-child, td:first-child {{
            text-align: left;
            font-weight: 600;
            background: #f0f0f0;
        }}
        .cell {{
            position: relative;
            cursor: pointer;
            transition: transform 0.1s;
        }}
        .cell:hover {{
            transform: scale(1.05);
            z-index: 10;
        }}
        .value {{
            font-weight: 600;
            font-size: 14px;
        }}
        .legend {{
            text-align: center;
            margin: 20px 0;
        }}
        .legend-item {{
            display: inline-block;
            width: 50px;
            height: 20px;
            margin: 0 5px;
            vertical-align: middle;
        }}
        .best {{
            border: 2px solid #4CAF50;
            border-radius: 4px;
        }}
        .worst {{
            border: 2px solid #f44336;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="info">Generated: {self.timestamp}</div>

    <table>
        <thead>
            <tr>
                <th>Model \\ Category</th>
"""

        # Add category headers
        for category in categories:
            html += f'                <th>{category}</th>\n'

        html += "            </tr>\n        </thead>\n        <tbody>\n"

        # Find best/worst values for each column
        best_per_category = {}
        worst_per_category = {}

        for category in categories:
            values = [
                matrix[model].get(category, float('inf') if matrix_type == 'speed' else 0)
                for model in models
            ]
            if matrix_type == 'speed':
                best_per_category[category] = min(values)
                worst_per_category[category] = max(values)
            else:
                best_per_category[category] = max(values)
                worst_per_category[category] = min(values)

        # Add data rows
        for model in models:
            html += f'            <tr>\n                <td>{model}</td>\n'

            for category in categories:
                value = matrix[model].get(category, 0)

                # Determine color based on value
                if matrix_type == 'speed':
                    # Lower is better (green), higher is worse (red)
                    normalized = (value - min_val) / (max_val - min_val) if max_val > min_val else 0.5
                    # Invert: low = green, high = red
                    red = int(255 * normalized)
                    green = int(255 * (1 - normalized))
                    bg_color = f'rgb({red}, {green}, 0)'
                else:
                    # Higher is better (green), lower is worse (red)
                    normalized = (value - min_val) / (max_val - min_val) if max_val > min_val else 0.5
                    green = int(255 * normalized)
                    red = int(255 * (1 - normalized))
                    bg_color = f'rgb({red}, {green}, 0)'

                # Check if best or worst
                cell_class = 'cell'
                if value == best_per_category.get(category):
                    cell_class += ' best'
                elif value == worst_per_category.get(category):
                    cell_class += ' worst'

                # Format value
                if matrix_type == 'speed':
                    display_value = f'{value:.2f}s'
                else:
                    display_value = f'{value:.2%}'

                html += f'                <td class="{cell_class}" style="background-color: {bg_color}">\n'
                html += f'                    <span class="value">{display_value}</span>\n'
                html += f'                </td>\n'

            html += '            </tr>\n'

        html += """        </tbody>
    </table>

    <div class="legend">
        <p><strong>Legend:</strong></p>
"""

        if matrix_type == 'speed':
            html += """        <span class="legend-item" style="background: rgb(0,255,0);"></span> Fastest (Best)
        <span class="legend-item" style="background: rgb(128,128,0);"></span> Average
        <span class="legend-item" style="background: rgb(255,0,0);"></span> Slowest (Worst)
        <p>Green cells with thick border = Best in category | Red cells with thick border = Worst in category</p>
"""
        else:
            html += """        <span class="legend-item" style="background: rgb(0,255,0);"></span> Most Accurate (Best)
        <span class="legend-item" style="background: rgb(128,128,0);"></span> Average
        <span class="legend-item" style="background: rgb(255,0,0);"></span> Least Accurate (Worst)
        <p>Green cells with thick border = Best in category | Red cells with thick border = Worst in category</p>
"""

        html += """
    </div>

    <script>
        // Add click-to-copy functionality
        document.querySelectorAll('.cell').forEach(cell => {
            cell.addEventListener('click', function() {
                const value = this.querySelector('.value').textContent;
                navigator.clipboard.writeText(value).then(() => {
                    const original = this.style.backgroundColor;
                    this.style.backgroundColor = '#ffff00';
                    setTimeout(() => {
                        this.style.backgroundColor = original;
                    }, 200);
                });
            });
        });
    </script>
</body>
</html>"""

        path = self.run_dir / f"{matrix_type}_matrix.html"
        with open(path, 'w') as f:
            f.write(html)

        return path

    def _generate_csv(self, raw_metrics: List[Dict[str, Any]]) -> Path:
        """Generate CSV export of raw metrics."""
        if not raw_metrics:
            path = self.run_dir / "detailed_metrics.csv"
            with open(path, 'w') as f:
                f.write("No metrics collected\n")
            return path

        # Get all unique keys from metrics
        fieldnames = set()
        for metric in raw_metrics:
            fieldnames.update(metric.keys())
        fieldnames = sorted(fieldnames)

        path = self.run_dir / "detailed_metrics.csv"
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(raw_metrics)

        return path

    def _generate_recommendations(
        self,
        recommendations: Dict[str, str]
    ) -> Path:
        """Generate recommendations JSON file."""
        # Add explanation
        detailed_rec = {
            "timestamp": self.timestamp,
            "summary": "Routing recommendations based on benchmark results",
            "recommendations": recommendations,
            "explanation": {
                "agentic": "Multi-step reasoning and planning tasks",
                "document": "Document writing, editing, and summarization",
                "code": "Code generation, debugging, and optimization",
                "creative": "Creative writing and content generation",
                "factual": "Quick factual questions and definitions"
            }
        }

        path = self.run_dir / "recommendations.json"
        with open(path, 'w') as f:
            json.dump(detailed_rec, f, indent=2)

        return path

    def calculate_matrices(
        self,
        metrics_list: List[Any],
        quality_scores_list: List[Dict[str, float]]
    ) -> tuple[
        Dict[str, Dict[str, float]],  # speed_matrix
        Dict[str, Dict[str, float]],  # accuracy_matrix
        Dict[str, str]                 # recommendations
    ]:
        """
        Calculate speed and accuracy matrices from raw metrics.

        Args:
            metrics_list: List of BenchmarkMetrics
            quality_scores_list: List of quality score dicts

        Returns:
            Tuple of (speed_matrix, accuracy_matrix, recommendations)
        """
        speed_matrix: Dict[str, Dict[str, float]] = {}
        accuracy_matrix: Dict[str, Dict[str, float]] = {}

        # Aggregate data
        speed_sums: Dict[str, Dict[str, List[float]]] = {}
        accuracy_sums: Dict[str, Dict[str, List[float]]] = {}

        for metrics, quality_scores in zip(metrics_list, quality_scores_list):
            model = metrics.model
            category = metrics.category

            # Initialize dicts if needed
            if model not in speed_sums:
                speed_sums[model] = {}
            if model not in accuracy_sums:
                accuracy_sums[model] = {}

            if category not in speed_sums[model]:
                speed_sums[model][category] = []
            if category not in accuracy_sums[model]:
                accuracy_sums[model][category] = []

            # Add speed (convert ms to seconds)
            speed_sums[model][category].append(
                metrics.total_latency_ms / 1000
            )

            # Add accuracy
            accuracy = quality_scores.get("overall_accuracy", 0.0)
            accuracy_sums[model][category].append(accuracy)

        # Calculate averages
        for model in speed_sums:
            speed_matrix[model] = {}
            for category in speed_sums[model]:
                values = speed_sums[model][category]
                speed_matrix[model][category] = sum(values) / len(values)

        for model in accuracy_sums:
            accuracy_matrix[model] = {}
            for category in accuracy_sums[model]:
                values = accuracy_sums[model][category]
                accuracy_matrix[model][category] = sum(values) / len(values)

        # Generate recommendations (best model per category)
        recommendations = {}

        categories = set()
        for model_data in speed_matrix.values():
            categories.update(model_data.keys())

        for category in categories:
            # Find best model based on combined score
            # Lower speed + higher accuracy = better
            best_model = None
            best_score = float('-inf')

            for model in speed_matrix:
                if category not in speed_matrix[model]:
                    continue

                speed = speed_matrix[model][category]
                accuracy = accuracy_matrix.get(model, {}).get(category, 0.0)

                # Normalize and combine (60% accuracy, 40% speed)
                # Lower speed is better, so invert it
                max_speed = max(
                    speed_matrix[m][category]
                    for m in speed_matrix
                    if category in speed_matrix[m]
                )
                normalized_speed = 1 - (speed / max_speed) if max_speed > 0 else 0

                combined_score = (accuracy * 0.6) + (normalized_speed * 0.4)

                if combined_score > best_score:
                    best_score = combined_score
                    best_model = model

            if best_model:
                recommendations[category] = best_model

        return speed_matrix, accuracy_matrix, recommendations


__all__ = ["MatrixGenerator"]
