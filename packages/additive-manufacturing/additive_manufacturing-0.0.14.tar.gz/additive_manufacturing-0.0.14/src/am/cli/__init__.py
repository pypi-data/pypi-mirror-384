from .__main__ import app
from .version import register_version

from am.mcp.cli import app as mcp_app
from am.part.cli import app as part_app
from am.process_map.cli import app as process_map_app
from am.schema.cli import app as schema_app
from am.segmenter.cli import app as segmenter_app
from am.solver.cli import app as solver_app

__all__ = ["app"]

app.add_typer(mcp_app, name="mcp")
app.add_typer(part_app, name="part")
app.add_typer(process_map_app, name="process-map")
app.add_typer(schema_app, name="schema")
app.add_typer(segmenter_app, name="segmenter")
app.add_typer(solver_app, name="solver")

_ = register_version(app)

if __name__ == "__main__":
    app()
