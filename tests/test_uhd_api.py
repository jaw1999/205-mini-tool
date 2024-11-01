# test_uhd_api.py
import uhd
from uhd import libpyuhd
import sys

def inspect_uhd():
    print("Python version:", sys.version)
    print("\nUHD module location:", uhd.__file__)
    print("\nUHD attributes:")
    print(dir(uhd))
    
    print("\nLibpyuhd attributes:")
    print(dir(libpyuhd))
    
    # Create test USRP
    print("\nCreating test USRP...")
    usrp = uhd.usrp.MultiUSRP()
    print("\nUSRP attributes:")
    print(dir(usrp))
    
    print("\nTesting stream creation:")
    try:
        stream_args = {
            "cpu_format": "fc32",
            "otw_format": "sc16",
            "channels": [0],
        }
        rx_streamer = usrp.get_rx_stream(stream_args)
        print("Successfully created RX streamer")
        print("Max num samps:", rx_streamer.get_max_num_samps())
    except Exception as e:
        print("Failed to create streamer:", str(e))
        print("Exception type:", type(e))

if __name__ == "__main__":
    try:
        inspect_uhd()
    except Exception as e:
        print(f"Error during inspection: {e}")
        print(f"Exception type: {type(e)}")