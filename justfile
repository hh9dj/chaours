set shell := ["bash", "-cu"]

frontend := "frontend"

default:
    @just --list

setup:
    pnpm -C {{ frontend }} install

backend-setup:
    uv sync --directory backend

dev:
    pnpm -C {{ frontend }} dev

build:
    pnpm -C {{ frontend }} build

test:
    pnpm -C {{ frontend }} test

backend-test:
    uv run --directory backend pytest

backend-typecheck:
    uv run --directory backend mypy

backend-check: backend-test backend-typecheck

backend-run:
    uv run --directory backend python cli.py

backend-api:
    uv run --directory backend uvicorn api.app:app --reload

manim-check:
    uv run --directory backend python ../animation/check_example.py

manim-preview:
    manim -ql --media_dir animation/media animation/pipeline.py PipelineScene

manim-render:
    manim -qh --media_dir animation/media --output_file chaours-pipeline animation/pipeline.py PipelineScene
    mkdir -p animation/out
    cp animation/media/videos/pipeline/1080p60/chaours-pipeline.mp4 animation/out/

check: test build backend-check

clean:
    rm -rf {{ frontend }}/dist {{ frontend }}/node_modules
