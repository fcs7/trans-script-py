#!/usr/bin/env python3
"""
Script de tradução EN → PT-BR para arquivos PHP de localização.
Usa translate-shell (trans) para traduzir os valores de $msg_arr.
Suporta resume: se interrompido, continua de onde parou.

Uso:
  python3 translate.py --dir-in ./en --dir-out ./br
  python3 translate.py --dir-in /caminho/entrada --dir-out /caminho/saida --delay 0.3
"""

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import time

# === Configuração padrão ===
SOURCE_LANG = 'en'
TARGET_LANG = 'pt-br'
DEFAULT_DELAY = 0.5

# === Regex ===
SINGLE_QUOTE_RE = re.compile(
    r"^(\$msg_arr\[.*?\]\s*=\s*')((?:[^'\\]|\\.)*)(';\s*;?\s*)$"
)
DOUBLE_QUOTE_RE = re.compile(
    r'^(\$msg_arr\[.*?\]\s*=\s*")((?:[^"\\]|\\.)*)(";?\s*;?\s*)$'
)
PLACEHOLDER_RE = re.compile(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}')


# =============================================================================
# Detecção de sistema e auto-instalação do translate-shell
# =============================================================================

def detect_pkg_manager():
    """Detecta o gerenciador de pacotes do sistema."""
    managers = [
        ('apt',    ['sudo', 'apt', 'install', '-y', 'translate-shell']),
        ('dnf',    ['sudo', 'dnf', 'install', '-y', 'translate-shell']),
        ('yum',    ['sudo', 'yum', 'install', '-y', 'translate-shell']),
        ('pacman', ['sudo', 'pacman', '-S', '--noconfirm', 'translate-shell']),
        ('zypper', ['sudo', 'zypper', 'install', '-y', 'translate-shell']),
        ('brew',   ['brew', 'install', 'translate-shell']),
    ]
    for name, cmd in managers:
        if shutil.which(name):
            return name, cmd
    return None, None


def install_trans():
    """Instala translate-shell automaticamente de acordo com o sistema."""
    pkg_name, install_cmd = detect_pkg_manager()

    if not pkg_name:
        print("ERRO: Não foi possível detectar o gerenciador de pacotes.")
        print("Instale o translate-shell manualmente:")
        print("  https://github.com/soimort/translate-shell")
        sys.exit(1)

    print(f"translate-shell não encontrado. Instalando via {pkg_name}...")
    print(f"  Executando: {' '.join(install_cmd)}")

    try:
        subprocess.run(install_cmd, check=True)
        print("translate-shell instalado com sucesso!")
    except subprocess.CalledProcessError:
        print(f"ERRO: Falha ao instalar via {pkg_name}.")
        print("Tente instalar manualmente:")
        print("  https://github.com/soimort/translate-shell")
        sys.exit(1)


def ensure_trans():
    """Garante que o comando 'trans' está disponível."""
    if shutil.which('trans'):
        return
    install_trans()
    if not shutil.which('trans'):
        print("ERRO: 'trans' ainda não encontrado após instalação.")
        sys.exit(1)


# =============================================================================
# Funções de tradução
# =============================================================================

def protect_placeholders(text):
    """Substitui {placeholder} por tokens opacos antes da tradução."""
    mapping = {}
    counter = [0]

    def replacer(match):
        token = f"__PH{counter[0]}__"
        mapping[token] = match.group(0)
        counter[0] += 1
        return token

    protected = PLACEHOLDER_RE.sub(replacer, text)
    return protected, mapping


def restore_placeholders(text, mapping):
    """Restaura tokens opacos de volta para {placeholder}."""
    for token, original in mapping.items():
        text = text.replace(token, original)
    return text


def prepare_for_translation(value, quote_char):
    """Remove escapes PHP para obter texto natural para tradução."""
    if quote_char == "'":
        return value.replace("\\'", "'").replace("\\\\", "\\")
    else:
        return value.replace('\\"', '"')


def re_escape(translated, quote_char):
    """Reaplica escapes PHP após tradução."""
    if quote_char == "'":
        translated = translated.replace("\\", "\\\\")
        translated = translated.replace("'", "\\'")
    else:
        translated = translated.replace('"', '\\"')
    return translated


def translate_text(text, delay):
    """Traduz texto usando trans -b en:pt-br. Retry 1x em caso de falha."""
    if not text.strip():
        return text

    for attempt in range(2):
        try:
            result = subprocess.run(
                ['trans', '-b', f'{SOURCE_LANG}:{TARGET_LANG}', text],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except subprocess.TimeoutExpired:
            pass

        if attempt == 0:
            time.sleep(2)

    print(f"  AVISO: falha na tradução, mantendo original: {text[:60]}")
    return text


# =============================================================================
# Processamento de arquivos
# =============================================================================

def process_file(src_path, dst_path, dst_dir, delay):
    """Lê arquivo PHP, traduz valores de $msg_arr, escreve no destino."""
    with open(src_path, 'r', encoding='utf-8') as f:
        src_lines = f.readlines()

    total_lines = len(src_lines)

    # Resume: checar se já existe saída parcial
    start_line = 0
    if os.path.exists(dst_path):
        with open(dst_path, 'r', encoding='utf-8') as f:
            existing = f.readlines()
        start_line = len(existing)
        if start_line >= total_lines:
            print(f"  Pulando (já completo): {os.path.relpath(dst_path, dst_dir)}")
            return
        print(f"  Resumindo da linha {start_line + 1}/{total_lines}")
    else:
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    mode = 'a' if start_line > 0 else 'w'
    translated_count = 0

    with open(dst_path, mode, encoding='utf-8') as out:
        for i in range(start_line, total_lines):
            line = src_lines[i]
            stripped = line.rstrip('\n')

            m = SINGLE_QUOTE_RE.match(stripped)
            quote_char = "'"

            if not m:
                m = DOUBLE_QUOTE_RE.match(stripped)
                quote_char = '"'

            if m:
                prefix = m.group(1)
                raw_value = m.group(2)
                suffix = m.group(3)

                text = prepare_for_translation(raw_value, quote_char)
                text, ph_map = protect_placeholders(text)
                translated = translate_text(text, delay)
                translated = restore_placeholders(translated, ph_map)
                translated = re_escape(translated, quote_char)

                out.write(prefix + translated + suffix + '\n')
                translated_count += 1

                if translated_count % 50 == 0:
                    print(f"  [{translated_count}] linha {i + 1}/{total_lines}")

                time.sleep(delay)
            else:
                out.write(line)

            out.flush()

    print(f"  Concluído: {translated_count} strings traduzidas")


# =============================================================================
# Main
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='Traduz arquivos PHP de localização (EN → PT-BR) usando translate-shell.'
    )
    parser.add_argument(
        '--dir-in', required=True,
        help='Diretório de entrada com os arquivos em inglês (ex: ./en)'
    )
    parser.add_argument(
        '--dir-out', required=True,
        help='Diretório de saída para os arquivos traduzidos (ex: ./br)'
    )
    parser.add_argument(
        '--delay', type=float, default=DEFAULT_DELAY,
        help=f'Delay em segundos entre chamadas ao tradutor (padrão: {DEFAULT_DELAY})'
    )
    return parser.parse_args()


def main():
    args = parse_args()

    src_dir = os.path.abspath(os.path.expanduser(args.dir_in))
    dst_dir = os.path.abspath(os.path.expanduser(args.dir_out))

    if not os.path.isdir(src_dir):
        print(f"ERRO: Diretório de entrada não encontrado: {src_dir}")
        sys.exit(1)

    # Garantir que translate-shell está instalado
    ensure_trans()

    print(f"Origem:  {src_dir}")
    print(f"Destino: {dst_dir}")
    print(f"Idioma:  {SOURCE_LANG} → {TARGET_LANG}")
    print(f"Delay:   {args.delay}s entre chamadas")
    print()

    file_count = 0

    for dirpath, dirnames, filenames in os.walk(src_dir):
        dirnames.sort()
        for filename in sorted(filenames):
            if not filename.endswith('.php'):
                continue

            src_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(src_path, src_dir)
            dst_path = os.path.join(dst_dir, rel_path)

            file_count += 1
            print(f"[{file_count}] {rel_path}")
            process_file(src_path, dst_path, dst_dir, args.delay)
            print()

    print(f"Completo. {file_count} arquivos processados.")


if __name__ == '__main__':
    main()
