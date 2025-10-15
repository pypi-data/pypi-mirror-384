#! /usr/bin/env bash

function abadpour_clean() {
    pushd $(python3 -m abadpour locate)/../src >/dev/null
    rm *.aux
    rm *.dvi
    rm *.log
    rm *.out
    rm *.ps
    popd >/dev/null
}
