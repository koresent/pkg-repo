#!/usr/bin/env bash
set -eu

say_error() {
    printf '%s\n' "$1" >&2
    if [ ! -t 2 ]; then
        if command -v zenity >/dev/null 2>&1; then
            zenity --error --no-markup --title="Antigravity Unlocker" --text="$1" 2>/dev/null
        elif command -v kdialog >/dev/null 2>&1; then
            kdialog --error "$1" 2>/dev/null
        elif command -v xmessage >/dev/null 2>&1; then
            xmessage -center "$1" 2>/dev/null
        fi
    fi
}

if [ "$(id -u)" -eq 0 ] && [ -n "${SUDO_USER:-}" ]; then
    say_error "Запускайте без sudo. Программа работает от обычного пользователя."
    exit 1
fi

BIN="/usr/lib/antigravity-unlocker/ag_unlocker"

if [ ! -x "$BIN" ]; then
    say_error "Не найден исполняемый файл: $BIN"
    exit 1
fi

if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    if [ -t 0 ] && [ -t 1 ]; then
        exec "$BIN" --tui "$@"
    fi
    say_error "Нет графической сессии (не заданы DISPLAY и WAYLAND_DISPLAY). Запустите из терминала с флагом --tui."
    exit 1
fi

exec "$BIN" "$@"
