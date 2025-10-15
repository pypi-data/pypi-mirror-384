#!/usr/bin/env python3
"""
ASCII Plotting Module for Terminal Visualization
Uses plotext for clean, readable terminal charts
"""

import sys
from typing import List, Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import plotext
try:
    import plotext as plt
    PLOTEXT_AVAILABLE = True
except ImportError:
    PLOTEXT_AVAILABLE = False
    logger.warning("plotext not installed - ASCII plotting unavailable")


class ASCIIPlotter:
    """
    Terminal-based plotting using plotext
    Generates clean ASCII charts for data visualization
    """
    
    def __init__(self, width: int = 70, height: int = 20):
        """
        Initialize plotter
        
        Args:
            width: Plot width in characters
            height: Plot height in characters
        """
        self.width = width
        self.height = height
        self.available = PLOTEXT_AVAILABLE
    
    def plot_line(
        self,
        x: List[float],
        y: List[float],
        title: str = "Line Plot",
        xlabel: str = "X",
        ylabel: str = "Y",
        label: Optional[str] = None
    ) -> str:
        """
        Create a line plot
        
        Args:
            x: X-axis data
            y: Y-axis data
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            label: Data series label
        
        Returns:
            ASCII art string representation of the plot
        """
        if not self.available:
            return self._fallback_plot(x, y, title)
        
        try:
            plt.clf()  # Clear previous plot
            plt.plot_size(self.width, self.height)
            plt.plot(x, y, label=label)
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            if label:
                plt.legend()
            
            # Get the plot as string
            return plt.build()
        
        except Exception as e:
            logger.error(f"Plotting failed: {e}")
            return self._fallback_plot(x, y, title)
    
    def plot_multiple_lines(
        self,
        data: List[Tuple[List[float], List[float], str]],
        title: str = "Multi-Line Plot",
        xlabel: str = "X",
        ylabel: str = "Y"
    ) -> str:
        """
        Create a multi-line plot
        
        Args:
            data: List of (x, y, label) tuples
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
        
        Returns:
            ASCII art string representation of the plot
        """
        if not self.available:
            return f"[Plot unavailable: plotext not installed]\n{title}"
        
        try:
            plt.clf()
            plt.plot_size(self.width, self.height)
            
            for x, y, label in data:
                plt.plot(x, y, label=label)
            
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.legend()
            
            return plt.build()
        
        except Exception as e:
            logger.error(f"Multi-line plotting failed: {e}")
            return f"[Plot error: {str(e)}]\n{title}"
    
    def plot_scatter(
        self,
        x: List[float],
        y: List[float],
        title: str = "Scatter Plot",
        xlabel: str = "X",
        ylabel: str = "Y",
        label: Optional[str] = None
    ) -> str:
        """Create a scatter plot"""
        if not self.available:
            return self._fallback_plot(x, y, title)
        
        try:
            plt.clf()
            plt.plot_size(self.width, self.height)
            plt.scatter(x, y, label=label)
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            if label:
                plt.legend()
            
            return plt.build()
        
        except Exception as e:
            logger.error(f"Scatter plot failed: {e}")
            return self._fallback_plot(x, y, title)
    
    def plot_bar(
        self,
        categories: List[str],
        values: List[float],
        title: str = "Bar Chart",
        xlabel: str = "Category",
        ylabel: str = "Value"
    ) -> str:
        """Create a bar chart"""
        if not self.available:
            return f"[Plot unavailable: plotext not installed]\n{title}"
        
        try:
            plt.clf()
            plt.plot_size(self.width, self.height)
            plt.bar(categories, values)
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            
            return plt.build()
        
        except Exception as e:
            logger.error(f"Bar chart failed: {e}")
            return f"[Plot error: {str(e)}]\n{title}"
    
    def plot_histogram(
        self,
        data: List[float],
        bins: int = 20,
        title: str = "Histogram",
        xlabel: str = "Value",
        ylabel: str = "Frequency"
    ) -> str:
        """Create a histogram"""
        if not self.available:
            return f"[Plot unavailable: plotext not installed]\n{title}"
        
        try:
            plt.clf()
            plt.plot_size(self.width, self.height)
            plt.hist(data, bins=bins)
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            
            return plt.build()
        
        except Exception as e:
            logger.error(f"Histogram failed: {e}")
            return f"[Plot error: {str(e)}]\n{title}"
    
    def _fallback_plot(self, x: List[float], y: List[float], title: str) -> str:
        """
        Simple fallback visualization when plotext is unavailable
        Creates a basic ASCII representation
        """
        if not x or not y:
            return f"[No data to plot]\n{title}"
        
        # Simple text representation
        output = [f"\n{title}", "─" * 40]
        
        # Show min, max, mean
        try:
            output.append(f"Data points: {len(y)}")
            output.append(f"Min: {min(y):.2f}")
            output.append(f"Max: {max(y):.2f}")
            output.append(f"Mean: {sum(y)/len(y):.2f}")
        except Exception:
            output.append("Data statistics unavailable")
        
        output.append("─" * 40)
        output.append("[Install plotext for visual charts: pip install plotext]")
        
        return "\n".join(output)
    
    @staticmethod
    def is_available() -> bool:
        """Check if plotting is available"""
        return PLOTEXT_AVAILABLE


# Convenience functions for quick plotting

def plot_quick_line(x: List[float], y: List[float], title: str = "Plot") -> str:
    """Quick line plot"""
    plotter = ASCIIPlotter()
    return plotter.plot_line(x, y, title=title)


def plot_quick_bar(categories: List[str], values: List[float], title: str = "Chart") -> str:
    """Quick bar chart"""
    plotter = ASCIIPlotter()
    return plotter.plot_bar(categories, values, title=title)


# Example usage and testing
def example_usage():
    """Demonstrate ASCII plotting capabilities"""
    
    print("ASCII Plotter Demo\n")
    print("=" * 70)
    
    # Check availability
    if not ASCIIPlotter.is_available():
        print("❌ plotext not installed")
        print("Install with: pip install plotext")
        return
    
    print("✅ plotext available\n")
    
    # Example 1: Simple line plot
    x = list(range(2020, 2025))
    y = [100, 120, 115, 140, 150]
    
    plotter = ASCIIPlotter(width=60, height=15)
    
    print("Example 1: GDP Growth Over Time")
    print(plotter.plot_line(x, y, title="GDP Growth (2020-2024)", 
                           xlabel="Year", ylabel="GDP ($B)"))
    
    # Example 2: Multiple lines
    print("\n\nExample 2: Multi-Country Comparison")
    data = [
        (x, [100, 110, 105, 115, 120], "USA"),
        (x, [90, 95, 92, 100, 105], "UK"),
        (x, [80, 85, 88, 95, 100], "Japan")
    ]
    print(plotter.plot_multiple_lines(data, title="GDP Growth Comparison",
                                     xlabel="Year", ylabel="GDP Index"))
    
    # Example 3: Bar chart
    print("\n\nExample 3: Quarterly Revenue")
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    revenue = [250, 280, 290, 310]
    print(plotter.plot_bar(quarters, revenue, title="2024 Revenue by Quarter",
                          xlabel="Quarter", ylabel="Revenue ($M)"))
    
    print("\n" + "=" * 70)
    print("✅ ASCII plotting demo complete!")


if __name__ == "__main__":
    example_usage()
