set shell := ["bash", "-cu"]

frontend := "frontend"

default:
    @just --list

setup:
    pnpm -C {{frontend}} install

backend-setup:
    uv sync --directory backend

dev:
    pnpm -C {{frontend}} dev

build:
    pnpm -C {{frontend}} build

test:
    pnpm -C {{frontend}} test

backend-test:
    uv run --directory backend pytest

backend-typecheck:
    uv run --directory backend mypy

backend-check: backend-test backend-typecheck

backend-run:
    uv run --directory backend python -m chaours

backend-benchmark:
    uv run --directory backend python -m chaours --benchmark

check: test build backend-check

clean:
    rm -rf {{frontend}}/dist {{frontend}}/node_modules
