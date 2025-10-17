import typer

from .commands.agent import app as agent_app
from .commands.auth import app as auth_app
from .commands.user import app as user_app

app = typer.Typer(
    help="Prim Voices CLI to interact with the Prim Voices API.",
    add_completion=True,
)
app.add_typer(auth_app, help="Authentication commands.")
app.add_typer(user_app, help="User commands.")
app.add_typer(agent_app, help="Manage agents, their functions, and environments.")

if __name__ == "__main__":
    app()
