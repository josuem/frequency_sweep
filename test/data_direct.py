#%% libreries and configuration
import numpy as np
import pyvisa
import os
import matplotlib.pyplot as plt
import time
import pandas as pd
import logging
from logging import info, error, basicConfig
import sys

# logging configuration
logging.basicConfig(format="[%(levelname)s] %(message)s") # stream=sys.stdout
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Conecta al osciloscopio
os.system('cls')

info('Load libraries')
rm = pyvisa.ResourceManager()
print(rm.list_resources())

osc = rm.open_resource("USB0::0x1AB1::0x0514::DS7F221000027::INSTR")
osc.timeout = 1000

sample_rate 	= '100k' #'100k' 	
time_base 		= '0.1' #'0.1'

info('Configuring oscilloscope')
osc.write('RUN')
time.sleep(1)
osc.write(f'TIMebase:MAIN:SCALe {time_base}')
time.sleep(0.5)
osc.write(f"ACQuire:MDEPth {sample_rate}")
osc.write('STOP')

#%% Read data from oscilloscope

def dictionary_measurements(channel=1):
	"""Create a dictionary of measurements' parameters"""
	dict = {
			"timescale" : osc.query_ascii_values(":TIM:SCAL?")[0],
			"timeoffset" : osc.query_ascii_values(":TIM:OFFS?")[0],
			"voltscale" : osc.query_ascii_values(':CHAN'+str(channel)+':SCAL?')[0],
			"voltoffset" : osc.query_ascii_values(":CHAN"+str(channel)+":OFFS?")[0], # "voltoffset2" : osc.query_ascii_values(":CHAN2:OFFS?")[0],
			"sample_rate" :osc.query_ascii_values('ACQuire:SRATe?')[0],
			"XRef" :osc.query_ascii_values("WAVeform:XINCrement?")[0] ,
			"YRef" :osc.query_ascii_values("WAVeform:YREFerence?")[0],
			"dV" :osc.query_ascii_values(":WAVeform:YINCrement?")[0]
	}	
	return dict


osc.write("WAV:MODE RAW")  #BYTE  ASCii, Establecer el modo de adquisición de puntos

# CH1
info("Getting data from CH1")
osc.write("WAV:SOUR CHAN1")  # Solicitar la forma de onda del canal 1
dictionary_measurements1 = dictionary_measurements(channel=1)
# Convertir los valores del diccionario a listas
dictionary_measurements1 = {k: [v] for k, v in dictionary_measurements1.items()}
try:
	data1 = osc.query_binary_values("WAV:DATA?", datatype='B', container=np.array)
except:
	error("Error getting CH1")


time.sleep(1)

# CH2
info("Getting data from CH2")
osc.write("WAV:SOUR CHAN2")  # Solicitar la forma de onda del canal 2
dictionary_measurements2 = dictionary_measurements(channel=2)
# Convertir los valores del diccionario a listas
dictionary_measurements2 = {k: v for k, v in dictionary_measurements2.items()}
try:
	data2 = osc.query_binary_values("WAV:DATA?", datatype='B', container=np.array)
except:
	error("Error getting CH2")

# Create a dataframe with the configuration of measurements
info('Creating dataframe')
df_setup = pd.DataFrame(dictionary_measurements1)
df_setup = pd.concat([df_setup, pd.DataFrame(dictionary_measurements2, index=[0])], ignore_index=True)


#%% convert data to voltage
def CH_to_voltaje(data1, df_setup, channel=1):
	"""Convert bit data to voltage"""
	YRef 		= df_setup["YRef"][channel-1]
	voltoffset  = df_setup["voltoffset"][channel-1]
	dV 			= df_setup["dV"][channel-1]

	return (data1-YRef)*dV # - voltoffset/2 # Se elimina la referencia, se escala en voltaje y se elimina offset de pantalla
    

data_size = len(data1)

t = np.linspace(0, (len(data1)-1)*df_setup["XRef"][0], len(data1))

info("Converting data to voltage")
df_measurements = pd.DataFrame({
								"Tiempo s": t, 
								"CH1 V": CH_to_voltaje(data1, df_setup, channel=1),
								"CH2 V": CH_to_voltaje(data2, df_setup, channel=2)
							})

# %% Plot
info("Plot measurements")
plt.plot(t, df_measurements["CH1 V"], "k.", label="CH 1")
plt.plot(t, df_measurements["CH2 V"], "r.", label="CH 2")

plt.show() # block=True

print(data_size)
print(np.max(df_measurements["CH1 V"]))

df_setup

df_measurements.to_csv("./TEST/measurements_CH1_CH2.csv")
df_setup.to_csv(("./TEST/setup_measurements_CH1_CH2.csv"))
#%% close connections
info("Closed connections")
osc.close()
rm.close()
# %%
