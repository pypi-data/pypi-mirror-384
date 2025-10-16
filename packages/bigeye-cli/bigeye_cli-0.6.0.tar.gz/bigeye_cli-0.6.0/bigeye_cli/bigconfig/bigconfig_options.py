import typer
from typing import List, Optional

input_path: Optional[List[str]] = typer.Option(
    None
    , "--input_path"
    , "-ip"
    , help="List of paths containing Bigconfig files or pointing to a Bigconfig file. E.g. -ip path1 -ip path2."
           " If no input path is defined then current working directory will be used."
)
output_path: str = typer.Option(
    None
    , "--output_path"
    , "-op"
    , help="Output path where reports and fixme files will be saved. If no output path is defined "
           "then current working directory will be used."
)
purge_source_names: Optional[List[str]] = typer.Option(
    None
    , "--purge_source_name"
    , "-psn"
    , help="List of source names to purge  E.g. -psn source_1 -psn source_2."
)
purge_all_sources: bool = typer.Option(
    False
    , "--purge_all_sources"
    , "-purge_all"
    , help="Purge all sources: True or False."
)
no_queue: bool = typer.Option(
    False
    , "--no_queue"
    , "-nq"
    , help="Don't submit to queue: True or False. [DEPRECATED]"
)
recursive: bool = typer.Option(
    False
    , "--recursive"
    , "-r"
    , help="Search all input directories recursively."
)
strict_mode: bool = typer.Option(
    False
    , "--strict_mode"
    , "-strict"
    , help="API errors cause an exception if True. (Validation errors still cause an exception)"
)
auto_approve: bool = typer.Option(
    False
    , "--auto_approve"
    , "-auto_approve"
    , help="Explicit plan approval is not needed prior to execution."
)
namespace: Optional[str] = typer.Option(
    None
    , "--namespace"
    , "-n"
    , help="The namespace for the deployment. (This must match across all files or namespace should not be set in files)"
)
