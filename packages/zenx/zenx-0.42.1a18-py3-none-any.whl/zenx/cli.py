from typing import Annotated, List
import pathlib
import typer

from zenx.discovery import discover_local_module, load_spider_from_file
from zenx.engine import Engine
from zenx.monitors import Monitor
from zenx.pipelines import Pipeline
from zenx.spiders import Spider

BUILTIN_PIPELINES = [
    "preprocess",
    "synoptic_websocket",
    "synoptic_free_websocket",
    "synoptic_grpc",
    "synoptic_grpc_useast1",
    "synoptic_grpc_eucentral1",
    "synoptic_grpc_euwest2",
    "synoptic_grpc_useast1chi2a",
    "synoptic_grpc_useast1nyc2a",
    "synoptic_grpc_apnortheast1",
    "synoptic_discord",
]

app = typer.Typer()


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    if ctx.invoked_subcommand != "runspider":
        discover_local_module("spiders")
        discover_local_module("pipelines")


@app.command(name="list")
def list_all():
    spiders_available = Spider.spider_list()
    typer.secho("Available spiders:", fg=typer.colors.GREEN, bold=True)
    for spider in spiders_available:
        typer.echo(f"- {spider}")
    
    custom_pipelines = {
        name
        for name, cls in Pipeline._registry.items()
        if not cls.__module__.startswith("zenx.pipelines")
    }
    # The remaining registered pipelines are the active built-in ones.
    builtin_pipelines_active = sorted(
        list(set(Pipeline._registry.keys()) - custom_pipelines)
    )
    typer.secho("Built-in pipelines:", fg=typer.colors.GREEN, bold=True)
    if builtin_pipelines_active:
        for pipeline in builtin_pipelines_active:
            typer.echo(f"- {pipeline}")
    else:
        typer.echo(" (No built-in pipelines are active)")
    if custom_pipelines:
        typer.secho("Custom pipelines:", fg=typer.colors.GREEN, bold=True)
        for pipeline in sorted(list(custom_pipelines)):
            typer.echo(f"- {pipeline}")

    builtin_monitors = list(Monitor._registry.keys())
    typer.secho("Built-in monitors:", fg=typer.colors.GREEN, bold=True)
    for monitor in builtin_monitors:
        typer.echo(f"- {monitor}")

@app.command()
def crawl(
    spiders: List[str],
    forever: Annotated[bool, typer.Option(help="Run spiders continuously")] = False,
    exclude: Annotated[
        List[str], typer.Option("--exclude", help="Spiders to exclude.")
    ] = None,
    spider_arg: Annotated[
        List[str], typer.Option("--spider-arg", "-a", help="Argument to pass to the spiders.")
    ] = [],
):
    spiders_available = Spider.spider_list()
    engine = Engine(forever=forever)
    if not spiders_available:
        typer.secho("❌ No spiders found to run.", fg=typer.colors.RED)
        raise typer.Exit()

    spider_kwargs = {arg.split("=")[0]: arg.split("=")[1] for arg in spider_arg} if spider_arg else {}
    if len(spiders) > 1:
        for spider in spiders:
            if spider not in spiders_available:
                typer.secho(
                    f"❌ Spider '{spider}' not found. Check available spiders with the 'list' command.",
                    fg=typer.colors.RED,
                )
                raise typer.Exit()
        typer.secho(f"🚀 Starting spiders: {', '.join(spiders)}", fg=typer.colors.CYAN)
        engine.run_spiders(spiders, spider_kwargs)

    elif spiders[0] == "all":
        spiders_to_run = spiders_available
        if exclude:
            spiders_to_run = [s for s in spiders_available if s not in exclude]

        typer.secho(
            f"🚀 Starting spiders: {', '.join(spiders_to_run)}", fg=typer.colors.CYAN
        )
        engine.run_spiders(spiders_to_run, spider_kwargs)

    else:
        spider = spiders[0]
        if spider not in spiders_available:
            typer.secho(f"❌ Spider '{spider}' not found. Check available spiders with the 'list' command.", fg=typer.colors.RED)
            raise typer.Exit()
        typer.secho(f"🚀 Starting spider: {spider}", fg=typer.colors.CYAN)
        engine.run_spider(spider, spider_kwargs)


@app.command()
def runspider(
    spider_file: pathlib.Path,
    forever: Annotated[bool, typer.Option(help="Run spiders continuously")] = False,
    spider_arg: Annotated[
        List[str], typer.Option("--spider-arg", "-a", help="Argument to pass to the spider.")
    ] = [],
):
    if not spider_file.exists():
        typer.secho(f"❌ File '{spider_file}' not found.", fg=typer.colors.RED)
        raise typer.Exit()

    try:
        spider_name = load_spider_from_file(spider_file)
    except ImportError as e:
        typer.secho(f"❌ Error loading spider: {e}", fg=typer.colors.RED)
        raise typer.Exit()

    spider_kwargs = {arg.split("=")[0]: arg.split("=")[1] for arg in spider_arg} if spider_arg else {}
    engine = Engine(forever=forever)
    typer.secho(f"🚀 Starting spider: {spider_name} from {spider_file}", fg=typer.colors.CYAN)
    engine.run_spider(spider_name, spider_kwargs)


@app.command()
def startproject(project_name: str):
    # e.g project_root/
    # /project_root/{project_name}
    project_path = pathlib.Path(project_name)
    # /project_root/{project_name}/spiders
    spiders_path = project_path / "spiders"
    # /project_root/zenx.toml
    config_path = project_path.parent / "zenx.toml"

    if project_path.exists():
        typer.secho(f"❌ Project '{project_name}' already exists in this directory.", fg=typer.colors.RED)
        raise typer.Exit()
    try:
        spiders_path.mkdir(parents=True, exist_ok=True)
        (spiders_path / "__init__.py").touch()
        config_path.write_text(f'project = "{project_name}"\n')

        typer.secho(f"✅ Project '{project_name}' created successfully.", fg=typer.colors.GREEN)
    except OSError as e:
        typer.secho(f"❌ Error creating project: {e}", fg=typer.colors.RED)
        raise typer.Exit()


@app.command()
def mitm():
    import uvloop
    from zenx import mitm
    typer.secho("🚀 Starting mitm...", fg=typer.colors.CYAN)
    uvloop.run(mitm.run())
