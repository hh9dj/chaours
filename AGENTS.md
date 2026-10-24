# Agent Guidelines

## Project

Project context and functional requirements are in the [spec](./spec/README.md) and the [README](./README.md).

## Stack

- Nix flake for the dev shell, activated with direnv through `.envrc`.
- TypeScript, Vue 3, and Tailwind CSS for the frontend.
- Python and FastAPI for the backend.
- SQLite for the database.
- Task automation with a justfile.

## Rules

- Frontend:
  - All text and content in French.
  - The interface targets desktop browsers.
  - Keep it simple and straightforward to use.

- When working inside a separate worktree, sync dependencies:
  - `uv sync --directory backend`
  - `pnpm --dir frontend install`
