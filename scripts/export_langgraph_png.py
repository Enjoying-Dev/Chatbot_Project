from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.Agent.chat import chat_service
from src.Agent.graph.export_diagram import write_compiled_graph_png

def main() -> None:
    out = ROOT / "assets" / "langgraph_status.png"
    try:
        write_compiled_graph_png(chat_service.graph, out)
    except Exception as exc:
        mmd = ROOT / "assets" / "langgraph_status.mmd"
        mmd.parent.mkdir(parents=True, exist_ok=True)
        mmd.write_text(chat_service.graph.get_graph().draw_mermaid(), encoding="utf-8")
        print(f"PNG render failed ({exc!r}).", file=sys.stderr)
        print(f"Wrote Mermaid source to {mmd}", file=sys.stderr)
        print("Open https://mermaid.live, paste the file, Export as PNG.", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"Wrote {out} ({out.stat().st_size} bytes)")

if __name__ == "__main__":
    main()