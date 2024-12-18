import sys
import os
import webbrowser
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QLineEdit, QPushButton, QToolBar, QMenu, QAction, QVBoxLayout, QTextEdit
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from pygments import highlight
from pygments.lexers import HtmlLexer
from pygments.formatters import HtmlFormatter


class BrowserTab(QWebEngineView):
    def __init__(self, parent_window, parent=None):
        super().__init__(parent)
        self.parent_window = parent_window  # Reference to BrowserWindow
        self.setUrl(QUrl("https://duckduckgo.com"))  # Default homepage
        self.setMinimumHeight(500)

        # Connect URL and title changes to handle updates
        self.urlChanged.connect(self.on_url_changed)
        self.titleChanged.connect(self.on_title_changed)

    def on_url_changed(self, url):
        """Print current URL to the terminal."""
        print(f"Currently on: {url.toString()}")

    def on_title_changed(self, title):
        """Update the tab title in the parent window."""
        self.parent_window.update_tab_title(self, title)

    def contextMenuEvent(self, event):
        """Custom right-click menu."""
        menu = QMenu(self)

        back_action = QAction("Back", self)
        back_action.triggered.connect(self.back)
        menu.addAction(back_action)

        forward_action = QAction("Forward", self)
        forward_action.triggered.connect(self.forward)
        menu.addAction(forward_action)

        reload_action = QAction("Reload", self)
        reload_action.triggered.connect(self.reload)
        menu.addAction(reload_action)

        view_source_action = QAction("View Page Source", self)
        view_source_action.triggered.connect(self.view_page_source)
        menu.addAction(view_source_action)

        open_in_default_browser_action = QAction("Open in Default Browser", self)
        open_in_default_browser_action.triggered.connect(self.open_in_default_browser)
        menu.addAction(open_in_default_browser_action)

        menu.exec_(event.globalPos())

    def view_page_source(self):
        """Load the page source in a new tab with syntax highlighting."""
        self.page().toHtml(self.show_source)

    def show_source(self, html):
        """Display the source code with syntax highlighting."""
        formatter = HtmlFormatter(full=True, linenos=True, style="monokai")
        highlighted_html = highlight(html, HtmlLexer(), formatter)

        # Create a new tab to display the source
        source_tab = QTextEdit()
        source_tab.setReadOnly(True)
        source_tab.setHtml(highlighted_html)

        # Add the source tab
        tab_index = self.parent_window.browser_tabs.addTab(source_tab, "Source Code")
        self.parent_window.browser_tabs.setCurrentIndex(tab_index)

    def open_in_default_browser(self):
        """Open the current URL in the system's default browser."""
        webbrowser.open(self.url().toString())


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Anonymous Browser")
        self.setGeometry(300, 100, 1200, 800)  # Initial window size

        # Tab management
        self.browser_tabs = QTabWidget()
        self.browser_tabs.setTabsClosable(True)  # Allow tabs to have close buttons
        self.browser_tabs.tabCloseRequested.connect(self.close_tab)  # Handle tab closing
        self.setCentralWidget(self.browser_tabs)

        # Create the first tab (homepage)
        self.create_new_tab()

        # Modern dark theme for the whole window
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
                color: #FFFFFF;
            }
            QToolBar {
                background-color: #333333;
                border: none;
            }
            QLineEdit {
                background-color: #2C2C2C;
                color: #FFFFFF;
                border: 1px solid #444444;
                padding: 6px 10px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #444444;
                color: #FFFFFF;
                border: 1px solid #666666;
                padding: 6px 12px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QTabWidget::pane {
                border: none;
                background: #181818;
                margin: 5px;
            }
            QTabBar::tab {
                background-color: #2C2C2C;
                color: #D3D3D3;
                padding: 8px;
                min-width: 100px;
                border-radius: 4px;
                border: 1px solid #444444;
            }
            QTabBar::tab:selected {
                background-color: #555555;
                color: #FFFFFF;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)

        # Create the toolbar with a search bar and buttons
        self.toolbar = QToolBar(self)
        self.search_bar = QLineEdit(self)
        self.search_button = QPushButton("Search", self)
        self.new_tab_button = QPushButton("New Tab", self)
        self.github_button = QPushButton("Visit Our GitHub", self)

        self.search_button.clicked.connect(self.perform_search)
        self.new_tab_button.clicked.connect(self.create_new_tab)
        self.github_button.clicked.connect(self.open_github)

        self.toolbar.addWidget(self.search_bar)
        self.toolbar.addWidget(self.search_button)
        self.toolbar.addWidget(self.new_tab_button)
        self.toolbar.addWidget(self.github_button)

        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

    def create_new_tab(self):
        """Create a new tab with a default homepage (DuckDuckGo)."""
        if self.browser_tabs.count() == 0:
            self.load_index_html()
        else:
            tab = BrowserTab(self)
            tab.setUrl(QUrl("https://duckduckgo.com"))
            tab.setPage(QWebEnginePage())

            tab_index = self.browser_tabs.addTab(tab, "New Tab")
            self.browser_tabs.setCurrentIndex(tab_index)

    def load_index_html(self):
        """Load the index.html from the current directory if no tabs are open."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        index_path = os.path.join(script_dir, "index.html")

        if os.path.exists(index_path):
            url = QUrl.fromLocalFile(index_path)
            index_tab = BrowserTab(self)
            index_tab.setUrl(url)

            tab_index = self.browser_tabs.addTab(index_tab, "Index Page")
            self.browser_tabs.setCurrentIndex(tab_index)
        else:
            print("index.html not found in the current directory.")

    def perform_search(self):
        """Search and load the result on the current tab or navigate to a URL."""
        query = self.search_bar.text().strip()

        if query.lower().startswith("http://") or query.lower().startswith("https://"):
            current_tab = self.browser_tabs.currentWidget()
            current_tab.setUrl(QUrl(query))
        else:
            search_url = f"https://duckduckgo.com/?q={query}"
            current_tab = self.browser_tabs.currentWidget()
            current_tab.setUrl(QUrl(search_url))

    def open_github(self):
        """Open the GitHub page in the default web browser."""
        webbrowser.open("https://github.com/TechOps29")

    def update_tab_title(self, tab, title):
        """Update the tab title when the page title changes."""
        tab_index = self.browser_tabs.indexOf(tab)
        if tab_index != -1:
            self.browser_tabs.setTabText(tab_index, title)

    def close_tab(self, index):
        """Close the tab at the given index."""
        tab = self.browser_tabs.widget(index)
        self.browser_tabs.removeTab(index)
        tab.deleteLater()

    def closeEvent(self, event):
        """Override closeEvent to ensure proper cleanup."""
        for index in range(self.browser_tabs.count()):
            tab = self.browser_tabs.widget(index)
            tab.deleteLater()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Apply global dark theme
    app.setStyle("Fusion")

    window = BrowserWindow()
    window.show()
    sys.exit(app.exec_())