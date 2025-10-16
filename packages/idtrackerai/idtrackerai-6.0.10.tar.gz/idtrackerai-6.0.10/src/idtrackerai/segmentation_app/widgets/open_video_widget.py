from collections.abc import Sequence
from pathlib import Path

from qtpy.QtCore import Qt, Signal  # type: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QFocusEvent
from qtpy.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QListView,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from idtrackerai import IdtrackeraiError, Session
from idtrackerai.GUI_tools import GUIBase, WrappedLabel, key_event_modifier
from idtrackerai.utils import load_toml, resolve_path


class AdaptativeList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setAlternatingRowColors(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setMovement(QListView.Movement.Free)
        self.model().rowsInserted.connect(self.set_size)
        self.model().rowsRemoved.connect(self.set_size)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.set_size()

    def set_size(self):
        content_height = self.sizeHintForRow(0) * max(1, min(5, self.count()))
        scroll_bar = self.horizontalScrollBar()
        self.setFixedHeight(
            content_height
            + 2 * self.frameWidth()
            + (scroll_bar.height() if scroll_bar.isVisible() else 0)
        )

    def keyPressEvent(self, e):
        event = key_event_modifier(e)
        if event is not None:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, e):
        event = key_event_modifier(e)
        if event is not None:
            super().keyReleaseEvent(event)

    def focusOutEvent(self, event: QFocusEvent):
        super().focusOutEvent(event)
        if event.reason() is not Qt.FocusReason.ActiveWindowFocusReason:
            self.clearSelection()  # this IF fixes drag and drop errors on Wayland


class OpenVideoWidget(QWidget):
    new_video_paths = Signal(list, tuple, int, float, list)
    path_clicked = Signal(int)
    video_paths_reordered = Signal(list)
    new_episodes = Signal(list, object)
    new_parameters = Signal(dict)

    def __init__(self, parent: GUIBase, frames_per_episode: int):
        super().__init__()
        self.setLayout(QHBoxLayout())
        self.parent_widget = parent
        self.frames_per_episode = frames_per_episode
        self.button_open = QPushButton("Open...")
        self.button_open.setShortcut("Ctrl+O")
        self.button_open.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.button_open.clicked.connect(self.open_file_dialog)
        self.button_open.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        self.list_of_files = AdaptativeList()
        self.list_of_files.model().rowsMoved.connect(self.video_paths_reordered_func)
        self.single_file_label = WrappedLabel(framed=True)
        self.layout().addWidget(self.button_open)
        self.layout().addWidget(self.list_of_files)
        self.layout().addWidget(self.single_file_label)
        self.list_of_files.setVisible(False)
        self.list_of_files.itemSelectionChanged.connect(self.video_path_clicked)
        self.list_of_files.itemClicked.connect(self.video_path_clicked)
        self.single_file_label.setVisible(False)
        self.single_file_label.clicked.connect(self.button_open.click)
        self.tracking_intervals = None

    def open_file_dialog(self) -> None:
        file_dialog = QFileDialog()
        settings_key = f"{self.__class__.__name__}_filedialog_state"
        state = self.parent_widget.settings.value(settings_key, b"")
        if state:
            file_dialog.restoreState(state)
        file_paths, _ = file_dialog.getOpenFileNames(
            self.parent_widget, "Open a video file to track"
        )
        self.parent_widget.settings.setValue(settings_key, file_dialog.saveState())
        self.process_paths(file_paths)

    def video_path_clicked(self):
        items = self.list_of_files.selectedItems()
        if items:
            self.path_clicked.emit(self.video_path_start[items[0].text()][0])

    def video_paths_reordered_func(self):
        self.video_path_start.clear()
        i = 0
        for video_path in self.video_paths:
            n_frames = self.video_path_n_frames[video_path]
            self.video_path_start[video_path] = (i, i + n_frames)
            i += n_frames
        self.video_paths_reordered.emit(self.video_paths)
        self.n_frames, video_paths_n_frames, _, self.episodes = (
            Session.get_processing_episodes(
                self.video_paths, self.frames_per_episode, self.tracking_intervals
            )
        )
        self.new_episodes.emit(self.video_paths, self.episodes)

    def process_paths(self, video_paths_: Sequence[str | Path]) -> None:
        if not video_paths_:  # empty sequence
            return

        video_paths = sorted(map(resolve_path, video_paths_))

        if any(path.suffix == ".toml" for path in video_paths):
            if len(video_paths) > 1:
                QMessageBox.warning(
                    self,
                    "Error loading video",
                    "You can only load one single toml file or one or multiple video"
                    " files. You tried to load:\n  "
                    + "\n  ".join(map(str, video_paths)),
                )
                return
            parameters = load_toml(video_paths[0])
            self.new_parameters.emit(parameters)
            return

        self.open_video_paths(video_paths)

    def open_video_paths(self, video_paths: Sequence[Path | str] | None | str | Path):
        if not video_paths:
            return
        if isinstance(video_paths, (str, Path)):
            video_paths = [video_paths]
        try:
            Session.assert_video_paths(video_paths)
            self.video_width, self.video_height, self.fps = (
                Session.get_info_from_video_paths(video_paths)
            )
            self.n_frames, video_paths_n_frames, _, self.episodes = (
                Session.get_processing_episodes(
                    video_paths, self.frames_per_episode, self.tracking_intervals
                )
            )
        except (ValueError, IdtrackeraiError, FileNotFoundError) as exc:
            QMessageBox.warning(self, "Video paths error", str(exc))
            return

        self.single_file = len(video_paths) == 1
        if self.single_file:
            self.single_file_label.setText(str(video_paths[0]))
        else:
            self.list_of_files.clear()
            self.list_of_files.addItems(map(str, video_paths))

        self.single_file_label.setVisible(self.single_file)
        self.list_of_files.setVisible(not self.single_file)

        self.video_path_n_frames = dict(zip(self.video_paths, video_paths_n_frames))

        self.video_path_start = {}
        i = 0
        for video_path in self.video_paths:
            n_frames = self.video_path_n_frames[video_path]
            self.video_path_start[video_path] = (i, i + n_frames)
            i += n_frames

        self.n_frames = i
        self.new_video_paths.emit(
            self.video_paths,
            (self.video_width, self.video_height),
            self.n_frames,
            self.fps,
            self.episodes,
        )

    def set_tracking_interval(self, tracking_intervals):
        self.tracking_intervals = tracking_intervals

        if not hasattr(self, "video_paths"):
            return

        self.n_frames, video_paths_n_frames, _, self.episodes = (
            Session.get_processing_episodes(
                self.video_paths, self.frames_per_episode, self.tracking_intervals
            )
        )
        self.new_episodes.emit(self.video_paths, self.episodes)

    @property
    def video_paths(self):
        return self.getVideoPaths()

    def getVideoPaths(self) -> list[str]:
        if self.single_file:
            return [self.single_file_label.text()]
        return [
            self.list_of_files.item(i).text() for i in range(self.list_of_files.count())
        ]
