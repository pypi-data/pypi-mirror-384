#! /usr/bin/env bash

function test_abadpour_help() {
    local options=$1

    local module
    for module in \
        "abadpour build" \
        "abadpour clean" \
        \
        "abadpour"; do
        bluer_ai_eval ,$options \
            bluer_ai_help $module
        [[ $? -ne 0 ]] && return 1

        bluer_ai_hr
    done

    return 0
}
