"""Export the compiled LangGraph to a PNG via LangChain Mermaid renderer (uses network)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_compiled_graph_png(compiled_graph: Any, output_path: Path) -> None:
    """Render graph structure to PNG bytes and write output_path."""
    png = compiled_graph.get_graph().draw_mermaid_png()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(png)