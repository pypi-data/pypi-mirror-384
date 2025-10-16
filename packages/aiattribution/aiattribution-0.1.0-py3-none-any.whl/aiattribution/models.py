from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class AIAttributionComponent(Enum):
    def __init__(self, abbr: str, display_name: str, explanation: str):
        self.abbr = abbr
        self.display_name = display_name
        self.explanation = explanation

    def __str__(self):
        return f"{self.display_name} ({self.abbr}) - {self.explanation}"


class Proportion(AIAttributionComponent):
    """Proportion of AI use in the work."""

    ENTIRELY_AI = ("EAI", "Entirely AI", "The work was entirely AI-generated.")
    PRIMARILY_AI = ("PAI", "Primarily AI", "The work was primarily AI-generated.")
    HUMAN_AI_BLEND = (
        "HAb",
        "Human-AI Blend",
        "The work was created with an even blend of human and AI contributions.",
    )
    PRIMARILY_HUMAN = ("Ph", "Primarily Human", "The work was primarily human-created.")
    ENTIRELY_HUMAN = (
        "Eh",
        "Entirely Human",
        "This work was entirely human-created, without the use of AI.",
    )


class Contribution(AIAttributionComponent):
    """Types of AI contributions."""

    STYLISTIC_EDITS = (
        "Se",
        "Stylistic Edits",
        "AI was used to make stylistic edits, such as changes to structure, wording, and clarity.",
    )
    CONTENT_EDITS = (
        "Ce",
        "Content Edits",
        "AI was used to make content edits, such as changes to scope, information, and ideas.",
    )
    NEW_CONTENT = (
        "Nc",
        "New Content",
        "AI was used to make new content, such as text, images, analysis, and ideas.",
    )


class Initiative(AIAttributionComponent):
    """Who initiated the AI contributions."""

    HUMAN_INITIATED = (
        "Hin",
        "Human-Initiated",
        "AI was prompted for its contributions, or AI assistance was enabled.",
    )
    AI_INITIATED = (
        "Ain",
        "AI-Initiated",
        "The AI made proactive contributions, such as via auto-completion or unprompted changes.",
    )


class Review(AIAttributionComponent):
    """Whether AI-generated content was reviewed."""

    REVIEWED = ("R", "Reviewed", "AI-generated content was reviewed and approved.")
    NO_REVIEW = ("Nr", "No Review", "AI-generated content was not reviewed.")


@dataclass
class AIAttribution:
    """AI Attribution statement."""

    proportion: Proportion
    initiative: List[Initiative]
    review: Review
    contributions: Optional[List[Contribution]] = None
    model: Optional[str] = None
    version: str = "1.0"

    def validate(self) -> None:
        """Validate the attribution statement."""
        # Contributions can only be specified for PAI, HAb, or Ph
        if self.contributions:
            if self.proportion in [Proportion.ENTIRELY_AI, Proportion.ENTIRELY_HUMAN]:
                raise ValueError(
                    f"Contributions cannot be specified for {self.proportion.abbr}. "
                    "They are only valid for PAI, HAb, or Ph."
                )

        # Initiative must have at least one value
        if not self.initiative:
            raise ValueError("At least one initiative must be specified.")

        # Initiative cannot have duplicates
        if len(self.initiative) != len(set(self.initiative)):
            raise ValueError("Initiative cannot contain duplicates.")

        # Contributions cannot have duplicates
        if self.contributions and len(self.contributions) != len(set(self.contributions)):
            raise ValueError("Contributions cannot contain duplicates.")

    def to_statement(self) -> str:
        """Convert to AI Attribution statement string."""
        self.validate()

        parts = ["AIA", self.proportion.abbr]

        if self.contributions:
            parts.extend([c.abbr for c in self.contributions])

        parts.extend([i.abbr for i in self.initiative])
        parts.append(self.review.abbr)

        if self.model:
            parts.append(self.model)

        parts.append(f"v{self.version}")

        return " ".join(parts)

    def to_explanation(self) -> str:
        """Convert to human-readable explanation."""
        self.validate()

        lines = [self.proportion.explanation]

        if self.contributions:
            for contribution in self.contributions:
                lines.append(contribution.explanation)

        for initiative in self.initiative:
            lines.append(initiative.explanation)

        lines.append(self.review.explanation)

        if self.model:
            lines.append(f"The following model(s) or application(s) were used: {self.model}.")

        return " ".join(lines)
