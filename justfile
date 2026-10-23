set shell := ["bash", "-cu"]

frontend := "frontend"

default:
    @just --list

setup:
    pnpm -C {{frontend}} install

dev:
    pnpm -C {{frontend}} dev

build:
    pnpm -C {{frontend}} build

test:
    pnpm -C {{frontend}} test

backend-test:
    uv run --directory backend pytest

backend-run:
    uv run --directory backend python -m chaours

check: test build

clean:
    rm -rf {{frontend}}/dist {{frontend}}/node_modules
