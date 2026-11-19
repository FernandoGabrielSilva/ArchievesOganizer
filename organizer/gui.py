"""Interface gráfica (PySide6 + qfluentwidgets) do Organizador de Arquivos."""
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, qInstallMessageHandler
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
    QSizePolicy, QHeaderView, QTableWidget, QTableWidgetItem,
)
from PySide6.QtGui import QAction, QPainter

# PySide6 6.12 tem um bug de refcount em QPainter.setClipping(True) que aborta
# o processo (`none_dealloc`/`bool_dealloc`) ao pintar a tabela do
# qfluentwidgets. Passar um int evita tocar no singleton True/False do Python.
_original_set_clipping = QPainter.setClipping


def _safe_set_clipping(self, enabled):
    return _original_set_clipping(self, 1 if enabled else 0)


try:
    QPainter.setClipping = _safe_set_clipping
except Exception:
    pass

from qfluentwidgets import ScrollArea, isDarkTheme
from qfluentwidgets import (
    FluentWindow, FluentIcon as FIF, PushButton, PrimaryPushButton, LineEdit,
    ComboBox, CheckBox, TableWidget, ProgressBar, TextEdit, ListWidget,
    CardWidget, SubtitleLabel, BodyLabel, CaptionLabel, InfoBar,
    InfoBarPosition, setTheme, Theme, setThemeColor, NavigationItemPosition,
)

# O qfluentwidgets cria animações de "drop" para InfoBars empilhadas sem
# endValue; o Qt imprime um aviso inofensivo nesses casos. Silencia apenas
# esse aviso específico, mantendo todas as outras mensagens do Qt.
_qt_msg_handler_original = qInstallMessageHandler(None)


def _qt_message_handler(mode, context, message):
    if "starting an animation without end value" in message:
        return
    if _qt_msg_handler_original is not None:
        _qt_msg_handler_original(mode, context, message)
    else:
        print(message, file=sys.stderr)


qInstallMessageHandler(_qt_message_handler)


def _safe_scroll_handle_paint(self, event):
    """Evita abort do Qt no paintEvent da barra de rolagem do qfluentwidgets.

    Versões recentes do PySide6 (6.12+) podem abortar dentro de
    QPainter.drawRoundedRect() quando o handle da barra é muito fino (3 px).
    Um retângulo simples tem o mesmo visual nessa espessura e é seguro.
    """
    if self.width() <= 0 or self.height() <= 0:
        return
    painter = QPainter(self)
    try:
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setOpacity(self.opacity)
        painter.setBrush(self.darkColor if isDarkTheme() else self.lightColor)
        painter.drawRect(self.rect())
    finally:
        painter.end()


try:
    from qfluentwidgets.components.widgets.scroll_bar import ScrollBarHandle
    ScrollBarHandle.paintEvent = _safe_scroll_handle_paint
except Exception:
    pass

from .config import load_config, save_config, ensure_dirs, DEFAULT_CATEGORIES, DEFAULT_CONFIG
from .classifier import plan_moves
from .mover import execute_moves, list_history, undo_history
from .i18n import t, set_language, get_language, load_language_from_config
from .version import __version__
from . import updater


class Worker(QThread):
    finished = Signal(object)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            res = self.fn(*self.args, **self.kwargs)
            self.finished.emit({"ok": True, "result": res})
        except Exception as e:
            self.finished.emit({"ok": False, "error": str(e)})


class SourceListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.listw = ListWidget()
        self.listw.setToolTip(
            "Lista de pastas que serão analisadas.\n"
            "Arquivos encontrados (e subpastas, se recursivo) serão movidos."
        )
        lay.addWidget(self.listw)
        btns = QHBoxLayout()
        self.btn_add = PushButton(t("btn_add_folder"))
        self.btn_add.setToolTip(t("tooltip_sources"))
        self.btn_remove = PushButton(t("btn_remove"))
        self.btn_remove.setToolTip("Remove a pasta selecionada da lista.")
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_remove)
        lay.addLayout(btns)
        self.btn_add.clicked.connect(self.add)
        self.btn_remove.clicked.connect(self.remove)

    def add(self):
        d = QFileDialog.getExistingDirectory(self, "Escolher pasta de origem")
        if d:
            self.listw.addItem(d)

    def remove(self):
        for it in self.listw.selectedItems():
            self.listw.takeItem(self.listw.row(it))

    def values(self):
        return [self.listw.item(i).text() for i in range(self.listw.count())]

    def set_values(self, vals):
        self.listw.clear()
        for v in vals:
            self.listw.addItem(v)


class CategoryEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        hint = CaptionLabel("Categorias e extensões. Cada linha: nome da pasta de destino e extensões (separadas por vírgula).")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        self.table = TableWidget()
        self.table.setColumnCount(2)
        self.table.setRowCount(0)
        self.table.setHorizontalHeaderLabels([t("cat_col_name"), t("cat_col_exts")])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setToolTip(t("tooltip_categories"))
        lay.addWidget(self.table)
        btns = QHBoxLayout()
        self.btn_add = PushButton(t("btn_new_category"))
        self.btn_add.setToolTip("Adiciona uma nova categoria.")
        self.btn_remove = PushButton(t("btn_remove"))
        self.btn_remove.setToolTip("Remove a categoria selecionada.")
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_remove)
        lay.addLayout(btns)
        self.btn_add.clicked.connect(self.add_row)
        self.btn_remove.clicked.connect(self.remove_row)

    def add_row(self, name="", exts=""):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(name) if False else __import__("PySide6.QtWidgets", fromlist=["QTableWidgetItem"]).QTableWidgetItem(name))
        self.table.setItem(r, 1, __import__("PySide6.QtWidgets", fromlist=["QTableWidgetItem"]).QTableWidgetItem(exts))

    def remove_row(self):
        for idx in sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(idx)

    def load(self, categories: dict):
        from PySide6.QtWidgets import QTableWidgetItem
        self.table.setRowCount(0)
        for name, exts in categories.items():
            self.add_row(name, ", ".join(exts))

    def collect(self) -> dict:
        from PySide6.QtWidgets import QTableWidgetItem
        out = {}
        for r in range(self.table.rowCount()):
            name_item = self.table.item(r, 0)
            ext_item = self.table.item(r, 1)
            if not name_item:
                continue
            name = name_item.text().strip()
            if not name:
                continue
            exts = []
            if ext_item:
                for e in ext_item.text().split(","):
                    e = e.strip()
                    if not e:
                        continue
                    if not e.startswith("."):
                        e = "." + e
                    exts.append(e.lower())
            out[name] = exts
        return out


from PySide6.QtWidgets import QTableWidgetItem


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("app_title"))
        self.resize(1120, 780)
        self.cfg = load_config()
        ensure_dirs()
        self.current_moves = []

        self._apply_theme("dark")

        # Interfaces
        self.config_iface = QWidget()
        self.config_iface.setObjectName("config_iface")
        self.organize_iface = QWidget()
        self.organize_iface.setObjectName("organize_iface")
        self.history_iface = QWidget()
        self.history_iface.setObjectName("history_iface")

        self._build_config(self.config_iface)
        self._build_organize(self.organize_iface)
        self._build_history(self.history_iface)

        self.addSubInterface(self.organize_iface, FIF.FOLDER, t("tab_organize"), NavigationItemPosition.TOP)
        self.addSubInterface(self.history_iface, FIF.HISTORY, t("tab_history"), NavigationItemPosition.TOP)
        self.addSubInterface(self.config_iface, FIF.SETTING, t("tab_config"), NavigationItemPosition.BOTTOM)

        self._load_config_to_ui()
        self._notify(t("msg_ready"), success=True)

    def _apply_theme(self, theme="dark"):
        setTheme(Theme.DARK)
        setThemeColor("#3b82f6")

    # ---------- CONFIG ----------
    def _build_config(self, parent):
        outer = QVBoxLayout(parent)
        outer.setContentsMargins(20, 20, 20, 20)
        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        scroll.setWidget(inner)
        outer.addWidget(scroll)
        cl = QVBoxLayout(inner)
        cl.setSpacing(14)

        title = SubtitleLabel("Configuração")
        cl.addWidget(title)
        sub = CaptionLabel("Defina pastas de origem, destino, comportamento e categorias.")
        cl.addWidget(sub)

        # Origem
        grp_src = self._group(t("group_sources"), t("group_sources_desc"))
        gsl = grp_src._inner
        self.src_list = SourceListWidget()
        gsl.addWidget(self.src_list)
        cl.addWidget(grp_src)

        # Destino
        grp_dest = self._group(t("group_dest"), t("group_dest_desc"))
        gdl = grp_dest._inner
        row = QHBoxLayout()
        self.dest_edit = LineEdit()
        self.dest_edit.setToolTip("Pasta base de destino. As categorias viram subpastas aqui (ex.: ~/Imagens).")
        row.addWidget(self.dest_edit)
        self.btn_dest = PushButton(t("btn_browse"))
        self.btn_dest.setToolTip(t("tooltip_dest"))
        self.btn_dest.clicked.connect(self._browse_dest)
        row.addWidget(self.btn_dest)
        gdl.addLayout(row)
        cl.addWidget(grp_dest)

        # Comportamento
        grp_beh = self._group(t("group_behavior"), t("group_behavior_desc"))
        gbl = grp_beh._inner
        self.chk_recursive = CheckBox(t("chk_recursive"))
        self.chk_recursive.setToolTip(t("tooltip_recursive"))
        self.chk_hidden = CheckBox(t("chk_hidden"))
        self.chk_hidden.setToolTip(t("tooltip_hidden"))
        self.chk_skip_unknown = CheckBox(t("chk_skip_unknown"))
        self.chk_skip_unknown.setToolTip(t("tooltip_skip_unknown"))
        gbl.addWidget(self.chk_recursive)
        gbl.addWidget(self.chk_hidden)
        gbl.addWidget(self.chk_skip_unknown)

        row2 = QHBoxLayout()
        row2.addWidget(BodyLabel(t("label_conflict")))
        self.combo_conflict = ComboBox()
        self.combo_conflict.addItems(["rename", "overwrite", "skip"])
        self.combo_conflict.setToolTip(t("tooltip_conflict"))
        row2.addWidget(self.combo_conflict)
        gbl.addLayout(row2)

        row_lang = QHBoxLayout()
        row_lang.addWidget(BodyLabel(t("label_language")))
        self.combo_lang = ComboBox()
        from .i18n import LANGUAGES
        for code, name in LANGUAGES.items():
            self.combo_lang.addItem(name, userData=code)
        self.combo_lang.setToolTip("Idioma da interface / Interface language.")
        row_lang.addWidget(self.combo_lang)
        gbl.addLayout(row_lang)

        cl.addWidget(grp_beh)

        # Atualizações
        grp_upd = self._group(t("group_updates"), t("group_updates_desc"))
        ubl = QVBoxLayout()
        self.lbl_version = CaptionLabel(t("current_version", v=__version__))
        ubl.addWidget(self.lbl_version)
        self.chk_auto_check = CheckBox(t("chk_auto_check"))
        self.chk_auto_install = CheckBox(t("chk_auto_install"))
        ubl.addWidget(self.chk_auto_check)
        ubl.addWidget(self.chk_auto_install)
        row_upd = QHBoxLayout()
        self.btn_check_now = PushButton(t("btn_check_now"))
        row_upd.addWidget(self.btn_check_now)
        self.lbl_update_status = CaptionLabel("")
        row_upd.addWidget(self.lbl_update_status)
        row_upd.addStretch()
        ubl.addLayout(row_upd)
        grp_upd.layout().addLayout(ubl)
        cl.addWidget(grp_upd)

        # Categorias
        grp_cat = self._group(t("group_categories"), t("group_categories_desc"))
        gcl = grp_cat._inner
        self.cat_editor = CategoryEditor()
        gcl.addWidget(self.cat_editor)
        cl.addWidget(grp_cat)

        # Save
        save_row = QHBoxLayout()
        self.btn_save_cfg = PrimaryPushButton(t("btn_save_config"))
        self.btn_save_cfg.setToolTip("Salva todas as configurações acima.")
        self.btn_restore = PushButton(t("btn_restore_defaults"))
        self.btn_restore.setToolTip("Restaura a configuração padrão (categorias, opções).")
        save_row.addWidget(self.btn_save_cfg)
        save_row.addWidget(self.btn_restore)
        cl.addLayout(save_row)
        cl.addStretch(1)

        self.btn_save_cfg.clicked.connect(self._save_config)
        self.btn_restore.clicked.connect(self._restore_defaults)
        self.btn_check_now.clicked.connect(self._check_updates_now)

    # ---------- ORGANIZE ----------
    def _build_organize(self, parent):
        ol = QVBoxLayout(parent)
        ol.setContentsMargins(20, 20, 20, 20)
        ol.setSpacing(10)

        title = SubtitleLabel("Organizar")
        ol.addWidget(title)
        sub = CaptionLabel("Analise as pastas, revise o preview e aplique os movimentos.")
        ol.addWidget(sub)

        action_row = QHBoxLayout()
        self.btn_help = PushButton("❓  " + t("btn_howto"))
        self.btn_help.setToolTip("Mostra instruções de uso do programa.")
        self.btn_help.clicked.connect(self._howto)
        action_row.addWidget(self.btn_help)
        self.btn_analyze = PrimaryPushButton(t("btn_analyze"))
        self.btn_analyze.setToolTip("Varre as pastas de origem e mostra quais arquivos seriam movidos, sem mover nada.")
        self.btn_apply = PrimaryPushButton(t("btn_apply"))
        self.btn_apply.setEnabled(False)
        self.btn_apply.setToolTip("Executa os movimentos mostrados no preview. Pede confirmação antes.")
        action_row.addWidget(self.btn_analyze)
        action_row.addWidget(self.btn_apply)
        ol.addLayout(action_row)

        self.progress = ProgressBar()
        self.progress.setToolTip("Progresso da operação em andamento.")
        self.progress.setVisible(False)
        ol.addWidget(self.progress)

        self.table_moves = TableWidget()
        self.table_moves.setColumnCount(3)
        self.table_moves.setRowCount(0)
        self.table_moves.setHorizontalHeaderLabels([t("table_col_src"), t("table_col_dst"), t("table_col_cat")])

        self.stats_label = CaptionLabel(t("stats_none"))
        self.stats_label.setWordWrap(True)
        ol.addWidget(self.stats_label)
        self.table_moves.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_moves.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_moves.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_moves.setToolTip(t("tooltip_categories"))
        self.table_moves.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_moves.setSelectionBehavior(QTableWidget.SelectRows)
        ol.addWidget(self.table_moves, 1)

        self.log_text = TextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(110)
        self.log_text.setToolTip("Log das operações realizadas.")
        ol.addWidget(self.log_text)

        self.btn_analyze.clicked.connect(self._analyze)
        self.btn_apply.clicked.connect(self._apply)

    # ---------- HISTORY ----------
    def _build_history(self, parent):
        hl = QVBoxLayout(parent)
        hl.setContentsMargins(20, 20, 20, 20)
        hl.setSpacing(10)
        title = SubtitleLabel("Histórico")
        hl.addWidget(title)
        sub = CaptionLabel(t("history_hint"))
        hl.addWidget(sub)
        self.hist_list = ListWidget()
        self.hist_list.setToolTip("Lista de operações realizadas. Selecione e clique em 'Desfazer'.")
        hl.addWidget(self.hist_list, 1)
        hbtns = QHBoxLayout()
        self.btn_refresh_hist = PushButton(t("btn_refresh"))
        self.btn_refresh_hist.setToolTip("Recarrega a lista de histórico.")
        self.btn_undo = PushButton(t("btn_undo"))
        self.btn_undo.setToolTip("Desfaz a operação selecionada, movendo os arquivos de volta.")
        hbtns.addWidget(self.btn_refresh_hist)
        hbtns.addWidget(self.btn_undo)
        hl.addLayout(hbtns)

        self.btn_refresh_hist.clicked.connect(self._refresh_history)
        self.btn_undo.clicked.connect(self._undo)
        self._refresh_history()

    # ---------- LOGIC ----------
    def _group(self, title, description=""):
        card = CardWidget()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(8)
        t = SubtitleLabel(title)
        lay.addWidget(t)
        if description:
            d = CaptionLabel(description)
            d.setWordWrap(True)
            lay.addWidget(d)
        card._inner = lay
        return card

    def _build_menu(self):
        menubar = self.menuBar()
        help_menu = menubar.addMenu("Ajuda")
        act_howto = QAction("Como usar", self)
        act_howto.triggered.connect(self._howto)
        help_menu.addAction(act_howto)
        act_about = QAction("Sobre", self)
        act_about.triggered.connect(self._about)
        help_menu.addAction(act_about)

    def _howto(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, t("howto_title"),
            t("howto_body")
        )

    def _about(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(self, t("about_title"),
            t("about_body")
        )

    def _browse_dest(self):
        d = QFileDialog.getExistingDirectory(self, "Escolher pasta de destino base")
        if d:
            self.dest_edit.setText(d)

    def _load_config_to_ui(self):
        c = self.cfg
        self.src_list.set_values(c.get("source_dirs", []))
        self.dest_edit.setText(c.get("destination_base", str(Path.home())))
        self.chk_recursive.setChecked(c.get("recursive", False))
        self.chk_hidden.setChecked(c.get("include_hidden", False))
        self.chk_skip_unknown.setChecked(c.get("skip_unknown", False))
        idx = self.combo_conflict.findText(c.get("conflict_policy", "rename"))
        if idx >= 0:
            self.combo_conflict.setCurrentIndex(idx)
        # language
        lang = c.get("language", "pt_BR")
        for i in range(self.combo_lang.count()):
            if self.combo_lang.itemData(i) == lang:
                self.combo_lang.setCurrentIndex(i)
                break
        self.chk_auto_check.setChecked(bool(c.get("auto_check_updates", True)))
        self.chk_auto_install.setChecked(bool(c.get("auto_install_updates", False)))
        self.cat_editor.load(c.get("categories", DEFAULT_CATEGORIES))

    def _collect_config(self) -> dict:
        cats = self.cat_editor.collect()
        if "Outros" not in cats:
            cats["Outros"] = []
        cfg = {
            "source_dirs": self.src_list.values(),
            "destination_base": self.dest_edit.text().strip() or str(Path.home()),
            "recursive": self.chk_recursive.isChecked(),
            "include_hidden": self.chk_hidden.isChecked(),
            "skip_unknown": self.chk_skip_unknown.isChecked(),
            "conflict_policy": self.combo_conflict.currentText(),
            "language": self.combo_lang.currentData() or "pt_BR",
            "auto_check_updates": self.chk_auto_check.isChecked(),
            "auto_install_updates": self.chk_auto_install.isChecked(),
            "theme": "dark",
            "ignore_dirs": self.cfg.get("ignore_dirs", []),
            "categories": cats,
            "category_destinations": self.cfg.get("category_destinations", {}),
        }
        cd = cfg["category_destinations"]
        for k in cats:
            cd.setdefault(k, k)
        for k in list(cd.keys()):
            if k not in cats:
                del cd[k]
        cfg["category_destinations"] = cd
        return cfg

    def _save_config(self):
        old_lang = self.cfg.get("language", "pt_BR")
        cfg = self._collect_config()
        save_config(cfg)
        self.cfg = cfg
        self._apply_theme("dark")
        from .i18n import set_language
        set_language(cfg.get("language", "pt_BR"))
        if cfg.get("language") != old_lang:
            self._notify(t("restart_msg"), success=True)
        else:
            self._notify(t("msg_config_saved"), success=True)

    def _restore_defaults(self):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, t("btn_restore_defaults"),
                                     t("confirm_restore"),
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        cfg = dict(DEFAULT_CONFIG)
        save_config(cfg)
        self.cfg = cfg
        self._load_config_to_ui()
        self._apply_theme("dark")
        self._notify(t("msg_defaults_restored"), success=True)

    def _check_updates_now(self):
        self.lbl_update_status.setText("...")
        thr = _UpdateThread(self)
        thr.result.connect(self._on_update_result)
        thr.start()
        self._update_thread = thr

    def _auto_check_on_start(self):
        cfg = load_config()
        if not cfg.get("auto_check_updates", True):
            return
        thr = _UpdateThread(self)
        thr.result.connect(self._on_update_result_auto)
        thr.start()
        self._update_thread = thr

    def _on_update_result(self, info):
        if info.get("error"):
            self.lbl_update_status.setText(t("update_error", e=info["error"]))
            self._notify(t("update_error", e=info["error"]), success=False)
            return
        if not info.get("has"):
            self.lbl_update_status.setText(t("update_none", v=info.get("tag") or __version__))
            self._notify(t("update_none", v=info.get("tag") or __version__), success=True)
            return
        self.lbl_update_status.setText(t("update_available", v=info["tag"]))
        self._notify(t("update_available", v=info["tag"]), success=True)
        cfg = load_config()
        if cfg.get("auto_install_updates") and info.get("asset") and updater.is_appimage():
            self._download_and_install(info["asset"], info["tag"])
        elif info.get("url"):
            # store url for manual
            self._last_update_url = info["url"]

    def _on_update_result_auto(self, info):
        if info.get("error") or not info.get("has"):
            return
        self.lbl_update_status.setText(t("update_available", v=info["tag"]))
        self._notify(t("update_available", v=info["tag"]), success=True)
        cfg = load_config()
        if cfg.get("auto_install_updates") and info.get("asset") and updater.is_appimage():
            self._download_and_install(info["asset"], info["tag"])
        else:
            self._last_update_url = info.get("url")

    def _download_and_install(self, asset, tag):
        self.lbl_update_status.setText(t("update_downloading", p=0))
        thr = _DownloadThread(asset, self)
        thr.progress.connect(lambda d, tot: self.lbl_update_status.setText(
            t("update_downloading", p=int(d * 100 / tot) if tot else 0)))
        thr.finished_ok.connect(self._on_download_ok)
        thr.failed.connect(lambda e: (self.lbl_update_status.setText(t("update_error", e=e)),
                                     self._notify(t("update_error", e=e), success=False)))
        thr.start()
        self._download_thread = thr

    def _on_download_ok(self, path):
        self.lbl_update_status.setText(t("update_installing"))
        try:
            updater.apply_appimage_update(path)
            self._notify(t("update_restart"), success=True)
            QApplication.quit()
        except Exception as e:
            self.lbl_update_status.setText(t("update_error", e=str(e)))
            self._notify(t("update_error", e=str(e)), success=False)

    def _notify(self, msg, success=True):
        (InfoBar.success if success else InfoBar.error)(
            title="Organizador",
            content=msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )

    def _analyze(self):
        cfg = self._collect_config()
        self._notify("Analisando pastas...", success=True)
        self.btn_analyze.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.worker = Worker(plan_moves, cfg)
        self.worker.finished.connect(self._on_analyzed)
        self.worker.start()

    def _on_analyzed(self, res):
        self.btn_analyze.setEnabled(True)
        self.progress.setVisible(False)
        if not res["ok"]:
            self._notify(res["error"], success=False)

            return
        moves = res["result"]
        self.current_moves = moves
        self.table_moves.setRowCount(0)
        for m in moves:
            r = self.table_moves.rowCount()
            self.table_moves.insertRow(r)
            it_src = QTableWidgetItem(m["src"])
            it_dst = QTableWidgetItem(m["dst"])
            it_cat = QTableWidgetItem(m["category"])
            it_src.setToolTip(m["src"])
            it_dst.setToolTip(m["dst"])
            it_cat.setToolTip(f"Categoria: {m['category']}")
            self.table_moves.setItem(r, 0, it_src)
            self.table_moves.setItem(r, 1, it_dst)
            self.table_moves.setItem(r, 2, it_cat)
        self.btn_apply.setEnabled(len(moves) > 0)
        msg = t("msg_preview", n=len(moves))
        from collections import Counter
        cnt = Counter(m["category"] for m in moves)
        stats = "  |  ".join(f"{k}: {v}" for k, v in sorted(cnt.items()))
        self.stats_label.setText((f"Total: {len(moves)}  —  {stats}") if moves else t("stats_no_moves"))
        self.log(msg)


    def _apply(self):
        if not self.current_moves:
            return
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, t("confirm_title"),
            t("confirm_move", n=len(self.current_moves)),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        cfg = self._collect_config()
        self.btn_apply.setEnabled(False)
        self.btn_analyze.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.log("Movendo arquivos...")

        self.worker = Worker(execute_moves, self.current_moves, cfg)
        self.worker.finished.connect(self._on_applied)
        self.worker.start()

    def _on_applied(self, res):
        self.btn_analyze.setEnabled(True)
        self.progress.setVisible(False)
        if not res["ok"]:
            self._notify(res["error"], success=False)
            self.btn_apply.setEnabled(True)
    
            return
        r = res["result"]
        self.log(t("log_done", moved=r["moved"], skipped=r["skipped"], errs=len(r["errors"])))
        for e in r["errors"]:
            self.log(f"  ERRO: {e}")
        self.current_moves = []
        self.table_moves.setRowCount(0)
        self.btn_apply.setEnabled(False)
        self._refresh_history()
        msg = t("msg_done", n=r["moved"])

        self._notify(msg, success=True)

    def _refresh_history(self):
        self.hist_list.clear()
        for h in list_history():
            self.hist_list.addItem(t("history_item", created=h["created"], count=h["count"]))

    def _undo(self):
        items = self.hist_list.selectedItems()
        if not items:
            self._notify(t("select_history"), success=False)
            return
        # find id by index matching
        hs = list_history()
        idx = self.hist_list.currentRow()
        if idx < 0 or idx >= len(hs):
            self._notify(t("select_history"), success=False)
            return
        hid = hs[idx]["id"]
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, t("btn_undo"), t("confirm_undo", id=hid),
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        res = undo_history(hid)
        if "error" in res:
            self._notify(res["error"], success=False)
    
        else:
            self.log(t("log_undone", n=res["restored"], errs=len(res["errors"])))
            for e in res["errors"]:
                self.log(f"  ERRO: {e}")
            self._refresh_history()

            self._notify(t("msg_restored", n=res["restored"]), success=True)

    def log(self, msg):
        self.log_text.append(msg)



class _UpdateThread(QThread):
    result = Signal(object)
    def run(self):
        try:
            has, tag, asset, url, rel, err = updater.check_for_updates()
            self.result.emit({"has": has, "tag": tag, "asset": asset, "url": url, "error": err})
        except Exception as e:
            self.result.emit({"has": False, "tag": None, "asset": None, "url": None, "error": str(e)})


class _DownloadThread(QThread):
    progress = Signal(int, int)
    finished_ok = Signal(str)
    failed = Signal(str)
    def __init__(self, asset, parent=None):
        super().__init__(parent)
        self.asset = asset
    def run(self):
        try:
            path = updater.download_asset(self.asset, progress=lambda d, tot: self.progress.emit(d, tot))
            self.finished_ok.emit(str(path))
        except Exception as e:
            self.failed.emit(str(e))


def main():
    ensure_dirs()
    load_language_from_config()
    app = QApplication(sys.argv)
    app.setApplicationName(t("app_title"))
    from PySide6.QtGui import QPalette, QColor
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor("#202020"))
    pal.setColor(QPalette.WindowText, QColor("#ffffff"))
    pal.setColor(QPalette.Base, QColor("#252525"))
    pal.setColor(QPalette.AlternateBase, QColor("#2d2d2d"))
    pal.setColor(QPalette.ToolTipBase, QColor("#252525"))
    pal.setColor(QPalette.ToolTipText, QColor("#ffffff"))
    pal.setColor(QPalette.Text, QColor("#ffffff"))
    pal.setColor(QPalette.Button, QColor("#2d2d2d"))
    pal.setColor(QPalette.ButtonText, QColor("#ffffff"))
    pal.setColor(QPalette.BrightText, QColor("#ff0000"))
    pal.setColor(QPalette.Highlight, QColor("#3b82f6"))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(pal)
    w = MainWindow()
    w.show()
    w._auto_check_on_start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
