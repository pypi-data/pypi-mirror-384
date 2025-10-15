#!/bin/bash

INSTALL_DIR=___INSTALL_DIR___

. ${INSTALL_DIR}/etc/shell.conf


###
# Some Useful FUNCTIONS
###

err() {
	echo -e "${RED}✗ ERROR: $*${NC}"
}

success() {
  echo -e "${GREEN}✓ $*${NC}"
}


log() {
  [[ $VERBOSE -eq $YES ]] || return 0
  echo "INFO $*" >&2
}


die() {
  err "$*"
  echo "from (${BASH_SOURCE[1]} [${BASH_LINENO[0]}] ${FUNCNAME[1]})"
  kill 0
  exit 99
}


ask_user() {
  # INPUT
  #   $1 prompt
  # OUTPUT
  #   user response as text string
  local _msg="$1"
  [[ -z "$_msg" ]] && die "missing prompt in ask_user()"
  read -r -p "$_msg"
  echo "$REPLY"
}


ask_yes_no() {
  local rv=$NO
  local msg="Is this ok?"
  [[ -n "$1" ]] && msg="$1"
  echo "$msg"
  select yn in "Yes" "No"; do
    case $yn in
      Yes) rv=$YES;;
      No ) rv=$NO;;
    esac
    break
  done
  return $rv
}


# Function to print a green checkmark
print_green_checkmark() {
    echo -e "${GREEN}✓${NC}"
}

# Function to print a red "x"
print_red_x() {
    echo -e "${RED}✗${NC}"
}
