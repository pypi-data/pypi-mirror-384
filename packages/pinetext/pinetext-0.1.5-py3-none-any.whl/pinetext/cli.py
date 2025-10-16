import typer

from pinetext.client import PineText


app = typer.Typer(
    name="PineText",
    help="PineText CLI",
)


@app.command()
def run():
    client = PineText()
    client.run()
