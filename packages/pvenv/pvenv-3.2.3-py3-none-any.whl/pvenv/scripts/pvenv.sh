function venv {
    case "$1" in
    in)
        invenv "${@:2}"
        ;;
    out)
        outvenv "${@:2}"
        ;;
    activate)
        avenv "${@:2}"
        ;;
    deactivate)
        dvenv "${@:2}"
        ;;
    list)
        lsvenv "${@:2}"
        ;;
    make)
        mkvenv "${@:2}"
        ;;
    rm)
        rmvenv "${@:2}"
        ;;
    *)
        pvenv "$@"
        return
        ;;
    esac
}

function invenv {
    local LC_TYPE=C
    local IFS=$'\n'
    for command in $(pvenv in "$@"); do
        local first_char=$(printf '%d' "'${command:0:1}")
        if [[ "${first_char}" == 2 ]]; then
            eval "${command:1}"
        else
            echo "${command}"
        fi
    done
}

function outvenv {
    local LC_TYPE=C
    local IFS=$'\n'
    for command in $(pvenv out); do
        local first_char=$(printf '%d' "'${command:0:1}")
        if [[ "${first_char}" == 2 ]]; then
            eval "${command:1}"
        else
            echo "${command}"
        fi
    done
}

function avenv {
    local LC_TYPE=C
    local IFS=$'\n'
    for command in $(pvenv activate "$@"); do
        local first_char=$(printf '%d' "'${command:0:1}")
        if [[ "${first_char}" == 2 ]]; then
            eval "${command:1}"
        else
            echo "${command}"
        fi
    done
}

function dvenv {
    local LC_TYPE=C
    local IFS=$'\n'
    for command in $(pvenv deactivate "$@"); do
        local first_char=$(printf '%d' "'${command:0:1}")
        if [[ "${first_char}" == 2 ]]; then
            eval "${command:1}"
        else
            echo "${command}"
        fi
    done
}

function lsvenv {
    pvenv list "$@"
}

function mkvenv {
    local LC_TYPE=C
    local IFS=$'\n'
    for command in $(pvenv make "$@"); do
        local first_char=$(printf '%d' "'${command:0:1}")
        if [[ "${first_char}" == 2 ]]; then
            eval "${command:1}"
        else
            echo "${command}"
        fi
    done
}

function rmvenv {
    pvenv rm "$@"
}
