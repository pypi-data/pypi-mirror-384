#!/bin/bash

YES=0 #no touchee
NO=1  #no touchee


# ###
# User might want to change these, though should use environment vars
# ###
INSTALL_DIR="${IPF_INSTALL_DIR:-$HOME/ipf}"
DEBUG=$YES
VERBOSE=$YES
# ###
# END OF USER CONFIGURABLE SECTION
# ###


# NO USER CHANGES AFTER THIS
VENV="$INSTALL_DIR"/.venv
V_PYTHON="$VENV"/bin/python
USER_CONF="$HOME"/.config/ipf
SYSTEM_PYTHON=
SITE_PACKAGES=
IPF_PATH=
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'  # No Color


err() {
	echo -e "${RED}✗ ERROR: $*${NC}"
}


success() {
  echo -e "${GREEN}✓ $*${NC}"
}


die() {
  err "$*"
  echo "from (${BASH_SOURCE[1]} [${BASH_LINENO[0]}] ${FUNCNAME[1]})"
  kill 0
  exit 99
}


log() {
  [[ $VERBOSE -eq $YES ]] || return 0
  echo "INFO $*" >&2
}


debug() {
  [[ $DEBUG -eq $YES ]] || return 0
  echo "DEBUG (${BASH_SOURCE[1]} [${BASH_LINENO[0]}] ${FUNCNAME[1]}) $*"
}


get_system_python() {
  SYSTEM_PYTHON=$(which python3) 2>/dev/null
  [[ -z "$SYSTEM_PYTHON" ]] && {
    SYSTEM_PYTHON=$IPF_PYTHON_TO_USE
  }
  [[ -z "$SYSTEM_PYTHON" ]] && die "Unable to find Python on this system."
  success "Found system python at '$SYSTEM_PYTHON'"
}


mk_venv() {
  [[ $DEBUG -eq $YES ]] && set -x
  [[ -d "$VENV" ]] || {
    "$SYSTEM_PYTHON" -m venv "$VENV"
    success "Python venv created at '$VENV'"
    "${V_PYTHON}" -m pip install --upgrade pip
  }
  SITE_PACKAGES=$(
    "$V_PYTHON" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])'
  )
  IPF_PATH="$SITE_PACKAGES"/ipf
}


is_pre_release_allowed() {
  [[ $DEBUG -eq $YES ]] && set -x
  local _retval=$NO
  if [[  "$IPF_ALLOW_PRE_RELEASE" == "yes" \
      || "$IPF_ALLOW_PRE_RELEASE" == "YES" \
      || "$IPF_ALLOW_PRE_RELEASE" == "Y" \
      || "$IPF_ALLOW_PRE_RELEASE" == "y" \
      || "$IPF_ALLOW_PRE_RELEASE" -eq 1
     ]] ; then
     _retval=$YES
   fi
  return $_retval
}


install_ipf_pre_release() {
  [[ $DEBUG -eq $YES ]] && set -x
  "${V_PYTHON}" -m pip install \
    --upgrade \
    --no-cache-dir \
    --pre \
    --no-deps \
    --index-url https://test.pypi.org/simple/ \
    ipf \
    && success "Installed dev version of ipf"
}


install_ipf() {
  [[ $DEBUG -eq $YES ]] && set -x
  "${V_PYTHON}" -m pip install \
    --upgrade \
    ipf \
    && success "Ipf and dependencies installed"
}


update_files() {
  [[ $DEBUG -eq $YES ]] && set -x
  # Update any files that need INSTALL_DIR
  local _pattern='___INSTALL_DIR___'
  local _replacement="$INSTALL_DIR"
  grep -r --files-with-matches -F "$_pattern" "$IPF_PATH" \
  | while read; do
      sed -i -e "s?$_pattern?$_replacement?" "$REPLY"
    done
}


mk_symlinks() {
  [[ $DEBUG -eq $YES ]] && set -x
  pushd "$INSTALL_DIR"
  local _symlink_dirs=( bin etc configure lib var )
  for d in "${_symlink_dirs[@]}"; do
    [[ -L $d ]] || ln -s "$IPF_PATH"/$d
  done
  popd
}


restore_config_links() {
  [[ $DEBUG -eq $YES ]] && set -x
  /bin/bash "$INSTALL_DIR"/bin/save_configs.sh
}


[[ $DEBUG -eq $YES ]] && set -x

get_system_python

mk_venv

# installs ipf pre-release (only ipf, no deps)
is_pre_release_allowed && install_ipf_pre_release

install_ipf  #installs deps (and ipf if not done above)

update_files

mk_symlinks

restore_config_links
