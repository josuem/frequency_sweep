#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Title: Frequency Sweep

Description: This code performs a frequency sweep using two instruments:
AFG_2225 and MSO7024. It uses PyVISA library to communicate with the instruments and
generates a CSV file for each frequency with the corresponding sample rate.

Author: Josué Meneses Díaz

Date: 09-02-2023

"""

# %% libreries
import pyvisa
import time
import os 
import numpy as np
from tqdm import tqdm
import datetime
import pyfiglet

#%% Global configuration
start_frequency = 12500 # Hz
stop_frequency 	= 12800 # Hz
d_frequency 	= 1

voltaje_source 	= 20 	# V
time_waiting 	= 1 	# Seconds
# Memory Depth: {AUTO|1k|10k|100k|1M|10M|25M|50M|100M|125M|250M|500M|1000|10000|100000|1000000|10000000|25000000|50000000|100000000|125000000|250000000|500000000|1e3|1e4|1e5|1e6|1e7|2.5e7|5e7|1e8|1.25e8|2.5e8|5e8}
sample_rate 	= '100k' #'100k' 	
time_base 		= '0.1'

#%%
os.system('cls')
rm = pyvisa.ResourceManager()
# print(rm.list_resources())

now = datetime.datetime.now()
file_name = now.strftime("%Y-%m-%d_%H_%M_configuracion.txt")

directory_output = ""
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
	time.sleep(3.0)
	MSO7024.write(f'TIMebase:MAIN:SCALe {time_base}')
	time.sleep(0.5)
	MSO7024.write(f"ACQuire:MDEPth {sample_rate}")
	time.sleep(0.5)
	MSO7024.write('TRIGger:EDGE:SOURce CHANnel2')
	time.sleep(0.5)
	MSO7024.write('TRIGger:EDGE:LEVel 0.16')
	time.sleep(0.5)
	MSO7024.write('STOP')
	time.sleep(1.0)
	
	try:
		vec_sample[index] = MSO7024.query('ACQuire:SRATe?')
	except:
		pass


	MSO7024.write(f"SAVE:CSV D:\\{frequency}.csv;*OPC?")

	while True:
		try:
			status = MSO7024.query("*OPC?")
			# print(r"%s", status)
		except:
			status = '0\n'
			# print(r"%s", status)
		if status == '1\n':
			break
		
		time.sleep(1)


	time.sleep(time_waiting)

AFG_2225.write('OUTP1 OFF')

# %% Save the last measure configuration
Vch1 			= MSO7024.query('CHANnel1:SCALe?')
Vch1 			= Vch1.replace("\n", "")
Vch2 			= MSO7024.query('CHANnel2:SCALe?')
Vch2 			= Vch2.replace("\n", "")
time_base 		= MSO7024.query('TIMebase:MAIN:SCALe?')
time_base 		= time_base.replace("\n", "")
sample_rate 	= MSO7024.query('ACQuire:SRATe?')
sample_rate 	= sample_rate.replace("\n", "")
memorie_sample 	= MSO7024.query('ACQuire:MDEPth?')
memorie_sample 	= memorie_sample.replace("\n", "")


data = f"{sample_rate},{memorie_sample},{time_base},{Vch1},{Vch2},{start_frequency},{stop_frequency}\n"

with open(file_name, "w") as file:
    file.write("frecuencia muestreo [S/s],Samples [S],dt/div [s],ch1 [V/div],ch2 [V/div],start freq [Hz], stop freq [Hz]\n")	
    file.write(data)

#  %% Cerrando al comunicación con los instrumentos
print('Closing communication', end='... ')
AFG_2225.close()
print('AFG-2225 closed. ', end='')
MSO7024.close()
print('MSO7024 closed')
print('Finished!!!')