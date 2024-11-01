# gui/transmit_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox, QDoubleSpinBox, QFormLayout
from PyQt5.QtCore import pyqtSignal

class TransmitTab(QWidget):
    transmit_signal = pyqtSignal(float, float, str, float, float)  # Signal to trigger transmission with parameters

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Frequency Input
        self.freq_input = QDoubleSpinBox()
        self.freq_input.setRange(70.0, 6000.0)  # Adjust to your USRP limits
        self.freq_input.setDecimals(3)
        self.freq_input.setValue(900.0)
        form_layout.addRow("Frequency (MHz):", self.freq_input)

        # Bandwidth Input
        self.bandwidth_input = QDoubleSpinBox()
        self.bandwidth_input.setRange(0.1, 100.0)  # MHz range
        self.bandwidth_input.setDecimals(2)
        self.bandwidth_input.setValue(1.0)
        form_layout.addRow("Bandwidth (MHz):", self.bandwidth_input)

        # Modulation Type
        self.modulation_type = QComboBox()
        self.modulation_type.addItems(["AM", "FM", "PSK", "QAM"])
        form_layout.addRow("Modulation Type:", self.modulation_type)

        # Amplitude Control
        self.amplitude_input = QDoubleSpinBox()
        self.amplitude_input.setRange(0.0, 1.0)
        self.amplitude_input.setDecimals(2)
        self.amplitude_input.setValue(0.5)
        form_layout.addRow("Amplitude:", self.amplitude_input)

        # Duration
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 60)  # Transmission duration in seconds
        self.duration_input.setValue(5)
        form_layout.addRow("Duration (s):", self.duration_input)

        # Transmit Button
        self.transmit_button = QPushButton("Transmit")
        self.transmit_button.clicked.connect(self.on_transmit_clicked)
        layout.addLayout(form_layout)
        layout.addWidget(self.transmit_button)
        self.setLayout(layout)

    def on_transmit_clicked(self):
        # Emit signal with user-defined parameters for transmission
        freq = self.freq_input.value()
        bandwidth = self.bandwidth_input.value()
        modulation = self.modulation_type.currentText()
        amplitude = self.amplitude_input.value()
        duration = self.duration_input.value()
        self.transmit_signal.emit(freq, bandwidth, modulation, amplitude, duration)
