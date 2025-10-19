#!/usr/bin/env python3
# GSearch.py — Google Advanced Search Builder (PyQt6)
# Includes date pickers (after/before) with checkboxes.
# Fixed previous syntax/truncation issues.
# Added features: terms location dropdown, number range, quick date buttons, search type dropdown, clear all button.
# Added at least 20 useful advanced search examples.
# Updated about text.
# Changed recent queries storage to INI file in application directory.
# Fixed issue with loading recent queries from INI file.
# Added advanced image search options similar to Google's advanced image search.

import json
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus
from configparser import ConfigParser

from PyQt6 import QtCore, QtGui, QtWidgets

APP_NAME = "GSearch"
RECENT_FILENAME = Path(__file__).parent / "GSearch.ini"
MAX_RECENT = 20


@dataclass
class SearchParts:
    all_words: str = ""
    terms_location: str = "anywhere"
    exact_phrase: str = ""
    exclude_words: str = ""
    or_words: str = ""
    site: str = ""
    filetype: str = ""
    intitle: str = ""
    inurl: str = ""
    range_from: str = ""
    range_to: str = ""
    range_unit: str = ""
    before: str = ""
    after: str = ""
    search_type: str = "Web"
    image_size: str = "Any size"
    aspect_ratio: str = "Any aspect ratio"
    color_filter: str = "Any color"
    specific_color: str = ""
    image_type: str = "Any type"
    region: str = "Any region"
    usage_rights: str = "All"

    def build_query(self) -> str:
        pieces: List[str] = []

        if self.all_words:
            words = self.all_words.strip()
            if self.terms_location == "title":
                pieces.append(f"allintitle:{words}")
            elif self.terms_location == "text":
                pieces.append(f"allintext:{words}")
            elif self.terms_location == "url":
                pieces.append(f"allinurl:{words}")
            elif self.terms_location == "links":
                pieces.append(f"allinanchor:{words}")
            else:  # anywhere
                pieces.append(words)

        if self.exact_phrase:
            pieces.append(f"\"{self.exact_phrase.strip()}\"")

        if self.exclude_words:
            ex = " ".join(f"-{w}" for w in self.exclude_words.split())
            pieces.append(ex)

        if self.or_words:
            ors = " OR ".join([t.strip() for t in self.or_words.split("|") if t.strip()])
            if ors:
                pieces.append(f"({ors})")

        if self.site:
            pieces.append(f"site:{self.site.strip()}")

        if self.filetype:
            pieces.append(f"filetype:{self.filetype.strip()}")

        if self.intitle:
            pieces.append(f"intitle:{self.intitle.strip()}")

        if self.inurl:
            pieces.append(f"inurl:{self.inurl.strip()}")

        if self.range_from and self.range_to:
            r_from = self.range_from.strip()
            r_to = self.range_to.strip()
            unit = self.range_unit.strip()
            range_str = f"{unit}{r_from}..{unit}{r_to}" if unit else f"{r_from}..{r_to}"
            pieces.append(range_str)

        if self.before:
            pieces.append(f"before:{self.before.strip()}")

        if self.after:
            pieces.append(f"after:{self.after.strip()}")

        return " ".join(pieces).strip()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(960, 800)  # Taller for image options

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        # ---------- Form layout ----------
        form_layout = QtWidgets.QGridLayout()
        form_layout.setColumnStretch(1, 1)
        row = 0

        def add_label_widget(label_text, widget, tip=None):
            nonlocal row
            lbl = QtWidgets.QLabel(label_text)
            lbl.setToolTip(tip or "")

            # wrap layouts into QWidget
            if isinstance(widget, QtWidgets.QLayout):
                container = QtWidgets.QWidget()
                container.setLayout(widget)
                widget_to_add = container
            else:
                widget_to_add = widget

            form_layout.addWidget(lbl, row, 0, QtCore.Qt.AlignmentFlag.AlignTop)
            form_layout.addWidget(widget_to_add, row, 1)
            row += 1

        # All these words with terms location
        self.all_input = QtWidgets.QLineEdit()
        self.all_input.setPlaceholderText("words separated by spaces (must all appear)")
        self.terms_combo = QtWidgets.QComboBox()
        self.terms_combo.addItems([
            "anywhere in the page",
            "in the title of the page",
            "in the text of the page",
            "in the URL of the page",
            "in links to the page"
        ])
        all_container = QtWidgets.QHBoxLayout()
        all_container.addWidget(self.all_input)
        all_container.addWidget(self.terms_combo)
        add_label_widget("All these words:", all_container, "Terms that must all appear (space-separated)")

        self.exact_input = QtWidgets.QLineEdit()
        self.exact_input.setPlaceholderText("Exact phrase (will be quoted)")
        add_label_widget("This exact word or phrase:", self.exact_input)

        self.exclude_input = QtWidgets.QLineEdit()
        self.exclude_input.setPlaceholderText("words to exclude (space-separated)")
        add_label_widget("None of these words (-):", self.exclude_input)

        self.or_input = QtWidgets.QLineEdit()
        self.or_input.setPlaceholderText("word1|word2|word3  — separate with |")
        add_label_widget("Any of these words (OR):", self.or_input, "Use | to separate OR terms")

        self.site_input = QtWidgets.QLineEdit()
        self.site_input.setPlaceholderText("example.com")
        add_label_widget("Site or domain:", self.site_input)

        self.filetype_input = QtWidgets.QLineEdit()
        self.filetype_input.setPlaceholderText("pdf, docx, xls")
        add_label_widget("File type:", self.filetype_input)

        self.intitle_input = QtWidgets.QLineEdit()
        self.intitle_input.setPlaceholderText("words that must appear in the title")
        add_label_widget("intitle:", self.intitle_input)

        self.inurl_input = QtWidgets.QLineEdit()
        self.inurl_input.setPlaceholderText("words in the URL")
        add_label_widget("inurl:", self.inurl_input)

        # Number range
        self.range_from = QtWidgets.QLineEdit()
        self.range_from.setPlaceholderText("from")
        self.range_to = QtWidgets.QLineEdit()
        self.range_to.setPlaceholderText("to")
        self.range_unit = QtWidgets.QLineEdit()
        self.range_unit.setPlaceholderText("unit e.g. $ (optional)")
        range_container = QtWidgets.QHBoxLayout()
        range_container.addWidget(self.range_from)
        range_container.addWidget(self.range_to)
        range_container.addWidget(self.range_unit)
        add_label_widget("Numbers ranging from:", range_container, "e.g., 100 to 200, with optional unit like $")

        # ---------- Date pickers with checkboxes and quick buttons ----------
        # After
        self.after_checkbox = QtWidgets.QCheckBox("Use after")
        self.after_dateedit = QtWidgets.QDateEdit()
        self.after_dateedit.setCalendarPopup(True)
        self.after_dateedit.setDisplayFormat("yyyy-MM-dd")
        qd_after = QtCore.QDate.currentDate().addDays(-30)
        self.after_dateedit.setDate(qd_after)

        # Before
        self.before_checkbox = QtWidgets.QCheckBox("Use before")
        self.before_dateedit = QtWidgets.QDateEdit()
        self.before_dateedit.setCalendarPopup(True)
        self.before_dateedit.setDisplayFormat("yyyy-MM-dd")
        self.before_dateedit.setDate(QtCore.QDate.currentDate())

        # Layout: checkbox + dateedit pairs
        after_container = QtWidgets.QHBoxLayout()
        after_container.addWidget(self.after_checkbox)
        after_container.addWidget(self.after_dateedit)

        before_container = QtWidgets.QHBoxLayout()
        before_container.addWidget(self.before_checkbox)
        before_container.addWidget(self.before_dateedit)

        # Quick buttons
        quick_buttons = QtWidgets.QHBoxLayout()
        past_24h = QtWidgets.QPushButton("Past 24h")
        past_24h.clicked.connect(lambda: self.set_date_preset(days=1))
        past_week = QtWidgets.QPushButton("Past week")
        past_week.clicked.connect(lambda: self.set_date_preset(days=7))
        past_month = QtWidgets.QPushButton("Past month")
        past_month.clicked.connect(lambda: self.set_date_preset(months=1))
        past_year = QtWidgets.QPushButton("Past year")
        past_year.clicked.connect(lambda: self.set_date_preset(years=1))
        quick_buttons.addWidget(past_24h)
        quick_buttons.addWidget(past_week)
        quick_buttons.addWidget(past_month)
        quick_buttons.addWidget(past_year)
        quick_buttons.addStretch()

        # Date main container
        date_container = QtWidgets.QVBoxLayout()
        date_h_container = QtWidgets.QHBoxLayout()
        date_h_container.addLayout(after_container)
        date_h_container.addSpacing(12)
        date_h_container.addLayout(before_container)
        date_h_container.addStretch()
        date_container.addLayout(date_h_container)
        date_container.addLayout(quick_buttons)

        add_label_widget("Date range (optional):", date_container, "Check a date to include it (after: / before:) or use quick presets")

        # Add form layout to main
        main_layout.addLayout(form_layout)

        # ---------- Image Search Options ----------
        self.image_group = QtWidgets.QGroupBox("Image Search Options")
        image_layout = QtWidgets.QGridLayout(self.image_group)
        row_i = 0

        def add_image_label_widget(label_text, widget, tip=None):
            nonlocal row_i
            lbl = QtWidgets.QLabel(label_text)
            lbl.setToolTip(tip or "")
            image_layout.addWidget(lbl, row_i, 0, QtCore.Qt.AlignmentFlag.AlignTop)
            if isinstance(widget, QtWidgets.QLayout):
                container = QtWidgets.QWidget()
                container.setLayout(widget)
                image_layout.addWidget(container, row_i, 1)
            else:
                image_layout.addWidget(widget, row_i, 1)
            row_i += 1

        self.image_size_combo = QtWidgets.QComboBox()
        self.image_size_combo.addItems(["Any size", "Large", "Medium", "Icon"])
        self.image_size_combo.currentIndexChanged.connect(self.update_preview)
        add_image_label_widget("Image size:", self.image_size_combo)

        self.aspect_combo = QtWidgets.QComboBox()
        self.aspect_combo.addItems(["Any aspect ratio", "Square", "Tall", "Wide", "Panoramic"])
        self.aspect_combo.currentIndexChanged.connect(self.update_preview)
        add_image_label_widget("Aspect ratio:", self.aspect_combo)

        self.color_combo = QtWidgets.QComboBox()
        self.color_combo.addItems(["Any color", "Full color", "Black and white", "Transparent", "Specific color"])
        self.color_combo.currentTextChanged.connect(lambda text: self.specific_color_combo.setVisible(text == "Specific color"))
        self.color_combo.currentTextChanged.connect(self.update_preview)
        self.specific_color_combo = QtWidgets.QComboBox()
        self.specific_color_combo.addItems(["Black", "Blue", "Brown", "Gray", "Green", "Orange", "Pink", "Purple", "Red", "Teal", "White", "Yellow"])
        self.specific_color_combo.currentIndexChanged.connect(self.update_preview)
        self.specific_color_combo.setVisible(False)
        color_container = QtWidgets.QHBoxLayout()
        color_container.addWidget(self.color_combo)
        color_container.addWidget(self.specific_color_combo)
        add_image_label_widget("Colors in image:", color_container)

        self.image_type_combo = QtWidgets.QComboBox()
        self.image_type_combo.addItems(["Any type", "Face", "Photo", "Clip art", "Line drawing", "Animated"])
        self.image_type_combo.currentIndexChanged.connect(self.update_preview)
        add_image_label_widget("Type of image:", self.image_type_combo)

        self.region_combo = QtWidgets.QComboBox()
        self.regions = ["Any region", "United States", "United Kingdom", "Canada", "Australia", "Germany", "France", "India", "Japan", "Brazil", "Afghanistan", "Albania", "Algeria"]
        self.region_combo.addItems(self.regions)
        self.region_combo.currentIndexChanged.connect(self.update_preview)
        add_image_label_widget("Region:", self.region_combo)

        self.region_map = {
            "Afghanistan": "countryAF",
            "Albania": "countryAL",
            "Algeria": "countryDZ",
            "Australia": "countryAU",
            "Brazil": "countryBR",
            "Canada": "countryCA",
            "France": "countryFR",
            "Germany": "countryDE",
            "India": "countryIN",
            "Japan": "countryJP",
            "United Kingdom": "countryGB",
            "United States": "countryUS",
        }

        self.usage_combo = QtWidgets.QComboBox()
        self.usage_combo.addItems(["All", "Free to use or share", "Free to use or share commercially", "Free to use or share or modify", "Free to use or share or modify commercially"])
        self.usage_combo.currentIndexChanged.connect(self.update_preview)
        add_image_label_widget("Usage rights:", self.usage_combo)

        main_layout.addWidget(self.image_group)

        # ---------- Preview and Controls ----------
        preview_label = QtWidgets.QLabel("Preview URL parameters:")
        preview_label.setStyleSheet("font-weight: 600;")
        main_layout.addWidget(preview_label)

        self.preview = QtWidgets.QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setAcceptRichText(False)
        self.preview.setFixedHeight(120)
        main_layout.addWidget(self.preview)

        # Search type dropdown
        search_type_label = QtWidgets.QLabel("Search type:")
        self.search_type_combo = QtWidgets.QComboBox()
        self.search_type_combo.addItems(["Web", "Images", "Videos", "News"])
        self.search_type_combo.currentTextChanged.connect(lambda text: self.image_group.setEnabled(text == "Images"))
        self.search_type_combo.currentIndexChanged.connect(self.update_preview)
        search_type_container = QtWidgets.QHBoxLayout()
        search_type_container.addWidget(search_type_label)
        search_type_container.addWidget(self.search_type_combo)
        search_type_container.addStretch()
        main_layout.addLayout(search_type_container)

        self.image_group.setEnabled(self.search_type_combo.currentText() == "Images")

        controls_layout = QtWidgets.QHBoxLayout()
        self.copy_btn = QtWidgets.QPushButton("Copy (Ctrl+C)")
        self.open_btn = QtWidgets.QPushButton("Search in browser (Ctrl+Enter)")
        self.save_btn = QtWidgets.QPushButton("Save to Recent (Ctrl+S)")
        self.clear_btn = QtWidgets.QPushButton("Clear all")
        controls_layout.addWidget(self.copy_btn)
        controls_layout.addWidget(self.open_btn)
        controls_layout.addWidget(self.save_btn)
        controls_layout.addWidget(self.clear_btn)
        controls_layout.addStretch()

        # Right side: recent queries
        right_section = QtWidgets.QGroupBox("Recent queries")
        right_layout = QtWidgets.QVBoxLayout(right_section)
        self.recent_list = QtWidgets.QListWidget()
        self.recent_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        right_layout.addWidget(self.recent_list)
        recent_btns = QtWidgets.QHBoxLayout()
        self.load_recent_btn = QtWidgets.QPushButton("Load")
        self.delete_recent_btn = QtWidgets.QPushButton("Delete")
        recent_btns.addWidget(self.load_recent_btn)
        recent_btns.addWidget(self.delete_recent_btn)
        right_layout.addLayout(recent_btns)

        # bottom layout to hold controls and recent list
        bottom_layout = QtWidgets.QHBoxLayout()
        left_widget = QtWidgets.QWidget()
        left_layout_wrapper = QtWidgets.QVBoxLayout(left_widget)
        left_layout_wrapper.setContentsMargins(0, 0, 0, 0)
        left_layout_wrapper.addLayout(controls_layout)
        left_layout_wrapper.addStretch()
        bottom_layout.addWidget(left_widget, 2)
        bottom_layout.addWidget(right_section, 1)
        main_layout.addLayout(bottom_layout)

        # Status bar
        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)

        # Menu
        menu = self.menuBar()
        examples_menu = menu.addMenu("Examples")
        ex1 = QtGui.QAction("1. Find PDFs on example.com", self)
        ex1.triggered.connect(self._example_1)
        examples_menu.addAction(ex1)
        ex2 = QtGui.QAction("2. Exact phrase + exclude", self)
        ex2.triggered.connect(self._example_2)
        examples_menu.addAction(ex2)
        ex3 = QtGui.QAction("3. Price range for laptops", self)
        ex3.triggered.connect(self._example_3)
        examples_menu.addAction(ex3)
        ex4 = QtGui.QAction("4. Recipes with ingredients OR", self)
        ex4.triggered.connect(self._example_4)
        examples_menu.addAction(ex4)
        ex5 = QtGui.QAction("5. News articles in last month", self)
        ex5.triggered.connect(self._example_5)
        examples_menu.addAction(ex5)
        ex6 = QtGui.QAction("6. Tutorials in URL", self)
        ex6.triggered.connect(self._example_6)
        examples_menu.addAction(ex6)
        ex7 = QtGui.QAction("7. Files excluding certain types", self)
        ex7.triggered.connect(self._example_7)
        examples_menu.addAction(ex7)
        ex8 = QtGui.QAction("8. Books in title", self)
        ex8.triggered.connect(self._example_8)
        examples_menu.addAction(ex8)
        ex9 = QtGui.QAction("9. Events in specific year range", self)
        ex9.triggered.connect(self._example_9)
        examples_menu.addAction(ex9)
        ex10 = QtGui.QAction("10. Products in price range with unit", self)
        ex10.triggered.connect(self._example_10)
        examples_menu.addAction(ex10)
        ex11 = QtGui.QAction("11. Research papers on site", self)
        ex11.triggered.connect(self._example_11)
        examples_menu.addAction(ex11)
        ex12 = QtGui.QAction("12. Quotes exact phrase", self)
        ex12.triggered.connect(self._example_12)
        examples_menu.addAction(ex12)
        ex13 = QtGui.QAction("13. Exclude common sites", self)
        ex13.triggered.connect(self._example_13)
        examples_menu.addAction(ex13)
        ex14 = QtGui.QAction("14. Images filetype", self)
        ex14.triggered.connect(self._example_14)
        examples_menu.addAction(ex14)
        ex15 = QtGui.QAction("15. Videos in URL", self)
        ex15.triggered.connect(self._example_15)
        examples_menu.addAction(ex15)
        ex16 = QtGui.QAction("16. All words in text", self)
        ex16.triggered.connect(self._example_16)
        examples_menu.addAction(ex16)
        ex17 = QtGui.QAction("17. Links to page with anchor", self)
        ex17.triggered.connect(self._example_17)
        examples_menu.addAction(ex17)
        ex18 = QtGui.QAction("18. Date range for historical events", self)
        ex18.triggered.connect(self._example_18)
        examples_menu.addAction(ex18)
        ex19 = QtGui.QAction("19. Number range without unit", self)
        ex19.triggered.connect(self._example_19)
        examples_menu.addAction(ex19)
        ex20 = QtGui.QAction("20. Combined operators", self)
        ex20.triggered.connect(self._example_20)
        examples_menu.addAction(ex20)
        help_menu = menu.addMenu("Help")
        about_action = QtGui.QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        # ---------- Event wiring ----------
        text_fields = [
            self.all_input,
            self.exact_input,
            self.exclude_input,
            self.site_input,
            self.filetype_input,
            self.intitle_input,
            self.inurl_input,
            self.or_input,
            self.range_from,
            self.range_to,
            self.range_unit,
        ]
        for w in text_fields:
            w.textChanged.connect(self.update_preview)

        # combo changes
        self.terms_combo.currentIndexChanged.connect(self.update_preview)

        # date edits & checkboxes should update preview
        self.after_checkbox.toggled.connect(self.update_preview)
        self.before_checkbox.toggled.connect(self.update_preview)
        self.after_dateedit.dateChanged.connect(self.update_preview)
        self.before_dateedit.dateChanged.connect(self.update_preview)

        # Connect buttons (slots accept optional args)
        self.copy_btn.clicked.connect(self.copy_query)
        self.open_btn.clicked.connect(self.open_in_browser)
        self.save_btn.clicked.connect(self.save_current_query)
        self.clear_btn.clicked.connect(self.clear_all)
        self.load_recent_btn.clicked.connect(self.load_selected_recent)
        self.delete_recent_btn.clicked.connect(self.delete_selected_recent)
        self.recent_list.itemDoubleClicked.connect(self.load_selected_recent)

        # keyboard shortcuts
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self, activated=self.open_in_browser)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Enter"), self, activated=self.open_in_browser)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+C"), self, activated=self.copy_query)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self, activated=self.save_current_query)

        # load recent
        self._recent_data: List[dict] = []
        self.load_recent_from_disk()

        # initial preview
        self.update_preview()

        # style
        self._apply_fusion_dark_mode()

    def _apply_fusion_dark_mode(self):
        QtWidgets.QApplication.setStyle("Fusion")
        dark_palette = QtGui.QPalette()
        dark_palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(255, 255, 255))
        dark_palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(35, 35, 35))
        dark_palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor(255, 255, 255))
        dark_palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor(255, 255, 255))
        dark_palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(220, 220, 220))
        dark_palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(255, 255, 255))
        dark_palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtGui.QColor(255, 0, 0))
        dark_palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(42, 130, 218))
        dark_palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(0, 0, 0))
        QtWidgets.QApplication.setPalette(dark_palette)

    def gather_parts(self) -> SearchParts:
        after_str = ""
        before_str = ""

        if self.after_checkbox.isChecked():
            after_qdate = self.after_dateedit.date()
            after_str = after_qdate.toString("yyyy-MM-dd")

        if self.before_checkbox.isChecked():
            before_qdate = self.before_dateedit.date()
            before_str = before_qdate.toString("yyyy-MM-dd")

        terms_location_map = {
            "anywhere in the page": "anywhere",
            "in the title of the page": "title",
            "in the text of the page": "text",
            "in the URL of the page": "url",
            "in links to the page": "links",
        }
        terms_location = terms_location_map[self.terms_combo.currentText()]

        specific_color = ""
        if self.color_combo.currentText() == "Specific color":
            specific_color = self.specific_color_combo.currentText()

        return SearchParts(
            all_words=self.all_input.text(),
            terms_location=terms_location,
            exact_phrase=self.exact_input.text(),
            exclude_words=self.exclude_input.text(),
            or_words=self.or_input.text(),
            site=self.site_input.text(),
            filetype=self.filetype_input.text(),
            intitle=self.intitle_input.text(),
            inurl=self.inurl_input.text(),
            range_from=self.range_from.text(),
            range_to=self.range_to.text(),
            range_unit=self.range_unit.text(),
            before=before_str,
            after=after_str,
            search_type=self.search_type_combo.currentText(),
            image_size=self.image_size_combo.currentText(),
            aspect_ratio=self.aspect_combo.currentText(),
            color_filter=self.color_combo.currentText(),
            specific_color=specific_color,
            image_type=self.image_type_combo.currentText(),
            region=self.region_combo.currentText(),
            usage_rights=self.usage_combo.currentText(),
        )

    def update_preview(self):
        sp = self.gather_parts()
        q = sp.build_query()
        if not q:
            self.preview.setPlainText("<empty — enter search terms>")
            return

        url_frag = "q=" + quote_plus(q)
        search_type = self.search_type_combo.currentText()
        tbm_map = {
            "Images": "isch",
            "Videos": "vid",
            "News": "nws",
        }
        if search_type in tbm_map:
            url_frag += "&tbm=" + tbm_map[search_type]

        if search_type == "Images":
            tbs_parts = []
            size_map = {
                "Large": "isz:l",
                "Medium": "isz:m",
                "Icon": "isz:i",
            }
            if sp.image_size in size_map:
                tbs_parts.append(size_map[sp.image_size])

            aspect_map = {
                "Square": "iar:s",
                "Tall": "iar:t",
                "Wide": "iar:w",
                "Panoramic": "iar:xw",
            }
            if sp.aspect_ratio in aspect_map:
                tbs_parts.append(aspect_map[sp.aspect_ratio])

            color_map = {
                "Full color": "ic:color",
                "Black and white": "ic:gray",
                "Transparent": "ic:trans",
            }
            if sp.color_filter in color_map:
                tbs_parts.append(color_map[sp.color_filter])
            elif sp.color_filter == "Specific color" and sp.specific_color:
                spec_map = {
                    "Black": "isc:black",
                    "Blue": "isc:blue",
                    "Brown": "isc:brown",
                    "Gray": "isc:gray",
                    "Green": "isc:green",
                    "Orange": "isc:orange",
                    "Pink": "isc:pink",
                    "Purple": "isc:purple",
                    "Red": "isc:red",
                    "Teal": "isc:teal",
                    "White": "isc:white",
                    "Yellow": "isc:yellow",
                }
                if sp.specific_color in spec_map:
                    tbs_parts.append(spec_map[sp.specific_color])

            type_map = {
                "Face": "itp:face",
                "Photo": "itp:photo",
                "Clip art": "itp:clipart",
                "Line drawing": "itp:lineart",
                "Animated": "itp:animated",
            }
            if sp.image_type in type_map:
                tbs_parts.append(type_map[sp.image_type])

            usage_map = {
                "Free to use or share": "sur:f",
                "Free to use or share commercially": "sur:fc",
                "Free to use or share or modify": "sur:fm",
                "Free to use or share or modify commercially": "sur:fmc",
            }
            if sp.usage_rights in usage_map:
                tbs_parts.append(usage_map[sp.usage_rights])

            if tbs_parts:
                url_frag += "&tbs=" + ",".join(tbs_parts)

            if sp.region in self.region_map:
                url_frag += "&cr=" + self.region_map[sp.region]

        self.preview.setPlainText(url_frag)
        self.status.showMessage("Preview updated", 1000)

    def copy_query(self, *_args):
        q = self.preview.toPlainText().strip()
        if not q or q.startswith("<empty"):
            self.status.showMessage("Nothing to copy", 2000)
            return
        QtWidgets.QApplication.clipboard().setText(q)
        self.status.showMessage("Query copied to clipboard", 2000)

    def open_in_browser(self, *_args):
        preview = self.preview.toPlainText().strip()
        if not preview or preview.startswith("<empty"):
            self.status.showMessage("Nothing to search", 2000)
            return
        url = "https://www.google.com/search?" + preview
        webbrowser.open(url)
        self.status.showMessage("Opened browser", 2000)

    def save_current_query(self, *_args):
        text_q = self.gather_parts().build_query()
        if not text_q:
            self.status.showMessage("Nothing to save", 2000)
            return
        parts = self.gather_parts().__dict__
        entry = {"query": text_q, "parts": parts}
        # dedupe recent
        self._recent_data = [e for e in self._recent_data if e["query"] != text_q]
        self._recent_data.insert(0, entry)
        self._recent_data = self._recent_data[:MAX_RECENT]
        self._write_recent_to_disk()
        self._refresh_recent_list()
        self.status.showMessage("Saved to recent", 2000)

    def load_selected_recent(self, item=None):
        # Defensive: item may be QListWidgetItem, bool (from button click), or None
        if isinstance(item, QtWidgets.QListWidgetItem):
            selected_item = item
        else:
            selected_item = self.recent_list.currentItem()

        if selected_item is None:
            self.status.showMessage("No recent item selected", 2000)
            return

        idx = self.recent_list.row(selected_item)
        if idx < 0 or idx >= len(self._recent_data):
            self.status.showMessage("Invalid recent selection", 2000)
            return

        data = self._recent_data[idx]
        parts = data.get("parts", {})
        # populate fields
        self.all_input.setText(parts.get("all_words", ""))
        terms_location_map_rev = {
            "anywhere": "anywhere in the page",
            "title": "in the title of the page",
            "text": "in the text of the page",
            "url": "in the URL of the page",
            "links": "in links to the page",
        }
        self.terms_combo.setCurrentText(terms_location_map_rev.get(parts.get("terms_location", "anywhere"), "anywhere in the page"))
        self.exact_input.setText(parts.get("exact_phrase", ""))
        self.exclude_input.setText(parts.get("exclude_words", ""))
        self.or_input.setText(parts.get("or_words", ""))
        self.site_input.setText(parts.get("site", ""))
        self.filetype_input.setText(parts.get("filetype", ""))
        self.intitle_input.setText(parts.get("intitle", ""))
        self.inurl_input.setText(parts.get("inurl", ""))
        self.range_from.setText(parts.get("range_from", ""))
        self.range_to.setText(parts.get("range_to", ""))
        self.range_unit.setText(parts.get("range_unit", ""))

        # image options
        self.image_size_combo.setCurrentText(parts.get("image_size", "Any size"))
        self.aspect_combo.setCurrentText(parts.get("aspect_ratio", "Any aspect ratio"))
        self.color_combo.setCurrentText(parts.get("color_filter", "Any color"))
        self.specific_color_combo.setCurrentText(parts.get("specific_color", "Red"))
        self.specific_color_combo.setVisible(self.color_combo.currentText() == "Specific color")
        self.image_type_combo.setCurrentText(parts.get("image_type", "Any type"))
        self.region_combo.setCurrentText(parts.get("region", "Any region"))
        self.usage_combo.setCurrentText(parts.get("usage_rights", "All"))

        self.search_type_combo.setCurrentText(parts.get("search_type", "Web"))

        # restore dates and checkboxes
        before_val = parts.get("before", "")
        after_val = parts.get("after", "")
        if after_val:
            qd = QtCore.QDate.fromString(after_val, "yyyy-MM-dd")
            if qd.isValid():
                self.after_dateedit.setDate(qd)
                self.after_checkbox.setChecked(True)
            else:
                self.after_checkbox.setChecked(False)
        else:
            self.after_checkbox.setChecked(False)

        if before_val:
            qd = QtCore.QDate.fromString(before_val, "yyyy-MM-dd")
            if qd.isValid():
                self.before_dateedit.setDate(qd)
                self.before_checkbox.setChecked(True)
            else:
                self.before_checkbox.setChecked(False)
        else:
            self.before_checkbox.setChecked(False)

        self.update_preview()
        self.status.showMessage("Loaded recent search", 2000)

    def delete_selected_recent(self, *_args):
        item = self.recent_list.currentItem()
        if not item:
            self.status.showMessage("Select an item to delete", 2000)
            return
        idx = self.recent_list.row(item)
        if idx < 0 or idx >= len(self._recent_data):
            self.status.showMessage("Invalid item selected", 2000)
            return
        try:
            del self._recent_data[idx]
            self._write_recent_to_disk()
            self._refresh_recent_list()
            self.status.showMessage("Deleted recent item", 2000)
        except Exception as e:
            self.status.showMessage(f"Failed to delete: {e}", 3000)

    def clear_all(self, *_args):
        self.all_input.clear()
        self.terms_combo.setCurrentIndex(0)
        self.exact_input.clear()
        self.exclude_input.clear()
        self.or_input.clear()
        self.site_input.clear()
        self.filetype_input.clear()
        self.intitle_input.clear()
        self.inurl_input.clear()
        self.range_from.clear()
        self.range_to.clear()
        self.range_unit.clear()
        self.after_checkbox.setChecked(False)
        self.before_checkbox.setChecked(False)
        self.search_type_combo.setCurrentIndex(0)
        self.image_size_combo.setCurrentIndex(0)
        self.aspect_combo.setCurrentIndex(0)
        self.color_combo.setCurrentIndex(0)
        self.specific_color_combo.setCurrentIndex(0)
        self.specific_color_combo.setVisible(False)
        self.image_type_combo.setCurrentIndex(0)
        self.region_combo.setCurrentIndex(0)
        self.usage_combo.setCurrentIndex(0)
        self.update_preview()
        self.status.showMessage("All fields cleared", 2000)

    def set_date_preset(self, days=0, months=0, years=0):
        current = QtCore.QDate.currentDate()
        if days:
            preset_date = current.addDays(-days)
        elif months:
            preset_date = current.addMonths(-months)
        elif years:
            preset_date = current.addYears(-years)
        else:
            return
        self.after_dateedit.setDate(preset_date)
        self.after_checkbox.setChecked(True)
        self.before_checkbox.setChecked(False)
        self.update_preview()
        self.status.showMessage("Date preset applied", 2000)

    def _write_recent_to_disk(self):
        try:
            config = ConfigParser()
            config['Recent'] = {}
            for i, entry in enumerate(self._recent_data, 1):
                config['Recent'][f'query_{i}'] = entry['query']
                config['Recent'][f'parts_{i}'] = json.dumps(entry['parts'])
            with open(RECENT_FILENAME, "w", encoding="utf-8") as f:
                config.write(f)
        except Exception as e:
            self.status.showMessage(f"Could not write recent file: {e}", 4000)

    def load_recent_from_disk(self):
        if not RECENT_FILENAME.exists():
            self._recent_data = []
            self._write_recent_to_disk()  # Create the file with current (empty) settings
            self._refresh_recent_list()
            return
        try:
            config = ConfigParser()
            config.read(RECENT_FILENAME)
            self._recent_data = []
            if 'Recent' in config:
                section = config['Recent']
                i = 1
                while f'query_{i}' in section:
                    query = section[f'query_{i}']
                    parts_str = section.get(f'parts_{i}', '{}')
                    parts = json.loads(parts_str)
                    self._recent_data.append({'query': query, 'parts': parts})
                    i += 1
        except Exception as e:
            self.status.showMessage(f"Could not load recent file: {e}", 4000)
            self._recent_data = []
        self._refresh_recent_list()

    def _refresh_recent_list(self):
        self.recent_list.clear()
        for entry in self._recent_data:
            q = entry.get("query", "")
            item = QtWidgets.QListWidgetItem(q)
            self.recent_list.addItem(item)

    def _example_1(self):
        self.all_input.setText("annual report")
        self.site_input.setText("example.com")
        self.filetype_input.setText("pdf")
        self.after_dateedit.setDate(QtCore.QDate.currentDate().addYears(-1))
        self.after_checkbox.setChecked(True)
        self.update_preview()

    def _example_2(self):
        self.exact_input.setText("system failure analysis")
        self.exclude_input.setText("draft sample")
        self.update_preview()

    def _example_3(self):
        self.all_input.setText("laptop")
        self.range_from.setText("500")
        self.range_to.setText("1000")
        self.range_unit.setText("$")
        self.update_preview()

    def _example_4(self):
        self.all_input.setText("recipe")
        self.or_input.setText("chicken|beef|tofu")
        self.exclude_input.setText("fried")
        self.update_preview()

    def _example_5(self):
        self.all_input.setText("climate change")
        self.site_input.setText("news.com")
        self.set_date_preset(months=1)
        self.update_preview()

    def _example_6(self):
        self.all_input.setText("python tutorial")
        self.inurl_input.setText("beginner")
        self.update_preview()

    def _example_7(self):
        self.all_input.setText("project management")
        self.filetype_input.setText("pdf")
        self.exclude_input.setText("pptx xlsx")
        self.update_preview()

    def _example_8(self):
        self.intitle_input.setText("best books 2023")
        self.update_preview()

    def _example_9(self):
        self.all_input.setText("olympic games")
        self.range_from.setText("2000")
        self.range_to.setText("2020")
        self.update_preview()

    def _example_10(self):
        self.all_input.setText("smartphone")
        self.range_from.setText("200")
        self.range_to.setText("500")
        self.range_unit.setText("€")
        self.update_preview()

    def _example_11(self):
        self.all_input.setText("machine learning")
        self.site_input.setText("arxiv.org")
        self.filetype_input.setText("pdf")
        self.update_preview()

    def _example_12(self):
        self.exact_input.setText("to be or not to be")
        self.all_input.setText("shakespeare")
        self.update_preview()

    def _example_13(self):
        self.all_input.setText("diy home repair")
        self.exclude_input.setText("youtube pinterest")
        self.update_preview()

    def _example_14(self):
        self.all_input.setText("mountain landscape")
        self.filetype_input.setText("jpg")
        self.search_type_combo.setCurrentText("Images")
        self.update_preview()

    def _example_15(self):
        self.all_input.setText("cooking tutorial")
        self.inurl_input.setText("video")
        self.search_type_combo.setCurrentText("Videos")
        self.update_preview()

    def _example_16(self):
        self.all_input.setText("quantum computing basics")
        self.terms_combo.setCurrentText("in the text of the page")
        self.update_preview()

    def _example_17(self):
        self.all_input.setText("recommended reading")
        self.terms_combo.setCurrentText("in links to the page")
        self.update_preview()

    def _example_18(self):
        self.all_input.setText("world war ii")
        self.after_dateedit.setDate(QtCore.QDate(1939, 1, 1))
        self.after_checkbox.setChecked(True)
        self.before_dateedit.setDate(QtCore.QDate(1945, 12, 31))
        self.before_checkbox.setChecked(True)
        self.update_preview()

    def _example_19(self):
        self.all_input.setText("population statistics")
        self.range_from.setText("1000000")
        self.range_to.setText("10000000")
        self.update_preview()

    def _example_20(self):
        self.all_input.setText("electric car")
        self.or_input.setText("tesla|rivian|nissan")
        self.exclude_input.setText("used")
        self.site_input.setText("reviews.com")
        self.intitle_input.setText("2023")
        self.update_preview()

    def _show_about(self):
        QtWidgets.QMessageBox.about(
            self,
            "About",
            f"{APP_NAME}\n\nBuild advanced Google queries with operators and open them in your browser.\n\nMade with PyQt6.\nProgrammer: Bob Paydar",
        )


def main(argv):
    app = QtWidgets.QApplication(argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main(sys.argv)