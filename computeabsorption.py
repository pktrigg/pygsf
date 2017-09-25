#name:			pygsf
#created:		July 2017
#by:			p.kennedy@fugro.com
#description:	python module to read and write a Generic Sensor Formaty (GSF) file natively
#notes:			See main at end of script for example how to use this
#based on GSF Version 3.05

# See readme.md for more details

import os.path
import struct
import pprint
import time
import datetime
import math
import random
from datetime import datetime
from datetime import timedelta
from statistics import mean
import csv

########################################
def main():

	# filename = "F:/Projects/multispectral/DataRev2/V2 - Aug 2017/20170526 - NEWBEX/CTD/025348_2017-05-24_13-17-00Down .csv"
	# filename = "F:/Projects/multispectral/DataRev2/V2 - Aug 2017/20170526 - NEWBEX/CTD/025348_2017-05-24_13-17-00Up .csv"
	filename = "F:/Projects/multispectral/DataRev2/V2 - Aug 2017/Bedford Basin/20170502 - CTD/CTD 025348_2017-04-30_17-13-05.csv"
	with open(filename, 'r') as csvfile:
		reader = csv.reader(csvfile, delimiter=',', quotechar='|')

		for row in reader:
			if len(row) == 0:
				continue
			if row[0].startswith('2017'):
				conductivity = float(row[2]) * 1000
				temperature = float(row[3])
				depth = float(row[4])
				salinity = computesalinity(conductivity, temperature)
				absorption100 = computAbsorption(100, temperature, salinity, depth)
				absorption200 = computAbsorption(200, temperature, salinity, depth)
				absorption400 = computAbsorption(400, temperature, salinity, depth)
				
				print("%.3f,%.3f,%.3f,%.3f,%.3f,%.3f" %(temperature, salinity, depth, absorption100, absorption200, absorption400))
	return
	#Pressure (Decibar),Depth (Meter),Temperature (Celsius),Conductivity (MicroSiemens per Centimeter),Specific conductance (MicroSiemens per Centimeter),Salinity (Practical Salinity Scale),Sound velocity (Meters per Second),Density (Kilograms per Cubic Meter)
	filename = "F:/Projects/multispectral/DataRev2/V2 - Aug 2017/20161130 - Patricia Bay/CTD/CC1345004_20161129_201702.csv"
	with open(filename, 'r') as csvfile:
		reader = csv.reader(csvfile, delimiter=',', quotechar='|')
		for row in reader:
			if row[0].startswith('%'):
				continue
			if row[0].startswith('P'):
				continue
			temperature = float(row[2])
			salinity = float(row[5])
			depth = float(row[1])
			# print(row)
			absorption100 = computAbsorption(100, temperature, salinity, depth)
			absorption200 = computAbsorption(200, temperature, salinity, depth)
			absorption400 = computAbsorption(400, temperature, salinity, depth)
			print("%.3f,%.3f,%.3f,%.3f,%.3f,%.3f" %(temperature, salinity, depth, absorption100, absorption200, absorption400))
	
########################################
#from: view-source:http:#resource.npl.co.uk/acoustics/techguides/seaabsorption/
def computAbsorption(frequency=1, temperature=8, salinity=35, depth=50, pH=8):
	'''compute the absoption of sound in seawater using the AinslieMcColm algortithm'''
	# calculation of absorption according to:
	# Ainslie & McColm, J. Acoust. Soc. Am., Vol. 103, No. 3, March 1998
	# f frequency (kHz)
	# T Temperature (degC)
	# S Salinity (ppt)
	# D Depth (metres)
	# pH Acidity

	# # Total absorption = Boric Acid Contrib. + Magnesium Sulphate Contrib. + Pure Water Contrib.

	Boric = 0		# boric acid contribution
	MgSO4 = 0		# magnesium sulphate contribution
	H2O = 0			# pure water contribution
	Alpha = 0		# total absorption (dB/km)

	T_kel = 0	 	# ambient temperature (Kelvin)

	A1 = 0			# (dB/km/kHz)
	A2 = 0			# (dB/km/kHz)
	A3 = 0			# (dB/km/kHz)

	P1 = 0			# pressure correction factor
	P2 = 0			#
	P3 = 0			#

	frequency1 = 0			# (kHz)
	frequency2 = 0			# (kHz)

	Kelvin = 273.1	# for converting to Kelvin (273.15)

	depth = depth / 1000
	# Measured ambient temp
	T_kel = Kelvin + temperature

	# Boric acid contribution
	A1 = 0.106 * math.exp((pH - 8)/0.56)
	P1 = 1
	frequency1 = 0.78 * math.sqrt(salinity / 35) * math.exp(temperature/26)
	Boric = (A1 * P1 * frequency1 * frequency**2)/(frequency**2 + frequency1**2)

	# MgSO4 contribution
	A2 = 0.52 * (salinity / 35) * (1 + temperature/43)
	P2 = math.exp(-depth/6)
	frequency2 = 42 * math.exp(temperature/17)
	MgSO4 = (A2 * P2 * frequency2 * frequency**2)/(frequency**2 + frequency2**2)

	# Pure water contribution
	A3 = 0.00049*math.exp(-(temperature/27 + depth/17))
	P3 = 1
	H2O = A3 * P3 * frequency**2

	# Total absorption (dB/km)
	Alpha = Boric + MgSO4 + H2O
	return Alpha

########################################
def computesalinity(conductivity=35000, temperature=10):
	'''gives salinity (psu)
	as a function of conductivity (micro S/cm)and temperature(C)
	rounded to nearest tenth of a psu
	code adapted from c-code found at http://www.fivecreeks.org/monitor/sal.html
	or see Standard Methods for the Examination of Water and Wastewater
	dps - Feb 17, 2003'''
	
	a0=0.008
	a1=-0.1692
	a2=25.3851
	a3=14.0941
	a4=-7.0261
	a5=2.7081

	b0=0.0005
	b1=-0.0056
	b2=-0.0066
	b3=-0.0375
	b4=0.0636
	b5=-0.0144

	c0=0.6766097
	c1=0.0200564
	c2=0.0001104259
	c3=-0.00000069698
	c4=0.0000000010031

	if (temperature < 0 or 30 < temperature):
		return None

	if (conductivity <= 0):
		sal="Out of range"

	r=conductivity/42914
	r /= (c0 + temperature * (c1 + temperature * (c2 + temperature * (c3 + temperature * c4))))

	r2=math.sqrt(r)
	ds=b0+r2*(b1+r2*(b2+r2*(b3+r2*(b4+r2*b5))))
	ds*=((temperature-15.0)/(1.0+0.0162*(temperature-15.0)))

	salinity=a0+r2*(a1+r2*(a2+r2*(a3+r2*(a4+r2*a5))))+ds

	return salinity

########################################
if __name__ == "__main__":
	main()
