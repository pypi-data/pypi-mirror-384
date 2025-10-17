# Data Journalist

a cli/sdk cli tool for managing datsets.

## Build Desktop
```
poetry run  pyinstaller --clean --name="DataJournalistDesktop" --windowed --add-data="assets:assets" src/desktop/main.py --paths="src"
```