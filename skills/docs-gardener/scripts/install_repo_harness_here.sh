#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install_repo_harness_here.sh [--dry-run] [--target PATH]

Install the docs-gardener repo harness into the current workspace.

Default target selection:
  1. git repository root, when the current directory is inside a git repo
  2. current working directory, when git root cannot be found

Options:
  --dry-run            Print planned changes without writing files.
  --target PATH        Install into PATH instead of auto-detecting the current workspace.
  -h, --help           Show this help.
EOF
}

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
installer="${script_dir}/install_repo_harness.py"

target=""
args=()

while (($#)); do
  case "$1" in
    --target)
      if (($# < 2)); then
        echo "error: --target requires a path" >&2
        exit 2
      fi
      target="$2"
      shift 2
      ;;
    --dry-run)
      args+=("$1")
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${target}" ]]; then
  if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    target="${git_root}"
  else
    target="${PWD}"
  fi
fi

echo "installing repo harness into: ${target}"
exec python3 "${installer}" "${target}" "${args[@]}"
