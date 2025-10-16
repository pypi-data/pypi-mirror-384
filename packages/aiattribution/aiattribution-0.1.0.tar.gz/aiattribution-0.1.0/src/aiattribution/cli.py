import shutil
import sys
import textwrap
from typing import List, Optional

import click
import questionary

from .models import AIAttribution, Contribution, Initiative, Proportion, Review
from .parser import ParserError, parse_statement

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
}


def wrap_explanation(text: str) -> str:
    terminal_width = shutil.get_terminal_size((100, 20))[0]
    if terminal_width > 100:
        return textwrap.fill(text, width=100)
    return text


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """AI Attribution statement creation and interpretation tool."""
    pass


@cli.command()
def create():
    """Interactively create an AI Attribution statement."""
    click.secho("Create an AI Attribution Statement\n", bold=True)

    # Proportion
    proportion_choices = [questionary.Choice(title=str(p), value=p) for p in Proportion]
    proportion = questionary.select(
        "How much of this work was created or assisted by AI?",
        choices=proportion_choices,
    ).ask()

    if proportion is None:
        sys.exit(0)

    # Contributions (only for PAI, HAb, Ph)
    contributions: Optional[List[Contribution]] = None
    if proportion not in [Proportion.ENTIRELY_AI, Proportion.ENTIRELY_HUMAN]:
        contribution_choices = [questionary.Choice(title=str(c), value=c) for c in Contribution]
        contributions = questionary.checkbox(
            "Select AI contribution(s) (optional):", choices=contribution_choices
        ).ask()

        if contributions is None:
            sys.exit(0)

        if not contributions:
            contributions = None

    # Initiative
    initiative_choices = [questionary.Choice(title=str(i), value=i) for i in Initiative]
    initiatives = questionary.checkbox(
        "Who initiated AI contributions? (at least one required)",
        choices=initiative_choices,
        validate=lambda x: len(x) > 0 or "At least one initiative must be selected",
    ).ask()

    if initiatives is None:
        sys.exit(0)

    # Review
    review_choices = [questionary.Choice(title=str(r), value=r) for r in Review]
    review = questionary.select("Select human review status", choices=review_choices).ask()

    if review is None:
        sys.exit(0)

    # Model
    model = questionary.text("Model or application used (optional)", default="").ask()

    if model is None:
        sys.exit(0)

    model = model.strip() or None

    try:
        attribution = AIAttribution(
            proportion=proportion,
            contributions=contributions,
            initiative=initiatives,
            review=review,
            model=model,
        )

        click.secho("\nAI Attribution Statement", bold=True)
        click.echo(f"\n{attribution.to_statement()}\n")
        click.secho("Explanation", bold=True)
        click.echo(f"\n{wrap_explanation(attribution.to_explanation())}\n")

    except ValueError as e:
        click.echo(f"\nError creating attribution: {e}")
        sys.exit(1)


@cli.command()
@click.argument("statement", nargs=-1, required=True)
def interpret(statement):
    """Interpret an AI Attribution statement."""
    statement_str = " ".join(statement)

    try:
        attribution = parse_statement(statement_str)
        click.secho("AI Attribution Statement\n", bold=True)
        click.echo(statement_str)
        click.secho("\nExplanation", bold=True)
        click.echo(f"\n{wrap_explanation(attribution.to_explanation())}\n")

    except ParserError as e:
        click.secho("ERROR: failed to parse AI Attribution statement", fg="red", bold=True)
        click.echo(f"Detail: {e}")
        sys.exit(1)
