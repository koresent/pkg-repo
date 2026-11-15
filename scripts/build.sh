#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="${REPO_NAME:-koresent}"
ARCH="${ARCH:-x86_64}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUBLIC_DIR="${ROOT_DIR}/public"
ARCH_DIR="${PUBLIC_DIR}/${ARCH}"
REMOTE_REPO_URL="${REMOTE_REPO_URL:-https://cachy.koresent.dev/${ARCH}}"
FORCE_REBUILD="${FORCE_REBUILD:-0}"

if [[ $EUID -eq 0 ]]; then
    if ! id -u builder &>/dev/null; then
        useradd -m -G wheel builder
        echo "builder ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
    fi
    git config --global --add safe.directory "${ROOT_DIR}" || true
    chown -R builder:builder "${ROOT_DIR}"
    exec sudo -u builder --preserve-env=REPO_NAME,ARCH,FORCE_REBUILD,REMOTE_REPO_URL bash "$0" "$@"
fi

MAKEPKG_FLAGS=("-f" "--noconfirm" "-d")

echo "Building Pacman repository: [${REPO_NAME}] for ${ARCH}"
mkdir -p "${ARCH_DIR}"

for pkg_dir in "${ROOT_DIR}"/packages/*; do
    if [[ ! -d "${pkg_dir}" || ! -f "${pkg_dir}/PKGBUILD" ]]; then
        continue
    fi
    pkg_name="$(basename "${pkg_dir}")"
    echo "Packaging: ${pkg_name}"
    
    (
        cd "${pkg_dir}"
        expected_pkg=""
        if command -v makepkg >/dev/null 2>&1; then
            expected_pkg="$(basename "$(makepkg --packagelist 2>/dev/null | head -n1 || true)")"
        fi

        if [[ -n "${expected_pkg}" && -f "${ARCH_DIR}/${expected_pkg}" && "${FORCE_REBUILD}" != "1" ]]; then
            echo "-> Already present in ${ARCH_DIR}: ${expected_pkg}"
        elif [[ -n "${expected_pkg}" && "${FORCE_REBUILD}" != "1" ]] && curl -sfI "${REMOTE_REPO_URL}/${expected_pkg}" >/dev/null 2>&1; then
            echo "-> Fetching prebuilt ${expected_pkg} from ${REMOTE_REPO_URL}..."
            curl -sfL "${REMOTE_REPO_URL}/${expected_pkg}" -o "${ARCH_DIR}/${expected_pkg}"
        else
            echo "-> Building ${pkg_name}..."
            makepkg "${MAKEPKG_FLAGS[@]}"
            mv -f ./*.pkg.tar.zst "${ARCH_DIR}/"
            rm -rf src pkg
        fi
    )
done

shopt -s nullglob
pkgs=("${ARCH_DIR}"/*.pkg.tar.zst)
if [[ ${#pkgs[@]} -eq 0 ]]; then
    echo "Error: No packages built in ${ARCH_DIR}" >&2
    exit 1
fi

echo "Updating database via repo-add..."
cd "${ARCH_DIR}"
repo-add -n -R "${REPO_NAME}.db.tar.gz" ./*.pkg.tar.zst

rm -f "${REPO_NAME}.db" "${REPO_NAME}.files"
cp -f "${REPO_NAME}.db.tar.gz" "${REPO_NAME}.db"
cp -f "${REPO_NAME}.files.tar.gz" "${REPO_NAME}.files"

touch "${PUBLIC_DIR}/.nojekyll"
echo "cachy.koresent.dev" > "${PUBLIC_DIR}/CNAME"

echo "Generating package index..."
cd "${ROOT_DIR}"
python3 scripts/generate-index.py

echo "Build complete: ${PUBLIC_DIR}"
ls -lh "${ARCH_DIR}"
