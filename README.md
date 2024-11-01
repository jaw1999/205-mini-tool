# USRP B205 Mini Spectrum Analyzer

This project provides a spectrum analyzer application for the USRP B205 Mini SDR device, focused on receiving and visualizing spectrum data in real time. Currently, only the RX (Receive) functionality is implemented.

## Features

- Real-time spectrum analysis for the RX channel.
- Adjustable RX settings: frequency, gain, sample rate, and bandwidth.
- Spectrum and waterfall plots with zoom and analysis tools.
- ROI (Region of Interest) functionality for in-depth analysis of specific spectrum portions.

## Requirements

- **Python 3.11+**
- **PyQt5**: For the graphical user interface.
- **PyQtGraph**: For spectrum and waterfall visualizations.
- **UHD**: UHD library from Ettus Research for USRP device control.
- **NumPy**: For efficient numerical computations.

Ensure that the following environment variables are set in the \`uhd_env\` virtual environment:

\`\`\`bash
export PYTHONPATH=/usr/local/lib/python3.11/site-packages:\$PYTHONPATH
export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH
\`\`\`

## Installation

1. Clone the repository:

   \`\`\`bash
   git clone https://github.com/your-username/205-mini-tool.git
   cd 205-mini-tool
   \`\`\`

2. Create a virtual environment and activate it:

   \`\`\`bash
   python3.11 -m venv uhd_env
   source uhd_env/bin/activate
   \`\`\`

3. Install the required dependencies:

   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. Ensure that UHD is properly installed. If not, refer to the [UHD installation guide](https://files.ettus.com/manual/page_build_guide.html).

## Usage

1. Activate the virtual environment:

   \`\`\`bash
   source uhd_env/bin/activate
   \`\`\`

2. Run the application:

   \`\`\`bash
   python3.11 main.py
   \`\`\`

## Project Structure

\`\`\`
205-mini-tool/
├── gui/
│   ├── main_window.py       # Main application window
│   └── ...
├── core/
│   ├── usrp_control.py      # USRP control functions
│   └── tx_rx.py             # RX functionality and processing
├── tests/
│   ├── test_rx.py           # Unit tests for RX functionality
│   └── ...
├── main.py                  # Application entry point
├── README.md                # Project documentation
└── requirements.txt         # Python dependencies
\`\`\`