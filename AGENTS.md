# Agent Guidelines

## Project

CHAOURS (Nuclear Planing) is an interactive decision-support simulator for scheduling nuclear unit outages. Read the [spec](./spec/README.md) for context, concepts, and business rules, the [backend spec](./backend/spec.md) for the backend architecture and roadmap, the [frontend spec](./frontend/spec.md) for the frontend architecture and roadmap, and the [README](./README.md) for an overview.

## Stack

- Nix flake for the dev shell, activated by direnv through `.envrc`.
- Backend: Python 3.12, NumPy, uv, pytest, and mypy.
- Frontend: TypeScript, Vue 3, Vite, Tailwind CSS v4, Vitest, and pnpm.
- Backend additions: Pydantic v2, FastAPI, SQLModel, and SQLite.
- Task automation with a justfile.

## Rules

- Frontend:
  - Write all text and content in French.
  - Target desktop browsers.
  - Keep the interface simple and straightforward.
- Do not merge parallel worktree changes automatically. The user must review and challenge them with hunk, then give the signal to merge.
- When applying a change, give purpose + explanation of changes for each file modified in your last conversation message.
