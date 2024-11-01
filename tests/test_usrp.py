# test_usrp.py
import uhd
import sys

def test_usrp():
    try:
        print("\nTrying to connect to USRP...")
        usrp = uhd.usrp.MultiUSRP()
        print("\nUSRP Info:")
        print(usrp.get_pp_string())
        
        # Try to get some basic parameters
        print("\nCurrent Settings:")
        print(f"RX Rate: {usrp.get_rx_rate()} Sps")
        print(f"RX Frequency: {usrp.get_rx_freq()} Hz")
        print(f"RX Gain: {usrp.get_rx_gain()} dB")
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {sys.exc_info()}")

if __name__ == "__main__":
    test_usrp()