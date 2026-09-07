#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/mikis13-evolution-engine"
LAB="$ROOT/state/language-lab"

rm -rf "$LAB"
mkdir -p "$LAB"

echo "===== PYTHON ====="

if command -v python >/dev/null; then
cat > "$LAB/hello.py" <<'PY'
print("Hello World from Mikis13 Python Worker")
PY
python "$LAB/hello.py"
fi

echo
echo "===== JAVASCRIPT ====="

if command -v node >/dev/null; then
cat > "$LAB/hello.js" <<'JS'
console.log("Hello World from Mikis13 JavaScript Worker");
JS
node "$LAB/hello.js"
fi

echo
echo "===== GO ====="

if command -v go >/dev/null; then
cat > "$LAB/hello.go" <<'GO'
package main

import "fmt"

func main() {
    fmt.Println("Hello World from Mikis13 Go Worker")
}
GO
go run "$LAB/hello.go"
fi

echo
echo "===== RUST ====="

if command -v rustc >/dev/null; then
cat > "$LAB/hello.rs" <<'RS'
fn main() {
    println!("Hello World from Mikis13 Rust Worker");
}
RS

rustc \
  "$LAB/hello.rs" \
  -o "$LAB/hello-rust"

"$LAB/hello-rust"
fi

echo
echo "===== JAVA ====="

if command -v javac >/dev/null; then
cat > "$LAB/HelloMikis.java" <<'JAVA'
public class HelloMikis {
    public static void main(String[] args) {
        System.out.println(
            "Hello World from Mikis13 Java Worker"
        );
    }
}
JAVA

(
  cd "$LAB" &&
  javac HelloMikis.java &&
  java HelloMikis
)
fi

echo
echo "===== C ====="

if command -v clang >/dev/null; then
cat > "$LAB/hello.c" <<'C'
#include <stdio.h>

int main(void) {
    puts("Hello World from Mikis13 C Worker");
    return 0;
}
C

clang \
  "$LAB/hello.c" \
  -o "$LAB/hello-c"

"$LAB/hello-c"
fi

echo
echo "===== C++ ====="

if command -v clang++ >/dev/null; then
cat > "$LAB/hello.cpp" <<'CPP'
#include <iostream>

int main() {
    std::cout
      << "Hello World from Mikis13 C++ Worker"
      << std::endl;

    return 0;
}
CPP

clang++ \
  "$LAB/hello.cpp" \
  -o "$LAB/hello-cpp"

"$LAB/hello-cpp"
fi

echo
echo "===== PHP ====="

if command -v php >/dev/null; then
php -r \
 'echo "Hello World from Mikis13 PHP Worker\n";'
fi

echo
echo "===== RUBY ====="

if command -v ruby >/dev/null; then
ruby -e \
 'puts "Hello World from Mikis13 Ruby Worker"'
fi

echo
echo "===== LUA ====="

if command -v lua >/dev/null; then
lua -e \
 'print("Hello World from Mikis13 Lua Worker")'
fi

echo
echo "===== PERL ====="

if command -v perl >/dev/null; then
perl -e \
 'print "Hello World from Mikis13 Perl Worker\n";'
fi

echo
echo "✅ Language lab klaar"
