#!/bin/bash

# Define color constants
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

set -e

step() {
    echo -e "${GREEN}---------- $1...${NC}"
}

fail() {
    echo -e "${RED}Error: $1 failed. Exiting.${NC}"
    exit 1
}

step "Formatting code with ruff"
uv run ruff format || fail "ruff format"
echo -e "\n"

step "Checking code with ruff"
uv run ruff check || fail "ruff check"
echo -e "\n"

step "Running type checks with pyright"
uv run pyright || fail "pyright"
echo -e "\n"

step "Running pytest"
uv run pytest -v || fail "pytest"
echo -e "\n"

echo -e "${GREEN}All required tools are installed and checks passed.${NC}"
