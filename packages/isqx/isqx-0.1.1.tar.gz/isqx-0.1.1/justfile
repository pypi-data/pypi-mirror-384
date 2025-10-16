check:
    uv run --python 3.9 ruff check src tests
    uv run --python 3.9 ruff format --check src tests
    uv run --python 3.9 mypy src tests
    # mkdocs doesn't detect wikipedia links that end with `)`
    rg -i '[^<]https://en.wikipedia.org/wiki/.*\(.*\)[^>#]' -g '!scripts/' --no-heading

check-katex:
    rg -i '_\{([A-Za-z_ ,]+)\}' src/isqx/details --no-heading
    rg -i '\"\w_([A-Za-z_ ,]+)\w*\"' src/isqx/details --no-heading

fix:
    uv run --python 3.9 ruff check --fix src tests
    uv run --python 3.9 ruff format src tests
    cd src/isqx_vis && pnpm run fmt

preview:
    uv run mkdocs build && npx http-server site -p 8080 -c-1 --brotli --gzip
