# AI Attribution

A Python utility for creating and interpreting AI Attribution statements, providing a standardized way to
communicate the level and nature of AI involvement in creative and professional work.

## About

This tool is based on the research published by IBM Research at
[https://aiattribution.github.io/](https://aiattribution.github.io/). AI Attribution statements provide transparency
about how AI tools were used in creating content, making it easier for readers, reviewers, and collaborators to
understand the role of AI in the creative process.

## What is an AI Attribution Statement?

AI Attribution statements consist of several components that describe:

- **Proportion of AI use**: How much of the work was AI-generated vs. human-created
- **AI contributions**: What types of contributions AI made (stylistic edits, content edits, new content)
- **Initiative**: Whether AI assistance was prompted by humans or proactively offered by AI
- **Human review**: Whether AI-generated content was reviewed and approved
- **Model information**: Which AI model or application was used

### Example

```
AIA PAI Ce Hin R Gemini 2.5 Pro v1.0
```

This translates to:

> This work was primarily AI-generated. AI was used to make content edits, such as changes to scope, information,
> and ideas. AI was prompted for its contributions, or AI assistance was enabled. AI-generated content was reviewed
> and approved. The following model(s) or application(s) were used: Gemini 2.5 Pro.

## Installation

```bash
uv tool install aiattribution
```

## Usage

```bash
# Create an AI Attribution statement
uv run aia create
```
```bash
# Understand an existing AI Attribution statement
uv run aia interpret "AIA PAI Ce Hin R Gemini 2.5 Pro v1.0"
```
