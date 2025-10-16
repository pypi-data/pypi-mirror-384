import typer
from typing_extensions import Annotated
import curcuma

app = typer.Typer()


@app.command()
def costs(
    config: Annotated[str, typer.Argument(help="Name of the curcuma config file")] = "ech.yml",
    filter: Annotated[str, typer.Option(help="A substring of the deployment name")] = None,
):
    # curcuma.configure_logger()

    cld = curcuma.CloudClient.by_config(config)

    try:
        cld.billing_costs.list(filter=filter)
    except curcuma.CurcumaException as e:
        print(f"Error: {e}")


# @app.command()
# def deployment(
#     config: Annotated[str, typer.Argument(help="Name of the curcuma config file")],
# ):
#     # curcuma.configure_logger()


@app.command()
def snapshots(
    name: Annotated[str, typer.Argument(help="Name of the deployment")],
    env: Annotated[str, typer.Option(help="Name of the environment")] = None,
):
    clt = curcuma.AzureClient.by_config("deployment.yml", {"name": name, "env": env})
    clt.es.snapshot.list()


@app.command()
def billing(
    config: Annotated[str, typer.Argument(help="Name of the curcuma config file")] = "ech.yml",
    filter: Annotated[str, typer.Option(help="A substring of the deployment name")] = None,
    country: Annotated[
        str, typer.Option(help="Country specific formating. Allowed are: 'de' and 'fr'. Default to 'en'")
    ] = "en",
):

    try:
        cld = curcuma.CloudClient.by_config(config)
        cld.billing_costs.list(filter=filter, country=country)
    except Exception as e:
        print(f"{e.__class__.__name__}: {e}")


if __name__ == "__main__":
    # from curcuma.cli import app

    app()
