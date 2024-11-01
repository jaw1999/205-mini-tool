from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QLabel, QPushButton, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QComboBox, QGridLayout, QSlider, QSpinBox, QCheckBox,
    QSplitter, QStatusBar, QDoubleSpinBox, QMenu, QAction, QDialog, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QColor
import pyqtgraph as pg
import numpy as np
from datetime import datetime
import traceback  # For enhanced error logging
import time  # For timing measurements
from core.usrp_control import USRPControl
from core.tx_rx import TxRx


class AnalysisWindow(QDialog):
    def __init__(self, roi_info, parent=None):
        super(AnalysisWindow, self).__init__(parent)
        self.setWindowTitle("ROI Analysis")
        self.setGeometry(150, 150, 400, 300)
        layout = QVBoxLayout()

        # Display ROI information
        info_label = QLabel("Selected ROI Information:")
        layout.addWidget(info_label)

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_content = (
            f"Frequency Range: {roi_info['freq_start']:.3f} MHz - {roi_info['freq_end']:.3f} MHz\n"
            f"Time Range: {roi_info['time_start']:.3f} s - {roi_info['time_end']:.3f} s"
        )
        info_text.setText(info_content)
        layout.addWidget(info_text)

        # Placeholder for further analysis options
        analysis_label = QLabel("Analysis Options:")
        layout.addWidget(analysis_label)

        # Example: Display average power within ROI
        average_power = roi_info['average_power']
        avg_label = QLabel(f"Average Power: {average_power:.2f} dBm")
        layout.addWidget(avg_label)

        self.setLayout(layout)


class SpectrumAnalysisWindow(QDialog):
    def __init__(self, roi_info, parent=None):
        super(SpectrumAnalysisWindow, self).__init__(parent)
        self.setWindowTitle("Spectrum ROI Analysis")
        self.setGeometry(200, 200, 500, 400)
        layout = QVBoxLayout()

        # Display ROI information
        info_label = QLabel("Spectrum ROI Information:")
        layout.addWidget(info_label)

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_content = (
            f"Frequency Range: {roi_info['freq_start']:.3f} MHz - {roi_info['freq_end']:.3f} MHz\n"
            f"Peak Power: {roi_info['peak_power']:.2f} dBm\n"
            f"Peak Frequency: {roi_info['peak_freq']:.3f} MHz"
        )
        info_text.setText(info_content)
        layout.addWidget(info_text)

        # Placeholder for further analysis charts
        analysis_label = QLabel("Analysis Charts:")
        layout.addWidget(analysis_label)

        # Example: Plot the spectrum within the ROI
        spectrum_plot = pg.PlotWidget()
        spectrum_plot.setBackground('w')
        spectrum_plot.setLabel('left', 'Power', units='dBm')
        spectrum_plot.setLabel('bottom', 'Frequency', units='MHz')

        # Extract frequency and power data
        freq_range = np.linspace(roi_info['freq_start'], roi_info['freq_end'], 100)
        # Generate dummy data for demonstration; replace with actual data
        power_data = np.random.normal(loc=roi_info['peak_power'], scale=1.0, size=100)

        spectrum_plot.plot(freq_range, power_data, pen=pg.mkPen(color='blue', width=2))
        layout.addWidget(spectrum_plot)

        self.setLayout(layout)


class WaterfallClipWindow(QDialog):
    def __init__(self, snapshot_data, freq_range, time_span, parent=None):
        super(WaterfallClipWindow, self).__init__(parent)
        self.setWindowTitle("Waterfall Snapshot")
        self.setGeometry(250, 250, 800, 600)
        self.snapshot_data = snapshot_data  # 2D numpy array (time, frequency)
        self.freq_range = freq_range  # Tuple (freq_start, freq_end) in MHz
        self.time_span = time_span  # Time span in seconds
        self.current_fft_size = snapshot_data.shape[1]  # Initial FFT size
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Controls for FFT size adjustment
        controls_layout = QHBoxLayout()
        fft_label = QLabel("FFT Size:")
        self.fft_combo = QComboBox()
        self.fft_combo.addItems(['512', '1024', '2048', '4096', '8192'])
        self.fft_combo.setCurrentText(str(self.current_fft_size))
        self.fft_combo.currentTextChanged.connect(self.on_fft_size_changed)
        controls_layout.addWidget(fft_label)
        controls_layout.addWidget(self.fft_combo)

        # Controls for Zoom
        zoom_label = QLabel("Zoom:")
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_in_button.clicked.connect(self.on_zoom_in)
        self.zoom_out_button.clicked.connect(self.on_zoom_out)
        controls_layout.addWidget(zoom_label)
        controls_layout.addWidget(self.zoom_in_button)
        controls_layout.addWidget(self.zoom_out_button)

        layout.addLayout(controls_layout)

        # Plot Widget for the snapshot
        self.snapshot_plot = pg.PlotWidget()
        self.snapshot_plot.setBackground('k')
        self.snapshot_plot.showGrid(x=True, y=True, alpha=0.3)
        self.snapshot_plot.setLabel('left', 'Power', units='dBm')
        self.snapshot_plot.setLabel('bottom', 'Frequency', units='MHz')

        # Initialize ImageItem
        self.image_item = pg.ImageItem()
        self.snapshot_plot.addItem(self.image_item)

        # Set initial image
        self.update_image()

        # Enable mouse interactions for zooming
        self.snapshot_plot.setMouseEnabled(x=True, y=True)

        layout.addWidget(self.snapshot_plot)

        self.setLayout(layout)

    def update_image(self):
        # Update the ImageItem with the current snapshot data
        try:
            image_data = self.snapshot_data.copy()
            # Adjust FFT size by truncating or zero-padding
            desired_fft = self.current_fft_size
            current_fft = image_data.shape[1]
            if current_fft != desired_fft:
                if current_fft > desired_fft:
                    image_data = image_data[:, :desired_fft]
                else:
                    padding = np.full((image_data.shape[0], desired_fft - current_fft), -120)  # Fill with reference level minus dynamic range
                    image_data = np.hstack((image_data, padding))
            self.image_item.setImage(
                image_data,
                autoLevels=False,
                levels=(np.min(image_data), np.max(image_data)),
                pos=(self.freq_range[0], 0),
                scale=( (self.freq_range[1] - self.freq_range[0]) / image_data.shape[1], self.time_span / image_data.shape[0])
            )
            self.snapshot_plot.setLimits(xMin=self.freq_range[0], xMax=self.freq_range[1], yMin=0, yMax=self.time_span)
            self.snapshot_plot.setRange(xRange=self.freq_range, yRange=(0, self.time_span))
        except Exception as e:
            tb = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update snapshot image:\n{str(e)}\n{tb}")

    def on_fft_size_changed(self, size_text):
        # Handle FFT size changes
        try:
            size = int(size_text)
            self.current_fft_size = size
            self.update_image()
        except Exception as e:
            tb = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to change FFT size:\n{str(e)}\n{tb}")

    def on_zoom_in(self):
        # Zoom in on the snapshot plot
        try:
            self.snapshot_plot.getViewBox().scaleBy((0.8, 0.8))
        except Exception as e:
            tb = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to zoom in:\n{str(e)}\n{tb}")

    def on_zoom_out(self):
        # Zoom out on the snapshot plot
        try:
            self.snapshot_plot.getViewBox().scaleBy((1.25, 1.25))
        except Exception as e:
            tb = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to zoom out:\n{str(e)}\n{tb}")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("USRP B205 Mini Spectrum Analyzer")
        self.setGeometry(100, 100, 1600, 900)

        self.setup_status_bar()
        self.init_variables()
        self.init_usrp()
        self.init_ui()
        self.setup_update_timer()

    def init_variables(self):
        # Initialize control variables
        self.max_hold_enabled = False
        self.averaging_enabled = False
        self.averaging_factor = 0.5
        self.current_colormap = 'viridis'
        self.is_receiving = False
        self.fft_size = 1024

        # Initialize timing variables for FPS calculation
        self.last_update_time = None
        self.fps = 0.0

        # Calibration factor for dBm adjustment (to be fine-tuned)
        self.calibration_db = 0.0

        # Dictionary to store ROIs per RX channel
        self.rois = {0: [], 1: []}

    def init_usrp(self):
        # Initialize USRP control and data reception
        try:
            self.usrp_control = USRPControl()
            self.tx_rx = TxRx(self.usrp_control)
            self.tx_rx.data_received_rx1.connect(lambda data, channel: self.process_received_data(data, 0))
            if self.tx_rx.rx2_available:
                self.tx_rx.data_received_rx2.connect(lambda data, channel: self.process_received_data(data, 1))
            self.update_status("USRP initialized successfully", "success")
        except Exception as e:
            self.update_status(f"Failed to initialize USRP: {str(e)}", "error")
            raise

    def init_ui(self):
        # Set up the main UI layout with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Create display and control widgets
        display_widget = QWidget()
        self.displays_layout = QVBoxLayout(display_widget)
        splitter.addWidget(display_widget)

        control_widget = QWidget()
        self.control_layout = QVBoxLayout(control_widget)
        splitter.addWidget(control_widget)

        # Set stretch factors to allocate space appropriately
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        # Initialize control panel before displays to ensure dependencies are met
        self.init_control_panel()
        self.init_displays()

    def init_displays(self):
        # Initialize displays for each available RX channel
        self.init_rx_displays(0)
        if self.tx_rx.rx2_available:
            self.init_rx_displays(1)

    def init_rx_displays(self, rx_channel):
        # Create group boxes for each RX channel
        channel_group = QGroupBox(f"{'TX/RX' if rx_channel == 0 else 'RX2'} Channel")
        channel_layout = QVBoxLayout()

        # Create spectrum and waterfall displays
        spectrum_widget = self.create_spectrum_display(rx_channel)
        channel_layout.addWidget(spectrum_widget, stretch=1)

        waterfall_widget = self.create_waterfall_display(rx_channel)
        channel_layout.addWidget(waterfall_widget, stretch=1)

        channel_group.setLayout(channel_layout)
        self.displays_layout.addWidget(channel_group)

    def create_spectrum_display(self, rx_channel):
        # Create the spectrum analyzer display
        spectrum_group = QGroupBox("Spectrum Analyzer")
        spectrum_layout = QVBoxLayout()

        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('k')
        plot_widget.showGrid(x=True, y=True, alpha=0.3)

        plot_widget.setLabel('left', 'Power', units='dBm')
        plot_widget.setLabel('bottom', 'Frequency', units='MHz')
        plot_widget.setYRange(-120, 0)

        # Define curve pens with explicit colors
        spectrum_curve = plot_widget.plot(pen=pg.mkPen(color='yellow', width=2), name='Current')
        max_hold_curve = plot_widget.plot(pen=pg.mkPen(color='red', width=1), name='Max Hold')
        average_curve = plot_widget.plot(pen=pg.mkPen(color='green', width=1), name='Average')

        plot_widget.addLegend()

        # Initially hide Max Hold and Averaging curves
        max_hold_curve.setVisible(self.max_hold_enabled)
        average_curve.setVisible(self.averaging_enabled)

        # Store references for later updates
        setattr(self, f'spectrum_plot_rx{rx_channel}', plot_widget)
        setattr(self, f'spectrum_curve_rx{rx_channel}', spectrum_curve)
        setattr(self, f'max_hold_curve_rx{rx_channel}', max_hold_curve)
        setattr(self, f'average_curve_rx{rx_channel}', average_curve)
        setattr(self, f'max_hold_data_rx{rx_channel}', None)
        setattr(self, f'average_data_rx{rx_channel}', None)

        # Lock the spectrum display to prevent panning and zooming
        plot_widget.setMouseEnabled(x=False, y=False)
        plot_widget.getViewBox().setMouseMode(pg.ViewBox.RectMode)  # Prevent dragging

        # Connect right-click to open context menu for adding ROIs
        plot_widget.scene().sigMouseClicked.connect(lambda event, rx=rx_channel: self.on_spectrum_clicked(event, rx))

        spectrum_layout.addWidget(plot_widget)
        spectrum_group.setLayout(spectrum_layout)
        return spectrum_group

    def create_waterfall_display(self, rx_channel):
        # Create the waterfall display using PlotWidget and ImageItem
        waterfall_group = QGroupBox("Waterfall")
        waterfall_layout = QVBoxLayout()

        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('k')
        plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Disable all mouse interactions to lock the waterfall display
        plot_widget.setMouseEnabled(x=False, y=False)
        plot_widget.getViewBox().setMouseMode(pg.ViewBox.RectMode)  # Prevent dragging

        # Create and add ImageItem to PlotWidget
        image_item = pg.ImageItem()
        plot_widget.addItem(image_item)

        # Configure axes
        plot_widget.setLabel('left', 'Time', units='s')
        plot_widget.setLabel('bottom', 'Frequency', units='MHz')

        # Set Y-axis range and invert it to have time flow from top to bottom
        plot_widget.setYRange(0, self.time_spin.value())
        plot_widget.getViewBox().invertY(True)  # Invert Y-axis

        # Calculate initial scaling factors
        time_span = self.time_spin.value()  # in seconds
        scale_x = 1.0  # MHz per pixel (to be updated dynamically)
        scale_y = time_span / 500  # seconds per pixel

        # Initialize waterfall data with reference level minus dynamic range
        initial_value = self.ref_level_spin.value() - self.range_spin.value() if hasattr(self, 'ref_level_spin') and hasattr(self, 'range_spin') else -120
        waterfall_data = np.full((500, self.fft_size), initial_value)
        image_item.setImage(waterfall_data, autoLevels=False, levels=(initial_value, 0))
        image_item.setRect(QtCore.QRectF(0, 0, self.fft_size, time_span))

        # Set color map
        image_item.setColorMap(pg.colormap.get(self.current_colormap))

        # Add horizontal lines for time markings (e.g., every second)
        self.add_time_markings(plot_widget)

        # Add a label to display current time
        time_label = QLabel("Time: 0.000 s")
        time_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 150);
                padding: 5px;
                border-radius: 3px;
            }
        """)
        time_label.setAlignment(Qt.AlignCenter)
        time_label.setFixedHeight(20)

        # Store references for later updates
        setattr(self, f'waterfall_plot_rx{rx_channel}', image_item)
        setattr(self, f'waterfall_data_rx{rx_channel}', waterfall_data)
        setattr(self, f'time_label_rx{rx_channel}', time_label)
        setattr(self, f'waterfall_plot_widget_rx{rx_channel}', plot_widget)

        # Connect right-click to open context menu for adding ROIs
        plot_widget.scene().sigMouseClicked.connect(lambda event, rx=rx_channel: self.on_waterfall_clicked(event, rx))

        waterfall_layout.addWidget(plot_widget)
        waterfall_layout.addWidget(time_label)
        waterfall_group.setLayout(waterfall_layout)
        return waterfall_group

    def add_time_markings(self, plot_widget):
        # Add horizontal dashed lines at regular time intervals
        try:
            # Remove existing InfiniteLine items to prevent duplication
            for item in plot_widget.listDataItems():
                if isinstance(item, pg.InfiniteLine):
                    plot_widget.removeItem(item)

            time_span = self.time_spin.value()
            num_markings = min(10, time_span)  # Adjust based on time_span

            for i in range(num_markings + 1):
                time_val = i * (time_span / num_markings)
                line = pg.InfiniteLine(pos=time_val, angle=0, pen=pg.mkPen(color='w', width=0.5, style=QtCore.Qt.DashLine))
                plot_widget.addItem(line)
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Error adding time markings: {str(e)}\n{tb}", "error")

    def init_control_panel(self):
        # Initialize all control panels
        self.create_rx_control()
        self.create_tuning_controls()
        self.create_display_controls()
        self.create_processing_controls()
        self.control_layout.addStretch()

    def create_rx_control(self):
        # Create RX Control group
        rx_group = QGroupBox("RX Control")
        rx_layout = QHBoxLayout()

        self.start_stop_button = QPushButton("Start RX")
        self.start_stop_button.clicked.connect(self.toggle_rx)
        rx_layout.addWidget(self.start_stop_button)

        rx_group.setLayout(rx_layout)
        self.control_layout.addWidget(rx_group)

    def create_tuning_controls(self):
        # Create Tuning Controls group
        tuning_group = QGroupBox("Tuning Controls")
        tuning_layout = QGridLayout()

        self.rx_select = QComboBox()
        self.rx_select.addItems(["TX/RX"])
        if self.tx_rx.rx2_available:
            self.rx_select.addItems(["RX2"])
        self.rx_select.currentTextChanged.connect(self.on_rx_channel_changed)
        tuning_layout.addWidget(QLabel("RX Channel:"), 0, 0)
        tuning_layout.addWidget(self.rx_select, 0, 1)

        # Frequency Slider
        self.freq_slider = QSlider(Qt.Horizontal)
        self.freq_slider.setRange(70, 6000)  # MHz
        self.freq_slider.setValue(2400)  # Default value
        self.freq_slider.valueChanged.connect(self.on_frequency_slider_changed)
        tuning_layout.addWidget(QLabel("Center Frequency (MHz):"), 1, 0)
        tuning_layout.addWidget(self.freq_slider, 1, 1)

        # Frequency Input
        self.freq_input = QDoubleSpinBox()
        self.freq_input.setRange(70.0, 6000.0)  # MHz
        self.freq_input.setDecimals(3)
        self.freq_input.setSingleStep(0.1)
        self.freq_input.setValue(2400.0)  # Default value
        self.freq_input.valueChanged.connect(self.on_frequency_input_changed)
        tuning_layout.addWidget(QLabel("Frequency Input (MHz):"), 2, 0)
        tuning_layout.addWidget(self.freq_input, 2, 1)

        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setRange(0, 76)
        self.gain_slider.setValue(40)
        self.gain_slider.valueChanged.connect(self.on_gain_changed)
        tuning_layout.addWidget(QLabel("Gain (dB):"), 3, 0)
        tuning_layout.addWidget(self.gain_slider, 3, 1)

        self.rate_combo = QComboBox()
        self.rate_combo.addItems(['1', '5', '10', '20', '40', '56'])
        self.rate_combo.currentTextChanged.connect(self.on_sample_rate_changed)
        tuning_layout.addWidget(QLabel("Sample Rate (MSps):"), 4, 0)
        tuning_layout.addWidget(self.rate_combo, 4, 1)

        tuning_group.setLayout(tuning_layout)
        self.control_layout.addWidget(tuning_group)

    def create_display_controls(self):
        # Create Display Settings group
        display_group = QGroupBox("Display Settings")
        display_layout = QGridLayout()

        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(['viridis', 'plasma', 'inferno', 'magma', 'hot'])
        self.colormap_combo.setCurrentText(self.current_colormap)
        self.colormap_combo.currentTextChanged.connect(self.on_colormap_changed)
        display_layout.addWidget(QLabel("Waterfall Colormap:"), 0, 0)
        display_layout.addWidget(self.colormap_combo, 0, 1)

        self.ref_level_spin = QSpinBox()
        self.ref_level_spin.setRange(-120, 10)
        self.ref_level_spin.setValue(0)
        self.ref_level_spin.valueChanged.connect(self.on_ref_level_changed)
        display_layout.addWidget(QLabel("Reference Level (dBm):"), 1, 0)
        display_layout.addWidget(self.ref_level_spin, 1, 1)

        self.range_spin = QSpinBox()
        self.range_spin.setRange(10, 150)
        self.range_spin.setValue(120)
        self.range_spin.valueChanged.connect(self.on_dynamic_range_changed)
        display_layout.addWidget(QLabel("Dynamic Range (dB):"), 2, 0)
        display_layout.addWidget(self.range_spin, 2, 1)

        self.time_spin = QSpinBox()
        self.time_spin.setRange(1, 60)
        self.time_spin.setValue(10)
        self.time_spin.valueChanged.connect(self.on_time_span_changed)
        display_layout.addWidget(QLabel("Waterfall Time Span (s):"), 3, 0)
        display_layout.addWidget(self.time_spin, 3, 1)

        # Add calibration control
        self.calibration_spin = QDoubleSpinBox()
        self.calibration_spin.setRange(-100.0, 100.0)
        self.calibration_spin.setSingleStep(0.1)
        self.calibration_spin.setValue(0.0)
        self.calibration_spin.valueChanged.connect(self.on_calibration_changed)
        display_layout.addWidget(QLabel("Calibration (dB):"), 4, 0)
        display_layout.addWidget(self.calibration_spin, 4, 1)

        display_group.setLayout(display_layout)
        self.control_layout.addWidget(display_group)

    def create_processing_controls(self):
        # Create Processing Settings group
        processing_group = QGroupBox("Processing Settings")
        processing_layout = QGridLayout()

        self.fft_combo = QComboBox()
        self.fft_combo.addItems(['512', '1024', '2048', '4096', '8192'])
        self.fft_combo.setCurrentText(str(self.fft_size))
        self.fft_combo.currentTextChanged.connect(self.on_fft_size_changed)
        processing_layout.addWidget(QLabel("FFT Size:"), 0, 0)
        processing_layout.addWidget(self.fft_combo, 0, 1)

        self.frame_spin = QSpinBox()
        self.frame_spin.setRange(1, 60)
        self.frame_spin.setValue(30)
        self.frame_spin.valueChanged.connect(self.on_frame_rate_changed)
        processing_layout.addWidget(QLabel("Update Rate (fps):"), 1, 0)
        processing_layout.addWidget(self.frame_spin, 1, 1)

        self.max_hold_check = QCheckBox("Enable Max Hold")
        self.max_hold_check.stateChanged.connect(self.on_max_hold_changed)
        processing_layout.addWidget(self.max_hold_check, 2, 0, 1, 2)

        self.averaging_check = QCheckBox("Enable Averaging")
        self.averaging_check.stateChanged.connect(self.on_averaging_changed)
        processing_layout.addWidget(self.averaging_check, 3, 0)

        self.averaging_spin = QDoubleSpinBox()
        self.averaging_spin.setRange(0.1, 0.9)
        self.averaging_spin.setSingleStep(0.1)
        self.averaging_spin.setValue(0.5)
        self.averaging_spin.valueChanged.connect(self.on_averaging_factor_changed)
        processing_layout.addWidget(QLabel("Averaging Factor:"), 4, 0)
        processing_layout.addWidget(self.averaging_spin, 4, 1)

        self.window_combo = QComboBox()
        self.window_combo.addItems(['Hamming', 'Hanning', 'Blackman', 'Rectangular'])
        self.window_combo.currentTextChanged.connect(self.on_window_changed)
        processing_layout.addWidget(QLabel("Window Function:"), 5, 0)
        processing_layout.addWidget(self.window_combo, 5, 1)

        processing_group.setLayout(processing_layout)
        self.control_layout.addWidget(processing_group)

    def setup_status_bar(self):
        # Initialize the status bar with labels
        self.status_bar = self.statusBar()
        self.rx_status = QLabel("RX: Stopped")
        self.freq_status = QLabel("Freq: -- MHz")
        self.rate_status = QLabel("Rate: -- MSps")
        self.fps_label = QLabel("FPS: 0.00")
        self.calibration_status = QLabel("Calibration: 0.0 dB")

        self.status_bar.addPermanentWidget(self.rx_status)
        self.status_bar.addPermanentWidget(self.freq_status)
        self.status_bar.addPermanentWidget(self.rate_status)
        self.status_bar.addPermanentWidget(self.fps_label)
        self.status_bar.addPermanentWidget(self.calibration_status)
        self.status_bar.showMessage("Initializing...")

    def setup_update_timer(self):
        # Set up a timer to update displays at regular intervals (~30 FPS)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_displays)
        self.update_timer.start(33)  # Approximately 30 fps

    def toggle_rx(self):
        # Start or stop the RX process
        if not self.is_receiving:
            try:
                self.tx_rx.start_receiving()
                self.is_receiving = True
                self.start_stop_button.setText("Stop RX")
                self.rx_status.setText("RX: Running")
                self.update_status("RX started successfully", "success")
            except Exception as e:
                self.update_status(f"Failed to start RX: {str(e)}", "error")
        else:
            try:
                self.tx_rx.stop_receiving()
                self.is_receiving = False
                self.start_stop_button.setText("Start RX")
                self.rx_status.setText("RX: Stopped")
                self.update_status("RX stopped successfully", "success")
            except Exception as e:
                self.update_status(f"Failed to stop RX: {str(e)}", "error")

    def process_received_data(self, data, rx_channel):
        # Process incoming data from USRP
        try:
            # Ensure data length matches FFT size
            if len(data) != self.fft_size:
                # Adjust data length by truncating or zero-padding
                if len(data) > self.fft_size:
                    data = data[:self.fft_size]
                else:
                    padding = np.zeros(self.fft_size - len(data))
                    data = np.concatenate((data, padding))
                self.update_status(f"Data length adjusted to match FFT size for RX channel {rx_channel}", "warning")

            window_name = self.window_combo.currentText()
            if window_name == 'Hamming':
                window = np.hamming(len(data))
            elif window_name == 'Hanning':
                window = np.hanning(len(data))
            elif window_name == 'Blackman':
                window = np.blackman(len(data))
            else:  # Rectangular
                window = np.ones(len(data))

            windowed_data = data * window
            spectrum = np.fft.fftshift(np.fft.fft(windowed_data))
            # Correct frequency bins calculation
            sample_rate_hz = self.usrp_control.get_rx_rate(rx_channel)  # in Hz
            freq_bins = np.fft.fftshift(np.fft.fftfreq(len(spectrum), d=1.0 / sample_rate_hz))  # in Hz
            power_db = 20 * np.log10(np.abs(spectrum) + 1e-12) + self.calibration_db  # Apply calibration

            # Ensure spectrum and freq_bins have correct shapes
            if spectrum.shape != (self.fft_size,):
                self.update_status(f"Spectrum shape mismatch: expected ({self.fft_size},), got {spectrum.shape}", "error")
                return
            if freq_bins.shape != (self.fft_size,):
                self.update_status(f"Frequency bins shape mismatch: expected ({self.fft_size},), got {freq_bins.shape}", "error")
                return

            # Store spectrum data
            setattr(self, f'current_spectrum_rx{rx_channel}', power_db)
            setattr(self, f'current_freq_bins_rx{rx_channel}', freq_bins)

            # Implement Max Hold
            if self.max_hold_enabled:
                max_hold_data = getattr(self, f'max_hold_data_rx{rx_channel}')
                if max_hold_data is None:
                    max_hold_data = power_db.copy()
                else:
                    max_hold_data = np.maximum(max_hold_data, power_db)
                setattr(self, f'max_hold_data_rx{rx_channel}', max_hold_data)

            # Implement Averaging
            if self.averaging_enabled:
                avg_data = getattr(self, f'average_data_rx{rx_channel}')
                if avg_data is None:
                    avg_data = power_db.copy()
                else:
                    avg_data = self.averaging_factor * avg_data + (1 - self.averaging_factor) * power_db
                setattr(self, f'average_data_rx{rx_channel}', avg_data)

            # Update waterfall data by rolling and adding new data at the end
            waterfall_data = getattr(self, f'waterfall_data_rx{rx_channel}')
            if waterfall_data.shape[1] != self.fft_size:
                # Resize waterfall_data to match new FFT size
                new_waterfall_data = np.full((waterfall_data.shape[0], self.fft_size),
                                             self.ref_level_spin.value() - self.range_spin.value())
                min_size = min(self.fft_size, waterfall_data.shape[1])
                new_waterfall_data[:, :min_size] = waterfall_data[:, :min_size]
                waterfall_data = new_waterfall_data
                setattr(self, f'waterfall_data_rx{rx_channel}', waterfall_data)
                self.update_status(f"Waterfall data resized for RX channel {rx_channel} to FFT size {self.fft_size}", "info")

            # Roll the waterfall data upwards and insert new spectrum at the bottom
            waterfall_data = np.roll(waterfall_data, -1, axis=0)
            waterfall_data[-1, :] = power_db
            setattr(self, f'waterfall_data_rx{rx_channel}', waterfall_data)

        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Error processing data: {str(e)}\n{tb}", "error")

    def update_displays(self):
        # Update both spectrum and waterfall displays
        try:
            self.update_channel_displays(0)
            if self.tx_rx.rx2_available:
                self.update_channel_displays(1)
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Display update error: {str(e)}\n{tb}", "error")

        # **Timing Measurements: Calculate FPS**
        current_time = time.time()
        if self.last_update_time is not None:
            delta = current_time - self.last_update_time
            if delta > 0:
                self.fps = 1.0 / delta
            self.last_update_time = current_time
            self.fps_label.setText(f"FPS: {self.fps:.2f}")
        else:
            self.last_update_time = current_time

    def update_channel_displays(self, rx_channel):
        # Update displays for a specific RX channel
        spectrum = getattr(self, f'current_spectrum_rx{rx_channel}', None)
        freq_bins = getattr(self, f'current_freq_bins_rx{rx_channel}', None)

        if spectrum is not None and freq_bins is not None:
            center_freq_hz = self.usrp_control.get_rx_freq(rx_channel)  # in Hz
            sample_rate_hz = self.usrp_control.get_rx_rate(rx_channel)  # in Hz

            # Convert freq_bins to MHz and shift by center frequency
            freq_bins_mhz = freq_bins / 1e6  # Convert Hz to MHz
            center_freq_mhz = center_freq_hz / 1e6  # Convert Hz to MHz
            freq_points = freq_bins_mhz + center_freq_mhz  # Final frequency points in MHz

            # Update spectrum plot
            spectrum_curve = getattr(self, f'spectrum_curve_rx{rx_channel}')
            spectrum_curve.setData(freq_points, spectrum)

            # Update Max Hold curve if enabled
            if self.max_hold_enabled:
                max_hold_data = getattr(self, f'max_hold_data_rx{rx_channel}')
                if max_hold_data is not None:
                    max_hold_curve = getattr(self, f'max_hold_curve_rx{rx_channel}')
                    max_hold_curve.setData(freq_points, max_hold_data)

            # Update Averaging curve if enabled
            if self.averaging_enabled:
                avg_data = getattr(self, f'average_data_rx{rx_channel}')
                if avg_data is not None:
                    average_curve = getattr(self, f'average_curve_rx{rx_channel}')
                    average_curve.setData(freq_points, avg_data)

            # Update waterfall plot
            image_item = getattr(self, f'waterfall_plot_rx{rx_channel}')
            waterfall_data = getattr(self, f'waterfall_data_rx{rx_channel}')

            # **Calculate Frequency and Time Scale for Waterfall**
            frequency_range = freq_points[-1] - freq_points[0]  # in MHz
            time_span = self.time_spin.value()  # in seconds

            scale_x = frequency_range / self.fft_size  # MHz per pixel
            scale_y = time_span / waterfall_data.shape[0]  # seconds per pixel

            # **Set pos and scale correctly**
            if hasattr(self, 'ref_level_spin') and hasattr(self, 'range_spin'):
                ref_level = self.ref_level_spin.value()
                dynamic_range = self.range_spin.value()
                levels = (ref_level - dynamic_range, ref_level)
            else:
                levels = (-120, 0)  # Default levels

            # **Ensure freq_points matches waterfall_data's width**
            if len(freq_points) != self.fft_size:
                self.update_status(f"Frequency points length {len(freq_points)} does not match FFT size {self.fft_size}", "error")
                return

            # **Update the ImageItem with new data and scaling**
            image_item.setImage(
                waterfall_data,
                autoLevels=False,
                levels=levels,
                pos=(freq_points[0], 0),
                scale=(scale_x, scale_y)
            )

            # **Update the color map in case it was changed**
            image_item.setColorMap(pg.colormap.get(self.current_colormap))

            # **Update the time label**
            time_label = getattr(self, f'time_label_rx{rx_channel}')
            time_label.setText(f"Time: {datetime.now().strftime('%H:%M:%S')}")

    def on_rx_channel_changed(self, channel_text):
        # Handle RX channel selection changes
        channel = 0 if channel_text == "TX/RX" else 1
        try:
            freq = self.usrp_control.get_rx_freq(channel) / 1e6  # MHz
            gain = self.usrp_control.get_rx_gain(channel)
            # Update both slider and input without triggering signals
            self.freq_slider.blockSignals(True)
            self.freq_input.blockSignals(True)
            self.freq_slider.setValue(int(freq))
            self.freq_input.setValue(freq)
            self.freq_slider.blockSignals(False)
            self.freq_input.blockSignals(False)
            self.gain_slider.setValue(int(gain))
            self.update_status(f"Switched to {channel_text}", "info")
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Failed to switch channel: {str(e)}\n{tb}", "error")

    def on_frequency_slider_changed(self, value):
        # Handle frequency slider changes
        try:
            freq_mhz = float(value)
            # Update frequency input without triggering its signal
            self.freq_input.blockSignals(True)
            self.freq_input.setValue(freq_mhz)
            self.freq_input.blockSignals(False)
            # Set the frequency
            self.set_frequency(freq_mhz)
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Frequency slider error: {str(e)}\n{tb}", "error")

    def on_frequency_input_changed(self, value):
        # Handle frequency input changes
        try:
            freq_mhz = float(value)
            # Update frequency slider without triggering its signal
            self.freq_slider.blockSignals(True)
            self.freq_slider.setValue(int(freq_mhz))
            self.freq_slider.blockSignals(False)
            # Set the frequency
            self.set_frequency(freq_mhz)
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Frequency input error: {str(e)}\n{tb}", "error")

    def set_frequency(self, freq_mhz):
        # Common method to set frequency
        try:
            channel = 0 if self.rx_select.currentText() == "TX/RX" else 1
            freq_hz = freq_mhz * 1e6  # Convert MHz to Hz
            self.usrp_control.set_rx_freq(freq_hz, channel)
            self.freq_status.setText(f"Freq: {freq_mhz:.3f} MHz")
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Frequency setting error: {str(e)}\n{tb}", "error")

    def on_gain_changed(self, gain):
        # Handle gain slider changes
        try:
            channel = 0 if self.rx_select.currentText() == "TX/RX" else 1
            self.usrp_control.set_rx_gain(gain, channel)
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Gain error: {str(e)}\n{tb}", "error")

    def on_sample_rate_changed(self, rate_text):
        # Handle sample rate selection changes
        try:
            rate = float(rate_text) * 1e6  # Convert MSps to Sps
            channel = 0 if self.rx_select.currentText() == "TX/RX" else 1
            self.usrp_control.set_rx_rate(rate, channel)
            self.rate_status.setText(f"Rate: {rate_text} MSps")
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Sample rate error: {str(e)}\n{tb}", "error")

    def on_colormap_changed(self, colormap):
        # Handle colormap selection changes
        self.current_colormap = colormap
        try:
            for rx in range(2):
                if self.tx_rx.rx2_available or rx == 0:
                    image_item = getattr(self, f'waterfall_plot_rx{rx}', None)
                    if image_item is not None:
                        image_item.setColorMap(pg.colormap.get(colormap))
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Colormap change error: {str(e)}\n{tb}", "error")

    def on_ref_level_changed(self, level):
        # Handle reference level changes
        self.update_displays()

    def on_dynamic_range_changed(self, range_db):
        # Handle dynamic range changes
        self.update_displays()

    def on_time_span_changed(self, span):
        # Handle waterfall time span changes
        try:
            plot_widget = None
            # Update all waterfall plots
            for rx_channel in [0, 1]:
                if not self.tx_rx.rx2_available and rx_channel == 1:
                    continue
                plot_widget = getattr(self, f'waterfall_plot_widget_rx{rx_channel}', None)
                if plot_widget is not None:
                    # Update Y-axis range
                    plot_widget.setYRange(0, span)
                    # Recalculate and add new grid lines
                    self.add_time_markings(plot_widget)
            self.update_displays()
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Time span change error: {str(e)}\n{tb}", "error")

    def on_fft_size_changed(self, size_text):
        # Handle FFT size changes
        try:
            size = int(size_text)
            self.fft_size = size
            self.tx_rx.set_fft_size(size)
            for rx in range(2):
                if self.tx_rx.rx2_available or rx == 0:
                    waterfall_data = getattr(self, f'waterfall_data_rx{rx}', None)
                    if waterfall_data is not None:
                        # Resize the waterfall data while preserving existing data
                        new_waterfall_data = np.full((waterfall_data.shape[0], size),
                                                     self.ref_level_spin.value() - self.range_spin.value())
                        min_size = min(size, waterfall_data.shape[1])
                        new_waterfall_data[:, :min_size] = waterfall_data[:, :min_size]
                        setattr(self, f'waterfall_data_rx{rx}', new_waterfall_data)
            self.update_status(f"FFT size set to {size}", "success")
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"FFT size error: {str(e)}\n{tb}", "error")

    def on_frame_rate_changed(self, rate):
        # Handle frame rate changes
        try:
            self.tx_rx.set_frame_rate(rate)
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Frame rate error: {str(e)}\n{tb}", "error")

    def on_max_hold_changed(self, state):
        # Handle Max Hold toggle
        self.max_hold_enabled = bool(state)
        # Enable or disable the Max Hold curve for all available RX channels
        for rx_channel in [0, 1]:
            if not self.tx_rx.rx2_available and rx_channel == 1:
                continue  # Skip RX2 if not available
            max_hold_curve = getattr(self, f'max_hold_curve_rx{rx_channel}', None)
            if max_hold_curve is not None:
                max_hold_curve.setVisible(self.max_hold_enabled)
            if not self.max_hold_enabled:
                # Clear Max Hold data when disabled
                setattr(self, f'max_hold_data_rx{rx_channel}', None)
                # Optionally, clear the Max Hold curve
                if max_hold_curve is not None:
                    max_hold_curve.clear()

    def on_averaging_changed(self, state):
        # Handle Averaging toggle
        self.averaging_enabled = bool(state)
        self.averaging_spin.setEnabled(self.averaging_enabled)
        # Enable or disable the Averaging curve for all available RX channels
        for rx_channel in [0, 1]:
            if not self.tx_rx.rx2_available and rx_channel == 1:
                continue  # Skip RX2 if not available
            average_curve = getattr(self, f'average_curve_rx{rx_channel}', None)
            if average_curve is not None:
                average_curve.setVisible(self.averaging_enabled)
            if not self.averaging_enabled:
                # Clear Averaging data when disabled
                setattr(self, f'average_data_rx{rx_channel}', None)
                # Optionally, clear the Averaging curve
                if average_curve is not None:
                    average_curve.clear()

    def on_averaging_factor_changed(self, factor):
        # Handle Averaging Factor changes
        self.averaging_factor = factor

    def on_window_changed(self, window_type):
        # Handle Window Function changes (placeholder for future implementation)
        pass

    def on_calibration_changed(self, calibration_db):
        # Handle Calibration changes
        self.calibration_db = calibration_db
        self.calibration_status.setText(f"Calibration: {self.calibration_db:.1f} dB")
        self.update_displays()

    def update_status(self, message, level="info"):
        # Update the status bar with messages and color coding
        style = {
            "info": "color: white",
            "success": "color: green",
            "error": "color: red",
            "warning": "color: yellow"
        }
        self.status_bar.showMessage(message)
        self.status_bar.setStyleSheet(style.get(level, "color: white"))

    def closeEvent(self, event):
        # Handle application closure
        try:
            self.update_timer.stop()
            if hasattr(self, 'tx_rx'):
                self.tx_rx.stop_receiving()
            event.accept()
        except Exception as e:
            print(f"Error during shutdown: {str(e)}")
            event.accept()

    def set_frequency(self, freq_mhz):
        # Common method to set frequency
        try:
            channel = 0 if self.rx_select.currentText() == "TX/RX" else 1
            freq_hz = freq_mhz * 1e6  # Convert MHz to Hz
            self.usrp_control.set_rx_freq(freq_hz, channel)
            self.freq_status.setText(f"Freq: {freq_mhz:.3f} MHz")
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Frequency setting error: {str(e)}\n{tb}", "error")

    def on_spectrum_clicked(self, event, rx_channel):
        # Handle right-click on the spectrum plot to add ROI
        if event.button() == Qt.RightButton:
            pos = event.scenePos()
            plot_widget = getattr(self, f'spectrum_plot_rx{rx_channel}', None)
            vb = plot_widget.getViewBox()
            if plot_widget is not None:
                mouse_point = vb.mapSceneToView(pos)
                freq = mouse_point.x()

                # Create context menu
                menu = QMenu(self)
                add_roi_action = QAction("Add ROI", self)
                add_roi_action.triggered.connect(lambda: self.add_spectrum_roi(freq, rx_channel))
                menu.addAction(add_roi_action)
                menu.exec_(event.screenPos())

    def add_spectrum_roi(self, freq, rx_channel):
        # Define ROI size
        roi_width = self.fft_size * 0.05  # 5% of FFT size
        roi_height = 0  # Spectrum plot is 1D; height not needed

        # For spectrum, ROIs are vertical lines across frequency.
        # We'll use InfiniteLine for selection.

        # Create a Vertical Line ROI
        roi = pg.InfiniteLine(pos=freq, angle=90, pen=pg.mkPen(color='magenta', width=2), movable=True)

        # Store ROI in the dictionary
        self.rois[rx_channel].append(roi)

        # Add ROI to the plot
        plot_widget = getattr(self, f'spectrum_plot_rx{rx_channel}', None)
        if plot_widget is not None:
            plot_widget.addItem(roi)

        # Connect signals
        roi.sigPositionChanged.connect(lambda: self.on_spectrum_roi_changed(roi, rx_channel))
        roi.sigClicked.connect(lambda: self.on_spectrum_roi_clicked(roi, rx_channel))

    # Spectrum ROI handlers
    def on_spectrum_roi_changed(self, roi, rx_channel):
        # Handle ROI position changes (optional: update any related data)
        pass  # Placeholder for any real-time updates

    def on_spectrum_roi_clicked(self, roi, rx_channel):
        # Handle ROI click to open analysis options
        # Check if the click was a double-click or context menu
        if QtWidgets.QApplication.mouseButtons() == Qt.LeftButton:
            if QtWidgets.QApplication.keyboardModifiers() == Qt.NoModifier:
                # Simple click: you can decide what to do
                pass
        elif QtWidgets.QApplication.mouseButtons() == Qt.RightButton:
            # Right-click: show context menu for the ROI
            menu = QMenu(self)
            analyze_action = QAction("Analyze ROI", self)
            analyze_action.triggered.connect(lambda: self.analyze_spectrum_roi(roi, rx_channel))
            remove_action = QAction("Remove ROI", self)
            remove_action.triggered.connect(lambda: self.remove_spectrum_roi(roi, rx_channel))
            menu.addAction(analyze_action)
            menu.addAction(remove_action)
            menu.exec_(QtWidgets.QCursor.pos())

    def analyze_spectrum_roi(self, roi, rx_channel):
        # Redefine to analyze spectrum ROI
        # Extract ROI boundaries
        freq_position = roi.value()  # Current frequency position of the line
        bandwidth = self.fft_size * 0.05  # Define bandwidth around the line (e.g., ± bandwidth)

        freq_start = freq_position - bandwidth / 2
        freq_end = freq_position + bandwidth / 2

        # Extract corresponding spectrum data within ROI
        spectrum = getattr(self, f'current_spectrum_rx{rx_channel}', None)
        freq_bins = getattr(self, f'current_freq_bins_rx{rx_channel}', None)
        if spectrum is None or freq_bins is None:
            self.update_status(f"No spectrum data for RX channel {rx_channel}", "error")
            return

        # Map frequency to indices
        freq_indices = np.where((freq_bins / 1e6 >= freq_start) & (freq_bins / 1e6 <= freq_end))[0]

        if len(freq_indices) == 0:
            self.update_status("ROI does not overlap with data.", "warning")
            return

        # Extract the subset of data within ROI
        roi_data = spectrum[freq_indices]

        # Perform analysis (example: calculate peak power and frequency)
        peak_power = np.max(roi_data)
        peak_index = np.argmax(roi_data)
        peak_freq = freq_bins[freq_indices][peak_index] / 1e6  # Convert to MHz

        # Prepare ROI information
        roi_info = {
            'freq_start': freq_start,
            'freq_end': freq_end,
            'peak_power': peak_power,
            'peak_freq': peak_freq
        }

        # Open Analysis Window
        analysis_window = SpectrumAnalysisWindow(roi_info, self)
        analysis_window.exec_()

    def remove_spectrum_roi(self, roi, rx_channel):
        # Handle ROI removal
        if roi in self.rois[rx_channel]:
            self.rois[rx_channel].remove(roi)
        # Remove ROI from the plot
        plot_widget = getattr(self, f'spectrum_plot_rx{rx_channel}', None)
        if plot_widget is not None:
            plot_widget.removeItem(roi)

    def analyze_roi(self, roi, rx_channel):
        # Existing ROI analysis method for Waterfall
        # (No changes needed here)
        pass

    def on_waterfall_clicked(self, event, rx_channel):
        # Handle right-click on the waterfall plot to add ROI
        if event.button() == Qt.RightButton:
            pos = event.scenePos()
            plot_widget = getattr(self, f'waterfall_plot_widget_rx{rx_channel}', None)
            vb = plot_widget.getViewBox()
            if plot_widget is not None:
                mouse_point = vb.mapSceneToView(pos)
                freq = mouse_point.x()
                time = mouse_point.y()

                # Create context menu
                menu = QMenu(self)
                add_roi_action = QAction("Add ROI", self)
                add_roi_action.triggered.connect(lambda: self.add_roi(freq, time, rx_channel))
                menu.addAction(add_roi_action)
                menu.exec_(event.screenPos())

    def add_roi(self, freq, time, rx_channel):
        # Define ROI size
        roi_width = self.fft_size * 0.1  # 10% of FFT size
        roi_height = self.time_spin.value() * 0.1  # 10% of time span

        # Create a RectROI centered at (freq, time)
        roi = pg.RectROI(
            pos=(freq - roi_width / 2, time - roi_height / 2),
            size=(roi_width, roi_height),
            pen=pg.mkPen(color='cyan', width=2),
            movable=True,
            removable=True
        )
        roi.setZValue(10)  # Ensure ROI is on top

        # Store ROI in the dictionary
        self.rois[rx_channel].append(roi)

        # Add ROI to the plot
        plot_widget = getattr(self, f'waterfall_plot_widget_rx{rx_channel}', None)
        if plot_widget is not None:
            plot_widget.addItem(roi)

        # Connect signals
        roi.sigRegionChanged.connect(lambda: self.on_roi_changed(roi, rx_channel))
        roi.sigRemoved.connect(lambda: self.on_roi_removed(roi, rx_channel))
        roi.sigClicked.connect(lambda: self.on_roi_clicked(roi, rx_channel))

    def on_roi_changed(self, roi, rx_channel):
        # Handle ROI region changes (optional: update any related data)
        pass  # Placeholder for any real-time updates

    def on_roi_removed(self, roi, rx_channel):
        # Handle ROI removal
        if roi in self.rois[rx_channel]:
            self.rois[rx_channel].remove(roi)

    def on_roi_clicked(self, roi, rx_channel):
        # Handle ROI click to open analysis options or snapshot pop-up
        # Differentiate between clicking on the ROI boundaries and clicking inside the ROI
        # For simplicity, we'll assume any click inside the ROI opens the snapshot

        # Detect if the click is inside the ROI area
        if QtWidgets.QApplication.mouseButtons() == Qt.LeftButton:
            # Open snapshot pop-up
            self.open_waterfall_snapshot(roi, rx_channel)
        elif QtWidgets.QApplication.mouseButtons() == Qt.RightButton:
            # Right-click: show context menu for the ROI
            menu = QMenu(self)
            analyze_action = QAction("Analyze ROI", self)
            analyze_action.triggered.connect(lambda: self.analyze_roi(roi, rx_channel))
            remove_action = QAction("Remove ROI", self)
            remove_action.triggered.connect(lambda: roi.remove())
            menu.addAction(analyze_action)
            menu.addAction(remove_action)
            menu.exec_(QtWidgets.QCursor.pos())

    def open_waterfall_snapshot(self, roi, rx_channel):
        # Extract ROI boundaries
        roi_pos = roi.pos()
        roi_size = roi.size()
        freq_start = roi_pos.x()
        freq_end = roi_pos.x() + roi_size.x()
        time_start = roi_pos.y()
        time_end = roi_pos.y() + roi_size.y()

        # Extract corresponding waterfall data within ROI
        waterfall_data = getattr(self, f'waterfall_data_rx{rx_channel}', None)
        if waterfall_data is None:
            self.update_status(f"No waterfall data for RX channel {rx_channel}", "error")
            return

        freq_bins = getattr(self, f'current_freq_bins_rx{rx_channel}', None)
        if freq_bins is None:
            self.update_status(f"No frequency bins data for RX channel {rx_channel}", "error")
            return

        # Map frequency and time to indices
        freq_indices = np.where((freq_bins / 1e6 >= freq_start) & (freq_bins / 1e6 <= freq_end))[0]
        time_indices = np.where((np.linspace(0, self.time_spin.value(), waterfall_data.shape[0]) >= time_start) &
                                (np.linspace(0, self.time_spin.value(), waterfall_data.shape[0]) <= time_end))[0]

        if len(freq_indices) == 0 or len(time_indices) == 0:
            self.update_status("ROI does not overlap with data.", "warning")
            return

        # Extract the subset of data within ROI
        snapshot_data = waterfall_data[np.ix_(time_indices, freq_indices)]
        snapshot_freq_start = freq_bins[freq_indices][0] / 1e6  # MHz
        snapshot_freq_end = freq_bins[freq_indices][-1] / 1e6  # MHz
        snapshot_time_span = time_end - time_start  # seconds

        # Open Waterfall Clip Window
        snapshot_window = WaterfallClipWindow(
            snapshot_data=snapshot_data,
            freq_range=(snapshot_freq_start, snapshot_freq_end),
            time_span=snapshot_time_span,
            parent=self
        )
        snapshot_window.exec_()

    def analyze_roi(self, roi, rx_channel):
        # Existing ROI analysis method for Waterfall
        try:
            # Extract ROI boundaries
            roi_pos = roi.pos()
            roi_size = roi.size()
            freq_start = roi_pos.x()
            freq_end = roi_pos.x() + roi_size.x()
            time_start = roi_pos.y()
            time_end = roi_pos.y() + roi_size.y()

            # Extract corresponding waterfall data within ROI
            waterfall_data = getattr(self, f'waterfall_data_rx{rx_channel}', None)
            if waterfall_data is None:
                self.update_status(f"No waterfall data for RX channel {rx_channel}", "error")
                return

            freq_bins = getattr(self, f'current_freq_bins_rx{rx_channel}', None)
            if freq_bins is None:
                self.update_status(f"No frequency bins data for RX channel {rx_channel}", "error")
                return

            # Map frequency and time to indices
            freq_indices = np.where((freq_bins / 1e6 >= freq_start) & (freq_bins / 1e6 <= freq_end))[0]
            time_indices = np.where((np.linspace(0, self.time_spin.value(), waterfall_data.shape[0]) >= time_start) &
                                    (np.linspace(0, self.time_spin.value(), waterfall_data.shape[0]) <= time_end))[0]

            if len(freq_indices) == 0 or len(time_indices) == 0:
                self.update_status("ROI does not overlap with data.", "warning")
                return

            # Extract the subset of data within ROI
            roi_data = waterfall_data[np.ix_(time_indices, freq_indices)]

            # Perform analysis (example: calculate average power)
            average_power = np.mean(roi_data)

            # Prepare ROI information
            roi_info = {
                'freq_start': freq_start,
                'freq_end': freq_end,
                'time_start': time_start,
                'time_end': time_end,
                'average_power': average_power
            }

            # Open Analysis Window
            analysis_window = AnalysisWindow(roi_info, self)
            analysis_window.exec_()
        except Exception as e:
            tb = traceback.format_exc()
            self.update_status(f"Error analyzing ROI: {str(e)}\n{tb}", "error")

    def update_status(self, message, level="info"):
        # Update the status bar with messages and color coding
        style = {
            "info": "color: white",
            "success": "color: green",
            "error": "color: red",
            "warning": "color: yellow"
        }
        self.status_bar.showMessage(message)
        self.status_bar.setStyleSheet(style.get(level, "color: white"))

    def closeEvent(self, event):
        # Handle application closure
        try:
            self.update_timer.stop()
            if hasattr(self, 'tx_rx'):
                self.tx_rx.stop_receiving()
            event.accept()
        except Exception as e:
            print(f"Error during shutdown: {str(e)}")
            event.accept()
