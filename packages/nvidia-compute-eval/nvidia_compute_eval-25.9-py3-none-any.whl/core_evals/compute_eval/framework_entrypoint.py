import warnings
from nemo_evaluator.api.run import run_eval


def main():
    warnings.warn(
        "This command is deprecated and will be removed in the next release. Please use the `eval-factory` command instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Add this `framework_entrypoint:main` as an entrypoint to `pyproject.toml`, example
    run_eval()