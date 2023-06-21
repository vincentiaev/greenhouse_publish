from machine import Pin, ADC
from time import sleep, ticks_us
import network
import machine
from umqtt.simple import MQTTClient
import ubinascii
import micropython
import esp
import gc
import dht

esp.osdebug(None)
gc.collect()

ssid = 'PCU_Sistem_Kontrol'
password = 'lasikonn'
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid,password)

sensor_dht = dht.DHT11(Pin(14)) #pin d5
soil_sensor = ADC(0) #pin A0

while station.isconnected() == False:
  pass

print('connect success')
print(station.ifconfig())


broker = '192.168.41.70'
clientid = ubinascii.hexlify(machine.unique_id())
topicsub = b'4170/dht11/temp'
topicpub_temp = b'4170/dht11/temp'
topicpub_hum = b'4170/dht11/hum'
topicpub_soil = b'4170/soil'
topicpub_ldr = b'4170/ldr'
topicpub_flow = b'4170/flow'

def subscribecallback(topic, msg):
  print(topic, msg)
  # if topic == b'.....' and msg == b'.....'
  #   .....
  
def connect():
  global clientid,broker,topicsub,topicpub
  client = MQTTClient(clientid,broker)
  client.set_callback(subscribecallback)
  client.connect()
  client.subscribe(topicsub)
  print('Connected to %s, subscribed to %s' % (broker, topicsub))
  return client

def restartandconnect():
  print('failed to connect, restarting....')
  sleep(10)
  machine.reset()
  
def read_sensor_dht():
  while True:
    try:
      sleep(1)
      sensor_dht.measure()
      temp = sensor_dht.temperature()
      hum = sensor_dht.humidity()
      #print('Temperature: %3.1f C' %temp)
      #print('Humidity: %3.1f %%' %hum)
      return temp, hum
    except OSError as e:
      print('Failed to read sensor.')

def read_sensor_soil():
  while True:
    try:
      moisture = soil_sensor.read()
      sleep(1)
      moisture_percent = ((1023 - moisture) / 1023) * 100
      #print('Soil Moisture: %d%%' %moisture_percent)
      return moisture_percent
    except OSError as e:
      print('Failed to read sensor.')

def ldr_dummy():
  while True:
    sleep(1)
    ldr = (float(ticks_us()) % 2001) / 123 * 172 + 10000
    return ldr

def flow_dummy():
  while True:
    sleep(1)
    flow = (float(ticks_us()) % 101) / 105 * 110 + 200
    return flow
  
try:
  client = connect()
except OSError as e:
  restartandconnect()

while True:
  try:
    sleep(1)
    temp, hum = read_sensor_dht()
    moisture_percent = read_sensor_soil()
    ldr = ldr_dummy()
    flow = flow_dummy()
    msg = client.check_msg()
    if msg != 'None':
      client.publish(topicpub_temp, '%3.1f' %temp)
      client.publish(topicpub_hum, '%3.1f' %hum)
      client.publish(topicpub_soil, '%d' %moisture_percent)
      client.publish(topicpub_ldr, '%3.1f' %ldr)
      client.publish(topicpub_flow, '%3.1f' %flow)
        
  except OSError as e:
    restartandconnect()
    



