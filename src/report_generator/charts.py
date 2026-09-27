"""Data visualization module using Matplotlib.

Generates publication-quality charts for executive business reporting:
- Category Revenue Comparison (Bar Chart)
- Revenue Timeline / Trend Analysis (Area & Line Chart)
- Category Revenue Contribution (Donut Chart)
"""

from pathlib import Path
from typing import Dict, Union

# pyrefly: ignore [missing-import]
import matplotlib
# Use headless backend for automation and server environments
matplotlib.use("Agg")
# pyrefly: ignore [missing-import]
import matplotlib.dates as mdates
# pyrefly: ignore [missing-import]
import matplotlib.pyplot as plt
# pyrefly: ignore [missing-import]
import matplotlib.ticker as ticker
import pandas as pd

from report_generator.data_processor import ProcessedData
from report_generator.logger import get_logger

logger = get_logger("charts")

# Enterprise color palette
PALETTE = [
    "#1E3A8A",  # Deep Navy
    "#2563EB",  # Royal Blue
    "#0D9488",  # Teal Green
    "#D97706",  # Amber
    "#7C3AED",  # Violet
    "#DB2777",  # Magenta
    "#475569",  # Slate
]


class ChartGenerator:
    """Generates styled charts and saves high-resolution image artifacts."""

    def __init__(self, output_dir: Union[str, Path] = "charts", currency_symbol: str = "₹") -> None:
        """Initialize ChartGenerator.

        Args:
            output_dir: Directory where generated image files will be saved.
            currency_symbol: Currency symbol for axis ticks and labels.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.currency_symbol = currency_symbol

        # Configure global aesthetic defaults
        plt.rcParams.update({
            "font.family": "sans-serif",
            "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial"],
            "axes.edgecolor": "#CBD5E1",
            "axes.linewidth": 1.0,
            "grid.color": "#F1F5F9",
            "grid.linestyle": "--",
            "grid.alpha": 0.8,
        })

    def generate_category_revenue_chart(
        self,
        category_summary: pd.DataFrame,
        filename: str = "revenue_by_category.png",
    ) -> Path:
        """Create a horizontal bar chart displaying revenue by business category.

        Args:
            category_summary: DataFrame with 'category' and 'revenue'.
            filename: Target image filename.

        Returns:
            Path: Absolute or resolved path to the saved PNG image.
        """
        target_path = self.output_dir / filename
        logger.info("Generating category revenue bar chart -> %s", target_path)

        df = category_summary.sort_values(by="revenue", ascending=True)

        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
        bars = ax.barh(
            df["category"],
            df["revenue"],
            color=PALETTE[:len(df)],
            height=0.6,
            edgecolor="#FFFFFF",
            linewidth=1.2,
        )

        ax.set_title("Revenue by Product Category", fontsize=13, fontweight="bold", pad=15, color="#1E293B")
        ax.set_xlabel(f"Total Revenue ({self.currency_symbol})", fontsize=10, fontweight="bold", color="#475569", labelpad=10)
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{self.currency_symbol}{x:,.0f}"))
        ax.xaxis.grid(True, linestyle="--", alpha=0.7)
        ax.set_axisbelow(True)

        # Remove top and right spines
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CBD5E1")
        ax.spines["bottom"].set_color("#CBD5E1")

        # Add data labels at the end of each bar
        max_rev = df["revenue"].max()
        for bar in bars:
            width = bar.get_width()
            ax.annotate(
                f"{self.currency_symbol}{width:,.0f}",
                xy=(width, bar.get_y() + bar.get_height() / 2),
                xytext=(6, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=8.5,
                fontweight="semibold",
                color="#1E293B",
            )

        ax.set_xlim(0, max_rev * 1.18)
        fig.tight_layout()
        fig.savefig(target_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return target_path

    def generate_revenue_trend_chart(
        self,
        date_summary: pd.DataFrame,
        filename: str = "revenue_trend.png",
    ) -> Path:
        """Create a timeline trend chart displaying daily or periodic revenue.

        Args:
            date_summary: DataFrame with 'date' and 'revenue'.
            filename: Target image filename.

        Returns:
            Path: Resolved path to the saved PNG image.
        """
        target_path = self.output_dir / filename
        logger.info("Generating revenue trend line chart -> %s", target_path)

        df = date_summary.copy()
        df["date_dt"] = pd.to_datetime(df["date"])
        df = df.sort_values(by="date_dt")

        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)

        # Plot line and filled area beneath
        ax.plot(
            df["date_dt"],
            df["revenue"],
            color="#2563EB",
            linewidth=2.2,
            marker="o",
            markersize=4.5,
            markerfacecolor="#1D4ED8",
            markeredgecolor="#FFFFFF",
            markeredgewidth=1.0,
            label="Daily Revenue",
        )
        ax.fill_between(df["date_dt"], df["revenue"], color="#3B82F6", alpha=0.15)

        ax.set_title("Revenue Timeline & Performance Trend", fontsize=13, fontweight="bold", pad=15, color="#1E293B")
        ax.set_ylabel(f"Revenue ({self.currency_symbol})", fontsize=10, fontweight="bold", color="#475569", labelpad=10)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{self.currency_symbol}{x:,.0f}"))
        ax.yaxis.grid(True, linestyle="--", alpha=0.7)
        ax.set_axisbelow(True)

        # Date formatting on X-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        fig.autofmt_xdate(rotation=30, ha="right")

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CBD5E1")
        ax.spines["bottom"].set_color("#CBD5E1")

        fig.tight_layout()
        fig.savefig(target_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return target_path

    def generate_top_categories_donut_chart(
        self,
        category_summary: pd.DataFrame,
        filename: str = "top_categories.png",
    ) -> Path:
        """Create a donut chart illustrating category percentage contribution.

        Args:
            category_summary: DataFrame with 'category' and 'revenue'.
            filename: Target image filename.

        Returns:
            Path: Resolved path to the saved PNG image.
        """
        target_path = self.output_dir / filename
        logger.info("Generating category contribution donut chart -> %s", target_path)

        df = category_summary.copy()
        colors = PALETTE[:len(df)]

        fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)

        wedges, texts, autotexts = ax.pie(
            df["revenue"],
            labels=df["category"],
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            pctdistance=0.75,
            wedgeprops=dict(width=0.45, edgecolor="#FFFFFF", linewidth=2.0),
        )

        for text in texts:
            text.set_color("#1E293B")
            text.set_fontsize(9)
            text.set_fontweight("semibold")

        for autotext in autotexts:
            autotext.set_color("#FFFFFF")
            autotext.set_fontsize(8.5)
            autotext.set_fontweight("bold")

        ax.set_title("Category Revenue Contribution Share", fontsize=13, fontweight="bold", pad=15, color="#1E293B")

        # Center circle indicator text
        center_text = f"Total Categories\n{len(df)}"
        ax.text(0, 0, center_text, ha="center", va="center", fontsize=9, fontweight="bold", color="#64748B")

        fig.tight_layout()
        fig.savefig(target_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return target_path

    def generate_all(self, data: ProcessedData) -> Dict[str, Path]:
        """Generate all standard report charts and return a mapping of paths.

        Args:
            data: ProcessedData instance containing summarized statistics.

        Returns:
            Dict[str, Path]: Mapping of chart identifiers to output file paths.
        """
        category_chart = self.generate_category_revenue_chart(data.category_summary)
        trend_chart = self.generate_revenue_trend_chart(data.date_summary)
        top_chart = self.generate_top_categories_donut_chart(data.category_summary)

        return {
            "category_revenue": category_chart,
            "revenue_trend": trend_chart,
            "top_categories": top_chart,
        }
