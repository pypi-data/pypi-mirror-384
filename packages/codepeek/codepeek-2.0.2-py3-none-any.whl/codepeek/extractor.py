import os
import time
import zipfile
import requests
import tempfile
import concurrent.futures
from pathlib import Path
from typing import Optional, Tuple
from io import StringIO

from .constants import CODE_EXTENSIONS, IGNORE_PATTERNS
from .utils import is_binary_file, get_file_size_mb


class RepoExtractor:
    def __init__(self, max_file_size_mb: float = 2.0):
        self.max_file_size_mb = max_file_size_mb
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RepoExtractor/2.0'
        })

    # ------------------------- Ignore / Branch Detection -------------------------

    def should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored (like .git, node_modules, etc.)"""
        path_str = str(path).lower()
        name = path.name.lower()

        for pattern in IGNORE_PATTERNS:
            if pattern in path_str or pattern in name:
                return True

        if name.startswith('.') and name not in {'.gitignore', '.env.example'}:
            return True

        return False

    def detect_default_branch(self, repo_url: str) -> str:
        """Detect the default branch of a GitHub repo (main / master / develop)"""
        if 'github.com' in repo_url:
            try:
                api_url = repo_url.replace('github.com', 'api.github.com/repos')
                response = self.session.get(api_url, timeout=5)
                if response.status_code == 200:
                    return response.json().get('default_branch', 'main')
            except Exception:
                pass

        for branch in ['main', 'master', 'develop']:
            try:
                zip_url = f"{repo_url}/archive/refs/heads/{branch}.zip"
                response = self.session.head(zip_url, timeout=3)
                if response.status_code == 200:
                    return branch
            except Exception:
                continue

        return 'main'

    # ------------------------- Download & Extract -------------------------

    def download_repo(self, repo_url: str, extract_to: str, branch: Optional[str] = None) -> Path:
        """Download GitHub repo as ZIP, extract and return path."""
        if repo_url.endswith('/'):
            repo_url = repo_url[:-1]

        if not branch:
            branch = self.detect_default_branch(repo_url)

        zip_url = f"{repo_url}/archive/refs/heads/{branch}.zip"

        try:
            response = self.session.get(zip_url, timeout=60, stream=True)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"❌ Download failed: {e}")

        zip_path = os.path.join(extract_to, "repo.zip")

        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

        os.remove(zip_path)

        extracted_folders = [f for f in Path(extract_to).iterdir() if f.is_dir()]
        return extracted_folders[0] if extracted_folders else Path(extract_to)

    # ------------------------- File Reading -------------------------

    def read_file_content(self, file_path: Path) -> Tuple[str, str]:
        """Read code file content with safety (ignore binaries and large files)."""
        file_size_mb = get_file_size_mb(file_path)

        if file_size_mb > self.max_file_size_mb:
            return "large", f"File too large: {file_size_mb:.1f}MB"

        if is_binary_file(file_path):
            return "binary", "Binary file"

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                if content.strip():
                    lines = []
                    for i, line in enumerate(content.splitlines(), 1):
                        lines.append(f'{i:4d}: {line}')
                    return "success", '\n'.join(lines)
                else:
                    return "empty", "Empty file"
        except Exception:
            return "error", "Read error"

    # ------------------------- Structure Extraction -------------------------

    def extract_structure(self, root_path: Path, output_file: Path):
        """Extract repository structure and save to file."""
        total_stats = {'processed': 0, 'skipped': 0, 'binary': 0, 'large': 0, 'total': 0}

        with open(output_file, 'w', encoding='utf-8', buffering=16384) as out:
            out.write(f"Repository: {root_path.name}\n")
            out.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            out.write("=" * 80 + "\n\n")

            file_tasks = []

            for folder_path, dirs, files in os.walk(root_path):
                current_path = Path(folder_path)

                if self.should_ignore(current_path):
                    dirs.clear()
                    continue

                dirs[:] = [d for d in dirs if not self.should_ignore(current_path / d)]
                dirs.sort()

                level = folder_path.replace(str(root_path), '').count(os.sep)
                indent = '  ' * level
                folder_name = os.path.basename(folder_path) or root_path.name
                out.write(f'{indent}{folder_name}/\n')

                subindent = '  ' * (level + 1)

                valid_files = []
                for file in sorted(files):
                    file_path = current_path / file
                    if not self.should_ignore(file_path):
                        valid_files.append(file_path)
                        total_stats['total'] += 1

                for file_path in valid_files:
                    file_size_mb = get_file_size_mb(file_path)
                    is_code = file_path.suffix.lower() in CODE_EXTENSIONS

                    out.write(f'{subindent}{file_path.name}')
                    if file_size_mb > 0.1:
                        out.write(f' ({file_size_mb:.1f}MB)')
                    out.write('\n')

                    if is_code:
                        file_tasks.append((file_path, subindent))

            if file_tasks:
                out.write('\n' + '=' * 80 + '\n')
                out.write('FILE CONTENTS\n')
                out.write('=' * 80 + '\n\n')

                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                    future_to_file = {
                        executor.submit(self.read_file_content, file_path): (file_path, subindent)
                        for file_path, subindent in file_tasks
                    }

                    file_results = {}
                    for future in concurrent.futures.as_completed(future_to_file):
                        file_path, subindent = future_to_file[future]
                        try:
                            status, content = future.result()
                            file_results[str(file_path)] = (status, content, subindent)
                        except Exception:
                            file_results[str(file_path)] = ('error', 'Processing error', subindent)

                    for file_path, subindent in file_tasks:
                        status, content, _ = file_results.get(str(file_path), ('error', 'Not processed', subindent))

                        out.write(f'{subindent}{"=" * 60}\n')
                        out.write(f'{subindent}File: {file_path.name}\n')
                        out.write(f'{subindent}{"=" * 60}\n')

                        if status == 'success':
                            for line in content.split('\n'):
                                out.write(f'{subindent}{line}\n')
                            total_stats['processed'] += 1
                        else:
                            out.write(f'{subindent}[{content}]\n')
                            if status == 'binary':
                                total_stats['binary'] += 1
                            elif status == 'large':
                                total_stats['large'] += 1
                            else:
                                total_stats['skipped'] += 1

                        out.write(f'{subindent}{"=" * 60}\n\n')

            out.write("=" * 80 + "\n")
            out.write("SUMMARY:\n")
            out.write(f"Total files: {total_stats['total']}\n")
            out.write(f"Code files processed: {total_stats['processed']}\n")
            out.write(f"Binary files: {total_stats['binary']}\n")
            out.write(f"Large files skipped: {total_stats['large']}\n")
            out.write(f"Other files skipped: {total_stats['skipped']}\n")

    # ------------------------- For AI Analysis -------------------------

    def extract_structure_for_analysis(self, root_path: Path) -> Tuple[str, str]:
        """Extract structure + content for AI model input."""
        structure_buffer = StringIO()
        content_buffer = StringIO()

        structure_buffer.write(f"{root_path.name}/\n")
        file_tasks = []

        for folder_path, dirs, files in os.walk(root_path):
            current_path = Path(folder_path)

            if self.should_ignore(current_path):
                dirs.clear()
                continue

            dirs[:] = [d for d in dirs if not self.should_ignore(current_path / d)]
            dirs.sort()

            level = folder_path.replace(str(root_path), '').count(os.sep)
            indent = '  ' * level
            folder_name = os.path.basename(folder_path) or root_path.name
            structure_buffer.write(f'{indent}{folder_name}/\n')

            subindent = '  ' * (level + 1)

            for file in sorted(files):
                file_path = current_path / file
                if not self.should_ignore(file_path):
                    structure_buffer.write(f'{subindent}{file}\n')
                    if file_path.suffix.lower() in CODE_EXTENSIONS:
                        file_tasks.append(file_path)

        if file_tasks:
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                future_to_file = {executor.submit(self.read_file_content, f): f for f in file_tasks}
                for future in concurrent.futures.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    status, content = future.result()
                    if status == 'success':
                        content_buffer.write(f"\n\n# FILE: {file_path.relative_to(root_path)}\n")
                        content_buffer.write(content[:4000])
                        content_buffer.write("\n")

        structure_str = structure_buffer.getvalue()
        content_str = content_buffer.getvalue()
        structure_buffer.close()
        content_buffer.close()
        return structure_str, content_str

    # ------------------------- Wrapper for CLI -------------------------

    def extract_repo(self, repo_url: str, output_file: str):
        """Wrapper for CLI: download + summarize GitHub repo."""
        print(f"⬇️ Starting extraction for {repo_url}...")
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = self.download_repo(repo_url, temp_dir)
            print(f"✅ Downloaded to: {repo_path}")
            self.extract_structure(Path(repo_path), Path(output_file))
            print(f"✅ Summary saved to {output_file}")
