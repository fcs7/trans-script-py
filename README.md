# PHP Translation Tool (EN → PT-BR)

Ferramenta automática para traduzir arquivos de localização PHP do inglês para português brasileiro usando [translate-shell](https://github.com/soimort/translate-shell).

## 📋 Características

- ✅ Traduz apenas os **valores** das strings (lado direito do `=`)
- ✅ Preserva **chaves**, **estrutura** e **formatação** do código
- ✅ Protege **placeholders** como `{variable_name}` (não são traduzidos)
- ✅ Mantém **HTML** e **escapes** PHP (`\'`, `\"`, `\n`) intactos
- ✅ **Resume automático**: se interrompido, continua de onde parou
- ✅ **Auto-instalação** do translate-shell de acordo com o sistema
- ✅ Suporta qualquer diretório via parâmetros CLI

## 🚀 Instalação

```bash
# Clone ou baixe o script
wget https://github.com/fcs7/trans-script-py.git
chmod +x translate.py

# OU copie para um diretório no PATH
sudo cp translate.py /usr/local/bin/php-translate
```

**Dependências**: Python 3.6+ (já vem na maioria dos sistemas Linux)

O script detecta automaticamente seu sistema e instala o `translate-shell` se necessário:
- **Debian/Ubuntu**: `apt`
- **RHEL/Fedora/CentOS**: `dnf` ou `yum`
- **Arch Linux**: `pacman`
- **openSUSE**: `zypper`
- **macOS**: `brew`

## 📖 Uso

### Sintaxe básica

```bash
python3 translate.py --dir-in <diretório_entrada> --dir-out <diretório_saída>
```

### Exemplos

```bash
# Exemplo 1: Diretórios locais
python3 translate.py --dir-in ./en --dir-out ./br

# Exemplo 2: Caminhos absolutos
python3 translate.py --dir-in ~/Documentos/en --dir-out ~/Documentos/br

# Exemplo 3: Com delay customizado (mais rápido)
python3 translate.py --dir-in ./en --dir-out ./br --delay 0.3

# Exemplo 4: Delay maior (para evitar rate limiting)
python3 translate.py --dir-in ./en --dir-out ./br --delay 1.0
```

### Parâmetros

| Parâmetro | Obrigatório | Descrição | Padrão |
|-----------|-------------|-----------|--------|
| `--dir-in` | ✅ Sim | Diretório com arquivos PHP em inglês | - |
| `--dir-out` | ✅ Sim | Diretório de saída para arquivos traduzidos | - |
| `--delay` | ❌ Não | Delay em segundos entre traduções | `0.5` |

## 📁 Estrutura de arquivos

O script preserva a estrutura de diretórios:

```
Entrada (--dir-in):          Saída (--dir-out):
en/                          br/
├── common.php               ├── common.php
├── interface.php            ├── interface.php
└── api/                     └── api/
    ├── REST/                    ├── REST/
    │   └── lang.php             │   └── lang.php
    └── soap/                    └── soap/
        └── lang.php                 └── lang.php
```

## 🔧 Como funciona

O script processa arquivos `.php` linha por linha:

### Formato reconhecido

```php
$msg_arr['chave'] = 'valor em inglês';
```

### Processo de tradução

```
1. Entrada:
   $msg_arr['btn_save'] = 'Save changes';

2. Extrai valor: "Save changes"

3. Protege placeholders: "Save changes" (sem {})

4. Traduz: "Salvar alterações"

5. Reconstrói:
   $msg_arr['btn_save'] = 'Salvar alterações';
```

### Casos especiais tratados

#### ✅ Aspas escapadas
```php
// Entrada
$msg_arr['key'] = 'The \'Maximum\' value must be a number';

// Saída
$msg_arr['key'] = 'O valor \'Máximo\' deve ser um número';
```

#### ✅ Placeholders preservados
```php
// Entrada
$msg_arr['msg'] = 'User {username} has {count} messages';

// Saída
$msg_arr['msg'] = 'Usuário {username} tem {count} mensagens';
```

#### ✅ HTML mantido
```php
// Entrada
$msg_arr['alert'] = '<b>Warning:</b> This action cannot be undone';

// Saída
$msg_arr['alert'] = '<b>Aviso:</b> Esta ação não pode ser desfeita';
```

#### ✅ Linhas não-traduzíveis copiadas
```php
<?php
// Este comentário não é traduzido
$msg_arr = array();
define('CONSTANT', 'value');
?>
```

## ⚡ Performance

- **Delay padrão**: 0.5s entre traduções
- **Estimativa**: ~10.000 strings levam aproximadamente 1.5 horas
- **Resume**: Ctrl+C para pausar, execute novamente para continuar

### Ajustando a velocidade

```bash
# Mais rápido (pode causar rate limiting)
--delay 0.2

# Mais lento (mais seguro)
--delay 1.0
```

## 🛠️ Troubleshooting

### Erro: "translate-shell não encontrado"

O script tenta instalar automaticamente. Se falhar:

```bash
# Instalação manual - Debian/Ubuntu
sudo apt install translate-shell

# Instalação manual - Fedora/RHEL
sudo dnf install translate-shell

# Instalação manual - Arch
sudo pacman -S translate-shell

# Verificar instalação
trans --version
```

### Erro: "Diretório de entrada não encontrado"

Verifique se o caminho está correto:

```bash
ls -la ~/Documentos/en  # Deve listar os arquivos .php
```

### Traduções incorretas

- Aumente o `--delay` para evitar rate limiting
- Verifique sua conexão de internet
- O Google Translate (usado pelo translate-shell) pode ter limitações temporárias

### Script muito lento

Arquivo grande (`interface.php` com 8.000+ linhas) é normal:

```bash
# Monitore o progresso
python3 translate.py --dir-in ./en --dir-out ./br

# Saída mostra progresso a cada 50 strings:
[50] linha 125/8868
[100] linha 250/8868
...
```

## ✅ Verificação pós-tradução

```bash
# 1. Verificar se todos arquivos foram criados
diff <(find en -name '*.php' | sort) \
     <(find br -name '*.php' | sed 's|br/|en/|' | sort)

# 2. Comparar contagem de linhas (devem ser iguais)
wc -l en/*.php
wc -l br/*.php

# 3. Verificar sintaxe PHP
find br -name '*.php' -exec php -l {} \;

# 4. Checar se placeholders não vazaram
grep -r '__PH' br/
# (não deve retornar nada)
```

## 📝 Exemplo completo

```bash
# 1. Preparar estrutura
mkdir -p project/en project/br
cp -r /caminho/original/* project/en/

# 2. Executar tradução
cd project
python3 ~/Documents/translate.py --dir-in ./en --dir-out ./br

# 3. Verificar resultado
php -l br/interface.php
grep -c "msg_arr\[" en/interface.php  # Contar strings originais
grep -c "msg_arr\[" br/interface.php  # Deve ser igual

# 4. Usar os arquivos traduzidos
cp -r br/* /var/www/html/lang/pt-br/
```

## 🤝 Contribuindo

Melhorias são bem-vindas:

1. Fork o repositório
2. Crie uma branch: `git checkout -b minha-feature`
3. Commit: `git commit -am 'Adiciona nova feature'`
4. Push: `git push origin minha-feature`
5. Abra um Pull Request

## 📄 Licença

MIT License - sinta-se livre para usar e modificar.

## 🔗 Links úteis

- [translate-shell](https://github.com/soimort/translate-shell) - Ferramenta de tradução via CLI
- [Google Translate API](https://translate.google.com) - Engine de tradução (usado pelo translate-shell)

## ⚠️ Avisos

- **Revisão recomendada**: Traduções automáticas podem conter erros ou imprecisões
- **Rate limiting**: Google Translate pode bloquear temporariamente após muitas requisições
- **Contexto**: O tradutor não entende contexto de software, revise termos técnicos
- **Backup**: Sempre mantenha backup dos arquivos originais

---

**Desenvolvido para facilitar a localização de projetos PHP** 🚀
