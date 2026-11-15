#!/usr/bin/env python3
import glob
import os
import re
from datetime import datetime, timezone

REPO_NAME = os.environ.get("REPO_NAME", "koresent")
ARCH = os.environ.get("ARCH", "x86_64")
PUBLIC_DIR = os.environ.get("PUBLIC_DIR", "public")
ARCH_DIR = os.path.join(PUBLIC_DIR, ARCH)

DOWNLOAD_ICON_SVG = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>"""

def parse_pkgbuild(pkgbuild_path):
    info = {"pkgname": "", "pkgver": "", "pkgrel": "1", "pkgdesc": "", "url": "", "arch": "x86_64"}
    if not os.path.isfile(pkgbuild_path):
        return info
    with open(pkgbuild_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    for key in ["pkgname", "pkgver", "pkgrel", "pkgdesc", "url"]:
        match = re.search(rf'^{key}=["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
        if match:
            info[key] = match.group(1).strip()
    arch_match = re.search(r'^arch=\(([^)]+)\)', content, re.MULTILINE)
    if arch_match:
        arch_val = arch_match.group(1).replace("'", "").replace('"', '').strip()
        info["arch"] = "any" if "any" in arch_val.split() else "x86_64"
    return info

def get_packages():
    packages = []
    pkg_dirs = sorted(glob.glob("packages/*"))
    for pdir in pkg_dirs:
        pkgbuild = os.path.join(pdir, "PKGBUILD")
        if os.path.isfile(pkgbuild):
            meta = parse_pkgbuild(pkgbuild)
            pkgname = meta.get("pkgname", os.path.basename(pdir))
            pattern = os.path.join(ARCH_DIR, f"{pkgname}-*-*.pkg.tar.zst")
            matching_files = [f for f in glob.glob(pattern) if not f.endswith('.sig')]
            filename = os.path.basename(matching_files[0]) if matching_files else ""
            size_str = "-"
            if matching_files:
                size_bytes = os.path.getsize(matching_files[0])
                if size_bytes >= 1024 * 1024:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                else:
                    size_str = f"{size_bytes / 1024:.1f} KB"
            packages.append({
                "name": pkgname,
                "version": f"{meta.get('pkgver')}-{meta.get('pkgrel')}",
                "desc": meta.get("pkgdesc", "Personal package"),
                "url": meta.get("url", f"https://github.com/koresent/{pkgname}"),
                "file": filename,
                "size": size_str,
                "arch": meta.get("arch", "x86_64"),
            })
    return packages

def generate_html():
    packages = get_packages()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows_html = ""
    cards_html = ""

    for p in packages:
        if p["file"]:
            download_btn = (
                f'<a class="dl-btn" href="{ARCH}/{p["file"]}" download="{p["file"]}" '
                f'title="Download {p["name"]} ({p["size"]})" aria-label="Download {p["name"]}">'
                f'{DOWNLOAD_ICON_SVG}</a>'
            )
        else:
            download_btn = '<span class="status-building">Pending build</span>'

        rows_html += f"""        <tr>
          <td><a class="pkg-title" href="{p['url']}" target="_blank" rel="noopener">{p['name']}</a></td>
          <td><span class="badge">{p['version']}</span></td>
          <td class="desc-col">{p['desc']}</td>
          <td><code>{p['arch']}</code></td>
          <td class="size-col"><code>{p['size']}</code></td>
          <td class="action-col">{download_btn}</td>
        </tr>
"""

        cards_html += f"""        <div class="pkg-card">
          <div class="pkg-card-header">
            <a class="pkg-title" href="{p['url']}" target="_blank" rel="noopener">{p['name']}</a>
            <span class="badge">{p['version']}</span>
          </div>
          <p class="pkg-card-desc">{p['desc']}</p>
          <div class="pkg-card-footer">
            <div class="pkg-card-meta">
              <code>{p['arch']}</code>
              <code class="meta-size">{p['size']}</code>
            </div>
            <div class="pkg-card-action">
              {download_btn}
            </div>
          </div>
        </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>cachy.koresent.dev &bull; CachyOS Repository</title>
  <style>
    :root {{
      --bg0: #282828;
      --bg1: #32302f;
      --bg2: #3c3836;
      --bg3: #504945;
      --code-bg: #1d2021;
      --fg: #ebdbb2;
      --fg-dim: #a89984;
      --yellow: #fabd2f;
      --green: #b8bb26;
      --blue: #83a598;
      --aqua: #8ec07c;
      --orange: #fe8019;
      --border: #443e3b;
      --font-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      --font-mono: ui-monospace, "SF Mono", "Cascadia Code", "JetBrains Mono", Menlo, Consolas, monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg0);
      color: var(--fg);
      font-family: var(--font-sans);
      line-height: 1.55;
      padding: 2.5rem 1rem;
      -webkit-font-smoothing: antialiased;
    }}
    .container {{
      max-width: 900px;
      margin: 0 auto;
    }}
    header {{
      margin-bottom: 2rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1.25rem;
    }}
    h1 {{
      color: var(--yellow);
      font-size: 1.75rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin-bottom: 0.35rem;
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.65rem;
    }}
    .repo-badge {{
      background: var(--bg3);
      color: var(--aqua);
      font-size: 0.8rem;
      font-weight: 600;
      padding: 0.15rem 0.55rem;
      border-radius: 4px;
      letter-spacing: 0.02em;
    }}
    p.subtitle {{
      color: var(--fg-dim);
      font-size: 0.95rem;
    }}
    .card {{
      background: var(--bg1);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 1.75rem;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }}
    .card h2 {{
      color: var(--green);
      font-size: 1.15rem;
      font-weight: 600;
      margin-bottom: 0.85rem;
    }}
    p.hint {{
      color: var(--fg-dim);
      font-size: 0.9rem;
      margin-bottom: 0.5rem;
    }}
    p.hint-sub {{
      color: var(--fg-dim);
      font-size: 0.9rem;
      margin: 1rem 0 0.5rem;
    }}
    pre {{
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.75rem 1rem;
      overflow-x: auto;
      margin: 0;
      line-height: 1.45;
    }}
    pre code {{
      background: transparent !important;
      padding: 0 !important;
      margin: 0 !important;
      border-radius: 0 !important;
      font-family: var(--font-mono);
      font-size: 0.875rem;
      color: var(--fg);
      display: block;
      white-space: pre;
    }}
    :not(pre) > code {{
      background: var(--bg2);
      color: var(--orange);
      padding: 0.15rem 0.4rem;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-size: 0.85em;
    }}
    .code-comment {{ color: var(--fg-dim); }}
    .code-section {{ color: var(--yellow); font-weight: 600; }}
    .code-key {{ color: var(--blue); }}
    .code-val {{ color: var(--green); }}

    .table-container {{
      width: 100%;
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
    }}
    th, td {{
      padding: 0.75rem 0.85rem;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }}
    th {{
      color: var(--yellow);
      font-weight: 600;
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    tr:last-child td {{
      border-bottom: none;
    }}
    .pkg-title {{
      color: var(--blue);
      text-decoration: none;
      font-weight: 600;
      font-size: 0.95rem;
    }}
    .pkg-title:hover {{
      color: var(--aqua);
      text-decoration: underline;
    }}
    .desc-col {{
      color: var(--fg);
    }}
    .size-col {{
      white-space: nowrap;
    }}
    .badge {{
      background: var(--bg2);
      color: var(--yellow);
      font-family: var(--font-mono);
      font-size: 0.8rem;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      white-space: nowrap;
    }}
    .action-col {{
      text-align: right;
      width: 60px;
    }}
    .dl-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      background: var(--bg2);
      color: var(--fg);
      text-decoration: none;
      border-radius: 6px;
      border: 1px solid var(--border);
      transition: background 0.15s, color 0.15s, border-color 0.15s;
    }}
    .dl-btn:hover {{
      background: var(--green);
      color: var(--bg0);
      border-color: var(--green);
    }}
    .status-building {{
      color: var(--fg-dim);
      font-size: 0.8rem;
      font-style: italic;
    }}

    .mobile-cards {{
      display: none;
      flex-direction: column;
      gap: 0.75rem;
    }}
    .pkg-card {{
      background: var(--bg0);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.85rem 1rem;
    }}
    .pkg-card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.35rem;
    }}
    .pkg-card-desc {{
      color: var(--fg);
      font-size: 0.875rem;
      margin-bottom: 0.75rem;
    }}
    .pkg-card-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 0.5rem;
      border-top: 1px solid var(--border);
    }}
    .pkg-card-meta {{
      display: flex;
      gap: 0.5rem;
      align-items: center;
    }}
    .meta-size {{
      color: var(--fg-dim);
    }}
    .pkg-card-action .dl-btn {{
      width: 40px;
      height: 40px;
    }}

    footer {{
      margin-top: 2.5rem;
      text-align: center;
      color: var(--fg-dim);
      font-size: 0.8rem;
      border-top: 1px solid var(--border);
      padding-top: 1.25rem;
    }}
    footer a {{ color: var(--blue); text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}

    @media (max-width: 640px) {{
      body {{
        padding: 1.25rem 0.75rem;
      }}
      h1 {{
        font-size: 1.4rem;
      }}
      .card {{
        padding: 1rem;
      }}
      .table-container {{
        display: none;
      }}
      .mobile-cards {{
        display: flex;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>
        <span>cachy.koresent.dev</span>
        <span class="repo-badge">CachyOS</span>
      </h1>
      <p class="subtitle">Personal binary repository for Arch Linux / CachyOS.</p>
    </header>

    <div class="card">
      <h2>Configuration</h2>
      <p class="hint">Append the repository block to <code>/etc/pacman.conf</code>:</p>
      <pre><code><span class="code-section">[{REPO_NAME}]</span>
<span class="code-key">SigLevel</span> = <span class="code-val">Optional TrustAll</span>
<span class="code-key">Server</span> = <span class="code-val">https://cachy.koresent.dev/$arch</span></code></pre>
      <p class="hint-sub">Synchronize package databases and install target packages:</p>
      <pre><code>sudo pacman -Syu
sudo pacman -S kclip kfont kgreet klock korob snap-hud sweep</code></pre>
    </div>

    <div class="card">
      <h2>Packages ({len(packages)})</h2>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Package</th>
              <th>Version</th>
              <th>Description</th>
              <th>Arch</th>
              <th>Size</th>
              <th class="action-col"></th>
            </tr>
          </thead>
          <tbody>
{rows_html}          </tbody>
        </table>
      </div>
      <div class="mobile-cards">
{cards_html}      </div>
    </div>

    <footer>
      Repository generated on {now_str} &bull; Hosted on <a href="https://github.com/koresent/pkg-repo" target="_blank" rel="noopener">GitHub</a>
    </footer>
  </div>
</body>
</html>
"""
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    out_path = os.path.join(PUBLIC_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {out_path} with {len(packages)} packages.")

if __name__ == "__main__":
    generate_html()
