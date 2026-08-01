#!/bin/zsh
# Source this file to set PYTHON_BIN to a supported local interpreter.
set -euo pipefail

python_is_supported() {
  local candidate="$1"
  [[ -x "$candidate" ]] || return 1
  "$candidate" -c 'import sys; raise SystemExit(0 if (3, 11) <= sys.version_info[:2] < (3, 15) else 1)' >/dev/null 2>&1
}

if [[ -n "${PYTHON_BIN:-}" ]]; then
  if ! python_is_supported "$PYTHON_BIN"; then
    print -u2 "PYTHON_BIN must point to Python 3.11 through 3.14: $PYTHON_BIN"
    return 1 2>/dev/null || exit 1
  fi
else
  for version in 3.14 3.13 3.12 3.11; do
    if command -v "python$version" >/dev/null 2>&1 && python_is_supported "$(command -v "python$version")"; then
      PYTHON_BIN="$(command -v "python$version")"; break
    fi
  done
  if [[ -z "${PYTHON_BIN:-}" ]] && command -v brew >/dev/null 2>&1; then
    for version in 3.14 3.13 3.12 3.11; do
      brew_prefix="$(brew --prefix "python@$version" 2>/dev/null || true)"
      brew_python="$brew_prefix/bin/python$version"
      if python_is_supported "$brew_python"; then PYTHON_BIN="$brew_python"; break; fi
    done
  fi
  if [[ -z "${PYTHON_BIN:-}" ]] && command -v python3 >/dev/null 2>&1 && python_is_supported "$(command -v python3)"; then
    PYTHON_BIN="$(command -v python3)"
  fi
  if [[ -z "${PYTHON_BIN:-}" ]]; then
    print -u2 'Python 3.11–3.14 is required. Install it with: brew install python@3.14'
    print -u2 'Then rerun this command, or set PYTHON_BIN to its executable path.'
    return 1 2>/dev/null || exit 1
  fi
fi

export PYTHON_BIN
