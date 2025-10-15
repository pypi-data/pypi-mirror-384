#!/usr/bin/bash

###
# VARIABLES
###

OUTFN=ca_certs.pem
TS=$( date +%Y-%m-%dT%H:%M:%S )
TMP1=$( mktemp )
TMP2=$( mktemp )
# ANSI escape codes for colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'  # No Color


###
# FUNCTIONS
###
err() {
  echo -e "${RED}✗ ERROR: $*${NC}" #| tee /dev/stderr
}
 
success() {
  echo -e "${GREEN}✓ $*${NC}" #| tee /dev/stderr
}
 
 
die() {
  err "$*"
  echo "from (${BASH_SOURCE[1]} [${BASH_LINENO[0]}] ${FUNCNAME[1]})"
  kill 0
  exit 99
}

ask_yes_no() {
  local rv=1
  local msg="Is this ok?"
  [[ -n "$1" ]] && msg="$1"
  echo "$msg"
  select yn in "Yes" "No"; do
    case $yn in
      Yes) rv=0;;
      No ) rv=1;;
    esac
    break
  done
  return $rv
}


ask_pem_files() {
  local _sources=( $( ls *.pem ) )
  local _pem_list=()
  oldPS3="$PS3"
  PS3="Choose pem file to include, or quit? "
  select fn in 'quit' "${_sources[@]}" ; do
    case $fn in
      (quit) break ;;
      (*) _pem_list+=( "$fn" ) ;;
    esac
  done
  PS3="$oldPS3"
  echo "${_pem_list[@]}"
}


ask_new_or_append() {
  ask_yes_no "Make new '$OUTFN'? (If \"No\", just append to it)" \
  && bkup_fn "$OUTFN"
  
}


bkup_fn() {
  [[ -n "$1" ]] && mv "$1" "$1".$TS
}


###
# MAIN
###

if [[ $# -gt 0 ]] ; then
  # If cmdline args provided, assume they are pem files to create a new $OUTFN
  : >"$OUTFN"
  pem_list=( "${@}" )
else
  # No cmdline args, prompt user for each step
  ask_new_or_append
  pem_list=( $( ask_pem_files ) )
fi
# check input files are valid pem certs
for f in "${pem_list[@]}"; do
	openssl x509 -in "$f" -noout || die "Not a cert file: '$f'"
done
cat "${pem_list[@]}" >> "$OUTFN"

# remove any exising comments
sed -i -e '/^#/d' "$OUTFN"

# add info for each cert
while openssl x509 -subject -enddate; do : ; done <"$OUTFN" 2>$TMP2 \
| sed \
    -e 's/^subject=/# &/' \
    -e 's/^notAfter=/# &/' 1>$TMP1 2>$TMP2
mv $TMP1 "$OUTFN"
# check if any errors happened (expect two lines from "while openssl")
num_lines=$(wc -l $TMP2 | awk '{print $1}')
[[ $num_lines -gt 2 ]] && { # (ignore two expected lines from "while openssl")
  echo "Errors detected:"
  cat $TMP2
}
rm $TMP2
