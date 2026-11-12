# koresent / pkg-repo

Personal CachyOS binary package repository, automatically built and deployed via **GitHub Actions** and hosted on **GitHub Pages**.

Live packages & status: **[cachy.koresent.dev](https://cachy.koresent.dev)**

---

## 📦 Using the Repository

### 1. Add Repository to Pacman
Append the following section to `/etc/pacman.conf` (or via your dotfiles manager / chezmoi):

```ini
[koresent]
SigLevel = Optional TrustAll
Server = https://cachy.koresent.dev/$arch
```

### 2. Sync and Install
```bash
sudo pacman -Syu
sudo pacman -S <package-name>
```

---

## 🛠️ How to Add a New Package

1. Create a directory under `packages/<package-name>/`.
2. Add a standard Arch/CachyOS `PKGBUILD` and any bundled assets (`.desktop`, icons, `.service`):
   ```text
   packages/
   └── my-tool/
       ├── PKGBUILD
       ├── my-tool.desktop
       └── my-tool.svg
   ```
3. Commit and push to the `main` branch:
   ```bash
   git add packages/my-tool
   git commit -m "feat: add my-tool package"
   git push origin main
   ```
4. **GitHub Actions** will automatically:
   - Build the package in a clean Arch Linux container (`makepkg`).
   - Add it to `koresent.db.tar.gz` using `repo-add`.
   - Update `index.html`.
   - Deploy everything to **GitHub Pages**.

---

## 💻 Local Testing & Building

You can build the entire repository locally at any time:

```bash
./scripts/build.sh
```

All built `.pkg.tar.zst` packages, the database, and `index.html` will be placed in `public/`.
