#!/usr/bin/env bash 
set -euo pipefail

# STC 720 — Initial repository setup
# Run from the repository root.

cd "$(dirname "$0")"

echo "Creating research directories..."

mkdir -p \
    docs \
    literature/papers \
    src \
    notebooks \
    tests \
    data/raw \
    data/processed \
    results/figures \
    results/tables \
    report

echo "Creating .gitignore..."

cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.ipynb_checkpoints/

# Virtual environments
.venv/
venv/

# Environment variables and credentials
.env
.env.*
!.env.example
*.key
*credentials*.json

# Generated datasets
data/raw/*
data/processed/*
!data/raw/.gitkeep
!data/processed/.gitkeep

# Generated experimental outputs
results/figures/*
results/tables/*
!results/figures/.gitkeep
!results/tables/.gitkeep

# Temporary files
*.log
*.tmp
.DS_Store

# LaTeX build artifacts
*.aux
*.out
*.toc
*.synctex.gz
*.fdb_latexmk
*.fls
EOF

echo "Creating directory placeholders..."

touch \
    docs/.gitkeep \
    literature/papers/.gitkeep \
    src/.gitkeep \
    notebooks/.gitkeep \
    tests/.gitkeep \
    data/raw/.gitkeep \
    data/processed/.gitkeep \
    results/figures/.gitkeep \
    results/tables/.gitkeep \
    report/.gitkeep

echo "Repository structure created successfully."

echo
echo "Git status:"
git status --short