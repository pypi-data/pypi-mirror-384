import os
import shutil
from pathlib import Path
import logging
from qtpy.QtWidgets import (
    QDockWidget,
    QTreeView,
    QFileDialog,
    QMenu,
    QMessageBox,
    QInputDialog,
    QWidget,
    QVBoxLayout,
    QCheckBox,
    QShortcut
)
from qtpy.QtCore import Qt, QDir, QModelIndex, QSortFilterProxyModel, QUrl, \
    Signal
from qtpy.QtWidgets import QFileSystemModel
from qtpy.QtGui import QDesktopServices, QKeySequence
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern
from .. import settings, themes

logger = logging.getLogger(__name__)

class LazyQFileSystemModel(QFileSystemModel):
    """A QFileSystemModel that only fetches children for 'expanded' paths.
    This prevents eagerly creating inotify watchers for large, collapsed directories.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded_paths = set()

    def setRootPath(self, root):
        idx = super().setRootPath(root)
        # Ensure the root path is always considered expanded
        if root:
            self._expanded_paths.add(root)
            # Force a fetch so we see the root directory contents
            if idx.isValid() and super().canFetchMore(idx):
                super().fetchMore(idx)
        return idx

    def notify_path_expanded(self, path):
        self._expanded_paths.add(path)
        # Manually trigger fetch
        index = self.index(path)
        if super().canFetchMore(index):
            super().fetchMore(index)

    def notify_path_collapsed(self, path):
        if path in self._expanded_paths:
            self._expanded_paths.remove(path)

    def canFetchMore(self, index):
        if not index.isValid():
            return super().canFetchMore(index)
        path = self.filePath(index)
        # Only allow fetch if path is in expanded set
        if path in self._expanded_paths:
            return super().canFetchMore(index)
        return False

    def fetchMore(self, index):
        if not index.isValid():
            return super().fetchMore(index)
        path = self.filePath(index)
        # Only do the actual fetch for expanded paths
        if path in self._expanded_paths:
            return super().fetchMore(index)

class GitignoreFilterProxyModel(QSortFilterProxyModel):
    """A QSortFilterProxyModel that hides paths ignored by .gitignore (when enabled).
    Parses .gitignore with pathspec. Also forwards hasChildren/fetchMore to the source
    model so that folders may be expanded.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gitignore_enabled = False
        self.root_folder = None
        self.pathspec = None

    def set_root_folder(self, folder):
        """Load .gitignore (if present) from 'folder' and parse it into a PathSpec.
        Keep the folder path for computing relative paths.
        """
        self.root_folder = folder
        self.pathspec = None
        if not self.gitignore_enabled:
            return

        gitignore_path = os.path.join(folder, '.gitignore')
        if os.path.isfile(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    patterns = f.read().splitlines()
                # Use GitWildMatchPattern to mimic .gitignore logic
                self.pathspec = PathSpec.from_lines(GitWildMatchPattern, patterns)
            except Exception as e:
                logger.warning(f"Failed to parse .gitignore: {e}")

    def filterAcceptsRow(self, source_row, source_parent):
        # If not enabled or we have no pathspec, pass everything
        if not self.gitignore_enabled or not self.pathspec:
            return True

        index = self.sourceModel().index(source_row, 0, source_parent)
        if not index.isValid():
            return True

        source_model = self.sourceModel()
        abs_path = source_model.filePath(index)
        # Make sure our designated root folder is never hidden
        if abs_path == self.root_folder:
            return True
        if not self.root_folder:
            return True
        # Always keep directories. We need to be able to look inside them
        # because their children might be re-included by negated patterns in
        # .gitignore.
        if source_model.isDir(index):
            return True
        # Ignore explicitly ignored folders
        path_parts = Path(abs_path).parts
        if any(ignored in path_parts for ignored in settings.ignored_folders):
            return False
        # Compute relative path from the repository root
        rel_path = os.path.relpath(abs_path, self.root_folder)
        # If matched by pathspec => it is ignored => filter out
        return not self.pathspec.match_file(rel_path)

    # ----------------------
    # Overridden methods to ensure directories can still expand
    # ----------------------

    def hasChildren(self, parent):
        """Delegate hasChildren to the source model so the tree can show expandable folders."""
        source_index = self.mapToSource(parent)
        return self.sourceModel().hasChildren(source_index)

    def canFetchMore(self, parent):
        """Ask the source model if it can fetch more items for lazy loading."""
        source_index = self.mapToSource(parent)
        return self.sourceModel().canFetchMore(source_index)

    def fetchMore(self, parent):
        """Delegate fetchMore to the source model so subfolders are properly loaded."""
        source_index = self.mapToSource(parent)
        self.sourceModel().fetchMore(source_index)

class ProjectExplorer(QDockWidget):

    closed = Signal(object)

    def __init__(self, editor_panel, root_path=None, parent=None):
        super().__init__(os.path.basename(root_path), parent)
        self._editor_panel = editor_panel

        # Our local "clipboard" for cut/copy/paste
        self._clipboard_operation = None  # 'cut' or 'copy'
        self._clipboard_source_path = None

        # Underlying LazyQFileSystemModel
        self._model = LazyQFileSystemModel(self)

        # Add a filter proxy to hide items from .gitignore if enabled
        self._filter_proxy = GitignoreFilterProxyModel(self)
        self._filter_proxy.setSourceModel(self._model)

        self._display_root = root_path or QDir.currentPath()

        # Create a container widget and layout, so we can have the treeview + an optional checkbox
        container_widget = QWidget(self)
        layout = QVBoxLayout(container_widget)
        layout.setContentsMargins(*themes.OUTER_CONTENT_MARGINS)

        # Create our TreeView and attach the proxy model
        self._tree_view = QTreeView(container_widget)
        self._tree_view.setModel(self._filter_proxy)
        layout.addWidget(self._tree_view)

        # Connect expanded/collapsed signals through the proxy => model
        self._tree_view.expanded.connect(self._on_expanded_proxy)
        self._tree_view.collapsed.connect(self._on_collapsed_proxy)

        # Optional: Hide columns other than the file name
        self._set_single_column_view(True)

        # Only if .gitignore exists in the root, create the checkbox
        gitignore_path = os.path.join(self._display_root, '.gitignore')
        if os.path.isfile(gitignore_path):
            # Enabled by default
            self._gitignore_checkbox = QCheckBox("Use .gitignore", container_widget)
            self._gitignore_checkbox.setChecked(True)
            # Connect toggling to set_gitignore_enabled
            self._gitignore_checkbox.toggled.connect(self._toggle_gitignore)
            layout.addWidget(self._gitignore_checkbox)
            self._toggle_gitignore(True)
        else:
            self._toggle_gitignore(False)

        # Configure QTreeView
        self._tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree_view.customContextMenuRequested.connect(self._show_context_menu)
        self._tree_view.doubleClicked.connect(self._on_double_click)

        # Set our container widget as the dock widget's main widget
        self.setWidget(container_widget)

        # Set up global keyboard shortcuts
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """Set up keyboard shortcuts for common actions."""
        shortcut_f2 = QShortcut(QKeySequence("F2"), self)
        shortcut_f2.setContext(Qt.WidgetWithChildrenShortcut)
        shortcut_f2.activated.connect(lambda: self._handle_rename_shortcut())
        
        shortcut_delete = QShortcut(QKeySequence.Delete, self)
        shortcut_delete.setContext(Qt.WidgetWithChildrenShortcut)
        shortcut_delete.activated.connect(lambda: self._handle_delete_shortcut())
        
        shortcut_cut = QShortcut(QKeySequence.Cut, self)
        shortcut_cut.setContext(Qt.WidgetWithChildrenShortcut)
        shortcut_cut.activated.connect(lambda: self._handle_cut_shortcut())
        
        shortcut_copy = QShortcut(QKeySequence.Copy, self)
        shortcut_copy.setContext(Qt.WidgetWithChildrenShortcut)
        shortcut_copy.activated.connect(lambda: self._handle_copy_shortcut())
        
        shortcut_paste = QShortcut(QKeySequence.Paste, self)
        shortcut_paste.setContext(Qt.WidgetWithChildrenShortcut)
        shortcut_paste.activated.connect(lambda: self._handle_paste_shortcut())

    def _handle_rename_shortcut(self):
        """Handle F2 shortcut for rename."""
        proxy_index = self._tree_view.selectionModel().currentIndex()
        if proxy_index.isValid():
            source_index = self._filter_proxy.mapToSource(proxy_index)
            if source_index.isValid():
                path = self._model.filePath(source_index)
                self._rename_file_or_folder(path)

    def _handle_delete_shortcut(self):
        """Handle Delete shortcut for delete."""
        proxy_index = self._tree_view.selectionModel().currentIndex()
        if proxy_index.isValid():
            source_index = self._filter_proxy.mapToSource(proxy_index)
            if source_index.isValid():
                path = self._model.filePath(source_index)
                self._delete_file_or_folder(path)

    def _handle_cut_shortcut(self):
        """Handle Ctrl+X shortcut for cut."""
        proxy_index = self._tree_view.selectionModel().currentIndex()
        if proxy_index.isValid():
            source_index = self._filter_proxy.mapToSource(proxy_index)
            if source_index.isValid():
                path = self._model.filePath(source_index)
                self._clipboard_operation = 'cut'
                self._clipboard_source_path = path

    def _handle_copy_shortcut(self):
        """Handle Ctrl+C shortcut for copy."""
        proxy_index = self._tree_view.selectionModel().currentIndex()
        if proxy_index.isValid():
            source_index = self._filter_proxy.mapToSource(proxy_index)
            if source_index.isValid():
                path = self._model.filePath(source_index)
                self._clipboard_operation = 'copy'
                self._clipboard_source_path = path

    def _handle_paste_shortcut(self):
        """Handle Ctrl+V shortcut for paste."""
        if not self._clipboard_source_path:
            return

        if not self._tree_view.selectionModel().hasSelection():
            # Paste into root if nothing is selected
            root_path = self._model.rootPath()
            if os.path.isdir(root_path):
                self._paste_file_or_folder(root_path)
        else:
            proxy_index = self._tree_view.selectionModel().currentIndex()
            source_index = self._filter_proxy.mapToSource(proxy_index)
            if source_index.isValid():
                path = self._model.filePath(source_index)
                if os.path.isdir(path):
                    self._paste_file_or_folder(path)
                else:
                    # If a file is selected, use its directory
                    self._paste_file_or_folder(os.path.dirname(path))

    def list_files(self) -> list[str]:
        """Returns a list of all non-ignored files under the display root,
        applying the same .gitignore-based logic.
        If there are more than max_files files, returns empty list.
        """
        if not self._display_root:
            return []

        results = []
        gitignore_enabled = self._filter_proxy.gitignore_enabled
        pathspec = self._filter_proxy.pathspec
        # Recursively walk the filesystem from _display_root
        for dirpath, dirnames, filenames in os.walk(self._display_root):
            path_parts = Path(dirpath).parts
            if any(ignored in path_parts for ignored in settings.ignored_folders):
                continue
            # Now gather files that are not ignored
            for f in filenames:
                abs_file = os.path.normpath(os.path.join(dirpath, f))
                # Avoid filtering _display_root, though it shouldn't typically be a file
                if abs_file == self._display_root:
                    continue

                if gitignore_enabled and pathspec:
                    rel_file = os.path.relpath(abs_file, self._display_root)
                    # If pathspec matches => "ignored"
                    if pathspec.match_file(rel_file):
                        continue
                results.append(abs_file)
                if len(results) > settings.max_files:
                    logger.warning("Too many files in project")
                    return []

        return results

    @classmethod
    def open_folder(cls, editor_panel, parent=None) -> object | None:
        """Shows a folder picker dialog to open a folder.
        If a folder is selected, a ProjectExplorer instance is created and returned.
        Otherwise None is returned.
        """
        options = QFileDialog.Options(QFileDialog.ShowDirsOnly)
        if os.environ.get("DONT_USE_NATIVE_FILE_DIALOG", False):
            options |= QFileDialog.Option.DontUseNativeDialog
            logger.info('not using native file dialog')
        selected_dir = QFileDialog.getExistingDirectory(parent,
            "Open Project Folder", "", options=options)
        if not selected_dir:
            return None
        settings.current_folder = selected_dir
        # Add selected folder to project folders but make sure we don't
        # duplicate
        settings.project_folders = '::'.join(
            set(str(settings.project_folders).split('::')) | {selected_dir})
        explorer = cls(editor_panel, root_path=selected_dir, parent=parent)
        return explorer

    def _toggle_gitignore(self, enabled):
        """Toggles the .gitignore filter on or off and refreshes the model.
        """
        self._filter_proxy.gitignore_enabled = enabled
        self._model.setRootPath(self._display_root)
        self._filter_proxy.set_root_folder(self._display_root)
        self._filter_proxy.invalidateFilter()
        # Make the root folder visible and expanded
        root_idx = self._model.index(self._display_root)
        if root_idx.isValid():
            proxy_root_index = self._filter_proxy.mapFromSource(root_idx)
            self._tree_view.setRootIndex(proxy_root_index)
            # Expand the root so it behaves like an expanded folder
            self._tree_view.expand(proxy_root_index)

    def _on_expanded_proxy(self, proxy_index):
        """Convert the proxy index to the source model index and notify LazyQFileSystemModel.
        """
        source_index = self._filter_proxy.mapToSource(proxy_index)
        if source_index.isValid():
            path = self._model.filePath(source_index)
            self._model.notify_path_expanded(path)

    def _on_collapsed_proxy(self, proxy_index):
        """Convert the proxy index to the source model index and notify LazyQFileSystemModel.
        """
        source_index = self._filter_proxy.mapToSource(proxy_index)
        if source_index.isValid():
            path = self._model.filePath(source_index)
            self._model.notify_path_collapsed(path)

    def _set_single_column_view(self, single_column=True):
        """If single_column=True, show only the file name column with no header."""
        if single_column:
            # Hide columns 1,2,3 (Size, Type, Date Modified) and hide the header
            self._tree_view.setHeaderHidden(True)
            for col in range(1, 4):
                self._tree_view.setColumnHidden(col, True)
        else:
            # Show all columns and show the header
            self._tree_view.setHeaderHidden(False)
            for col in range(1, 4):
                self._tree_view.setColumnHidden(col, False)

    def _on_double_click(self, proxy_index: QModelIndex):
        """Open file on double-click if it's not a directory."""
        source_index = self._filter_proxy.mapToSource(proxy_index)
        path = self._model.filePath(source_index)
        if os.path.isfile(path):
            logger.info(f"Double-click opening file: {path}")
            self._editor_panel.open_file(path)
        else:
            logger.info(f"Double-clicked on directory: {path}")

    def _show_context_menu(self, pos):
        """Build and show a context menu on right-click."""
        proxy_index = self._tree_view.indexAt(pos)
        source_index = self._filter_proxy.mapToSource(proxy_index)

        menu = QMenu(self)

        if not source_index.isValid():
            # Clicked on empty space
            new_file_action = menu.addAction("New File…")
            new_folder_action = menu.addAction("New Folder…")
            chosen_action = menu.exec_(self._tree_view.mapToGlobal(pos))

            if chosen_action == new_file_action:
                root_path = self._model.rootPath()
                if os.path.isdir(root_path):
                    self._create_new_file(root_path)
            elif chosen_action == new_folder_action:
                root_path = self._model.rootPath()
                if os.path.isdir(root_path):
                    self._create_new_folder(root_path)

        else:
            path = self._model.filePath(source_index)
            is_file = os.path.isfile(path)

            if is_file:
                # Right-clicked on a file
                open_action = menu.addAction("Open")
                open_sys_action = menu.addAction("Open containing folder")
                rename_action = menu.addAction("Rename…")
                rename_action.setShortcut(QKeySequence("F2"))
                delete_action = menu.addAction("Delete")
                delete_action.setShortcut(QKeySequence.Delete)

                menu.addSeparator()
                cut_action = menu.addAction("Cut")
                cut_action.setShortcut(QKeySequence.Cut)
                copy_action = menu.addAction("Copy")
                copy_action.setShortcut(QKeySequence.Copy)
                paste_action = menu.addAction("Paste")
                paste_action.setShortcut(QKeySequence.Paste)
                paste_action.setEnabled(self._clipboard_source_path is not None)

                chosen_action = menu.exec_(self._tree_view.mapToGlobal(pos))
                if chosen_action == open_action:
                    self._editor_panel.open_file(path)
                elif chosen_action == open_sys_action:
                    # Open the file's parent folder
                    containing_folder = os.path.dirname(path)
                    try:
                        QDesktopServices.openUrl(QUrl.fromLocalFile(containing_folder))
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to open folder:\n{str(e)}")
                elif chosen_action == rename_action:
                    self._rename_file_or_folder(path)
                elif chosen_action == delete_action:
                    self._delete_file_or_folder(path)
                elif chosen_action == cut_action:
                    self._clipboard_operation = 'cut'
                    self._clipboard_source_path = path
                elif chosen_action == copy_action:
                    self._clipboard_operation = 'copy'
                    self._clipboard_source_path = path
                elif chosen_action == paste_action:
                    self._paste_file_or_folder(path)

            else:
                # Right-clicked on a folder
                open_action = menu.addAction("Open")
                open_action.setShortcut(QKeySequence.Open)
                open_sys_action = menu.addAction("Open folder")
                new_file_action = menu.addAction("New File…")
                new_file_action.setShortcut(QKeySequence.New)
                new_folder_action = menu.addAction("New Folder…")
                new_folder_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
                rename_action = menu.addAction("Rename…")
                rename_action.setShortcut(QKeySequence("F2"))
                delete_action = menu.addAction("Delete")
                delete_action.setShortcut(QKeySequence.Delete)

                menu.addSeparator()
                cut_action = menu.addAction("Cut")
                cut_action.setShortcut(QKeySequence.Cut)
                copy_action = menu.addAction("Copy")
                copy_action.setShortcut(QKeySequence.Copy)
                paste_action = menu.addAction("Paste")
                paste_action.setShortcut(QKeySequence.Paste)
                paste_action.setEnabled(self._clipboard_source_path is not None)

                chosen_action = menu.exec_(self._tree_view.mapToGlobal(pos))
                if chosen_action == open_action:
                    # Expand in the tree if not already expanded
                    if proxy_index.isValid() and not self._tree_view.isExpanded(proxy_index):
                        self._tree_view.expand(proxy_index)
                elif chosen_action == open_sys_action:
                    # Open the folder in system browser
                    try:
                        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to open folder:\n{str(e)}")
                elif chosen_action == new_file_action:
                    self._create_new_file(path)
                elif chosen_action == new_folder_action:
                    self._create_new_folder(path)
                elif chosen_action == rename_action:
                    self._rename_file_or_folder(path)
                elif chosen_action == delete_action:
                    self._delete_file_or_folder(path)
                elif chosen_action == cut_action:
                    self._clipboard_operation = 'cut'
                    self._clipboard_source_path = path
                elif chosen_action == copy_action:
                    self._clipboard_operation = 'copy'
                    self._clipboard_source_path = path
                elif chosen_action == paste_action:
                    self._paste_file_or_folder(path)

    def _create_new_file(self, folder):
        """Create a new file in the specified folder."""
        if not os.path.isdir(folder):
            return

        file_name, ok = QInputDialog.getText(self, "New File", "File name:")
        if not ok or not file_name:
            return

        # Add default extension if none provided
        if '.' not in file_name:
            file_name += '.txt'

        file_path = os.path.join(folder, file_name)

        try:
            with open(file_path, 'w', encoding='utf8') as f:
                f.write("")
            logger.info(f"Created file: {file_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create file:\n{str(e)}")

    def _create_new_folder(self, parent_folder):
        """Creates a new subfolder inside 'parent_folder'."""
        if not os.path.isdir(parent_folder):
            return
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if not ok or not folder_name:
            return

        new_path = os.path.join(parent_folder, folder_name)
        try:
            os.mkdir(new_path)
            logger.info(f"Created folder: {new_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create folder:\n{str(e)}")

    def _rename_file_or_folder(self, path):
        """Rename a file or folder via an input dialog, then rename in filesystem."""
        old_name = os.path.basename(path)
        parent_dir = os.path.dirname(path)
        
        # Show dialog with current name pre-filled
        new_name, ok = QInputDialog.getText(
            self, 
            "Rename", 
            f"Rename '{old_name}' to:",
            text=old_name
        )
        
        if not ok or not new_name or new_name == old_name:
            return
            
        new_path = os.path.join(parent_dir, new_name)
        
        # Check if target already exists
        if os.path.exists(new_path):
            QMessageBox.warning(self, "Error", f"'{new_name}' already exists.")
            return
            
        try:
            os.rename(path, new_path)
            logger.info(f"Renamed '{old_name}' to '{new_name}'")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to rename:\n{str(e)}")

    def _delete_file_or_folder(self, path):
        """Delete a file or entire folder."""
        reply = QMessageBox.question(
            self, "Delete",
            f"Delete '{path}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        try:
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)
            logger.info(f"Deleted: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to delete:\n{str(e)}")

    def _paste_file_or_folder(self, target_path):
        """Paste files/folders from our local 'clipboard_operation' into target_path."""
        if not self._clipboard_operation or not self._clipboard_source_path:
            return
        if os.path.isfile(target_path):
            target_path = os.path.dirname(target_path)
        if not os.path.isdir(target_path):
            QMessageBox.warning(self, "Error", "Target is not a valid folder.")
            return

        src = self._clipboard_source_path
        dst = os.path.join(target_path, os.path.basename(src))

        # Handle the case where source and destination are the same (copy operation only)
        if self._clipboard_operation == 'copy' and os.path.abspath(src) == os.path.abspath(dst):
            base_name = os.path.basename(src)
            if os.path.isfile(src) and '.' in base_name:
                # For files with extensions
                name, ext = os.path.splitext(base_name)
                dst = os.path.join(target_path, f"{name} (Copy){ext}")
            else:
                # For folders or files without extensions
                dst = os.path.join(target_path, f"{base_name} (Copy)")

            # If that name also exists, add numbers
            counter = 2
            while os.path.exists(dst):
                if os.path.isfile(src) and '.' in base_name:
                    name, ext = os.path.splitext(base_name)
                    dst = os.path.join(target_path, f"{name} (Copy {counter}){ext}")
                else:
                    dst = os.path.join(target_path, f"{base_name} (Copy {counter})")
                counter += 1

        try:
            if self._clipboard_operation == 'copy':
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            elif self._clipboard_operation == 'cut':
                shutil.move(src, dst)
            logger.info(f"{self._clipboard_operation.title()} '{src}' to '{dst}'")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to {self._clipboard_operation}:\n{str(e)}")

        self._clipboard_operation = None
        self._clipboard_source_path = None

    def closeEvent(self, event):
        # Add selected folder to project folders but make sure we don't
        # duplicate
        settings.project_folders = '::'.join(
            set(str(settings.project_folders).split('::')) - {self._display_root})
        super().closeEvent(event)
        self.closed.emit(self)