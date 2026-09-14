#!/data/data/com.termux/files/usr/bin/bash
set -eu
cd -- "$(dirname -- "$0")"
pkg install python openssh -y
python -m pip install -r requirements-termux.txt
mkdir -p "$PREFIX/bin"
if [ -e "$PREFIX/bin/omega" ]; then
    cp "$PREFIX/bin/omega" "$PREFIX/bin/omega.backup-$(date +%Y%m%d-%H%M%S)"
fi
printf '#!/data/data/com.termux/files/usr/bin/bash\ncd -- %q\nexec python main.py "$@"\n' "$PWD" > "$PREFIX/bin/omega"
chmod 700 "$PREFIX/bin/omega"
echo 'Instalado. Use: omega, omega ligar pc ou omega desligar pc.'
