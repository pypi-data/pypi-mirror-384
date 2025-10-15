#!/bin/bash

INSTALL_DIR=___INSTALL_DIR___
. ${INSTALL_DIR}/lib/utils.sh

ETC="$INSTALL_DIR"/etc
CONF="$HOME"/.config/ipf


backup_configs() {
  [[ $DEBUG -eq $YES ]] && set -x
  mkdir -p "$CONF"
  local _config_list=(
    $( find "$ETC" -maxdepth 1 -type f -name 'configure*.conf' )
    $( find "$ETC" -maxdepth 1 -type f -name 'amqp.conf' )
  )
  for fname in "${_config_list[@]}"; do
    rsync --backup --suffix="$TS" --checksum "$fname" "$CONF"/
  done
}


mk_symlinks() {
  [[ $DEBUG -eq $YES ]] && set -x
  local _config_list=(
    $( find "$CONF" -maxdepth 1 -type f -name '*.conf' )
  )
  for src in "${_config_list[@]}"; do
    fn=$( basename "$src" )
    tgt="$ETC"/"$fn"
    ln -sf "$src" "$tgt"
  done
}


[[ $DEBUG -eq $YES ]] && set -x

backup_configs

mk_symlinks
