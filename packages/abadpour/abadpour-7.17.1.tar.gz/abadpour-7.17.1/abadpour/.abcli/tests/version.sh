#! /usr/bin/env bash

function test_abadpour_version() {
    local options=$1

    bluer_ai_eval ,$options \
        "abadpour version ${@:2}"

    return 0
}
