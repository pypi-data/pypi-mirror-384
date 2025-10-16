from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QWidget

from kevinbotlib.comm.abstract import AbstractSetGetNetworkClient
from kevinbotlib.comm.path import CommPath
from kevinbotlib.comm.sendables import DictSendable
from kevinbotlib.metrics import Metric


class ControlConsoleMetricsTab(QWidget):
    metrics_update = Signal(tuple)

    def __init__(self, client: AbstractSetGetNetworkClient, key: str | CommPath):
        super().__init__()

        self.metrics_update.connect(self.on_metrics_update)
        client.add_hook(
            CommPath(key) / "metrics", DictSendable, lambda key, sendable: self.metrics_update.emit((key, sendable))
        )

        root_layout = QHBoxLayout()
        self.setLayout(root_layout)

        self.text = QPlainTextEdit(placeholderText="Metrics Loading...", readOnly=True)
        root_layout.addWidget(self.text)

    def on_metrics_update(self, data: tuple[str, DictSendable | None]):
        if not data[1]:
            return

        text = ""

        for metric_dict in data[1].value.values():
            metric = Metric(**metric_dict)
            text += f"{metric.title}: {metric.display()}\n"

        self.text.setPlainText(text)
