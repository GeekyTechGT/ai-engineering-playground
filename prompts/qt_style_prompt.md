You are a senior UI/UX engineer specialized in Qt (Qt Widgets) and QSS.

TASK
Generate a single, production-ready Qt Style Sheet (.qss) file for a desktop application that looks modern, clean, and “premium” (2026 style). It must be consistent, readable, and easy to maintain.

REQUIREMENTS
1) Output ONLY the QSS file content (no explanations).
2) Must support both LIGHT and DARK themes in the same file using a top-level selector:
   - QWidget[theme="light"] { ... }
   - QWidget[theme="dark"]  { ... }
   Assume the application sets qApp->setProperty("theme", "dark") or sets it on a root widget.
3) Provide a “Design Tokens” section at the top as QSS comments containing:
   - base colors (background/surface/elevated/border/text/muted/accent/success/warning/error)
   - radii (xs/sm/md/lg/xl)
   - spacing (xs/sm/md/lg/xl)
   - font sizes (sm/base/lg/xl)
   - animation note (Qt has limited animations in QSS; just document interaction states)
4) Visual style:
   - Flat with subtle depth (soft borders, gentle hover, minimal gradients).
   - Rounded corners (not excessive).
   - High contrast text.
   - Accessible focus states (visible outline/ring).
   - Consistent padding and spacing.
5) Must style as many Qt Widgets as reasonably possible, including states and subcontrols:
   Core:
   - QWidget, QMainWindow, QDialog, QFrame, QGroupBox, QSplitter
   Text:
   - QLabel, QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit
   Buttons:
   - QPushButton, QToolButton, QCommandLinkButton, QDialogButtonBox
   Selection:
   - QCheckBox, QRadioButton, QComboBox, QFontComboBox
   Views:
   - QListView, QTreeView, QTableView, QHeaderView, QAbstractItemView, QColumnView, QUndoView
   Menus/Toolbars:
   - QMenuBar, QMenu, QToolBar, QStatusBar
   Navigation:
   - QTabWidget, QTabBar, QStackedWidget, QDockWidget
   Sliders/Scroll:
   - QScrollBar (horizontal/vertical + handle/add-line/sub-line), QSlider (groove/handle), QScrollArea
   Progress/Indicators:
   - QProgressBar (chunk), QBusyIndicator if present (provide generic), QToolTip
   Containers:
   - QDockWidget, QToolBox, QScrollArea
   Item delegates / selection:
   - item:selected, item:hover, item:!active, alternatingRowColors
   Dialog widgets:
   - QFileDialog, QMessageBox (best-effort)
   Advanced/common:
   - QCalendarWidget, QLCDNumber, QKeySequenceEdit, QCompleter popup, QAbstractSpinBox::up-button/down-button
   If a widget cannot be reliably styled in QSS, include best-effort selectors without breaking others.

6) Provide component variants via dynamic properties (examples):
   - QPushButton[variant="primary"], [variant="secondary"], [variant="ghost"], [variant="danger"]
   - QLineEdit[invalid="true"] for validation error state
   - QWidget[elevation="1|2"] for surfaces (optional)
   - QFrame[role="card"], QFrame[role="panel"]
7) Must include these interaction states everywhere relevant:
   - :hover, :pressed, :disabled, :focus, :checked, :selected
8) Typography:
   - Set a modern default font stack (system fonts) and font sizes.
9) Must avoid hard-to-render heavy gradients; keep performance-friendly.
10) Must not rely on external images. If icons are needed, style around them but don’t reference files.

OUTPUT FORMAT
- Start with a comment header:
  /* App Modern QSS - Generated */
  /* Theme: light + dark via QWidget[theme="..."] */
- Then tokens.
- Then base styles.
- Then widget-specific sections grouped logically with clear comment headers.

CONSTRAINTS
- Use Qt Style Sheet syntax only.
- Use concise, maintainable rules; avoid redundant duplicates where possible, but it’s okay to repeat values for clarity.
- Ensure the QSS will not make text unreadable in either theme.

OPTIONAL INPUT (if provided below, adapt the theme):
- Primary accent color: {{ACCENT_COLOR_HEX}}
- App name: {{APP_NAME}}
- Density: {{DENSITY}} (compact/comfortable)

NOW GENERATE THE FULL .qss CONTENT.