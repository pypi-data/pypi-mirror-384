import typer 

bigeye_conf: str = typer.Option(
            None
            , "--bigeye_conf"
            , "-b"
            , help="Bigeye Credential File Path"
            , envvar='BIGEYE_API_CRED_FILE')

config_file: str = typer.Option(
            None
            , "--config_file"
            , "-c"
            , help="Bigeye CLI Configuration File Path"
            , envvar='BIGEYE_API_CONFIG_FILE')

workspace: str = typer.Option(
            'DEFAULT'
            , "--workspace"
            , "-w"
            , help="Name of the workspace configuration."
            , envvar='BIGEYE_WORKSPACE')