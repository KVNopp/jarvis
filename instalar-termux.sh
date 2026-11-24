#!/data/data/com.termux/files/usr/bin/bash
# Instala ou atualiza o Omega no Termux. Pode rodar de novo sem perder o .env.
set -eu
cd -- "$(dirname -- "$0")"
pkg install python openssh git -y
python -m pip install -r requirements-termux.txt
if [ ! -e .env ]; then
    cp .env.example .env
    chmod 600 .env
    echo 'Criado o arquivo .env a partir do .env.example.'
fi
mkdir -p "$PREFIX/bin"
if [ -e "$PREFIX/bin/omega" ]; then
    cp "$PREFIX/bin/omega" "$PREFIX/bin/omega.backup-$(date +%Y%m%d-%H%M%S)"
fi
printf '#!/data/data/com.termux/files/usr/bin/bash\ncd -- %q\nif [ "${1:-}" = atualizar ]; then\n    git pull --ff-only && exec bash instalar-termux.sh\nfi\nexec python main.py "$@"\n' "$PWD" > "$PREFIX/bin/omega"
chmod 700 "$PREFIX/bin/omega"
echo
echo 'Omega instalado. Próximos passos:'
echo '  nano .env               preencher LIFEOS_SUPABASE_URL e LIFEOS_SUPABASE_KEY'
echo '  omega /lifeos entrar    entrar na conta do LIFE OS'
echo '  omega /hoje             ver o dia'
echo '  omega atualizar         baixar a versão nova do GitHub'
