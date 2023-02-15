# Frequency Sweep
Description: This code performs a frequency sweep using two instruments:
AFG_2225 and MSO7024. It uses PyVISA library to communicate with the instruments and
generates a CSV file for each frequency with the corresponding sample rate.

This program performs a frequency sweep using an MSO7024 oscilloscope connected via USB. The initial, final and increment frequency are defined by the user in the start_frequency, stop_frequency and d_frequency variables, respectively. The voltage and waiting time are also defined by the user in the voltage_source and time_waiting variables. The data is saved in a folder called "data" on drive D.

## Libraries
You need to have installed the [NI-VISA](https://www.ni.com/es-cl/support/downloads/drivers/download.ni-visa.html#460225) API in your computer for run this code.

### Python
Install the requirements.txt file using conda:

```bash
conda install --file requirements.txt
```

The following libraries are imported in the code:

- pyvisa
- time
- os
- numpy as np
- tqdm
- datetime
- pyfiglet

## Global Configuration
The following global configuration parameters are defined in the code:

- start_frequency: The starting frequency (in Hz) for the sweep
- stop_frequency: The stopping frequency (in Hz) for the sweep
- d_frequency: The increment frequency for the sweep
- voltaje_source: The voltage source (in V) for the oscilloscope
- time_waiting: The waiting time (in seconds) between measurements
- sample_rate: The sample rate of the oscilloscope, defined as memory depth
- time_base: The time base of the oscilloscope (in seconds)

## Main Loop
The main loop of the program performs the following steps:

- Clears the oscilloscope screen
- Sets the parameters for the AFG2225 and MSO7024 devices
- Ranges through the frequency values defined by start_frequency, stop_frequency, and d_frequency.
- For each frequency in the loop:
- Sets the frequency for the AFG2225 device
- Runs the oscilloscope measurement
- Sets the time base and sample rate for the MSO7024 device
- Triggers the oscilloscope measurement
- Stops the oscilloscope measurement
- Saves the sample rate for each frequency in an array, vec_sample
- The data is saved to a folder called "data" on drive D.