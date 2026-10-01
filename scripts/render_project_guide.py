"""Use Word for conversion when bundled LibreOffice is unavailable on Windows.

Keep the documents skill's canonical rasterization path for visual QA.
"""
import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path(r'C:\Users\sivaa\.codex\plugins\cache\openai-primary-runtime\documents\26.909.12148\skills\documents')
PWSH = Path(r'C:\Users\sivaa\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
temp_root = ROOT / 'tmp' / 'guide-render-temp'
temp_root.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(temp_root)
spec = importlib.util.spec_from_file_location('canonical_docx_renderer', SKILL / 'render_docx.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def word_conversion(doc_path, user_profile, convert_tmp_dir, stem, verbose=False):
    pdf = Path(convert_tmp_dir) / (stem + '.pdf')
    command = [str(PWSH), '-NoProfile', '-File', str(ROOT / 'scripts/export_guide_with_word.ps1'),
               '-InputDocx', str(Path(doc_path).resolve()), '-OutputPdf', str(pdf.resolve())]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    print(result.stdout.strip())
    return str(pdf), result.stdout + result.stderr


renderer.convert_to_pdf = word_conversion
pages = renderer.rasterize(str(ROOT / 'docs/Understanding_the_EnbPI_Project.docx'),
                           str(ROOT / 'tmp/guide-qa'), 120, verbose=True, emit_pdf=True)
print('Created', len(pages), 'page images using Word export and render_docx.py rasterization')
