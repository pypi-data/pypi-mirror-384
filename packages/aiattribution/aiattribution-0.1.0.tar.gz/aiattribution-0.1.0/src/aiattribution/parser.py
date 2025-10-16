from typing import List

from .models import AIAttribution, Contribution, Initiative, Proportion, Review


class ParserError(Exception):
    """Exception raised for parsing errors."""

    pass


def parse_statement(statement: str) -> AIAttribution:
    """Parse an AI Attribution statement string into an AIAttribution object.

    Args:
        statement: The AI Attribution statement string (e.g., "AIA PAI Ce Hin R Haiku 4.5 v1.0")

    Returns:
        AIAttribution object

    Raises:
        ParserError: If the statement is invalid
    """
    parts = statement.strip().split()

    if not parts:
        raise ParserError("Empty statement")

    if parts[0] != "AIA":
        raise ParserError("Statement must start with 'AIA'")

    # Extract and validate version
    version_str = parts[-1]
    if version_str.startswith("v"):
        if version_str != "v1.0":
            raise ParserError(f"Unsupported statement version; only v1.0 is supported.")
        else:
            version = version_str[1:]  # Remove "v" prefix
            parts = parts[:-1]
    else:
        raise ParserError(f"Missing statement version")

    parts = parts[1:]  # Remove "AIA"

    if not parts:
        raise ParserError(
            "Statement must contain at least Proportion, Initiative, and Review components"
        )

    # Parse Proportion
    proportion_abbr = parts[0]
    proportion = None
    for p in Proportion:
        if p.abbr == proportion_abbr:
            proportion = p
            break

    if proportion is None:
        raise ParserError(f"Invalid Proportion component: {proportion_abbr}")

    parts = parts[1:]

    # Parse Contributions (optional)
    contributions: List[Contribution] = []
    contribution_abbrs = {c.abbr for c in Contribution}

    while parts and parts[0] in contribution_abbrs:
        contrib_abbr = parts[0]
        for c in Contribution:
            if c.abbr == contrib_abbr:
                contributions.append(c)
                break
        parts = parts[1:]

    # Parse Initiatives (required, can be one or both)
    initiatives: List[Initiative] = []
    initiative_abbrs = {i.abbr for i in Initiative}

    while parts and parts[0] in initiative_abbrs:
        init_abbr = parts[0]
        for i in Initiative:
            if i.abbr == init_abbr:
                initiatives.append(i)
                break
        parts = parts[1:]

    if not initiatives:
        raise ParserError("Statement must contain at least one Initiative component")

    # Parse Review (required)
    if not parts:
        raise ParserError("Statement must contain a Review component")

    review_abbr = parts[0]
    review = None
    for r in Review:
        if r.abbr == review_abbr:
            review = r
            break

    if review is None:
        raise ParserError(f"Invalid Review component: {review_abbr}")

    parts = parts[1:]

    # Remaining parts are the model name
    model = None
    if parts:
        model = " ".join(parts)

    attribution = AIAttribution(
        proportion=proportion,
        contributions=contributions if contributions else None,
        initiative=initiatives,
        review=review,
        model=model,
        version=version,
    )

    try:
        attribution.validate()
    except ValueError as e:
        raise ParserError(str(e))

    return attribution
