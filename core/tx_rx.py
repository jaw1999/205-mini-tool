import numpy as np
import uhd
from uhd import libpyuhd
import threading
import time
import logging
from PyQt5.QtCore import QObject, pyqtSignal


class TxRx(QObject):
    # Signals for RX data
    data_received_rx1 = pyqtSignal(np.ndarray, int)  # Signal for RX1 data
    data_received_rx2 = pyqtSignal(np.ndarray, int)  # Signal for RX2 data

    def __init__(self, usrp_control):
        super().__init__()
        self.usrp = usrp_control.usrp
        self.fft_size = 1024
        self.frame_rate = 30  # Hz
        self.frame_interval = 1.0 / self.frame_rate
        self.last_frame_time = 0

        self.running = False
        self.rx_thread_rx1 = None
        self.rx_thread_rx2 = None
        self.tx_thread = None

        # Determine available RX channels and initialize streamers
        self.setup_rx_streamers()
        # Initialize TX streamer
        self.setup_tx_streamer()

    def setup_rx_streamers(self):
        """Setup RX streamers for available channels"""
        try:
            self.num_rx_channels = self.usrp.get_rx_num_channels()
            logging.info(f"Number of RX channels available: {self.num_rx_channels}")

            # Initialize RX1 (TX/RX) streamer
            stream_args = libpyuhd.usrp.stream_args("fc32", "sc16")
            stream_args.channels = [0]
            self.rx_streamer_rx1 = self.usrp.get_rx_stream(stream_args)
            logging.info("TX/RX Streamer initialized successfully")

            # Initialize RX2 streamer if available
            if self.num_rx_channels >= 2:
                stream_args.channels = [1]
                self.rx_streamer_rx2 = self.usrp.get_rx_stream(stream_args)
                self.rx2_available = True
                logging.info("RX2 Streamer initialized successfully")
            else:
                self.rx2_available = False
                logging.info("RX2 Streamer not available")

            # Get buffer sizes
            self.rx_buffer_size_rx1 = self.rx_streamer_rx1.get_max_num_samps()
            if self.rx2_available:
                self.rx_buffer_size_rx2 = self.rx_streamer_rx2.get_max_num_samps()

        except Exception as e:
            logging.error(f"Failed to initialize RX streamers: {e}")
            raise

    def setup_tx_streamer(self):
        """Setup TX streamer for channel 0"""
        try:
            stream_args = libpyuhd.usrp.stream_args("fc32", "sc16")
            stream_args.channels = [0]
            self.tx_streamer = self.usrp.get_tx_stream(stream_args)
            logging.info("TX Streamer initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize TX streamer: {e}")
            raise

    def start_receiving(self):
        """Start the receiving threads for RX channels"""
        if not self.running:
            try:
                self.running = True
                # Start TX/RX (RX1) thread
                self.rx_thread_rx1 = threading.Thread(target=self.receive_rx1, daemon=True)
                self.rx_thread_rx1.start()
                logging.info("TX/RX receiving thread started")

                # Start RX2 thread if available
                if self.rx2_available:
                    self.rx_thread_rx2 = threading.Thread(target=self.receive_rx2, daemon=True)
                    self.rx_thread_rx2.start()
                    logging.info("RX2 receiving thread started")

            except Exception as e:
                logging.error(f"Failed to start receiving threads: {e}")
                self.running = False
                raise

    def stop_receiving(self):
        """Stop the receiving threads safely"""
        try:
            self.running = False

            # Stop TX/RX thread
            if self.rx_thread_rx1 and self.rx_thread_rx1.is_alive():
                cmd = libpyuhd.types.stream_cmd(libpyuhd.types.stream_mode.stop_cont)
                self.rx_streamer_rx1.issue_stream_cmd(cmd)
                self.rx_thread_rx1.join(timeout=1.0)
                logging.info("TX/RX receiving thread stopped")

            # Stop RX2 thread if available
            if self.rx2_available and self.rx_thread_rx2 and self.rx_thread_rx2.is_alive():
                cmd = libpyuhd.types.stream_cmd(libpyuhd.types.stream_mode.stop_cont)
                self.rx_streamer_rx2.issue_stream_cmd(cmd)
                self.rx_thread_rx2.join(timeout=1.0)
                logging.info("RX2 receiving thread stopped")

        except Exception as e:
            logging.error(f"Failed to stop receiving threads: {e}")
            raise

    def start_transmitting(self, freq, bandwidth, modulation, amplitude, duration):
        """Start transmitting on TX port with specified parameters"""
        try:
            self.usrp.set_tx_freq(freq, channel=0)
            self.usrp.set_tx_rate(bandwidth * 1e6, channel=0)
            self.usrp.set_tx_gain(amplitude * 100, channel=0)

            # Generate waveform based on modulation
            sample_rate = self.usrp.get_tx_rate()
            t = np.arange(0, duration, 1 / sample_rate)

            if modulation == "AM":
                signal = amplitude * np.cos(2 * np.pi * freq * t)
            elif modulation == "FM":
                signal = amplitude * np.cos(2 * np.pi * freq * t + 0.5 * np.sin(2 * np.pi * 5 * t))
            elif modulation == "PSK":
                signal = amplitude * np.sign(np.sin(2 * np.pi * freq * t))
            elif modulation == "QAM":
                i = amplitude * np.cos(2 * np.pi * freq * t)
                q = amplitude * np.sin(2 * np.pi * freq * t)
                signal = i + 1j * q

            # Launch TX thread to transmit waveform
            self.tx_thread = threading.Thread(target=self._transmit_waveform, args=(signal.astype(np.complex64), duration), daemon=True)
            self.tx_thread.start()
            logging.info("TX thread started for signal transmission")

        except Exception as e:
            logging.error(f"Failed to start transmitting: {e}")
            raise

    def _transmit_waveform(self, waveform, duration):
        """Transmit a given waveform on the TX port for a specified duration"""
        try:
            cmd = libpyuhd.types.stream_cmd(libpyuhd.types.stream_mode.start_cont)
            cmd.stream_now = True
            self.tx_streamer.issue_stream_cmd(cmd)

            start_time = time.time()
            while time.time() - start_time < duration:
                self.tx_streamer.send(waveform, metadata=None)

            # Stop TX stream
            stop_cmd = libpyuhd.types.stream_cmd(libpyuhd.types.stream_mode.stop_cont)
            self.tx_streamer.issue_stream_cmd(stop_cmd)
            logging.info("TX stream stopped after transmitting waveform")

        except Exception as e:
            logging.error(f"Error during transmission: {e}")
            raise

    def receive_rx1(self):
        """Receive data continuously for TX/RX port"""
        self._receive_data(self.rx_streamer_rx1, 0)

    def receive_rx2(self):
        """Receive data continuously for RX2 port"""
        if self.rx2_available:
            self._receive_data(self.rx_streamer_rx2, 1)

    def _receive_data(self, rx_streamer, rx_channel):
        """Common method to receive data from a specified RX streamer"""
        try:
            cmd = libpyuhd.types.stream_cmd(libpyuhd.types.stream_mode.start_cont)
            cmd.stream_now = True
            rx_streamer.issue_stream_cmd(cmd)

            buffer_samps = min(self.fft_size, rx_streamer.get_max_num_samps())
            recv_buffer = np.zeros((buffer_samps,), dtype=np.complex64)
            metadata = libpyuhd.types.rx_metadata()

            logging.info(f"Starting RX{rx_channel} receive loop with buffer size: {buffer_samps}")

            while self.running:
                current_time = time.time()
                if current_time - self.last_frame_time >= self.frame_interval:
                    try:
                        samples_received = rx_streamer.recv(recv_buffer, metadata)

                        if samples_received:
                            data = recv_buffer[:samples_received].copy()
                            if rx_channel == 0:
                                self.data_received_rx1.emit(data, rx_channel)
                            else:
                                self.data_received_rx2.emit(data, rx_channel)
                            self.last_frame_time = current_time

                    except Exception as e:
                        if not self.running:
                            break
                        logging.warning(f"RX{rx_channel} receive error: {e}")
                        time.sleep(0.1)
                else:
                    time.sleep(0.001)

        except Exception as e:
            logging.error(f"Fatal error in RX{rx_channel} receive function: {e}")
            self.running = False
            raise
