from click import group


@group(no_args_is_help=True)
def cli():
    pass


@cli.command(name="list")
def list_checks():
    """
    List available checks
    """

    print("Okay")
