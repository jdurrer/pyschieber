# Issue tracker

This repo tracks work in GitHub Issues. The project uses the `gh` CLI for issue operations, and the hub is the GitHub repository configured in `git remote -v`.

## How to use it

- Create an issue: `gh issue create --title "..." --body "..."`
- View an issue: `gh issue view <number> --comments`
- List open issues: `gh issue list --state open`
- Comment on an issue: `gh issue comment <number> --body "..."`
- Add or remove labels: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- Close an issue: `gh issue close <number> --comment "..."`

## PRs as a triage surface

**PRs as a request surface: no.** This repo does not treat external pull requests as a first-class request channel for the engineering skills.

## Guidance for the engineering skills

When a skill says to "publish to the issue tracker", create a GitHub issue in this repository. When a skill says to "fetch the relevant ticket", use `gh issue view <number> --comments`.

## Related context

- `git remote -v` points at `https://github.com/jdurrer/pyschieber`
- The triage label mapping is stored in `docs/agents/triage-labels.md`
- The domain documentation conventions are stored in `docs/agents/domain.md`
