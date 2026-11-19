# Organizador de Arquivos (Archieves Organizer)

Aplicativo com interface gráfica (Fluent Design) para Linux que organiza arquivos
por tipo, movendo-os para pastas por categoria (Imagens, Vídeos, Músicas,
Documentos, Código, Compactados, etc.). Permite configurar pastas de origem,
destino, categorias e extensões. Sempre faz **preview (dry-run)** antes de mover
e mantém **histórico com desfazer (undo)**.

## Recursos

- GUI moderna em Fluent Design (PySide6 + PyQt-Fluent-Widgets), tema dark/light.
- Configuração de múltiplas pastas de origem e pasta de destino base.
- Categorias e extensões totalmente editáveis (adicionar/remover).
- Opções: recursivo, incluir arquivos ocultos, pular desconhecidos, política de
  conflito (rename / overwrite / skip).
- Preview (dry-run) com tabela de movimentos e estatísticas por categoria.
- Confirmação antes de aplicar; histórico persistente com desfazer.
- Tooltips explicativos em todos os campos e botão "Como usar".
- **Internacionalização (i18n)** com 28 idiomas (pt_BR, pt_PT, en, es, fr, de,
  it, ru, zh_CN, zh_TW, ja, ko, ar, hi, tr, pl, nl, sv, uk, cs, ro, hu, el,
  he, vi, th, id, ms). Seletor de idioma nas Configurações.
- Auto-contido: binário PyInstaller onefile e AppImage (~334 MB) não dependem de
  Python nem de bibliotecas instaladas.

## Instalação (usuário final)

### AppImage (recomendado)

Baixe `OrganizadorArquivos-x86_64.AppImage` na página de
[Releases](https://github.com/FernandoGabrielSilva/ArchievesOganizer/releases),
torne executável e rode:

```bash
chmod +x OrganizadorArquivos-x86_64.AppImage
./OrganizadorArquivos-x86_64.AppImage
```

### Binário (PyInstaller onefile)

```bash
chmod +x OrganizadorArquivos
./OrganizadorArquivos
```

### Wrapper no PATH (opcional)

```bash
mkdir -p ~/.local/bin
cp OrganizadorArquivos ~/.local/bin/organizador-arquivos
```

## Uso (GUI)

1. Abra a aba **Organizar**.
2. Configure as pastas em **Configuração** (origem, destino, comportamento,
   categorias) e clique em **Salvar configuração**.
3. Clique em **Analisar (preview)** e revise a tabela de movimentos.
4. Clique em **Aplicar movimentos** e confirme.
5. Use **Histórico** para desfazer uma operação.

## Uso (CLI)

```bash
python3 main.py --cli --source ~/Downloads --dest ~/ --recursive
python3 main.py --cli --source ~/Downloads --dest ~/ --apply
```

## Desenvolvimento

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## Gerar binário + AppImage

```bash
pyinstaller --noconfirm --windowed --onefile --name OrganizadorArquivos main.py \
  --hidden-import organizer --collect-all qfluentwidgets --collect-all PySide6
bash build_appimage.sh
ARCH=x86_64 appimagetool AppDir OrganizadorArquivos-x86_64.AppImage
```

## Estrutura

```
OrganizadorArquivos/
├── main.py
├── organizer/
│   ├── config.py        # configuração persistente
│   ├── classifier.py    # classificação e planejamento de movimentos
│   ├── mover.py         # execução, histórico, undo
│   ├── gui.py           # interface (Fluent Design)
│   ├── i18n.py          # internacionalização (28 idiomas)
│   └── theme.py         # tema dark
├── resources/           # ícone, AppRun, .desktop
├── build_appimage.sh
└── requirements.txt
```

## Configuração

- Configuração: `~/.config/organizador-arquivos/config.json`
- Histórico: `~/.local/share/organizador-arquivos/history/`

## Licença

MIT
PY