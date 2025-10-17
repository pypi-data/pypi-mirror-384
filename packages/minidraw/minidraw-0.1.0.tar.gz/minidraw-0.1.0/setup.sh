# commadn line arguments
CLEAN=false
while [[ $# -gt 0 ]]; do
  case $1 in
    -c|--clean)
      CLEAN=true
      shift
      ;;
  esac
done

# Path to workspace directory
if test -n "$ZSH_VERSION"; then
  export MINIDRAW_WS_PATH="${0:A:h}"
elif test -n "$BASH_VERSION"; then
  export MINIDRAW_WS_PATH=$(realpath $(dirname "$BASH_SOURCE"))
fi

export MINIDRAW_VENV="$MINIDRAW_WS_PATH/.venv"

# create if needed and source virtual environment
if [ ! -d "$MINIDRAW_VENV"  ] || [ "$CLEAN" = true ]; then
  rm -rf $MINIDRAW_VENV
  uv venv $MINIDRAW_VENV || { echo "Failed to create virtual environment" >&2; exit 1; }
  source $MINIDRAW_VENV/bin/activate

  uv pip install ipython
  uv pip install -e $MINIDRAW_WS_PATH
else
  source $MINIDRAW_VENV/bin/activate
fi
