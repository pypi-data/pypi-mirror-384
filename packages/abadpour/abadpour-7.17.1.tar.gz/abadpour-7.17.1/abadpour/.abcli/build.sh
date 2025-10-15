#! /usr/bin/env bash

function abadpour_build() {
    local options=$1
    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)
    local do_push=$(bluer_ai_option_int "$options" push 0)
    local do_rm=$(bluer_ai_option_int "$options" rm 1)
    local what=$(bluer_ai_option "$options" what cv+cv-full)

    local latex_options=$2

    bluer_ai_log "building $what ..."

    pushd $(python3 -m abadpour locate)/../src >/dev/null

    python3 -m abadpour build

    local filename
    local public_filename
    for filename in $(echo $what | tr + " "); do
        bluer_ai_latex build dryrun=$do_dryrun,$latex_options \
            ./$filename.tex
        [[ $? -ne 0 ]] && return 1

        public_filename=arash-abadpour-resume
        [[ "$filename" == *"full"* ]] && public_filename=$public_filename-full

        cp -v $filename.pdf \
            $abcli_path_git/abadpour/pdf/$public_filename.pdf

        [[ "$do_rm" == 1 ]] && rm -v $filename.pdf
    done

    popd >/dev/null

    [[ "$do_push" == 1 ]] &&
        bluer_ai_git \
            abadpour \
            push \
            "rebuild"

    return 0
}
