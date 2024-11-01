# check_rx_channels.py
import uhd

def list_rx_channels():
    try:
        # Initialize USRP device
        usrp = uhd.usrp.MultiUSRP()
        
        # Get the number of RX channels
        num_rx_channels = usrp.get_num_rx_channels()
        print(f"Number of RX channels available: {num_rx_channels}")
        
        # List details for each RX channel
        for i in range(num_rx_channels):
            antenna = usrp.get_rx_antenna(i)
            gain = usrp.get_rx_gain(i)
            freq = usrp.get_rx_freq(i)
            rate = usrp.get_rx_rate(i)
            bw = usrp.get_rx_bandwidth(i)
            print(f"\nRX Channel {i+1}:")
            print(f"  Antenna: {antenna}")
            print(f"  Gain: {gain} dB")
            print(f"  Frequency: {freq} Hz")
            print(f"  Sample Rate: {rate} S/s")
            print(f"  Bandwidth: {bw} Hz")
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    list_rx_channels()
