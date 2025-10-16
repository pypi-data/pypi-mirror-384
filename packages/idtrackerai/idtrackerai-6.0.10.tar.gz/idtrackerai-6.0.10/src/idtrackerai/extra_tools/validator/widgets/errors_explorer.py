import logging
import warnings

import numpy as np
from qtpy.QtCore import Qt, Signal  # type: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QKeyEvent
from qtpy.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from idtrackerai import ListOfBlobs
from idtrackerai.GUI_tools import get_icon, key_event_modifier


class CustomTableWidget(QTableWidget):
    def keyPressEvent(self, e: QKeyEvent):
        event = key_event_modifier(e)
        if event is not None:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, e: QKeyEvent):
        event = key_event_modifier(e)
        if event is not None:
            super().keyReleaseEvent(event)


class CustomTableWidgetItem(QTableWidgetItem):
    def __init__(self, value: str | int):
        super().__init__("" if value == -1 else str(value))
        self.setData(  # convert numpy ints into Python ints
            Qt.ItemDataRole.UserRole, value if isinstance(value, str) else int(value)
        )
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        return self.data(Qt.ItemDataRole.UserRole) < other.data(
            Qt.ItemDataRole.UserRole
        )


class ErrorsExplorer(QWidget):
    go_to_error = Signal(str, int, int, np.ndarray, int)
    # kind, start, end, where, id

    def __init__(self):
        super().__init__()
        self.table = CustomTableWidget(1, 4)
        horizontalHeader = self.table.horizontalHeader()
        horizontalHeader.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        horizontalHeader.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        horizontalHeader.setMinimumSectionSize(10)
        verticalHeader = self.table.verticalHeader()
        verticalHeader.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        verticalHeader.setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(["Type", "Id", "Start", "Length"])
        self.table.setSortingEnabled(True)
        self.table.currentCellChanged.connect(self.cell_clicked)
        self.table.cellDoubleClicked.connect(self.cell_clicked)

        long_jumps_row = QHBoxLayout()
        self.jumps_th_label = QLabel("Jumps threshold")
        long_jumps_row.addWidget(self.jumps_th_label)
        self.jumps_th = QSpinBox()
        self.jumps_th.setValue(10)
        self.jumps_th.setSpecialValueText("disabled")
        self.jumps_th.setSuffix(" std")
        self.jumps_th.setPrefix("avg + ")
        self.jumps_th.valueChanged.connect(self.update_list_of_errors)
        long_jumps_row.addWidget(self.jumps_th)
        self.reset_jumps = QToolButton()
        self.reset_jumps.setText("Reset")
        self.reset_jumps.clicked.connect(lambda: self.non_accepted_jumps.fill(True))
        self.reset_jumps.clicked.connect(self.update_list_of_errors)
        long_jumps_row.addWidget(self.reset_jumps)

        self.autoselect_errors = QCheckBox("Autoselect first error")

        layout = QVBoxLayout()
        left_widget = QWidget()
        left_widget.setLayout(layout)
        errors_header = QHBoxLayout()
        self.update_btn = QToolButton()
        self.update_btn.setIcon(get_icon("refresh"))
        self.update_btn.setShortcut(Qt.Key.Key_U)
        self.update_btn.clicked.connect(self.update_list_of_errors)
        self.left_label = QLabel()
        errors_header.addWidget(self.left_label)
        errors_header.addWidget(self.update_btn)
        layout.addLayout(errors_header)
        layout.addWidget(self.autoselect_errors)
        layout.addWidget(self.table)
        layout.addLayout(long_jumps_row)
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        self.trajectories: np.ndarray
        self.unidentified: np.ndarray
        self.duplicated: np.ndarray
        self.non_accepted_jumps: np.ndarray
        self.in_tracking_interval: np.ndarray

    def cell_clicked(self, row: int, col: int):
        if row < 0 or col < 0:
            return

        kind = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        identity = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
        start: int = self.table.item(row, 2).data(Qt.ItemDataRole.UserRole)
        length = self.table.item(row, 3).data(Qt.ItemDataRole.UserRole)
        self.selected_error = kind, identity, start, length

        where = self.trajectories[start]
        if kind in ("Jump", "Miss id"):
            if start > 0:
                where = self.trajectories[start - 1 : start + length + 1, identity - 1]
            else:
                where = self.trajectories[start : start + length + 1, identity - 1]
        elif kind == "No id":
            for blob in self.list_of_blobs.blobs_in_video[start]:
                for blob_id, centroid in blob.final_ids_and_centroids:
                    if blob_id in (None, 0):
                        where = np.asarray(centroid)
                        break
        elif kind == "Dupl":
            duplicated_centroids = []
            for blob in self.list_of_blobs.blobs_in_video[start]:
                for blob_id, centroid in blob.final_ids_and_centroids:
                    if blob_id == identity:
                        duplicated_centroids.append(centroid)
            where = np.asarray(duplicated_centroids)
        else:
            raise ValueError(kind)
        logging.debug(f"Error selected {kind=}, {start=}, {length=}, {identity=}")
        self.go_to_error.emit(kind, start, length, where, identity)

    def set_references(
        self,
        traj: np.ndarray,
        unidentified: np.ndarray,
        duplicated: np.ndarray,
        blobs: ListOfBlobs,
        tracking_intervals: list[list[int]] | None,
    ):
        self.trajectories = traj
        self.unidentified = unidentified
        self.duplicated = duplicated
        self.list_of_blobs = blobs
        self.non_accepted_jumps = np.ones((traj.shape[0] - 1, traj.shape[1]), bool)
        if tracking_intervals is None:
            self.in_tracking_interval = np.ones(len(traj), bool)
        else:
            self.in_tracking_interval = np.zeros(len(traj), bool)
            for start, end in tracking_intervals:
                self.in_tracking_interval[start:end] = True

        self.update_list_of_errors()

    def accepted_interpolation(self):
        "Connected from Interpolator.interpolation_accepted"
        if not hasattr(self, "selected_error"):
            return
        kind, identity, start, length = self.selected_error
        start -= 1
        if kind == "Jump":
            self.non_accepted_jumps[start : start + length, identity - 1] = False

    def getErrors(self) -> dict[str, list[tuple[int, np.ndarray, np.ndarray]]]:
        # TODO Add more errors (super-crossings)
        if np.isnan(self.trajectories).all():
            # not finished session
            return {}
        return {
            "Miss id": get_list_of_Trues_for_id(
                np.isnan(self.trajectories[..., 0]) & self.in_tracking_interval[:, None]
            ),
            "No id": [(-1,) + get_list_of_Trues(self.unidentified)],
            "Dupl": get_list_of_Trues_for_id(self.duplicated),
            "Jump": self.get_impossible_jumps(),
        }

    def update_list_of_errors(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for error_kind, errors_for_id in self.getErrors().items():
            for identity, starts, lengths in errors_for_id:
                for start, length in zip(starts, lengths):
                    self.table.insertRow(0)
                    self.table.setItem(0, 0, CustomTableWidgetItem(error_kind))
                    self.table.setItem(0, 1, CustomTableWidgetItem(identity))
                    self.table.setItem(0, 2, CustomTableWidgetItem(start))
                    self.table.setItem(0, 3, CustomTableWidgetItem(length))
        self.left_label.setText(f"List of errors ({self.table.rowCount()} errors)")
        self.table.setSortingEnabled(True)
        if self.autoselect_errors.isChecked():
            self.table.selectRow(0)

    def get_impossible_jumps(self):
        th = self.jumps_th.value()
        if th == 0:
            return []
        speed = np.sqrt((np.diff(self.trajectories, axis=0) ** 2).sum(-1))
        with warnings.catch_warnings():
            warnings.filterwarnings("error")
            try:
                mean, std = np.nanmean(speed), np.nanstd(speed)
            except RuntimeWarning:
                return []

        too_fast = (speed > (mean + th * float(std))) & self.non_accepted_jumps
        out = get_list_of_Trues_for_id(too_fast)
        for _id, start, _length in out:
            start += 1
        return out


def get_list_of_Trues(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Returns the start and the length of every True cluster in an array

    Input: [0,1,0,1,1,0]
    Output [1,3], [1,2] (one cluster at 1 of length 1 and another at 3 of length 2)
    """
    where = arr.nonzero()[0]
    is_edge = np.diff(where, prepend=-np.inf, append=np.inf) > 1
    starts = where[is_edge[:-1]]
    ends = where[is_edge[1:]]
    return starts, ends - starts + 1


def get_list_of_Trues_for_id(
    data: np.ndarray,
) -> list[tuple[int, np.ndarray, np.ndarray]]:
    return [
        (fish_id + 1,) + get_list_of_Trues(data[:, fish_id])
        for fish_id in range(data.shape[1])
    ]
