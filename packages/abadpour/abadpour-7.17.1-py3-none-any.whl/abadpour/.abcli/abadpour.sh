#! /usr/bin/env bash

function abadpour() {
    local task=${1:-version}

    bluer_ai_generic_task \
        plugin=abadpour,task=$task \
        "${@:2}"
}

bluer_ai_log $(abadpour version --show_icon 1)
