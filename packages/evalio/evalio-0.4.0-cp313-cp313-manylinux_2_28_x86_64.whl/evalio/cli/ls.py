from enum import StrEnum, auto
from typing import Annotated, Literal, Optional, TypeVar, TypedDict

import typer
from rapidfuzz.process import extract_iter
from rich import box
from rich.console import Console
from rich.table import Table

from evalio import datasets as ds, pipelines as pl

app = typer.Typer()

T = TypeVar("T")


def unique(lst: list[T]) -> list[T]:
    """Get unique elements from a list while preserving order

    Returns:
        List of unique elements
    """
    return list(dict.fromkeys(lst))


def extract_len(d: ds.Dataset) -> str:
    """Get the length of a dataset in a human readable format

    Args:
        d (Dataset): Dataset to get length of

    Returns:
        Length of dataset in minutes or '-' if length is unknown
    """
    length = d.quick_len()
    if length is None:
        return "[bright_black]-[/bright_black]"
    else:
        return f"{length / d.lidar_params().rate / 60:.1f}min".rjust(7)


class Kind(StrEnum):
    datasets = auto()
    pipelines = auto()


@app.command(no_args_is_help=True)
def ls(
    kind: Annotated[
        Kind, typer.Argument(help="The kind of object to list", show_default=False)
    ],
    search: Annotated[
        Optional[str],
        typer.Option(
            "--search",
            "-s",
            help="Fuzzy search for a pipeline or dataset by name",
            show_default=False,
        ),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Output less verbose information",
        ),
    ] = False,
    show_hyperlinks: Annotated[
        bool,
        typer.Option(
            "--show-hyperlinks",
            help="Output full links. For terminals that don't support hyperlinks (OSC 8).",
        ),
    ] = False,
    show: Annotated[
        bool,
        typer.Option(
            hidden=True,
        ),
    ] = True,
) -> Optional[Table]:
    """
    List dataset and pipeline information
    """
    ColOpts = TypedDict("ColOpts", {"vertical": Literal["top", "middle", "bottom"]})
    col_opts: ColOpts = {"vertical": "middle"}

    if kind == Kind.datasets:
        # Search for datasets using rapidfuzz
        # TODO: Make it search through sequences as well?
        all_datasets = list(ds.all_datasets().values())
        if search is not None:
            to_include = extract_iter(
                search, [d.dataset_name() for d in all_datasets], score_cutoff=90
            )
            to_include = [all_datasets[idx] for _name, _score, idx in to_include]
        else:
            to_include = all_datasets

        # For future self: To add a new column, the following needs to be done:
        # 1. Add the column to all_info
        # 2. Gather the info for that column in the for loop
        # 3. Add the column to the table
        # That should be about it, making the rest should be automatic

        # Gather all info
        all_info: dict[str, list[str]] = {
            "Name": [],
            "Sequences": [],
            "DL": [],
            "Size": [],
            "Len": [],
            "Env": [],
            "Vehicle": [],
            "IMU": [],
            "LiDAR": [],
            "Info": [],
        }
        for d in to_include:
            all_info["Name"].append(d.dataset_name())
            links_str = d.url()
            if not show_hyperlinks:
                links_str = f"[link={links_str}]link[/link]"
            all_info["Info"].append(links_str)

            size = [d(s).size_on_disk() for s in d.sequences()]
            env = [d(s).environment() for s in d.sequences()]
            vehicle = [d(s).vehicle() for s in d.sequences()]
            imu = [d(s).imu_params() for s in d.sequences()]
            imu = [f"{s.brand} {s.model}" for s in imu]
            lidar = [d(s).lidar_params() for s in d.sequences()]
            lidar = [f"{s.brand} {s.model}" for s in lidar]

            if quiet:
                all_info["Env"].append(" / ".join(unique(env)))
                all_info["Vehicle"].append(" / ".join(unique(vehicle)))
                all_info["IMU"].append(" / ".join(unique(imu)))
                all_info["LiDAR"].append(" / ".join(unique(lidar)))
                all_info["Size"].append(
                    f"{sum([s for s in size if s is not None]):.0f}G".rjust(4)
                )
            else:
                # sequences
                all_info["Sequences"].append("\n".join(d.sequences()))
                # downloaded
                downloaded = [d(s).is_downloaded() for s in d.sequences()]
                downloaded = "\n".join(
                    ["[green]✔[/green]" if d else "[red]-[/red]" for d in downloaded]
                )
                all_info["DL"].append(downloaded)
                # size
                size = "\n".join(
                    [
                        f"{s:.0f}G".rjust(4)
                        if s is not None
                        else "[bright_black]-[/bright_black]"
                        for s in size
                    ]
                )
                all_info["Size"].append(size)
                # length
                all_info["Len"].append(
                    "\n".join([extract_len(d(s)) for s in d.sequences()])
                )
                # misc info
                all_info["Env"].append("\n".join(env))
                all_info["Vehicle"].append("\n".join(vehicle))
                all_info["IMU"].append("\n".join(imu))
                all_info["LiDAR"].append("\n".join(lidar))

        if len(all_info["Name"]) == 0:
            print("No datasets found")
            return

        # Fill out table
        table = Table(
            title="Datasets",
            show_lines=not quiet,
            highlight=True,
            box=box.ROUNDED,
        )

        table.add_column("Name", justify="center", **col_opts)
        if not quiet:
            table.add_column("Sequences", justify="right", **col_opts)
            table.add_column("DL", justify="right", **col_opts)
        table.add_column("Size", justify="center", **col_opts)
        if not quiet:
            table.add_column("Len", justify="center", **col_opts)
        table.add_column("Env", justify="center", **col_opts)
        table.add_column("Vehicle", justify="center", **col_opts)
        table.add_column("IMU", justify="center", **col_opts)
        table.add_column("LiDAR", justify="center", **col_opts)
        table.add_column("Info", justify="center", **col_opts)

        for i in range(len(all_info["Name"])):
            row_info = [all_info[c.header][i] for c in table.columns]  # type: ignore
            table.add_row(*row_info)

        if show:
            Console().print(table)

        return table

    if kind == Kind.pipelines:
        # Search for pipelines using rapidfuzz
        # TODO: Make it search through parameters as well?
        all_pipelines = list(pl.all_pipelines().values())
        if search is not None:
            to_include = extract_iter(
                search, [d.name() for d in all_pipelines], score_cutoff=90
            )
            to_include = [all_pipelines[idx] for _name, _score, idx in to_include]
        else:
            to_include = all_pipelines

        # For future self: To add a new column, the following needs to be done:
        # 1. Add the column to all_info
        # 2. Gather the info for that column in the for loop
        # 3. Add the column to the table
        # That should be about it, making the rest should be automatic

        # Gather all info
        all_info = {
            "Name": [],
            "Params": [],
            "Default": [],
            "Info": [],
            "Version": [],
        }
        for p in to_include:
            all_info["Name"].append(p.name())
            links_str = p.url()
            if not show_hyperlinks:
                links_str = f"[link={links_str}]link[/link]"
            all_info["Info"].append(links_str)
            all_info["Version"].append(p.version())

            if not quiet:
                params = p.default_params()
                keys = "\n".join(params.keys())
                values = "\n".join([str(v) for v in params.values()])
                all_info["Params"].append(keys)
                all_info["Default"].append(values)

        if len(all_info["Name"]) == 0:
            print("No pipelines found")
            return

        # Fill out table
        table = Table(
            title="Pipelines",
            show_lines=not quiet,
            highlight=True,
            box=box.ROUNDED,
        )

        table.add_column("Name", justify="center", **col_opts)
        table.add_column("Version", justify="center", **col_opts)
        if not quiet:
            table.add_column("Params", justify="right", **col_opts)
            table.add_column("Default", justify="left", **col_opts)
        table.add_column("Info", justify="center", **col_opts)

        for i in range(len(all_info["Name"])):
            row_info = [all_info[c.header][i] for c in table.columns]  # type: ignore
            table.add_row(*row_info)

        if show:
            Console().print(table)

        return table
