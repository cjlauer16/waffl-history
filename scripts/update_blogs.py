#!/usr/bin/env python3
"""
Patch const BLOGS in index.html with the current contents of blog/*.md.

Run from the repo root:
    python scripts/update_blogs.py

No external dependencies — pure Python stdlib only.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG_DIR = ROOT / "blog"
INDEX = ROOT / "index.html"


def parse_frontmatter(text):
    m = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n', text, re.DOTALL)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip().strip('"\'')
    return meta, text[m.end():]


def load_blogs():
    posts = []
    for path in sorted(BLOG_DIR.glob('*.md'), reverse=True):
        text = path.read_text(encoding='utf-8')
        meta, body = parse_frontmatter(text)
        if not meta.get('title'):
            print(f"  Skipping {path.name}: no 'title' in frontmatter", file=sys.stderr)
            continue
        if meta.get('draft', '').lower() == 'true':
            print(f"  Skipping {path.name}: draft=true", file=sys.stderr)
            continue
        posts.append({
            'slug': path.stem,
            'title': meta.get('title', path.stem),
            'author': meta.get('author', 'Unknown'),
            'date': meta.get('date', ''),
            'body': body.strip(),
        })
    return posts


def patch_html(posts):
    html = INDEX.read_text(encoding='utf-8')
    blogs_json = json.dumps(posts, ensure_ascii=False)
    new_block = f'/*__BLOGS_START__*/const BLOGS = {blogs_json};/*__BLOGS_END__*/'
    patched, n = re.subn(
        r'/\*__BLOGS_START__\*/.*?/\*__BLOGS_END__\*/',
        new_block,
        html,
        flags=re.DOTALL,
    )
    if n == 0:
        print("ERROR: BLOGS marker not found in index.html — was it generated with the blog feature?", file=sys.stderr)
        sys.exit(1)
    INDEX.write_text(patched, encoding='utf-8')
    print(f"  Patched index.html with {len(posts)} blog post(s)")


if __name__ == '__main__':
    if not INDEX.exists():
        print(f"ERROR: {INDEX} not found", file=sys.stderr)
        sys.exit(1)
    posts = load_blogs()
    patch_html(posts)
    print(f"Done. Posts: {[p['slug'] for p in posts]}")
