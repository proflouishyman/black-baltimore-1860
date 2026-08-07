#!/bin/bash
# Environment for scripting the Homebrew-cask QGIS on this Mac.
#
# The cask installs QGIS as an app bundle that does not export its data paths,
# so both `qgis_process` and `pyqgis` fail out of the box: qgis_process prints
# "Cannot find proj.db" on every run, and `import qgis.core` aborts outright.
# Sourcing this file fixes both by pointing PROJ/GDAL/QGIS at the bundle.
#
# Usage (works in bash and zsh):
#   source scripts/qgis_env.sh
#   qgis_process --version
#   qgis_python -c "import qgis.core; print(qgis.core.Qgis.QGIS_VERSION)"
#
# Shell functions are used rather than aliases: aliases are not expanded in
# non-interactive shells, so `bash -c 'source ...; qgis_process'` would fail.
# The bundle name carries its version, so bump QGIS_APP after a QGIS upgrade.

QGIS_APP="/Applications/QGIS-final-4_2_1.app"
QGIS_CONTENTS="$QGIS_APP/Contents"
QGIS_RES="$QGIS_CONTENTS/Resources/qgis"

if [ ! -d "$QGIS_RES" ]; then
    echo "qgis_env.sh: QGIS not found at $QGIS_APP - update QGIS_APP" >&2
else
    export QGIS_PREFIX_PATH="$QGIS_RES"
    export PROJ_LIB="$QGIS_RES/proj"
    export GDAL_DATA="$QGIS_RES/gdal"
    export PYTHONPATH="$QGIS_RES/python${PYTHONPATH:+:$PYTHONPATH}"

    # QGIS ships its own python3.12; the project .venv python cannot import qgis.
    qgis_process() { "$QGIS_CONTENTS/MacOS/qgis_process" "$@"; }
    qgis_python()  { "$QGIS_CONTENTS/MacOS/python3.12" "$@"; }
fi

# Resolve the project root without BASH_SOURCE, which is empty under zsh.
if [ -n "$BASH_SOURCE" ]; then
    _qe_self="$BASH_SOURCE"
elif [ -n "$ZSH_VERSION" ]; then
    _qe_self="${(%):-%x}"
else
    _qe_self="$0"
fi
BALT_ROOT="$(cd "$(dirname "$_qe_self")/.." && pwd)"
unset _qe_self

# The project venv interpreter for everything that is NOT pyqgis: geopandas,
# shapely and pyproj live there and are the default for this project.
export BALT_ROOT
export BALT_PY="$BALT_ROOT/.venv/bin/python"
