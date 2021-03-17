from sds011 import *
import time
import aqi
import paho.mqtt.publish as publish
import adafruit_dht
from board import D4

# get 3 instances and take the average
def get_data(n=3):
        sensor.sleep(sleep=False)
        pmt_2_5 = 0
        pmt_10 = 0
        time.sleep(10)
        for _ in range (n):
            x = sensor.query()
            pmt_2_5 = pmt_2_5 + x[0]
            pmt_10 = pmt_10 + x[1]
            time.sleep(2)
        pmt_2_5 = round(pmt_2_5/n, 1)
        pmt_10 = round(pmt_10/n, 1)
        sensor.sleep(sleep=True)
        time.sleep(2)
        return pmt_2_5, pmt_10

# conversion from pmt_i to Air Quality Index
def conv_aqi(pmt_2_5, pmt_10):
    aqi_2_5 = aqi.to_iaqi(aqi.POLLUTANT_PM25, str(pmt_2_5))
    aqi_10 = aqi.to_iaqi(aqi.POLLUTANT_PM10, str(pmt_10))
    return aqi_2_5, aqi_10

# Save in a local file
def save_log():        
    with open("/home/pi/WORK_DIR/Air_purifier/air_quality_with_purifier.csv", "a") as log:
        pmt_2_5, pmt_10 = get_data()
        aqi_2_5, aqi_10 = conv_aqi(pmt_2_5, pmt_10)
	temperature = dht_device.temperature
        humidity = dht_device.humidity
        dt = datetime.now()
        log.write("{},{},{},{},{},{},{}\n".format(dt, pmt_2_5, aqi_2_5, pmt_10, aqi_10, temperature, humidity))
    log.close()

sensor = SDS011('/dev/ttyUSB0', use_query_mode=True)

# set up the mqtt via Thing Speak
channelID = 'THE CHANNEL ID' # set here the TS channel ID
apiKey = 'API KEY' # Set here the write api key provided by TS
topic = f'channels/{channelID}/publish/{apiKey}'
mqttHost = 'mqtt.thingspeak.com'

# Conventional TCP socket on port 1883.  
# This connection method is the simplest and requires the least system resources.
tTransport = "tcp"
tPort = 1883
tTLS = None

# initialize the temp/humi 
dht_device = adafruit_dht.DHT11(D4)

# infinite loop for sending data to ThingSpeak.com
while True:
    # retrieve pollution values
    pmt2_5, pmt_10 = get_data()
    aqi_2_5, aqi_10 = conv_aqi(pmt2_5, pmt_10)
    # retrieve temperature and humidity values
    try:
        temperature = dht_device.temperature
        humidity = dht_device.humidity
    except:
	# except since it happens that the sensor fails
        temperature = ''
        humidity = ''
    
    # Build the payload according to the format required for TS
    tPayload = "field1=" + str(pmt2_5)+ "&field2=" + str(aqi_2_5)\
        + "&field3=" + str(pmt_10)+ "&field4=" + str(aqi_10) \
        + "&field5="+str(temperature)+ "&field6=" + str(humidity)
    

    try:
	# Publish via mqtt and save in local
        publish.single(topic, payload=tPayload, hostname=mqttHost, port=tPort, tls=tTLS, transport=tTransport)
        save_log()
        print('[INFO] Data sent correctly')
    except:
        print('[INFO] Failure in sending data')
    time.sleep(120) # wait for 2 min before the next sending



