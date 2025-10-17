"""Command-line interface."""

import click


@click.command()
@click.version_option()
def main() -> None:
    """SSB GCP Identity Client."""


if __name__ == "__main__":
    main(prog_name="ssb-gcp-identity-client")  # pragma: no cover
