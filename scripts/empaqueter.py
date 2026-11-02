from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
output = root / 'dist' / 'MDM-hopital-projet-scolaire.zip'
output.parent.mkdir(exist_ok=True)
excluded = {'.git', '.venv', '__pycache__', '.ipynb_checkpoints', 'dist', 'tmp', 'workspace'}
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if not path.is_file() or any(part in excluded or part.startswith('workspace_') for part in relative.parts):
            continue
        if path.suffix in {'.pyc', '.sqlite3', '.log'}:
            continue
        archive.write(path, Path('MDM---hopital') / relative)
print(f'{output} ({output.stat().st_size / 1024 / 1024:.2f} Mo)')
