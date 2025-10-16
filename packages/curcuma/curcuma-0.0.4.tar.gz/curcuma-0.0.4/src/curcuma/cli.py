import typer
from typing_extensions import Annotated
import curcuma

app = typer.Typer()


@app.command()
def billing(filter: Annotated[str, typer.Option(help="A substring of the depoyment name")] = None):
    curcuma.configure_logger()

    cld = curcuma.CloudClient(
        api_key="essu_VDA1NU9IazFZMEpDTTNOVFlURm5jV1JIV1RjNk1qUmxlRVl4YW5wVE1rTm9RVUkzWVU5RmIxaHlkdz09AAAAANYE0DE=",
        organization_id="1263562222",
    )

    try:
        cld.billing_costs.list(filter=filter)
    except curcuma.CurcumaException as e:
        print(f"Error: {e}")


@app.command()
def hello(name: str):
    print(f"Hello {name}")


@app.command()
def goodbye(name: str, formal: bool = False):
    if formal:
        print(f"Goodbye Ms. {name}. Have a good day.")
    else:
        print(f"Bye {name}!")


if __name__ == "__main__":
    app()
