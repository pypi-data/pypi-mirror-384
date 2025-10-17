import os
from click import group, option, argument
from pathlib import Path
from debby.collector import Collector
from debby.artifacts import Manifest
from debby.runner import Runner



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


# TODO: currently the `model_path` arg is present just because pre-commit will pass
# a list of filenames when it runs. But we don't actually do anything with those model
# paths. We should eventually use them to filter the models that are checked. But there's
# two reasons this gets tricky:
# 1. What if the path is from a dbt project in a subdirectory? In that case the model path
#    will not align with the changed file path passed by pre-commit. So identifying which
#    model has actually changed is not directly straightforward.
# 2. What if we want to check multiple types of resources? Ie, how should we identify when
#    something like a macro has changed, to only test that resource?
@cli.command(name="run")
@option('--artifacts-path', default=Path(os.getcwd()) / 'target', type=Path, help="Path to a compiled dbt project's `target` directory.")
@argument('model-path', nargs=-1, type=Path)
def run_checks(artifacts_path: Path, model_path: list[Path]):
    """
    Run checks against a dbt project.
    """

    manifest = Manifest.from_path(artifacts_path / 'manifest.json')
    collector = Collector()
    runner = Runner(collector=collector, manifest=manifest)
    for _ in runner.run():
        pass
