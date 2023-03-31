#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Title: Frequency Sweep

Description: This code performs a frequency sweep using two instruments:
AFG_2225 and MSO7024. It uses PyVISA library to communicate with the instruments and
generates a CSV file for each frequency with the corresponding sample rate.

The program create a folder in med directory and save the data in a csv file.

Author	: Josué Meneses Díaz
Date	: 30-03-2023
Version	: 2.0

#TODO: calculate fft and find the maximum value

"""

# %% libreries
import pyvisa
import time 
import os 
import numpy as np
from tqdm import tqdm
import datetime
import pyfiglet
import logging
from logging import info, error
import pandas as pd
import matplotlib.pyplot as plt

# logging configuration
logging.basicConfig(format="[%(levelname)s] %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


#%% Definitions
def dictionary_measurements(osc, channel=1):
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

def CH_to_voltaje(data1, df_setup, channel=1):
	"""Convert bit data to voltage"""
	YRef 		= df_setup["YRef"][channel-1]
	voltoffset  = df_setup["voltoffset"][channel-1]
	dV 			= df_setup["dV"][channel-1]

	return (data1-YRef)*dV # - voltoffset/2 # Se elimina la referencia, se escala en voltaje y se elimina offset de pantalla
    
fig, axs = plt.subplots(2, 1)

# Define la función de actualización de subplots
def update_plots(axs, t, df_measurements):
	# Agrega los nuevos datos a los subplots
	axs[0].plot(t, df_measurements["CH1 V"], "k-", label="CH 1")
	axs[1].plot(t, df_measurements["CH2 V"], "r-", label="CH 2")

	# Configura los límites de los ejes x e y
	axs[0].set_xlim(0, 0.1)
	# axs[0].set_ylim(0, 10)
	axs[1].set_xlim(0, 0.1)
	#axs[1].set_ylim(0, 10)

	# Actualiza la figura
	plt.legend()
	plt.draw()
	plt.pause(0.01)
    
#%% Global configuration
name_measurements 	= "Barrido cilindro 7.5cm EMAR 1k-1.1kHz"
enable_plot 		= False #False
time_waiting 		= 1 	# Seconds

start_frequency = 30000 # Hz
stop_frequency 	= 40000 # Hz
d_frequency 	= 2

voltaje_source 	= 20 	# V
# Memory Depth: {AUTO|1k|10k|100k|1M|10M|25M|50M|100M|125M|250M|500M|1000|10000|100000|1000000|10000000|25000000|50000000|100000000|125000000|250000000|500000000|1e3|1e4|1e5|1e6|1e7|2.5e7|5e7|1e8|1.25e8|2.5e8|5e8}
sample_rate 	= '100k' #'100k' 	
time_base 		= '0.1' #'0.1'

df_global_config = pd.DataFrame({ 
			"start_frequency": [start_frequency], 
			"stop_frequency": [stop_frequency], 
			"d_frequency": [d_frequency],
			"voltaje_source": [voltaje_source],
			"sample_rate": [sample_rate],
			"time_base": [time_base]
		})

#%%
os.system('cls')
rm = pyvisa.ResourceManager()
# print(rm.list_resources())
directory_output = ""

now = datetime.datetime.now()
datestr   =  now.strftime("%Y-%m-%d_%H_%M")
file_name =  "./med/" + datestr + " " + name_measurements + "/" #"./config/"+datestr+"_configuracion.txt"
info("Creado carpeta " + file_name)

# Verificar si la carpeta ya existe
if not os.path.exists(file_name):
    # Crear la carpeta si no existe
    os.makedirs(file_name)
    print("Carpeta creada exitosamente.")
else:
    print("La carpeta ya existe.")

info("Guardando configuracion")
df_global_config.to_csv(file_name + "global_configuration.csv")

info("Configurando equipos")
AFG_2225 		 = rm.open_resource('ASRL3::INSTR')
AFG_2225.timeout = 10000  # set timeout to 10 seconds

MSO7024 = rm.open_resource('USB0::0x1AB1::0x0514::DS7F221000027::INSTR')
MSO7024.timeout = 5000

#%%
result = pyfiglet.figlet_format("Frequency Sweep", font = "univers", width=1000 ) # roman
print(result)

bar = tqdm(range(start_frequency, stop_frequency, d_frequency))
vec_sample = np.zeros(len(range(start_frequency, stop_frequency, d_frequency)))

MSO7024.write('CLE')

AFG_2225.write('OUTP1:LOAD INFinity') # High Z
AFG_2225.write('OUTP1 ON')
time.sleep(5)

AFG_2225.write(f'SOUR1:APPL:SIN {start_frequency}HZ,{voltaje_source},0')

# %% Loop principal
for index, frequency in enumerate(bar): #range(start_frequency, stop_frequency, d_frequency):
	bar.set_description(f"Generando frecuencia {frequency} Hz" )

	AFG_2225.write(f'SOUR1:APPL:SIN {frequency}HZ,{voltaje_source},0')
	# time.sleep(0.5)
	MSO7024.write('RUN')
	time.sleep(1)
	MSO7024.write(f'TIMebase:MAIN:SCALe {time_base}')
	time.sleep(0.5)
	MSO7024.write(f"ACQuire:MDEPth {sample_rate}")
	time.sleep(3)
	MSO7024.write('TRIGger:EDGE:SOURce CHANnel2')
	time.sleep(0.5)
	MSO7024.write('TRIGger:EDGE:LEVel 0.16')
	time.sleep(3)
	MSO7024.write('STOP')
	time.sleep(2)
	
	try:
		vec_sample[index] = MSO7024.query('ACQuire:SRATe?')
	except:
		pass

	# get data from oscilloscope
	MSO7024.write("WAV:MODE RAW")  #BYTE  ASCii, Establecer el modo de adquisición de puntos

	# CH1
	print("")
	info("Getting data from CH1")
	MSO7024.write("WAV:SOUR CHAN1")  # Solicitar la forma de onda del canal 1
	dictionary_measurements1 = dictionary_measurements(MSO7024, channel=1)
	# Convertir los valores del diccionario a listas
	dictionary_measurements1 = {k: [v] for k, v in dictionary_measurements1.items()}
	try:
		data1 = MSO7024.query_binary_values("WAV:DATA?", datatype='B', container=np.array)
	except:
		error("Error getting CH1")

	time.sleep(1)

	# CH2
	info("Getting data from CH2")
	MSO7024.write("WAV:SOUR CHAN2")  # Solicitar la forma de onda del canal 2
	dictionary_measurements2 = dictionary_measurements(MSO7024, channel=2)
	# Convertir los valores del diccionario a listas
	dictionary_measurements2 = {k: v for k, v in dictionary_measurements2.items()}

	try:
		data2 = MSO7024.query_binary_values("WAV:DATA?", datatype='B', container=np.array)
	except:
		error("Error getting CH2")

	# Create a dataframe with the configuration of measurements
	info('Creating dataframe')
	df_setup = pd.DataFrame(dictionary_measurements1)
	df_setup = pd.concat([df_setup, pd.DataFrame(dictionary_measurements2, index=[0])], ignore_index=True)


	data_size = len(data1)

	t = np.linspace(0, (len(data1)-1)*df_setup["XRef"][0], len(data1))

	info("Converting data to voltage")
	df_measurements = pd.DataFrame({
									"Tiempo s": t, 
									"CH1 V": CH_to_voltaje(data1, df_setup, channel=1),
									"CH2 V": CH_to_voltaje(data2, df_setup, channel=2)
								})

	# %% Plot
	if enable_plot==True:
		info("Plot measurements")
		update_plots(axs, t, df_measurements)

	# print(data_size)
	# print(np.max(df_measurements["CH1 V"]))

	info("Saving measurements " + str(frequency) + " Hz")
	# file_name =  "./med/" + datestr + "/"
	df_measurements.to_csv(file_name + str(frequency) + ".csv")
	df_setup.to_csv(file_name +  "setup_measurements_" + str(frequency) + ".csv")

	time.sleep(time_waiting)

info("Apagando Generador")
AFG_2225.write('OUTP1 OFF')


#  %% Cerrando al comunicación con los instrumentos
print('Closing communication', end='... ')
AFG_2225.close()
print('AFG-2225 closed. ', end='')
MSO7024.close()
print('MSO7024 closed')
print('Finished!!!')