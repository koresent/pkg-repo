#!/usr/bin/env bash
# ==============================================================================
# Build Arch Linux packages and update Pacman repository database
# ==============================================================================
set -euo pipefail

REPO_NAME="${REPO_NAME:-koresent}"
ARCH="${ARCH:-x86_64}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUBLIC_DIR="${ROOT_DIR}/public"
ARCH_DIR="${PUBLIC_DIR}/${ARCH}"

# If running as root (e.g. inside Docker container in CI), switch to builder user
if [[ $EUID -eq 0 ]]; then
    if ! id -u builder &>/dev/null; then
        useradd -m -G wheel builder
        echo "builder ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
    fi
    git config --global --add safe.directory "${ROOT_DIR}" || true
    chown -R builder:builder "${ROOT_DIR}"
    exec sudo -u builder --preserve-env=REPO_NAME,ARCH bash "$0" "$@"
fi

MAKEPKG_FLAGS=("-f" "--noconfirm")
if [[ "${CI:-}" == "true" ]]; then
    MAKEPKG_FLAGS=("-s" "${MAKEPKG_FLAGS[@]}")
fi

echo "==> Building Pacman repository: [${REPO_NAME}] for ${ARCH}"
mkdir -p "${ARCH_DIR}"

# Build all packages under packages/
for pkg_dir in "${ROOT_DIR}"/packages/*; do
    if [[ ! -d "${pkg_dir}" || ! -f "${pkg_dir}/PKGBUILD" ]]; then
        continue
    fi
    pkg_name="$(basename "${pkg_dir}")"
    echo "--> Packaging: ${pkg_name}"
    
    (
        cd "${pkg_dir}"
        makepkg "${MAKEPKG_FLAGS[@]}"
        mv -f ./*.pkg.tar.zst "${ARCH_DIR}/"
        # Clean up temporary makepkg dirs
        rm -rf src pkg
    )
done

# Check if we have packages to index
shopt -s nullglob
pkgs=("${ARCH_DIR}"/*.pkg.tar.zst)
if [[ ${#pkgs[@]} -eq 0 ]]; then
    echo "ERROR: No packages were built in ${ARCH_DIR}" >&2
    exit 1
fi

echo "==> Updating database with repo-add..."
cd "${ARCH_DIR}"
repo-add -n -R "${REPO_NAME}.db.tar.gz" ./*.pkg.tar.zst

# Replace symlinks created by repo-add with real files for CDNs/Pages
rm -f "${REPO_NAME}.db" "${REPO_NAME}.files"
cp -f "${REPO_NAME}.db.tar.gz" "${REPO_NAME}.db"
cp -f "${REPO_NAME}.files.tar.gz" "${REPO_NAME}.files"

# Prevent GitHub Pages from ignoring files and set custom domain
touch "${PUBLIC_DIR}/.nojekyll"
echo "cachy.koresent.dev" > "${PUBLIC_DIR}/CNAME"

# Generate index.html
echo "==> Generating HTML landing page..."
cd "${ROOT_DIR}"
python3 scripts/generate-index.py

echo "==> Repository build complete in ${PUBLIC_DIR}"
ls -lh "${ARCH_DIR}"
