#!/bin/bash

get_hash_status() {
  local name="$1"
  local with_remote_name="${2:-0}"
  HASH=$(git rev-parse --short HEAD)
  [ -n "$(git status --porcelain=v1)" ] && STATUS="dirty" || STATUS="clean"
  if [ $with_remote_name -eq 1 ]; then
    remote_name=$( basename -s .git $(git remote get-url origin) )
    echo "$name ($remote_name) $HASH-$STATUS"
  else
    echo "$name $HASH-$STATUS"
  fi
}
export -f get_hash_status

current_dir="${PWD##*/}"
SUPER_STATUS_CAPTURE=$( get_hash_status "$current_dir" 1 )
SUBMOD_STATUS_CAPTURE=$( git submodule foreach --quiet --recursive 'get_hash_status "$name"' )

if [[ -z "$SUBMOD_STATUS_CAPTURE" ]]; then
    SUMMARY=$SUPER_STATUS_CAPTURE
else
    sep=" | "
    RESULT_FORMATTED="${SUBMOD_STATUS_CAPTURE//$'\n'/$sep}"
    SUMMARY="$SUPER_STATUS_CAPTURE $sep $RESULT_FORMATTED"
fi

echo $SUMMARY
