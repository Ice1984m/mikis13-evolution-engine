#!/data/data/com.termux/files/usr/bin/bash

echo "=============================================="
echo " MIKIS13 PROGRAMMING LANGUAGE LAB"
echo "=============================================="

check() {
    local name="$1"
    local cmd="$2"
    local version="$3"

    if command -v "$cmd" >/dev/null 2>&1; then
        printf "✅ %-14s " "$name"
        eval "$version" 2>/dev/null | head -n1
    else
        printf "❌ %s ontbreekt\n" "$name"
    fi
}

check "Python"     python  'python --version'
check "JavaScript" node    'node --version'
check "npm"        npm     'npm --version'
check "Go"         go      'go version'
check "Rust"       rustc   'rustc --version'
check "Cargo"      cargo   'cargo --version'
check "Java"       java    'java -version'
check "Javac"      javac   'javac -version'
check "C/C++"      clang   'clang --version'
check "PHP"        php     'php --version'
check "Ruby"       ruby    'ruby --version'
check "Lua"        lua     'lua -v'
check "Perl"       perl    'perl -v'
check "SQLite"     sqlite3 'sqlite3 --version'
check "Git"        git     'git --version'
check "GitHub CLI" gh      'gh --version'
check "TGPT"       tgpt    'tgpt --version'
