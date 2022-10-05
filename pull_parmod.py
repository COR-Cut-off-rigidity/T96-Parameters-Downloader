import requests, sys, json
import numpy as np
from datetime import datetime
from astropy.time import Time
from astropy.time import TimeDelta
from html.parser import HTMLParser
from pyquery import PyQuery
from collections import OrderedDict
from multiprocessing import Pool, cpu_count

baseUrl = "https://omniweb.gsfc.nasa.gov/cgi/nx1.cgi"

def interpolate(A, nanValue):
	A[A==nanValue] = np.nan
	return np.interp(np.arange(len(A)), np.arange(len(A))[np.isnan(A) == False],  A[np.isnan(A) == False])

#by, bz, Pdyn, DST
def postProcess():
	(yearA, mmonthA, mdayA, hourA, doyA, aA, bA, cA, dA, errCodeA) = ([], [], [], [],  [],  [],  [],  [],  [],  [])
	with open('parmod_new_intermediate.dat', 'r') as file:
		lines = file.readlines()
		for line in lines:
			(year, mmonth, mday, hour, doy, a,b,c,d) = line.split()
			yearA.append(year)
			mmonthA.append(mmonth)
			mdayA.append(mday)
			hourA.append(hour)
			doyA.append(doy)
			aA.append(float(a))
			bA.append(float(b))
			cA.append(float(c))
			dA.append(float(d))
			errCode = 4 if float(a) == 999.9 else 0
			errCode |= 8 if float(b) == 999.9 else 0
			errCode |= 2 if float(c) == 99.99 else 0
			errCode |= 16 if float(d) == 99999 else 0
			errCodeA.append(int(errCode))#chr
	aA = np.array(aA)
	aA = interpolate(aA, 999.9)
	bA = np.array(bA)
	bA = interpolate(bA, 999.9)
	cA = np.array(cA)
	cA = interpolate(cA, 99.99)
	fullArray = np.column_stack((yearA, mmonthA, mdayA, hourA, doyA, aA, bA, cA, dA, errCodeA))
	with open('parmod_new_interp.dat', 'w') as file:
		file.write("#year;month;day;hour;doy;By;Bz;Pdyn;dst;bitwise or of missing columns before interpolation (4;8;2;16)\n")
		for line in fullArray:
			#print(line)
			(year, mmonth, mday, hour, doy, a,b,c,d, err) = line
			(year, mmonth, mday, hour, doy, a,b,c,d, err) = (year, mmonth, mday, hour, doy, float(a), float(b), float(c), float(d), err)
			file.write(year+" "+f'{str(int(mmonth)):>2}'+" "+f'{str(int(mday)):>2}'+" "+f'{hour:>2}'+" "+f'{doy:>3}'+" "+f'{a:6.1f}'+" "+f'{b:6.1f}'+" "+f'{c:7.2f}'+" "+f'{d:5.0f}'+" " + err +"\n")


def getTrueEndDate():
	trueEndDatetime = Time(datetime.utcnow(), scale='utc').strftime('%Y%m%d')
	payload = {'activity': 'retrieve', 'res': 'hour', 'spacecraft': 'omni2', 'start_date': trueEndDatetime, 'end_date': trueEndDatetime, 'vars': ['15','16','28','40']}
	r = requests.get(baseUrl, params=payload)
	pq = PyQuery(r.text)

	if pq('h1').text() == "Error":
		trueEndDatetime = pq('tt').text().split()[-1]
	(year, month, day) = (int(trueEndDatetime[0:4]), int(trueEndDatetime[4:6]), int(trueEndDatetime[6:8]))
	print(year, month, day)
	endDatetimeGlobal = Time(datetime(year, month, day))
	return endDatetimeGlobal

def getParmodDataForDates(startDate, endDate):
	st = startDate.strftime('%Y%m%d')
	end = endDate.strftime('%Y%m%d')
	print(st, end)
	payload = {'activity': 'retrieve', 'res': 'hour', 'spacecraft': 'omni2', 'start_date': st, 'end_date': end, 'vars': ['15','16','28','40']}
	r = requests.get(baseUrl, params=payload)
	outputArray = r.text.split('\n')
	trimmedArray = outputArray[11:-16]
	outArray = []
	for line in trimmedArray:
		(year, doy, hour, a,b,c,d) = line.split()
		lineTime = Time(year+":"+doy.zfill(3)+":00:00:00.000", format="yday")
		lineTimeStr = str(lineTime.to_value('iso', subfmt='date'))
		year, mmonth, mday = lineTimeStr.split("-")
		outArray.append(year+" "+f'{str(int(mmonth)):>2}'+" "+f'{str(int(mday)):>2}'+" "+f'{hour:>2}'+" "+f'{doy:>3}'+" "+f'{a:>6}'+" "+f'{b:>6}'+" "+f'{c:>7}'+" "+f'{d:>5}')
	return (startDate, "\n".join(outArray)  + "\n")

def pullToMap(key):
	outputMap[key[0]] = key[1]

def main():
	startDatetimeGlobal = Time('1968-01-01 00:00:00', scale='utc')
	endDatetimeGlobal = getTrueEndDate()

	with open('update_history.dat', 'a') as file:
		file.write(str(Time(datetime.utcnow(), scale='utc').strftime('%Y%m%d %H:%M:%S')) + " " + endDatetimeGlobal.strftime('%Y%m%d') + "\n")

	localStart = startDatetimeGlobal
	diff = endDatetimeGlobal - startDatetimeGlobal

	global outputMap
	outputMap = dict()

	while localStart < endDatetimeGlobal:
		endDate = localStart + TimeDelta(365.25*24*3600, format='sec')
		if endDate > endDatetimeGlobal:
			endDate = endDatetimeGlobal
		outputMap[localStart] = endDate
		localStart = endDate + TimeDelta(24*3600, format='sec')
	
	with Pool(processes = cpu_count()) as pool:
		for key in outputMap:
			pool.apply_async(getParmodDataForDates, [key, outputMap[key]], callback = pullToMap)
		pool.close()
		pool.join()
	
	outputMap = OrderedDict(sorted(outputMap.items()))##
	
	with open('parmod_new_intermediate.dat', 'w') as file:
		for key in outputMap:
			file.write(outputMap[key])

	postProcess()
	sys.exit()
	
main()
