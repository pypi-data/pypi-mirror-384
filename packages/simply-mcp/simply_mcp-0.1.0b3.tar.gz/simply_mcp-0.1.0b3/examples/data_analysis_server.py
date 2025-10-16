#!/usr/bin/env python3
"""Data Analysis MCP Server Example

This example demonstrates a data analysis server that showcases:
- Loading datasets (CSV, JSON, Excel)
- Running statistical analyses with progress reporting
- Generating visualizations as binary images
- Creating analysis reports as PDFs
- Prompt templates for different analysis types
- Authentication and rate limiting
- Resource endpoints for datasets and results

This is a practical example for data science workflows, analytics APIs,
or automated reporting systems.

Installation:
    # Base requirements
    pip install simply-mcp[http,security]

    # For data analysis (recommended)
    pip install pandas numpy matplotlib seaborn

    # For PDF reports (optional)
    pip install reportlab

Usage:
    # Development mode
    simply-mcp dev examples/data_analysis_server.py --transport http --port 8090

    # Production mode
    python examples/data_analysis_server.py

Testing:
    # Upload a dataset
    curl -X POST http://localhost:8090/mcp \\
      -H "Authorization: Bearer data-analyst-key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
          "name": "load_csv",
          "arguments": {
            "name": "sales_data",
            "csv_data": "date,product,amount\\n2024-01-01,A,100\\n2024-01-02,B,150"
          }
        }
      }'

    # Run analysis
    curl -X POST http://localhost:8090/mcp \\
      -H "Authorization: Bearer data-analyst-key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
          "name": "describe_dataset",
          "arguments": {
            "dataset_id": "ds_001"
          }
        }
      }'

    # Generate visualization
    curl -X POST http://localhost:8090/mcp \\
      -H "Authorization: Bearer data-analyst-key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
          "name": "create_chart",
          "arguments": {
            "dataset_id": "ds_001",
            "chart_type": "bar",
            "x_column": "product",
            "y_column": "amount"
          }
        }
      }'

Features:
    - Load CSV, JSON, and Excel datasets
    - Statistical analysis and summaries
    - Data filtering and transformation
    - Chart generation (bar, line, scatter, histogram)
    - Export results to CSV or JSON
    - PDF report generation
    - Progress tracking for long analyses
    - Secure authentication
    - Rate limiting
"""

import asyncio
import io
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from simply_mcp import BuildMCPServer
from simply_mcp.core.types import ProgressReporter
from simply_mcp.features.binary import BinaryContent
from simply_mcp.security.auth import APIKeyAuthProvider
from simply_mcp.security.rate_limiter import RateLimiter
from simply_mcp.transports.http import HTTPTransport

# Try to import optional dependencies
try:
    import numpy as np
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import matplotlib

    matplotlib.use("Agg")  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
)

logger = logging.getLogger(__name__)

# Storage
DATA_DIR = Path(tempfile.mkdtemp()) / "datasets"
RESULTS_DIR = Path(tempfile.mkdtemp()) / "results"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Dataset registry
DATASETS: dict[str, dict[str, Any]] = {}
RESULTS: dict[str, dict[str, Any]] = {}


def create_data_analysis_server() -> BuildMCPServer:
    """Create the data analysis MCP server.

    Returns:
        Configured BuildMCPServer instance
    """
    mcp = BuildMCPServer(
        name="data-analysis-server",
        version="1.0.0",
        description="Data analysis server with statistical analysis and visualization",
    )

    # ===================================================================
    # Tool 1: Load CSV Dataset
    # ===================================================================

    @mcp.tool(
        name="load_csv",
        description="Load a CSV dataset for analysis",
    )
    def load_csv(
        name: str,
        csv_data: str,
        delimiter: str = ",",
        has_header: bool = True,
    ) -> dict[str, Any]:
        """Load a CSV dataset from text data.

        Args:
            name: Name for the dataset
            csv_data: CSV content as string
            delimiter: Column delimiter (default: comma)
            has_header: Whether first row contains headers

        Returns:
            Dataset information and preview
        """
        if not PANDAS_AVAILABLE:
            return {
                "success": False,
                "error": "Data analysis not available (pandas not installed)",
                "install_hint": "pip install pandas numpy",
            }

        try:
            # Parse CSV
            df = pd.read_csv(
                io.StringIO(csv_data),
                delimiter=delimiter,
                header=0 if has_header else None,
            )

            # Generate dataset ID
            dataset_id = f"ds_{len(DATASETS):03d}"

            # Save dataset
            dataset_path = DATA_DIR / f"{dataset_id}_{name}.csv"
            df.to_csv(dataset_path, index=False)

            # Store metadata
            DATASETS[dataset_id] = {
                "name": name,
                "type": "csv",
                "path": str(dataset_path),
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "created_at": datetime.utcnow().isoformat(),
            }

            # Create preview
            preview = df.head(5).to_dict(orient="records")

            logger.info(
                f"Dataset loaded: {dataset_id}",
                extra={"dataset_id": dataset_id, "rows": len(df)},
            )

            return {
                "success": True,
                "dataset_id": dataset_id,
                "name": name,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "preview": preview,
                "message": f"Dataset loaded: {dataset_id}",
            }

        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ===================================================================
    # Tool 2: Load JSON Dataset
    # ===================================================================

    @mcp.tool(
        name="load_json",
        description="Load a JSON dataset for analysis",
    )
    def load_json(
        name: str,
        json_data: str,
        orient: str = "records",
    ) -> dict[str, Any]:
        """Load a JSON dataset.

        Args:
            name: Name for the dataset
            json_data: JSON content as string
            orient: JSON orientation (records, columns, index, values)

        Returns:
            Dataset information and preview
        """
        if not PANDAS_AVAILABLE:
            return {
                "success": False,
                "error": "Data analysis not available (pandas not installed)",
            }

        try:
            # Parse JSON
            data = json.loads(json_data)
            df = pd.DataFrame(data) if orient == "records" else pd.read_json(
                io.StringIO(json_data), orient=orient
            )

            # Generate dataset ID
            dataset_id = f"ds_{len(DATASETS):03d}"

            # Save dataset
            dataset_path = DATA_DIR / f"{dataset_id}_{name}.json"
            df.to_json(dataset_path, orient="records")

            # Store metadata
            DATASETS[dataset_id] = {
                "name": name,
                "type": "json",
                "path": str(dataset_path),
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "created_at": datetime.utcnow().isoformat(),
            }

            preview = df.head(5).to_dict(orient="records")

            logger.info(f"Dataset loaded: {dataset_id}")

            return {
                "success": True,
                "dataset_id": dataset_id,
                "name": name,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "preview": preview,
                "message": f"Dataset loaded: {dataset_id}",
            }

        except Exception as e:
            logger.error(f"Failed to load JSON: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ===================================================================
    # Tool 3: Describe Dataset
    # ===================================================================

    @mcp.tool(
        name="describe_dataset",
        description="Get statistical summary of a dataset",
    )
    async def describe_dataset(
        dataset_id: str,
        progress: ProgressReporter | None = None,
    ) -> dict[str, Any]:
        """Generate statistical summary of a dataset.

        Args:
            dataset_id: ID of the dataset
            progress: Progress reporter

        Returns:
            Statistical summary
        """
        if not PANDAS_AVAILABLE:
            return {
                "success": False,
                "error": "Data analysis not available",
            }

        if dataset_id not in DATASETS:
            return {
                "success": False,
                "error": f"Dataset not found: {dataset_id}",
            }

        try:
            dataset = DATASETS[dataset_id]

            if progress:
                await progress.update(20, message="Loading dataset")

            # Load dataset
            df = pd.read_csv(dataset["path"]) if dataset["type"] == "csv" else pd.read_json(dataset["path"])

            if progress:
                await progress.update(50, message="Computing statistics")
                await asyncio.sleep(0.1)

            # Generate statistics
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            stats = {}

            if len(numeric_cols) > 0:
                desc = df[numeric_cols].describe()
                stats = desc.to_dict()

            if progress:
                await progress.update(80, message="Preparing summary")

            # Additional info
            missing = df.isnull().sum().to_dict()
            unique_counts = {col: df[col].nunique() for col in df.columns}

            if progress:
                await progress.update(100, message="Analysis complete")

            logger.info(f"Dataset described: {dataset_id}")

            return {
                "success": True,
                "dataset_id": dataset_id,
                "name": dataset["name"],
                "rows": len(df),
                "columns": len(df.columns),
                "statistics": stats,
                "missing_values": missing,
                "unique_counts": unique_counts,
                "message": "Statistical summary generated",
            }

        except Exception as e:
            logger.error(f"Failed to describe dataset: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ===================================================================
    # Tool 4: Create Chart
    # ===================================================================

    @mcp.tool(
        name="create_chart",
        description="Create a visualization from dataset",
    )
    async def create_chart(
        dataset_id: str,
        chart_type: str,
        x_column: str | None = None,
        y_column: str | None = None,
        title: str | None = None,
        progress: ProgressReporter | None = None,
    ) -> dict[str, Any]:
        """Create a chart from dataset.

        Args:
            dataset_id: ID of the dataset
            chart_type: Type of chart (bar, line, scatter, histogram, box)
            x_column: Column for x-axis (if applicable)
            y_column: Column for y-axis (if applicable)
            title: Chart title
            progress: Progress reporter

        Returns:
            Chart details and ID for download
        """
        if not PANDAS_AVAILABLE or not MATPLOTLIB_AVAILABLE:
            return {
                "success": False,
                "error": "Visualization not available",
                "install_hint": "pip install pandas matplotlib seaborn",
            }

        if dataset_id not in DATASETS:
            return {
                "success": False,
                "error": f"Dataset not found: {dataset_id}",
            }

        valid_types = ["bar", "line", "scatter", "histogram", "box"]
        if chart_type not in valid_types:
            return {
                "success": False,
                "error": f"Invalid chart type: {chart_type}",
                "valid_types": valid_types,
            }

        try:
            dataset = DATASETS[dataset_id]

            if progress:
                await progress.update(20, message="Loading dataset")

            # Load data
            df = pd.read_csv(dataset["path"]) if dataset["type"] == "csv" else pd.read_json(dataset["path"])

            if progress:
                await progress.update(40, message=f"Creating {chart_type} chart")
                await asyncio.sleep(0.1)

            # Create figure
            plt.figure(figsize=(10, 6))
            sns.set_style("whitegrid")

            # Generate chart based on type
            if chart_type == "bar":
                if not x_column or not y_column:
                    return {"success": False, "error": "Bar chart requires x_column and y_column"}
                sns.barplot(data=df, x=x_column, y=y_column)

            elif chart_type == "line":
                if not x_column or not y_column:
                    return {"success": False, "error": "Line chart requires x_column and y_column"}
                plt.plot(df[x_column], df[y_column])

            elif chart_type == "scatter":
                if not x_column or not y_column:
                    return {"success": False, "error": "Scatter plot requires x_column and y_column"}
                sns.scatterplot(data=df, x=x_column, y=y_column)

            elif chart_type == "histogram":
                if not x_column:
                    return {"success": False, "error": "Histogram requires x_column"}
                plt.hist(df[x_column].dropna(), bins=20)

            elif chart_type == "box":
                if not y_column:
                    return {"success": False, "error": "Box plot requires y_column"}
                sns.boxplot(data=df, y=y_column)

            # Set title
            if title:
                plt.title(title)
            else:
                plt.title(f"{chart_type.title()} Chart: {dataset['name']}")

            if progress:
                await progress.update(70, message="Saving chart")
                await asyncio.sleep(0.1)

            # Save chart
            chart_id = f"chart_{len(RESULTS):03d}"
            chart_filename = f"{chart_id}_{chart_type}.png"
            chart_path = RESULTS_DIR / chart_filename

            plt.tight_layout()
            plt.savefig(chart_path, dpi=150, bbox_inches="tight")
            plt.close()

            if progress:
                await progress.update(90, message="Updating registry")

            # Store metadata
            RESULTS[chart_id] = {
                "type": "chart",
                "filename": chart_filename,
                "path": str(chart_path),
                "dataset_id": dataset_id,
                "chart_type": chart_type,
                "x_column": x_column,
                "y_column": y_column,
                "title": title,
                "created_at": datetime.utcnow().isoformat(),
            }

            if progress:
                await progress.update(100, message="Chart created")

            logger.info(f"Chart created: {chart_id}")

            return {
                "success": True,
                "chart_id": chart_id,
                "chart_type": chart_type,
                "filename": chart_filename,
                "message": f"Chart created: {chart_id}",
            }

        except Exception as e:
            logger.error(f"Failed to create chart: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ===================================================================
    # Tool 5: Generate Report
    # ===================================================================

    @mcp.tool(
        name="generate_report",
        description="Generate a PDF analysis report",
    )
    async def generate_report(
        dataset_id: str,
        title: str,
        include_stats: bool = True,
        progress: ProgressReporter | None = None,
    ) -> dict[str, Any]:
        """Generate a PDF report for a dataset.

        Args:
            dataset_id: ID of the dataset
            title: Report title
            include_stats: Include statistical summary
            progress: Progress reporter

        Returns:
            Report details
        """
        if not PANDAS_AVAILABLE or not REPORTLAB_AVAILABLE:
            return {
                "success": False,
                "error": "Report generation not available",
                "install_hint": "pip install pandas reportlab",
            }

        if dataset_id not in DATASETS:
            return {
                "success": False,
                "error": f"Dataset not found: {dataset_id}",
            }

        try:
            dataset = DATASETS[dataset_id]

            if progress:
                await progress.update(10, message="Loading dataset")

            df = pd.read_csv(dataset["path"]) if dataset["type"] == "csv" else pd.read_json(dataset["path"])

            if progress:
                await progress.update(30, message="Creating PDF")
                await asyncio.sleep(0.1)

            # Create PDF
            report_id = f"report_{len([k for k in RESULTS if k.startswith('report_')]):03d}"
            report_filename = f"{report_id}_{title.replace(' ', '_')}.pdf"
            report_path = RESULTS_DIR / report_filename

            doc = SimpleDocTemplate(str(report_path), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            # Title
            story.append(Paragraph(title, styles["Title"]))
            story.append(Spacer(1, 0.2 * inch))

            # Dataset info
            story.append(Paragraph(f"Dataset: {dataset['name']}", styles["Heading2"]))
            story.append(Paragraph(f"Rows: {len(df)}", styles["Normal"]))
            story.append(Paragraph(f"Columns: {len(df.columns)}", styles["Normal"]))
            story.append(Spacer(1, 0.2 * inch))

            if progress:
                await progress.update(60, message="Adding statistics")
                await asyncio.sleep(0.1)

            # Statistics
            if include_stats:
                story.append(Paragraph("Statistical Summary", styles["Heading2"]))
                numeric_cols = df.select_dtypes(include=[np.number]).columns

                if len(numeric_cols) > 0:
                    desc = df[numeric_cols].describe()
                    table_data = [["Statistic"] + numeric_cols.tolist()]

                    for idx in desc.index:
                        row = [idx] + [f"{desc.loc[idx, col]:.2f}" for col in numeric_cols]
                        table_data.append(row)

                    table = Table(table_data)
                    table.setStyle(
                        TableStyle([
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 12),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ])
                    )
                    story.append(table)

            if progress:
                await progress.update(90, message="Finalizing report")

            doc.build(story)

            if progress:
                await progress.update(100, message="Report complete")

            # Store metadata
            RESULTS[report_id] = {
                "type": "report",
                "filename": report_filename,
                "path": str(report_path),
                "dataset_id": dataset_id,
                "title": title,
                "created_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Report generated: {report_id}")

            return {
                "success": True,
                "report_id": report_id,
                "filename": report_filename,
                "file_size": report_path.stat().st_size,
                "message": f"Report generated: {report_id}",
            }

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ===================================================================
    # Tool 6: List Datasets
    # ===================================================================

    @mcp.tool(
        name="list_datasets",
        description="List all loaded datasets",
    )
    def list_datasets() -> dict[str, Any]:
        """List all datasets.

        Returns:
            List of datasets with metadata
        """
        datasets = [
            {"dataset_id": ds_id, **ds_data}
            for ds_id, ds_data in DATASETS.items()
        ]

        return {
            "success": True,
            "count": len(datasets),
            "datasets": datasets,
        }

    # ===================================================================
    # Resource: Download Result
    # ===================================================================

    @mcp.resource(
        uri="result://{result_id}",
        name="Download analysis result",
        description="Download a chart or report",
    )
    def download_result(result_id: str) -> BinaryContent | dict[str, Any]:
        """Download an analysis result.

        Args:
            result_id: ID of the result

        Returns:
            Binary content or error
        """
        if result_id not in RESULTS:
            return {
                "error": "Result not found",
                "result_id": result_id,
            }

        result = RESULTS[result_id]
        result_path = Path(result["path"])

        if not result_path.exists():
            return {
                "error": "Result file not found on disk",
                "result_id": result_id,
            }

        content = BinaryContent.from_file(result_path)
        # Update filename to match original
        content.filename = result["filename"]
        return content

    # ===================================================================
    # Prompts: Analysis Templates
    # ===================================================================

    @mcp.prompt(
        name="exploratory_analysis",
        description="Generate prompt for exploratory data analysis",
    )
    def exploratory_analysis_prompt(dataset_id: str) -> str:
        """Generate EDA prompt.

        Args:
            dataset_id: ID of the dataset

        Returns:
            Prompt text
        """
        return f"""Perform an exploratory data analysis on dataset {dataset_id}.

Please analyze:
1. Data structure and types
2. Descriptive statistics
3. Missing values and data quality
4. Distributions of key variables
5. Potential correlations
6. Outliers and anomalies

Provide insights and recommendations for further analysis."""

    @mcp.prompt(
        name="statistical_test",
        description="Generate prompt for statistical testing",
    )
    def statistical_test_prompt(dataset_id: str, test_type: str) -> str:
        """Generate statistical test prompt.

        Args:
            dataset_id: ID of the dataset
            test_type: Type of test (t-test, anova, correlation, etc.)

        Returns:
            Prompt text
        """
        return f"""Conduct a {test_type} analysis on dataset {dataset_id}.

Steps:
1. State the null and alternative hypotheses
2. Check assumptions
3. Perform the test
4. Interpret results
5. Draw conclusions

Provide detailed statistical output and interpretation."""

    return mcp


async def main() -> None:
    """Main entry point."""
    logger.info("Starting data analysis server...")

    # Create server
    mcp = create_data_analysis_server()

    # Configuration
    api_keys = ["data-analyst-key", "researcher-key-456"]
    host = "0.0.0.0"
    port = 8090

    # Initialize
    await mcp.initialize()

    # Setup
    auth_provider = APIKeyAuthProvider(api_keys=api_keys)
    rate_limiter = RateLimiter(requests_per_minute=20, burst_size=5)

    transport = HTTPTransport(
        server=mcp.server,
        host=host,
        port=port,
        cors_enabled=True,
        auth_provider=auth_provider,
        rate_limiter=rate_limiter,
    )

    # Print info
    print("=" * 70)
    print("Data Analysis MCP Server")
    print("=" * 70)
    print()
    print("Server: data-analysis-server v1.0.0")
    print(f"Listening: http://{host}:{port}")
    print()
    print("Features:")
    print(f"  - Data Analysis: {'Available' if PANDAS_AVAILABLE else 'Not available (install pandas)'}")
    print(f"  - Visualization: {'Available' if MATPLOTLIB_AVAILABLE else 'Not available (install matplotlib)'}")
    print(f"  - PDF Reports: {'Available' if REPORTLAB_AVAILABLE else 'Not available (install reportlab)'}")
    print("  - Authentication: Enabled")
    print("  - Rate Limiting: 20 req/min")
    print()
    print("API Keys:")
    for key in api_keys:
        print(f"  - {key}")
    print()
    print("=" * 70)
    print()
    print("Server is running. Press Ctrl+C to stop.")
    print()

    try:
        await transport.start()
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await transport.stop()


if __name__ == "__main__":
    asyncio.run(main())
