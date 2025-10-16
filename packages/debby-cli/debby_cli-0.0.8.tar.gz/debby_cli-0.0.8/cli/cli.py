from click import group
from cli.collector import Collector


@group(no_args_is_help=True)
def cli():
    pass


@cli.command(name="list")
def list_checks():
    """
    List available checks
    """

    collector = Collector()
    for check in collector.iter_checks():
        print(check.name)


@cli.command(name="run")
def run_checks():
    """
    Run checks against a dbt project
    """

    print("Okay")
