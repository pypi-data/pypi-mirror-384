#! /usr/bin/env bash

function test_bluer_ugv_help() {
    local options=$1

    local module
    for module in \
        "@swallow" \
        "@swallow dataset" \
        "@swallow dataset combine" \
        "@swallow dataset download" \
        "@swallow dataset edit" \
        "@swallow dataset list" \
        "@swallow dataset upload" \
        \
        "@swallow env" \
        "@swallow env cp" \
        "@swallow env list" \
        "@swallow env set" \
        \
        "@swallow debug" \
        "@swallow select_target" \
        \
        "@swallow ultrasonic" \
        "@swallow ultrasonic review" \
        "@swallow ultrasonic test" \
        \
        "@ugv" \
        \
        "@ugv git" \
        \
        "@ugv pypi" \
        "@ugv pypi browse" \
        "@ugv pypi build" \
        "@ugv pypi install" \
        \
        "@ugv pytest" \
        \
        "@ugv test" \
        "@ugv test list" \
        \
        "bluer_ugv"; do
        bluer_ai_eval ,$options \
            bluer_ai_help $module
        [[ $? -ne 0 ]] && return 1

        bluer_ai_hr
    done

    return 0
}
