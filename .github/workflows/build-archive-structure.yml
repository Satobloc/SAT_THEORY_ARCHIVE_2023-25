name: Build Archive Structure

on:
  workflow_dispatch:
  push:
    paths:
      - 'build_archive_structure.py'
      - '.[🎛️_DASHBOARD]/⚒️_STRUCTURE_BUILD.txt'
      - '.github/workflows/build-archive-structure.yml'

permissions:
  contents: write

jobs:
  build-archive-structure:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Copy structure builder into AI files
        run: |
          mkdir -p '.[⚙️_AI_FILES]/TOOLS'
          cp 'build_archive_structure.py' '.[⚙️_AI_FILES]/TOOLS/build_archive_structure.py'

      - name: Build requested archive structure
        run: |
          python 'build_archive_structure.py' '.[🎛️_DASHBOARD]/⚒️_STRUCTURE_BUILD.txt' --apply

      - name: Commit generated structure
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add '.[🎛️_DASHBOARD]' '.[⚙️_AI_FILES]'
          if git diff --cached --quiet; then
            echo "No structure changes to commit."
          else
            git commit -m "Build SATopedia dashboard and AI files structure"
            git push
          fi
