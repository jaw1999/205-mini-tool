import uhd
import numpy as np
import logging
import time

class USRPControl:
    def __init__(self):
        try:
            # Initialize USRP with default parameters
            self.usrp = uhd.usrp.MultiUSRP()
            self.setup_default_configuration()
            logging.info("USRP device initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize USRP device: {e}")
            raise

    def setup_default_configuration(self):
        """Set up default configuration for all available channels"""
        try:
            # Get number of channels
            self.num_channels = self.usrp.get_rx_num_channels()
            
            # Default settings
            default_freq = 2.4e9  # 2.4 GHz
            default_rate = 1e6    # 1 MSps
            default_gain = 30     # 30 dB
            default_bw = 20e6     # 20 MHz
            
            # Configure each channel
            for chan in range(self.num_channels):
                self.set_rx_freq(default_freq, chan)
                self.set_rx_rate(default_rate, chan)
                self.set_rx_gain(default_gain, chan)
                self.set_bandwidth(default_bw, chan)
                
            # Let the settings settle
            time.sleep(0.1)
            
        except Exception as e:
            logging.error(f"Failed to set default configuration: {e}")
            raise

    def set_rx_freq(self, freq, channel=0):
        try:
            self.usrp.set_rx_freq(freq, channel)
            actual_freq = self.usrp.get_rx_freq(channel)
            logging.info(f"RX{channel} frequency set to {actual_freq/1e6:.3f} MHz")
            return actual_freq
        except Exception as e:
            logging.error(f"Failed to set RX{channel} frequency: {e}")
            raise

    def set_rx_gain(self, gain, channel=0):
        try:
            self.usrp.set_rx_gain(gain, channel)
            actual_gain = self.usrp.get_rx_gain(channel)
            logging.info(f"RX{channel} gain set to {actual_gain:.1f} dB")
            return actual_gain
        except Exception as e:
            logging.error(f"Failed to set RX{channel} gain: {e}")
            raise

    def set_rx_rate(self, rate, channel=0):
        try:
            self.usrp.set_rx_rate(rate, channel)
            time.sleep(0.1)  # Allow for clock stabilization
            actual_rate = self.usrp.get_rx_rate(channel)
            logging.info(f"RX{channel} sample rate set to {actual_rate/1e6:.3f} MSps")
            return actual_rate
        except Exception as e:
            logging.error(f"Failed to set RX{channel} sample rate: {e}")
            raise

    def set_bandwidth(self, bw, channel=0):
        try:
            self.usrp.set_rx_bandwidth(bw, channel)
            actual_bw = self.usrp.get_rx_bandwidth(channel)
            logging.info(f"RX{channel} bandwidth set to {actual_bw/1e6:.3f} MHz")
            return actual_bw
        except Exception as e:
            logging.error(f"Failed to set RX{channel} bandwidth: {e}")
            raise

    def set_antenna(self, antenna_name, channel=0):
        try:
            self.usrp.set_rx_antenna(antenna_name, channel)
            actual_ant = self.usrp.get_rx_antenna(channel)
            logging.info(f"RX{channel} antenna set to {actual_ant}")
        except Exception as e:
            logging.error(f"Failed to set RX{channel} antenna: {e}")
            raise

    def get_rx_rate(self, channel=0):
        try:
            return self.usrp.get_rx_rate(channel)
        except Exception as e:
            logging.error(f"Failed to get RX{channel} sample rate: {e}")
            raise

    def get_rx_freq(self, channel=0):
        try:
            return self.usrp.get_rx_freq(channel)
        except Exception as e:
            logging.error(f"Failed to get RX{channel} frequency: {e}")
            raise

    def get_rx_gain(self, channel=0):
        try:
            return self.usrp.get_rx_gain(channel)
        except Exception as e:
            logging.error(f"Failed to get RX{channel} gain: {e}")
            raise
