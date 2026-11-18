# pkg-repo

Personal CachyOS binary package repository built with GitHub Actions and hosted on GitHub Pages.

Live package index: [cachy.koresent.dev](https://cachy.koresent.dev)

## Repository Configuration

Add the repository block to `/etc/pacman.conf`:

```ini
[koresent]
SigLevel = Optional TrustAll
Server = https://cachy.koresent.dev/$arch
```

Synchronize databases and install packages:

```bash
sudo pacman -Syu
sudo pacman -S <package-name>
```

## Adding Packages

1. Create a directory under `packages/<package-name>/`.
2. Add a standard `PKGBUILD` and optional assets (`.desktop`, icons, systemd units, PAM configs).
3. Commit and push to `main`:
   ```bash
   git add packages/<package-name>
   git commit -m "feat(pkg): add <package-name>"
   git push origin main
   ```
4. GitHub Actions builds the package, updates `koresent.db.tar.gz`, regenerates `index.html`, and deploys to GitHub Pages.

## Automation and Nightly Builds

Release pipelines in upstream repositories dispatch a `package-updated` event via the GitHub API upon publishing a release. The repository builder workflow catches this event, increments the package version (`0.1.0.r<count>.g<sha>`), and redeploys the repository.

To sync all package versions manually:

```bash
python3 scripts/update-pkgver.py --all
```

## Local Builds

Build all packages and package database locally:

```bash
./scripts/build.sh
```

All built `.pkg.tar.zst` packages, the database, and `index.html` are placed in `public/`.
