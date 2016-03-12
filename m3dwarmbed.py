import requests
import time
import atexit

restioserver = "http://localhost:8080"
extruderFanFetPort = "c5"
heaterFetPort = "c4"
thermistorPort = "c0"

thermistorRTable = [
    25339, 19872, 15698, 12488, 10000,
    8059, 6535, 5330, 4372, 3605, 2989,
    2490, 2084, 1753, 1481, 1256, 1070,
    915.4, 786, 677.3, 585.7, 508.3,
    442.6, 386.6, 338.7, 297.7, 262.4,
    231.9, 205.5, 182.6]

def restioService(service):
    response = requests.get(restioserver+service)
    if (not(response.ok)) :
        print(restioserver + " is not reachable.")
        exit()
    return response.json()

def currentTemperature():
    adcval = restioService("/0/analogRead/"+thermistorPort)["data"]
    resistance = 10000.0/ ((1023.0 / adcval) - 1.0)
    #Interpolate resistance to temperature
    for i in range(len(thermistorRTable)):
        if (resistance > thermistorRTable[i]):
            ratio = (resistance - thermistorRTable[i]) / (thermistorRTable[i + 1] - thermistorRTable[i])
            temp = (i + 1 + ratio)*5
            return temp

def exit_handler():
    print("Trying to turn stuff off before getting killed!")
    requests.get(restioserver+"/0/led/0")
    requests.get(restioserver+"/0/digitalWrite/"+heaterFetPort+"/0")
    requests.get(restioserver+"/0/digitalWrite/"+extruderFanFetPort+"/0")
    print("Tried my best. Bye!")

atexit.register(exit_handler)

devices = restioService("/devices")
print("Waiting for a restio device...")
while(len(devices) == 0) :
    time.sleep(1)
    devices = restioService("/devices")

print("Connected to device {dev}".format(dev=devices[0]["deviceName"]))
restioService("/0/led/0")

#Turn heater off
restioService("/0/digitalWrite/"+heaterFetPort+"/0")
#Turn extruder fan off
restioService("/0/digitalWrite/"+extruderFanFetPort+"/0")

print("Current bed temperature: {0:.2f} °C".format(currentTemperature()))
targetTemp = float(input("Enter target temperature in celcius: "))

#Some sort of value checking might be good here

#Turn extruder fan on
restioService("/0/digitalWrite/"+extruderFanFetPort+"/1")
print("Temperature: {0:.2f} °C Target: {1:.2f} °C".format(currentTemperature(),targetTemp))
time.sleep(2)

for i in range(0,20):
    restioService("/0/led/{v}".format(v=i%2))
    time.sleep(0.1)

infoCounter = 0

#Simple control loop
while True:
    heaterOn = "1" if targetTemp > currentTemperature() else "0"
    restioService("/0/digitalWrite/"+heaterFetPort+"/"+heaterOn)
    restioService("/0/led/"+heaterOn)
    time.sleep(1)
    infoCounter += 1
    if(infoCounter > 10):
        infoCounter = 0
        print("Temperature: {0:.2f} °C Target: {1:.2f} °C".format(currentTemperature(),targetTemp))

    
