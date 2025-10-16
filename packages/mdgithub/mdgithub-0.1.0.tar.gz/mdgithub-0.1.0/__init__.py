#!/usr/bin/env python3
"""
Flatten a GitHub repo into a single static HTML page for fast skimming and Ctrl+F.
Professional enhanced version with academic-quality UI/UX.
Fixed: Markdown images with relative paths now display correctly.
"""

from __future__ import annotations
import argparse
import html
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from dataclasses import dataclass
from typing import List
from datetime import datetime
from urllib.parse import urljoin, urlparse

# External deps
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_for_filename, TextLexer
import markdown

MAX_DEFAULT_BYTES = 50 * 1024
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".ico",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".mp3", ".mp4", ".mov", ".avi", ".mkv", ".wav", ".ogg", ".flac",
    ".ttf", ".otf", ".eot", ".woff", ".woff2",
    ".so", ".dll", ".dylib", ".class", ".jar", ".exe", ".bin",
}
MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkd", ".mkdn"}

@dataclass
class RenderDecision:
    include: bool
    reason: str

@dataclass
class FileInfo:
    path: pathlib.Path
    rel: str
    size: int
    decision: RenderDecision


def run(cmd: List[str], cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True)


def git_clone(url: str, dst: str) -> None:
    run(["git", "clone", "--depth", "1", url, dst])


def git_head_commit(repo_dir: str) -> str:
    try:
        cp = run(["git", "rev-parse", "HEAD"], cwd=repo_dir)
        return cp.stdout.strip()
    except Exception:
        return "(unknown)"


def git_commit_date(repo_dir: str) -> str:
    try:
        cp = run(["git", "log", "-1", "--format=%ci"], cwd=repo_dir)
        return cp.stdout.strip()
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_github_raw_base_url(repo_url: str, commit: str) -> str:
    """
    Convert GitHub repo URL to raw content base URL.
    Example: https://github.com/user/repo -> https://raw.githubusercontent.com/user/repo/commit/
    """
    # Remove .git suffix if present
    repo_url = repo_url.rstrip('/').replace('.git', '')
    
    # Extract user and repo name
    parsed = urlparse(repo_url)
    path_parts = parsed.path.strip('/').split('/')
    
    if len(path_parts) >= 2:
        user, repo = path_parts[0], path_parts[1]
        return f"https://raw.githubusercontent.com/{user}/{repo}/{commit}/"
    
    return None


def fix_markdown_relative_paths(md_text: str, file_rel_path: str, base_url: str) -> str:
    """修复 Markdown 中的相对路径图片和链接"""
    file_dir = str(pathlib.Path(file_rel_path).parent)
    if file_dir == ".":
        file_dir = ""
    
    def replace_path(match):
        alt_or_text = match.group(1)
        path = match.group(2)
        title = match.group(3) if match.lastindex >= 3 else ""
        
        # 跳过绝对 URL
        if path.startswith(('http://', 'https://', '//', '#')):
            return match.group(0)
        
        # 解析相对路径
        if file_dir:
            full_path = str(pathlib.Path(file_dir) / path)
        else:
            full_path = path
        
        # 规范化路径
        full_path = str(pathlib.Path(full_path).as_posix())
        
        # 构建绝对 URL
        absolute_url = urljoin(base_url, full_path)
        
        # 返回修复后的 Markdown（保持原格式）
        if title:
            return f'![{alt_or_text}]({absolute_url} {title})'
        else:
            return f'![{alt_or_text}]({absolute_url})'
    
    # 修复 Markdown 图片语法: ![alt](path) 或 ![alt](path "title")
    md_text = re.sub(
        r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)',
        replace_path,
        md_text
    )
    
    # 同样处理链接（如果需要）
    # md_text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_path, md_text)
    
    return md_text


def bytes_human(n: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    f = float(n)
    i = 0
    while f >= 1024.0 and i < len(units) - 1:
        f /= 1024.0
        i += 1
    if i == 0:
        return f"{int(f)} {units[i]}"
    else:
        return f"{f:.1f} {units[i]}"


def looks_binary(path: pathlib.Path) -> bool:
    ext = path.suffix.lower()
    if ext in BINARY_EXTENSIONS:
        return True
    try:
        with path.open("rb") as f:
            chunk = f.read(8192)
        if b"\x00" in chunk:
            return True
        try:
            chunk.decode("utf-8")
        except UnicodeDecodeError:
            return True
        return False
    except Exception:
        return True


def decide_file(path: pathlib.Path, repo_root: pathlib.Path, max_bytes: int) -> FileInfo:
    rel = str(path.relative_to(repo_root)).replace(os.sep, "/")
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        size = 0
    if "/.git/" in f"/{rel}/" or rel.startswith(".git/"):
        return FileInfo(path, rel, size, RenderDecision(False, "ignored"))
    if size > max_bytes:
        return FileInfo(path, rel, size, RenderDecision(False, "too_large"))
    if looks_binary(path):
        return FileInfo(path, rel, size, RenderDecision(False, "binary"))
    return FileInfo(path, rel, size, RenderDecision(True, "ok"))


def collect_files(repo_root: pathlib.Path, max_bytes: int) -> List[FileInfo]:
    infos: List[FileInfo] = []
    for p in sorted(repo_root.rglob("*")):
        if p.is_symlink():
            continue
        if p.is_file():
            infos.append(decide_file(p, repo_root, max_bytes))
    return infos


def generate_tree_fallback(root: pathlib.Path) -> str:
    lines: List[str] = []

    def walk(dir_path: pathlib.Path, prefix: str = ""):
        entries = [e for e in dir_path.iterdir() if e.name != ".git"]
        entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
        for i, e in enumerate(entries):
            last = i == len(entries) - 1
            branch = "└── " if last else "├── "
            lines.append(prefix + branch + e.name)
            if e.is_dir():
                extension = "    " if last else "│   "
                walk(e, prefix + extension)

    lines.append(root.name)
    walk(root)
    return "\n".join(lines)


def try_tree_command(root: pathlib.Path) -> str:
    try:
        cp = run(["tree", "-a", "."], cwd=str(root))
        return cp.stdout
    except Exception:
        return generate_tree_fallback(root)


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def render_markdown_text(md_text: str, file_rel_path: str, base_url: str) -> str:
    """Render markdown with fixed relative paths"""
    # Fix relative paths first
    fixed_md = fix_markdown_relative_paths(md_text, file_rel_path, base_url)
    
    # Then render to HTML
    return markdown.markdown(fixed_md, extensions=["fenced_code", "tables", "toc", "nl2br"])


def highlight_code(text: str, filename: str, formatter: HtmlFormatter) -> str:
    try:
        lexer = get_lexer_for_filename(filename, stripall=False)
    except Exception:
        lexer = TextLexer(stripall=False)
    return highlight(text, lexer, formatter)


def slugify(path_str: str) -> str:
    out = []
    for ch in path_str:
        if ch.isalnum() or ch in {"-", "_"}:
            out.append(ch)
        else:
            out.append("-")
    return "".join(out)


def get_file_icon(filename: str) -> str:
    ext = pathlib.Path(filename).suffix.lower()
    icon_map = {
        '.py': '🐍', '.js': '📜', '.ts': '📘', '.jsx': '⚛️', '.tsx': '⚛️',
        '.html': '🌐', '.css': '🎨', '.scss': '🎨', '.sass': '🎨',
        '.json': '📋', '.xml': '📋', '.yaml': '📋', '.yml': '📋', '.toml': '⚙️',
        '.md': '📝', '.txt': '📄', '.pdf': '📕', '.rst': '📝',
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.svg': '🖼️',
        '.mp4': '🎬', '.mov': '🎬', '.avi': '🎬',
        '.mp3': '🎵', '.wav': '🎵', '.ogg': '🎵',
        '.zip': '📦', '.tar': '📦', '.gz': '📦', '.rar': '📦',
        '.sh': '⚙️', '.bash': '⚙️', '.zsh': '⚙️',
        '.c': '©️', '.cpp': '©️', '.h': '©️', '.hpp': '©️',
        '.java': '☕', '.class': '☕', '.jar': '☕',
        '.go': '🐹', '.rs': '🦀', '.rb': '💎', '.php': '🐘',
        '.sql': '🗄️', '.db': '🗄️', '.sqlite': '🗄️',
        '.docker': '🐳', '.dockerfile': '🐳',
        '.git': '🔧', '.gitignore': '🔧', '.gitattributes': '🔧',
        '.lock': '🔒', '.env': '🔐',
    }
    return icon_map.get(ext, '📄')


def get_language_label(filename: str) -> str:
    ext = pathlib.Path(filename).suffix.lower()
    lang_map = {
        '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
        '.jsx': 'React JSX', '.tsx': 'React TSX',
        '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS',
        '.json': 'JSON', '.xml': 'XML', '.yaml': 'YAML', '.yml': 'YAML', '.toml': 'TOML',
        '.md': 'Markdown', '.txt': 'Plain Text', '.rst': 'reStructuredText',
        '.sh': 'Shell', '.bash': 'Bash', '.zsh': 'Zsh',
        '.c': 'C', '.cpp': 'C++', '.h': 'C Header', '.hpp': 'C++ Header',
        '.java': 'Java', '.go': 'Go', '.rs': 'Rust', '.rb': 'Ruby', '.php': 'PHP',
        '.sql': 'SQL', '.dockerfile': 'Dockerfile',
    }
    return lang_map.get(ext, 'Code')


def generate_cxml_text(infos: List[FileInfo], repo_dir: pathlib.Path) -> str:
    lines = ["<documents>"]
    rendered = [i for i in infos if i.decision.include]
    for index, i in enumerate(rendered, 1):
        lines.append(f'<document index="{index}">')
        lines.append(f"<source>{i.rel}</source>")
        lines.append("<document_content>")
        try:
            text = read_text(i.path)
            lines.append(text)
        except Exception as e:
            lines.append(f"Failed to read: {str(e)}")
        lines.append("</document_content>")
        lines.append("</document>")
    lines.append("</documents>")
    return "\n".join(lines)


def build_html(repo_url: str, repo_dir: pathlib.Path, head_commit: str, infos: List[FileInfo]) -> str:
    formatter = HtmlFormatter(nowrap=False, style='github-dark', linenos='table')
    pygments_css = formatter.get_style_defs('.highlight')

    # Get GitHub raw base URL for fixing relative paths
    github_raw_base = get_github_raw_base_url(repo_url, head_commit)

    rendered = [i for i in infos if i.decision.include]
    skipped_binary = [i for i in infos if i.decision.reason == "binary"]
    skipped_large = [i for i in infos if i.decision.reason == "too_large"]
    skipped_ignored = [i for i in infos if i.decision.reason == "ignored"]
    total_files = len(rendered) + len(skipped_binary) + len(skipped_large) + len(skipped_ignored)
    total_size = sum(i.size for i in rendered)
    commit_date = git_commit_date(str(repo_dir))

    tree_text = try_tree_command(repo_dir)
    cxml_text = generate_cxml_text(infos, repo_dir)

    # Group files by directory
    file_groups = {}
    for i in rendered:
        dir_name = os.path.dirname(i.rel) or "📁 Root"
        if dir_name not in file_groups:
            file_groups[dir_name] = []
        file_groups[dir_name].append(i)

    # Generate TOC with collapsible directories
    toc_items: List[str] = []
    for dir_idx, (dir_name, files) in enumerate(sorted(file_groups.items())):
        dir_id = f"dir-{slugify(dir_name)}"
        toc_items.append(f'''
        <li class="toc-dir">
          <div class="dir-header" onclick="toggleDir('{dir_id}')">
            <span class="dir-icon">📁</span>
            <strong>{html.escape(dir_name)}</strong>
            <span class="file-count">({len(files)})</span>
            <span class="chevron">▼</span>
          </div>
          <ul class="dir-files" id="{dir_id}">
        ''')
        for i in files:
            anchor = slugify(i.rel)
            icon = get_file_icon(i.rel)
            lang = get_language_label(i.rel)
            toc_items.append(
                f'''<li class="toc-file" data-path="{html.escape(i.rel.lower())}">
                  <a href="#file-{anchor}">
                    <span class="file-icon">{icon}</span>
                    <span class="file-name">{html.escape(os.path.basename(i.rel))}</span>
                    <span class="file-lang">{lang}</span>
                  </a>
                </li>'''
            )
        toc_items.append('</ul></li>')
    toc_html = "".join(toc_items)

    # Generate file sections
    sections: List[str] = []
    for i in rendered:
        anchor = slugify(i.rel)
        p = i.path
        ext = p.suffix.lower()
        icon = get_file_icon(i.rel)
        lang = get_language_label(i.rel)
        
        try:
            text = read_text(p)
            line_count = text.count('\n') + 1
            char_count = len(text)
            
            if ext in MARKDOWN_EXTENSIONS:
                # Fix relative paths in markdown before rendering
                body_html = f'<div class="markdown-body">{render_markdown_text(text, i.rel, github_raw_base)}</div>'
            else:
                code_html = highlight_code(text, i.rel, formatter)
                body_html = f'<div class="code-wrapper">{code_html}</div>'
        except Exception as e:
            body_html = f'<pre class="error">❌ Failed to render: {html.escape(str(e))}</pre>'
            line_count = 0
            char_count = 0
        
        sections.append(f"""
<section class="file-section" id="file-{anchor}" data-file-type="{ext[1:] if ext else 'unknown'}">
  <div class="file-header">
    <div class="file-title">
      <span class="file-icon-large">{icon}</span>
      <div class="file-info">
        <h2>{html.escape(i.rel)}</h2>
        <div class="file-path">{html.escape(os.path.dirname(i.rel) or '/')}</div>
      </div>
    </div>
    <div class="file-meta">
      <span class="badge badge-lang">{lang}</span>
      <span class="badge badge-size">{bytes_human(i.size)}</span>
      <span class="badge badge-lines">{line_count:,} lines</span>
      <span class="badge badge-chars">{char_count:,} chars</span>
      <button class="copy-btn" onclick="copyFileContent('{anchor}')" title="Copy file content">
        <span class="copy-icon">📋</span>
        <span class="copy-text">Copy</span>
      </button>
    </div>
  </div>
  <div class="file-body" id="content-{anchor}">{body_html}</div>
  <div class="file-footer">
    <a href="#top" class="back-link">↑ Back to top</a>
    <span class="file-stats">Last modified: {commit_date.split()[0]}</span>
  </div>
</section>
""")

    def render_skip_list(title: str, items: List[FileInfo], emoji: str, color: str) -> str:
        if not items:
            return ""
        total_size = sum(i.size for i in items)
        lis = [
            f'''<li>
              <span class="skip-icon">{get_file_icon(i.rel)}</span>
              <code>{html.escape(i.rel)}</code>
              <span class="skip-size">{bytes_human(i.size)}</span>
            </li>'''
            for i in items
        ]
        return f"""
        <details class="skip-section skip-{color}">
          <summary>
            <span class="summary-icon">{emoji}</span>
            <span class="summary-title">{html.escape(title)}</span>
            <span class="summary-count">{len(items)} files</span>
            <span class="summary-size">{bytes_human(total_size)}</span>
          </summary>
          <ul class='skip-list'>
            {"".join(lis)}
          </ul>
        </details>
        """

    skipped_html = (
        render_skip_list("Skipped Binary Files", skipped_binary, "🚫", "warning") +
        render_skip_list("Skipped Large Files", skipped_large, "📏", "info")
    )

    repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
    generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="description" content="Professional repository viewer for {html.escape(repo_name)}" />
<title>{html.escape(repo_name)} - Repository Analysis</title>
<style>
  :root {{
    --primary-color: #2563eb;
    --primary-hover: #1d4ed8;
    --primary-light: #dbeafe;
    --accent-color: #7c3aed;
    --accent-hover: #6d28d9;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --error-color: #ef4444;
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-tertiary: #f1f5f9;
    --bg-code: #0d1117;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #94a3b8;
    --border-color: #e2e8f0;
    --border-hover: #cbd5e1;
    --shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    --radius-sm: 6px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
  }}
  
  * {{ 
    box-sizing: border-box; 
    margin: 0;
    padding: 0;
  }}
  
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: var(--text-primary);
    background: var(--bg-secondary);
    overflow-x: hidden;
  }}
  
  /* Header Styles */
  .header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.5rem 2rem;
    box-shadow: var(--shadow-xl);
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(10px);
  }}
  
  .header-content {{
    max-width: 1600px;
    margin: 0 auto;
  }}
  
  .header h1 {{
    margin: 0 0 0.75rem 0;
    font-size: 2rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    letter-spacing: -0.025em;
  }}
  
  .header-meta {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    font-size: 0.9rem;
    opacity: 0.95;
    margin-bottom: 1.5rem;
  }}
  
  .meta-item {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }}
  
  .meta-item strong {{
    font-weight: 600;
    opacity: 0.9;
  }}
  
  .header-meta a {{
    color: white;
    text-decoration: none;
    border-bottom: 1px solid rgba(255,255,255,0.3);
    transition: border-color var(--transition-fast);
  }}
  
  .header-meta a:hover {{
    border-bottom-color: white;
  }}
  
  .stats-bar {{
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }}
  
  .stat-badge {{
    background: rgba(255,255,255,0.2);
    padding: 0.5rem 1rem;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    font-weight: 500;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.1);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: all var(--transition-base);
  }}
  
  .stat-badge:hover {{
    background: rgba(255,255,255,0.3);
    transform: translateY(-2px);
  }}
  
  /* Layout */
  .page {{
    display: grid;
    grid-template-columns: 340px minmax(0, 1fr);
    max-width: 1800px;
    margin: 0 auto;
    gap: 0;
    min-height: calc(100vh - 200px);
  }}
  
  /* Sidebar */
  #sidebar {{
    position: sticky;
    top: 200px;
    align-self: start;
    height: calc(100vh - 220px);
    overflow-y: auto;
    overflow-x: hidden;
    background: var(--bg-primary);
    border-right: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
  }}
  
  #sidebar::-webkit-scrollbar {{
    width: 10px;
  }}
  
  #sidebar::-webkit-scrollbar-track {{
    background: var(--bg-secondary);
  }}
  
  #sidebar::-webkit-scrollbar-thumb {{
    background: var(--border-color);
    border-radius: 5px;
    border: 2px solid var(--bg-secondary);
  }}
  
  #sidebar::-webkit-scrollbar-thumb:hover {{
    background: var(--text-muted);
  }}
  
  .sidebar-inner {{
    padding: 2rem 1.5rem;
  }}
  
  #sidebar h2 {{
    margin: 0 0 1.5rem 0;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    font-weight: 700;
  }}
  
  .search-box {{
    width: 100%;
    padding: 0.75rem 1rem;
    border: 2px solid var(--border-color);
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    margin-bottom: 1.5rem;
    transition: all var(--transition-base);
    background: var(--bg-secondary);
    color: var(--text-primary);
  }}
  
  .search-box:focus {{
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px var(--primary-light);
    background: var(--bg-primary);
  }}
  
  .search-box::placeholder {{
    color: var(--text-muted);
  }}
  
  /* TOC Styles */
  .toc {{
    list-style: none;
    padding: 0;
    margin: 0;
  }}
  
  .toc-dir {{
    margin-bottom: 0.5rem;
  }}
  
  .dir-header {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--transition-fast);
    user-select: none;
    font-size: 0.875rem;
  }}
  
  .dir-header:hover {{
    background: var(--bg-tertiary);
    transform: translateX(2px);
  }}
  
  .dir-header.collapsed .chevron {{
    transform: rotate(-90deg);
  }}
  
  .dir-icon {{
    font-size: 1rem;
    flex-shrink: 0;
  }}
  
  .file-count {{
    margin-left: auto;
    font-size: 0.75rem;
    color: var(--text-muted);
    background: var(--bg-tertiary);
    padding: 0.125rem 0.5rem;
    border-radius: var(--radius-sm);
  }}
  
  .chevron {{
    font-size: 0.75rem;
    color: var(--text-muted);
    transition: transform var(--transition-base);
    flex-shrink: 0;
  }}
  
  .dir-files {{
    list-style: none;
    padding-left: 1rem;
    margin-top: 0.5rem;
    overflow: hidden;
    transition: max-height var(--transition-slow);
  }}
  
  .dir-files.collapsed {{
    max-height: 0 !important;
    margin-top: 0;
  }}
  
  .toc-file {{
    margin: 0.25rem 0;
  }}
  
  .toc-file.hidden {{
    display: none;
  }}
  
  .toc-file a {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    color: var(--text-secondary);
    text-decoration: none;
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
    font-size: 0.875rem;
    border-left: 3px solid transparent;
  }}
  
  .toc-file a:hover {{
    background: var(--bg-secondary);
    color: var(--text-primary);
    transform: translateX(2px);
    border-left-color: var(--primary-color);
  }}
  
  .toc-file a.active {{
    background: var(--primary-light);
    color: var(--primary-color);
    font-weight: 600;
    border-left-color: var(--primary-color);
  }}
  
  .file-icon {{
    font-size: 1rem;
    flex-shrink: 0;
  }}
  
  .file-name {{
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  
  .file-lang {{
    font-size: 0.7rem;
    color: var(--text-muted);
    background: var(--bg-tertiary);
    padding: 0.125rem 0.375rem;
    border-radius: var(--radius-sm);
    flex-shrink: 0;
  }}
  
  /* Main Content */
  main.container {{
    padding: 2.5rem;
    background: var(--bg-secondary);
    min-height: 100vh;
  }}
  
  /* View Toggle */
  .view-toggle {{
    margin: 0 0 2.5rem 0;
    display: flex;
    gap: 0.75rem;
    align-items: center;
    background: var(--bg-secondary);
    padding: 1.25rem;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-color);
  }}
  
  .toggle-btn {{
    padding: 0.75rem 1.5rem;
    border: 2px solid var(--border-color);
    background: var(--bg-primary);
    cursor: pointer;
    border-radius: var(--radius-md);
    font-size: 0.9rem;
    font-weight: 600;
    transition: all var(--transition-base);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-secondary);
    position: relative;
    overflow: hidden;
  }}
  
  .toggle-btn::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
    opacity: 0;
    transition: opacity var(--transition-base);
    z-index: -1;
  }}
  
  .toggle-btn:hover:not(.active) {{
    background: var(--bg-tertiary);
    border-color: var(--border-hover);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }}
  
  .toggle-btn.active {{
    background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
    color: white;
    border-color: transparent;
    box-shadow: var(--shadow-lg);
    transform: translateY(-1px);
  }}
  
  .toggle-btn.active::before {{
    opacity: 1;
  }}
  
  /* File Section */
  section {{
    margin-bottom: 2.5rem;
  }}
  
  section > h2 {{
    font-size: 1.5rem;
    margin: 0 0 1.5rem 0;
    color: var(--text-primary);
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding-bottom: 0.75rem;
    border-bottom: 3px solid var(--border-color);
  }}
  
  .file-section {{
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-xl);
    padding: 0;
    margin-bottom: 2rem;
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-slow);
    overflow: hidden;
  }}
  
  .file-section:hover {{
    box-shadow: var(--shadow-lg);
    border-color: var(--border-hover);
  }}
  
  .file-section:target {{
    box-shadow: 0 0 0 4px var(--primary-light);
    border-color: var(--primary-color);
    animation: highlight-pulse 1s ease-out;
  }}
  
  @keyframes highlight-pulse {{
    0%, 100% {{ box-shadow: 0 0 0 4px var(--primary-light); }}
    50% {{ box-shadow: 0 0 0 8px var(--primary-light); }}
  }}
  
  .file-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 2rem;
    background: linear-gradient(to right, var(--bg-secondary), var(--bg-primary));
    border-bottom: 2px solid var(--border-color);
    flex-wrap: wrap;
    gap: 1rem;
  }}
  
  .file-title {{
    display: flex;
    align-items: center;
    gap: 1rem;
    flex: 1;
    min-width: 0;
  }}
  
  .file-icon-large {{
    font-size: 2.5rem;
    flex-shrink: 0;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
  }}
  
  .file-info {{
    flex: 1;
    min-width: 0;
  }}
  
  .file-info h2 {{
    margin: 0;
    font-size: 1.25rem;
    color: var(--text-primary);
    font-weight: 700;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    letter-spacing: -0.025em;
  }}
  
  .file-path {{
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
    font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  }}
  
  .file-meta {{
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
  }}
  
  .badge {{
    padding: 0.4rem 0.75rem;
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    transition: all var(--transition-fast);
  }}
  
  .badge-lang {{
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
  }}
  
  .badge-size {{
    background: var(--bg-tertiary);
    color: var(--text-secondary);
  }}
  
  .badge-lines {{
    background: #dbeafe;
    color: #1e40af;
  }}
  
  .badge-chars {{
    background: #fef3c7;
    color: #92400e;
  }}
  
  .badge:hover {{
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
  }}
  
  .copy-btn {{
    background: var(--primary-color);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: var(--radius-md);
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 600;
    transition: all var(--transition-base);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    box-shadow: var(--shadow-sm);
  }}
  
  .copy-btn:hover {{
    background: var(--primary-hover);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }}
  
  .copy-btn:active {{
    transform: translateY(0);
    box-shadow: var(--shadow-xs);
  }}
  
  .copy-icon {{
    font-size: 1rem;
  }}
  
  .file-body {{
    padding: 0;
    position: relative;
  }}
  
  .code-wrapper {{
    border-radius: 0;
    overflow: hidden;
    background: var(--bg-code);
  }}
  
  .highlight {{
    overflow-x: auto;
    background: var(--bg-code) !important;
    padding: 0;
    margin: 0;
    font-size: 0.875rem;
    line-height: 1.7;
  }}
  
  .highlight pre {{
    margin: 0;
    background: transparent !important;
    padding: 1.5rem 2rem;
    overflow-x: auto;
  }}
  
  .highlight table {{
    border-spacing: 0;
    width: 100%;
  }}
  
  .highlight .linenos {{
    background: rgba(0,0,0,0.2);
    color: rgba(255,255,255,0.3);
    text-align: right;
    padding: 1.5rem 1rem;
    user-select: none;
    border-right: 1px solid rgba(255,255,255,0.1);
  }}
  
  .highlight .linenos pre {{
    padding: 0;
  }}
  
  .highlight .code {{
    padding-left: 1rem;
  }}
  
  pre {{
    background: var(--bg-tertiary);
    padding: 1.5rem;
    overflow: auto;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-color);
    line-height: 1.6;
    font-size: 0.875rem;
  }}
  
  code {{
    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    font-size: 0.9em;
  }}
  
  /* Markdown Body - Enhanced for Images */
  .markdown-body {{
    padding: 2rem;
    background: var(--bg-primary);
    line-height: 1.8;
  }}
  
  .markdown-body img {{
    max-width: 100%;
    height: auto;
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-md);
    margin: 1.5rem 0;
    display: block;
    border: 1px solid var(--border-color);
  }}
  
  .markdown-body img:hover {{
    box-shadow: var(--shadow-lg);
    transform: scale(1.02);
    transition: all var(--transition-base);
  }}
  
  .markdown-body h1,
  .markdown-body h2,
  .markdown-body h3,
  .markdown-body h4,
  .markdown-body h5,
  .markdown-body h6 {{
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    font-weight: 700;
    line-height: 1.3;
    color: var(--text-primary);
  }}
  
  .markdown-body h1 {{
    font-size: 2rem;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 0.5rem;
  }}
  
  .markdown-body h2 {{
    font-size: 1.5rem;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.4rem;
  }}
  
  .markdown-body h3 {{
    font-size: 1.25rem;
  }}
  
  .markdown-body p {{
    margin-bottom: 1rem;
  }}
  
  .markdown-body ul,
  .markdown-body ol {{
    margin-bottom: 1rem;
    padding-left: 2rem;
  }}
  
  .markdown-body li {{
    margin-bottom: 0.5rem;
  }}
  
  .markdown-body a {{
    color: var(--primary-color);
    text-decoration: none;
    border-bottom: 1px solid var(--primary-light);
    transition: all var(--transition-fast);
  }}
  
  .markdown-body a:hover {{
    color: var(--primary-hover);
    border-bottom-color: var(--primary-color);
  }}
  
  .markdown-body code {{
    background: var(--bg-tertiary);
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
    font-size: 0.875em;
    color: var(--error-color);
  }}
  
  .markdown-body pre {{
    background: var(--bg-code);
    color: #e6edf3;
    padding: 1.5rem;
    border-radius: var(--radius-md);
    overflow-x: auto;
  }}
  
  .markdown-body pre code {{
    background: transparent;
    padding: 0;
    color: inherit;
  }}
  
  .markdown-body table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1rem;
  }}
  
  .markdown-body th,
  .markdown-body td {{
    border: 1px solid var(--border-color);
    padding: 0.75rem;
    text-align: left;
  }}
  
  .markdown-body th {{
    background: var(--bg-secondary);
    font-weight: 600;
  }}
  
  .markdown-body blockquote {{
    border-left: 4px solid var(--primary-color);
    padding-left: 1rem;
    margin: 1rem 0;
    color: var(--text-secondary);
    font-style: italic;
  }}
  
  .file-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: var(--bg-secondary);
    border-top: 1px solid var(--border-color);
    font-size: 0.875rem;
  }}
  
  .back-link {{
    color: var(--primary-color);
    text-decoration: none;
    font-weight: 600;
    transition: all var(--transition-fast);
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }}
  
  .back-link:hover {{
    color: var(--primary-hover);
    transform: translateX(-2px);
  }}
  
  .file-stats {{
    color: var(--text-muted);
  }}
  
  /* Skip Sections */
  .skip-section {{
    background: var(--bg-primary);
    padding: 0;
    border-radius: var(--radius-lg);
    margin-bottom: 1.5rem;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
    transition: all var(--transition-base);
  }}
  
  .skip-section:hover {{
    box-shadow: var(--shadow-md);
  }}
  
  .skip-section summary {{
    cursor: pointer;
    font-weight: 600;
    color: var(--text-primary);
    user-select: none;
    transition: all var(--transition-fast);
    padding: 1.25rem 1.5rem;
    background: var(--bg-secondary);
    display: flex;
    align-items: center;
    gap: 0.75rem;
    border-bottom: 1px solid transparent;
  }}
  
  .skip-section[open] summary {{
    border-bottom-color: var(--border-color);
  }}
  
  .skip-section summary:hover {{
    background: var(--bg-tertiary);
  }}
  
  .summary-icon {{
    font-size: 1.5rem;
  }}
  
  .summary-title {{
    flex: 1;
    font-size: 1rem;
  }}
  
  .summary-count {{
    background: var(--bg-tertiary);
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-sm);
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-secondary);
  }}
  
  .summary-size {{
    font-size: 0.85rem;
    color: var(--text-muted);
    font-weight: 500;
  }}
  
  .skip-warning {{
    border-left: 4px solid var(--warning-color);
  }}
  
  .skip-warning summary {{
    background: #fef3c7;
  }}
  
  .skip-info {{
    border-left: 4px solid var(--primary-color);
  }}
  
  .skip-info summary {{
    background: var(--primary-light);
  }}
  
  .skip-list {{
    list-style: none;
    padding: 1rem 1.5rem;
    margin: 0;
  }}
  
  .skip-list li {{
    padding: 0.75rem;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    gap: 0.75rem;
    transition: background var(--transition-fast);
  }}
  
  .skip-list li:last-child {{
    border-bottom: none;
  }}
  
  .skip-list li:hover {{
    background: var(--bg-secondary);
  }}
  
  .skip-icon {{
    font-size: 1.25rem;
    flex-shrink: 0;
  }}
  
  .skip-list code {{
    background: var(--bg-tertiary);
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
    font-size: 0.85em;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  
  .skip-size {{
    font-size: 0.8rem;
    color: var(--text-muted);
    font-weight: 600;
    flex-shrink: 0;
  }}
  
  /* LLM View */
  #llm-view {{
    display: none;
  }}
  
  #llm-text {{
    width: 100%;
    height: 70vh;
    font-family: 'SF Mono', Monaco, Consolas, monospace;
    font-size: 0.875rem;
    border: 2px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    resize: vertical;
    background: var(--bg-secondary);
    color: var(--text-primary);
    line-height: 1.6;
    transition: all var(--transition-base);
  }}
  
  #llm-text:focus {{
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 4px var(--primary-light);
    background: var(--bg-primary);
  }}
  
  .copy-hint {{
    margin-top: 1.5rem;
    padding: 1.25rem;
    background: linear-gradient(135deg, #fef3c7, #fde68a);
    border-left: 4px solid var(--warning-color);
    border-radius: var(--radius-md);
    color: #78350f;
    font-size: 0.9rem;
    line-height: 1.6;
    box-shadow: var(--shadow-sm);
  }}
  
  .copy-hint strong {{
    font-weight: 700;
    color: #92400e;
  }}
  
  /* Tree View */
  #tree-view {{
    display: none;
  }}
  
  #tree-view pre {{
    background: var(--bg-code);
    color: #e6edf3;
    padding: 2rem;
    border-radius: var(--radius-lg);
    overflow-x: auto;
    line-height: 1.6;
    font-size: 0.875rem;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
  }}
  
  /* Toast Notification */
  .toast {{
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    background: linear-gradient(135deg, var(--success-color), #059669);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-xl);
    opacity: 0;
    transform: translateY(2rem);
    transition: all var(--transition-slow);
    z-index: 1000;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    max-width: 400px;
  }}
  
  .toast.show {{
    opacity: 1;
    transform: translateY(0);
  }}
  
  .toast.error {{
    background: linear-gradient(135deg, var(--error-color), #dc2626);
  }}
  
  /* Utility Classes */
  .muted {{
    color: var(--text-muted);
    font-weight: normal;
    font-size: 0.9em;
  }}
  
  .error {{
    color: var(--error-color);
    background: #fef2f2;
    border: 1px solid #fecaca;
    padding: 1.5rem;
    border-radius: var(--radius-lg);
    font-weight: 500;
  }}
  
  /* Responsive Design */
  @media (max-width: 1200px) {{
    .page {{
      grid-template-columns: 300px minmax(0, 1fr);
    }}
    
    #sidebar {{
      top: 180px;
      height: calc(100vh - 200px);
    }}
  }}
  
  @media (max-width: 1000px) {{
    .page {{
      grid-template-columns: 1fr;
    }}
    
    #sidebar {{
      position: relative;
      top: 0;
      height: auto;
      max-height: 500px;
      border-right: none;
      border-bottom: 1px solid var(--border-color);
    }}
    
    .header {{
      padding: 1.5rem 1rem;
    }}
    
    .header h1 {{
      font-size: 1.5rem;
    }}
    
    main.container {{
      padding: 1.5rem;
    }}
    
    .file-header {{
      padding: 1rem 1.5rem;
    }}
    
    .file-icon-large {{
      font-size: 2rem;
    }}
    
    .file-info h2 {{
      font-size: 1rem;
    }}
  }}
  
  @media (max-width: 640px) {{
    .header {{
      padding: 1rem;
    }}
    
    .header h1 {{
      font-size: 1.25rem;
    }}
    
    .stats-bar {{
      gap: 0.5rem;
    }}
    
    .stat-badge {{
      font-size: 0.75rem;
      padding: 0.4rem 0.6rem;
    }}
    
    main.container {{
      padding: 1rem;
    }}
    
    .view-toggle {{
      flex-direction: column;
      align-items: stretch;
    }}
    
    .toggle-btn {{
      justify-content: center;
    }}
    
    .file-header {{
      flex-direction: column;
      align-items: flex-start;
      padding: 1rem;
    }}
    
    .file-meta {{
      width: 100%;
      justify-content: flex-start;
    }}
    
    .toast {{
      bottom: 1rem;
      right: 1rem;
      left: 1rem;
      max-width: none;
    }}
  }}
  
  /* Print Styles */
  @media print {{
    .header,
    #sidebar,
    .view-toggle,
    .copy-btn,
    .back-link,
    .toast {{
      display: none !important;
    }}
    
    .page {{
      grid-template-columns: 1fr;
    }}
    
    .file-section {{
      break-inside: avoid;
      page-break-inside: avoid;
    }}
  }}
  
  /* Animations */
  @keyframes fadeIn {{
    from {{
      opacity: 0;
      transform: translateY(1rem);
    }}
    to {{
      opacity: 1;
      transform: translateY(0);
    }}
  }}
  
  .file-section {{
    animation: fadeIn 0.3s ease-out;
  }}
  
  /* Scrollbar Styling for Main Content */
  main.container::-webkit-scrollbar {{
    width: 12px;
  }}
  
  main.container::-webkit-scrollbar-track {{
    background: var(--bg-secondary);
  }}
  
  main.container::-webkit-scrollbar-thumb {{
    background: var(--border-color);
    border-radius: 6px;
    border: 3px solid var(--bg-secondary);
  }}
  
  main.container::-webkit-scrollbar-thumb:hover {{
    background: var(--text-muted);
  }}
  
  {pygments_css}
</style>
</head>
<body>
<a id="top"></a>

<div class="header">
  <div class="header-content">
    <h1>📦 {html.escape(repo_name)}</h1>
    <div class="header-meta">
      <div class="meta-item">
        <strong>🔗 Repository:</strong>
        <a href="{html.escape(repo_url)}" target="_blank" rel="noopener">{html.escape(repo_url)}</a>
      </div>
      <div class="meta-item">
        <strong>📅 Generated:</strong>
        <span>{generation_time}</span>
      </div>
      <div class="meta-item">
        <strong>🔖 Commit:</strong>
        <code style="background: rgba(255,255,255,0.2); padding: 0.25rem 0.5rem; border-radius: 4px;">{head_commit[:8]}</code>
      </div>
      <div class="meta-item">
        <strong>📆 Commit Date:</strong>
        <span>{commit_date}</span>
      </div>
    </div>
    <div class="stats-bar">
      <div class="stat-badge">
        <span>📊</span>
        <span><strong>{total_files}</strong> Total Files</span>
      </div>
      <div class="stat-badge">
        <span>✅</span>
        <span><strong>{len(rendered)}</strong> Rendered</span>
      </div>
      <div class="stat-badge">
        <span>💾</span>
        <span><strong>{bytes_human(total_size)}</strong> Total Size</span>
      </div>
      {f'<div class="stat-badge"><span>🚫</span><span><strong>{len(skipped_binary)}</strong> Binary</span></div>' if skipped_binary else ''}
      {f'<div class="stat-badge"><span>📏</span><span><strong>{len(skipped_large)}</strong> Large</span></div>' if skipped_large else ''}
    </div>
  </div>
</div>

<div class="page">
  <aside id="sidebar">
    <div class="sidebar-inner">
      <h2>📑 Table of Contents</h2>
      <input 
        type="text" 
        id="searchBox" 
        class="search-box" 
        placeholder="🔍 Search files... (Ctrl+K)"
        autocomplete="off"
      />
      <ul class="toc">
        {toc_html}
      </ul>
    </div>
  </aside>
  
  <main class="container">
    <div class="view-toggle">
      <button class="toggle-btn active" onclick="showView('human')">
        <span>👁️</span>
        <span>Human View</span>
      </button>
      <button class="toggle-btn" onclick="showView('llm')">
        <span>🤖</span>
        <span>LLM View (CXML)</span>
      </button>
      <button class="toggle-btn" onclick="showView('tree')">
        <span>🌳</span>
        <span>Directory Tree</span>
      </button>
    </div>
    
    <div id="human-view">
      <section>
        <h2>📄 Repository Files</h2>
        {"".join(sections)}
      </section>
      
      {skipped_html}
    </div>
    
    <div id="llm-view">
      <section>
        <h2>🤖 LLM-Optimized Format (CXML)</h2>
        <p style="color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.8;">
          This view presents the repository in <strong>CXML format</strong>, optimized for Large Language Models.
          Each file is wrapped in structured XML tags for easy parsing and context understanding.
          Simply copy the content below and paste it into your LLM conversation.
        </p>
        <button class="copy-btn" onclick="copyLLMText()" style="margin-bottom: 1.5rem;">
          <span class="copy-icon">📋</span>
          <span class="copy-text">Copy All CXML Content</span>
        </button>
        <textarea id="llm-text" readonly>{html.escape(cxml_text)}</textarea>
        <div class="copy-hint">
          <strong>💡 Usage Tip:</strong> This CXML format is designed for LLMs like Claude, GPT-4, or other AI assistants.
          Copy the entire content and paste it into your conversation to provide complete repository context.
          The structured format helps the AI understand file relationships and content hierarchy.
        </div>
      </section>
    </div>
    
    <div id="tree-view">
      <section>
        <h2>🌳 Directory Structure</h2>
        <p style="color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.8;">
          Visual representation of the repository's directory structure.
          This tree view shows the hierarchical organization of all files and folders.
        </p>
        <pre>{html.escape(tree_text)}</pre>
      </section>
    </div>
  </main>
</div>

<div id="toast" class="toast"></div>

<script>
  // View switching with localStorage persistence
  function showView(view) {{
    ['human', 'llm', 'tree'].forEach(v => {{
      document.getElementById(v + '-view').style.display = 'none';
      document.querySelectorAll('.toggle-btn').forEach(btn => {{
        if (btn.textContent.toLowerCase().includes(v)) {{
          btn.classList.remove('active');
        }}
      }});
    }});
    
    document.getElementById(view + '-view').style.display = 'block';
    document.querySelectorAll('.toggle-btn').forEach(btn => {{
      if (btn.textContent.toLowerCase().includes(view)) {{
        btn.classList.add('active');
      }}
    }});
    
    // Save preference
    localStorage.setItem('preferredView', view);
    
    // Show feedback
    const viewNames = {{ human: 'Human View', llm: 'LLM View', tree: 'Tree View' }};
    showToast(`📍 Switched to ${{viewNames[view]}}`, 'success');
  }}
  
  // Copy file content with enhanced feedback
  function copyFileContent(anchor) {{
    const contentEl = document.getElementById('content-' + anchor);
    if (!contentEl) return;
    
    let text = '';
    const codeEl = contentEl.querySelector('pre');
    if (codeEl) {{
      text = codeEl.textContent || codeEl.innerText;
    }} else {{
      text = contentEl.textContent || contentEl.innerText;
    }}
    
    navigator.clipboard.writeText(text).then(() => {{
      showToast('✅ Content copied to clipboard!', 'success');
    }}).catch(err => {{
      console.error('Copy failed:', err);
      showToast('❌ Failed to copy. Please try again.', 'error');
    }});
  }}
  
  // Copy LLM text with progress indication
  function copyLLMText() {{
    const textarea = document.getElementById('llm-text');
    textarea.select();
    textarea.setSelectionRange(0, textarea.value.length);
    
    navigator.clipboard.writeText(textarea.value).then(() => {{
      showToast('✅ CXML content copied! Ready to paste into your LLM.', 'success');
    }}).catch(err => {{
      console.error('Copy failed:', err);
      showToast('❌ Copy failed. Please select and copy manually.', 'error');
    }});
  }}
  
  // Enhanced toast notification system
  function showToast(message, type = 'success') {{
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast';
    
    if (type === 'error') {{
      toast.classList.add('error');
    }}
    
    // Trigger reflow to restart animation
    void toast.offsetWidth;
    
    toast.classList.add('show');
    
    setTimeout(() => {{
      toast.classList.remove('show');
    }}, 3500);
  }}
  
  // Advanced search functionality with highlighting
  const searchBox = document.getElementById('searchBox');
  const tocFiles = document.querySelectorAll('.toc-file');
  const tocDirs = document.querySelectorAll('.toc-dir');
  
  searchBox.addEventListener('input', (e) => {{
    const query = e.target.value.toLowerCase().trim();
    
    if (!query) {{
      // Show all items when search is empty
      tocFiles.forEach(item => item.classList.remove('hidden'));
      tocDirs.forEach(dir => {{
        dir.style.display = 'block';
        const dirFiles = dir.querySelector('.dir-files');
        if (dirFiles) {{
          dirFiles.classList.remove('collapsed');
        }}
      }});
      return;
    }}
    
    // Filter files
    let visibleCount = 0;
    tocDirs.forEach(dir => {{
      const dirFiles = dir.querySelectorAll('.toc-file');
      let dirHasMatch = false;
      
      dirFiles.forEach(item => {{
        const text = item.textContent.toLowerCase();
        const path = item.getAttribute('data-path') || '';
        
        if (text.includes(query) || path.includes(query)) {{
          item.classList.remove('hidden');
          dirHasMatch = true;
          visibleCount++;
        }} else {{
          item.classList.add('hidden');
        }}
      }});
      
      // Show/hide directory based on matches
      if (dirHasMatch) {{
        dir.style.display = 'block';
        const dirFilesContainer = dir.querySelector('.dir-files');
        if (dirFilesContainer) {{
          dirFilesContainer.classList.remove('collapsed');
        }}
      }} else {{
        dir.style.display = 'none';
      }}
    }});
    
    // Show feedback if no results
    if (visibleCount === 0) {{
      showToast('🔍 No files found matching "' + query + '"', 'error');
    }}
  }});
  
  // Directory toggle functionality
  function toggleDir(dirId) {{
    const dirFiles = document.getElementById(dirId);
    const dirHeader = dirFiles.previousElementSibling;
    
    if (dirFiles.classList.contains('collapsed')) {{
      dirFiles.classList.remove('collapsed');
      dirHeader.classList.remove('collapsed');
    }} else {{
      dirFiles.classList.add('collapsed');
      dirHeader.classList.add('collapsed');
    }}
  }}
  
  // Smooth scroll for anchor links with offset
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
    anchor.addEventListener('click', function (e) {{
      e.preventDefault();
      const targetId = this.getAttribute('href');
      const target = document.querySelector(targetId);
      
      if (target) {{
        const headerOffset = 100;
        const elementPosition = target.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
        
        window.scrollTo({{
          top: offsetPosition,
          behavior: 'smooth'
        }});
        
        // Add temporary highlight
        target.style.transition = 'all 0.3s ease';
        setTimeout(() => {{
          target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}, 100);
      }}
    }});
  }});
  
  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {{
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {{
      e.preventDefault();
      searchBox.focus();
      searchBox.select();
    }}
    
    // Escape to clear search and blur
    if (e.key === 'Escape') {{
      if (document.activeElement === searchBox) {{
        searchBox.value = '';
        searchBox.dispatchEvent(new Event('input'));
        searchBox.blur();
      }}
    }}
    
    // Ctrl/Cmd + / to toggle view
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {{
      e.preventDefault();
      const views = ['human', 'llm', 'tree'];
      const currentView = views.find(v => 
        document.getElementById(v + '-view').style.display !== 'none'
      ) || 'human';
      const currentIndex = views.indexOf(currentView);
      const nextView = views[(currentIndex + 1) % views.length];
      showView(nextView);
    }}
  }});
  
  // Intersection Observer for TOC highlighting
  const observerOptions = {{
    threshold: 0.3,
    rootMargin: '-100px 0px -66% 0px'
  }};
  
  const observer = new IntersectionObserver((entries) => {{
    entries.forEach(entry => {{
      if (entry.isIntersecting) {{
        const id = entry.target.id;
        const anchor = id.replace('file-', '');
        
        // Update TOC active state
        document.querySelectorAll('.toc a').forEach(link => {{
          if (link.getAttribute('href') === '#' + id) {{
            link.classList.add('active');
            
            // Scroll TOC to show active item
            const sidebar = document.getElementById('sidebar');
            const linkTop = link.getBoundingClientRect().top;
            const sidebarTop = sidebar.getBoundingClientRect().top;
            
            if (linkTop < sidebarTop || linkTop > sidebarTop + sidebar.clientHeight) {{
              link.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            }}
          }} else {{
            link.classList.remove('active');
          }}
        }});
      }}
    }});
  }}, observerOptions);
  
  // Observe all file sections
  document.querySelectorAll('.file-section').forEach(section => {{
    observer.observe(section);
  }});
  
  // Restore preferred view from localStorage
  window.addEventListener('DOMContentLoaded', () => {{
    const preferredView = localStorage.getItem('preferredView') || 'human';
    showView(preferredView);
    
    // Initialize directory files max-height for collapse animation
    document.querySelectorAll('.dir-files').forEach(dirFiles => {{
      dirFiles.style.maxHeight = dirFiles.scrollHeight + 'px';
    }});
    
    // Show welcome toast
    setTimeout(() => {{
      showToast('👋 Welcome! Use Ctrl+K to search, Ctrl+/ to switch views.', 'success');
    }}, 500);
  }});
  
  // Performance: Lazy load code highlighting for off-screen elements
  const lazyLoadObserver = new IntersectionObserver((entries) => {{
    entries.forEach(entry => {{
      if (entry.isIntersecting) {{
        const section = entry.target;
        section.classList.add('loaded');
        lazyLoadObserver.unobserve(section);
      }}
    }});
  }}, {{ rootMargin: '200px' }});
  
  document.querySelectorAll('.file-section').forEach(section => {{
    lazyLoadObserver.observe(section);
  }});
  
  // Copy on double-click for code blocks
  document.querySelectorAll('.highlight pre, .markdown-body pre').forEach(pre => {{
    pre.addEventListener('dblclick', () => {{
      const text = pre.textContent || pre.innerText;
      navigator.clipboard.writeText(text).then(() => {{
        showToast('✅ Code block copied!', 'success');
      }});
    }});
    
    // Add visual hint
    pre.style.cursor = 'copy';
    pre.title = 'Double-click to copy';
  }});
  
  // Track scroll progress
  let scrollTimeout;
  window.addEventListener('scroll', () => {{
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(() => {{
      const scrollPercentage = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
      
      // Update progress indicator if exists
      const progressBar = document.querySelector('.scroll-progress');
      if (progressBar) {{
        progressBar.style.width = scrollPercentage + '%';
      }}
    }}, 100);
  }});
  
  // Add scroll progress bar
  const progressBar = document.createElement('div');
  progressBar.className = 'scroll-progress';
  progressBar.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
    width: 0%;
    z-index: 9999;
    transition: width 0.1s ease;
  `;
  document.body.appendChild(progressBar);
  
  // Add keyboard shortcut hint
  const shortcutHint = document.createElement('div');
  shortcutHint.style.cssText = `
    position: fixed;
    bottom: 1rem;
    left: 1rem;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.75rem;
    opacity: 0;
    transition: opacity 0.3s;
    z-index: 999;
    pointer-events: none;
  `;
  shortcutHint.innerHTML = `
    <strong>Keyboard Shortcuts:</strong><br>
    <kbd>Ctrl+K</kbd> Search &nbsp;
    <kbd>Ctrl+/</kbd> Switch View &nbsp;
    <kbd>Esc</kbd> Clear
  `;
  document.body.appendChild(shortcutHint);
  
  // Show hint on first visit
  if (!localStorage.getItem('shortcutsShown')) {{
    setTimeout(() => {{
      shortcutHint.style.opacity = '1';
      setTimeout(() => {{
        shortcutHint.style.opacity = '0';
        localStorage.setItem('shortcutsShown', 'true');
      }}, 5000);
    }}, 2000);
  }}
  
  // Show hint on Ctrl key hold
  let ctrlHoldTimeout;
  document.addEventListener('keydown', (e) => {{
    if (e.ctrlKey || e.metaKey) {{
      ctrlHoldTimeout = setTimeout(() => {{
        shortcutHint.style.opacity = '1';
      }}, 500);
    }}
  }});
  
  document.addEventListener('keyup', (e) => {{
    if (!e.ctrlKey && !e.metaKey) {{
      clearTimeout(ctrlHoldTimeout);
      shortcutHint.style.opacity = '0';
    }}
  }});
  
  // Console easter egg
  console.log('%c🎉 Repository Viewer Pro', 'font-size: 20px; font-weight: bold; color: #667eea;');
  console.log('%cKeyboard Shortcuts:', 'font-size: 14px; font-weight: bold; margin-top: 10px;');
  console.log('%c  Ctrl+K  : Search files', 'font-size: 12px;');
  console.log('%c  Ctrl+/  : Switch views', 'font-size: 12px;');
  console.log('%c  Esc     : Clear search', 'font-size: 12px;');
  console.log('%c  Double-click code : Copy', 'font-size: 12px;');
  console.log('%c✨ Image Fix Applied: Relative paths in Markdown are now absolute!', 'font-size: 12px; color: #10b981; font-weight: bold;');
  
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flatten a GitHub repo into a professional single HTML page with enhanced UI/UX."
    )
    parser.add_argument("repo_url", help="GitHub repository URL")
    parser.add_argument(
        "-o", "--output",
        default="repo.html",
        help="Output HTML file path (default: repo.html)"
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=MAX_DEFAULT_BYTES,
        help=f"Max file size in bytes to include (default: {MAX_DEFAULT_BYTES})"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open the browser automatically"
    )
    args = parser.parse_args()

    print(f"🚀 Cloning repository: {args.repo_url}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = pathlib.Path(tmpdir) / "repo"
        try:
            git_clone(args.repo_url, str(repo_dir))
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to clone repository: {e}", file=sys.stderr)
            sys.exit(1)

        print("📊 Analyzing files...")
        head_commit = git_head_commit(str(repo_dir))
        infos = collect_files(repo_dir, args.max_size)

        print("🎨 Generating professional HTML...")
        html_content = build_html(args.repo_url, repo_dir, head_commit, infos)

    output_path = pathlib.Path(args.output)
    output_path.write_text(html_content, encoding="utf-8")

    rendered_count = sum(1 for i in infos if i.decision.include)
    total_size = sum(i.size for i in infos if i.decision.include)

    print(f"\n{'='*60}")
    print(f"✅ Success! Generated professional repository viewer")
    print(f"{'='*60}")
    print(f"📈 Statistics:")
    print(f"   • Files rendered: {rendered_count}")
    print(f"   • Total size: {bytes_human(total_size)}")
    print(f"   • Output file: {output_path.absolute()}")
    print(f"   • File size: {bytes_human(output_path.stat().st_size)}")
    print(f"\n🎯 Features:")
    print(f"   • 👁️  Human-readable view with syntax highlighting")
    print(f"   • 🤖 LLM-optimized CXML format")
    print(f"   • 🌳 Directory tree visualization")
    print(f"   • 🔍 Real-time search (Ctrl+K)")
    print(f"   • 📋 One-click copy functionality")
    print(f"   • 📱 Fully responsive design")
    print(f"   • 🖼️  Fixed: Markdown images with relative paths now display!")
    print(f"{'='*60}\n")

    if not args.no_browser:
        print("🌐 Opening in browser...")
        webbrowser.open(f"file://{output_path.absolute()}")


if __name__ == "__main__":
    main()