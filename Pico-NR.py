#!/usr/bin/python3

import os
import time
import socket
import sys
import select
import requests
import json
import copy

#import math

TOPIC = '/pico/'

def calc_rev_crc16(s, poly=0x1189, start=0x0000):
    crc = start
    for c in s:
        for i in range(8):
            c_msb   = (c   >>  7)&1
            crc_msb = (crc >> 15)&1

            c       = (c   <<  1)&0xff
            crc     = (crc <<  1)&0xffff

            if c_msb ^ crc_msb:
                crc ^= poly
    return crc

def calc_rev_crc16_table(s, table, start=0x0000):
    crc = start
    for c in s:
        crc = ((crc << 8)&0xffff) ^ table[c ^ (crc >> 8)]

    return crc

def calc_table(poly):
    return tuple( calc_rev_crc16([i], poly) for i in range(256))

if False:
    table = calc_table(0x1189)

    print ( calc_rev_crc16(b"123456789abcdef", 0x1189) )
    print ( calc_rev_crc16_table(b"123456789abcdef", table) )

responses = [''] * 200
sensors = ['']

def debug(string):
        print (string)
        sys.stdout.flush()

def empty_socket(sock):
    """remove the data present on the socket"""
    input = [sock]
    while 1:
        inputready, o, e = select.select(input,[],[], 0.0)
        if len(inputready)==0: break
        for s in inputready: s.recv(1)

def striplist(l):
    return([x.strip() for x in l])

def hexdump(b):
    hex = ' '.join(["%02x" % b ])
    if (len(hex) == 3):
      hex = "0" + hex
    if (len(hex) == 2):
      hex = "00" + hex
    return hex[0:2] + " " + hex[2:4]

def HexToByte( hexStr ):
    """
    Convert a string hex byte values into a byte string. The Hex Byte values may
    or may not be space separated.
    """
    bytes = []
    hexStr = ''.join( hexStr.split(" ") )
    for i in range(0, len(hexStr), 2):
        bytes.append( chr( int (hexStr[i:i+2], 16 ) ) )
    return ''.join( bytes )

def ByteToHex( byteStr ):
    """
    Convert a byte string to it's hex string representation e.g. for output.
    """
    return ''.join( [ "%02X " % ord( x ) for x in byteStr ] ).strip()

def HexToInt(hex,lastBytes):
    return int(hex.replace(' ','')[-lastBytes:], 16)

def IntToDecimal(integer):
    return integer / float(10)

def BinToHex(message):
    response = ''
    for x in message:
      hexy = format(x, '02x')
      response = response + hexy + ' '
    return response

def parse(message):
    values = message.split(' ff')
    values = striplist(values)
    return values

def getNextField(response):
  field_nr = int(response[0:2], 16)
  field_type = int(response[3:5] , 16)
  if (field_type == 1):
      data = response[6:17]
      response = response[21:]
      a = int(data[0:5].replace(' ','') , 16)
      b = int(data[6:11].replace(' ','') , 16)
      field_data = [a, b]
      return (field_nr, field_data, response)
  if (field_type == 3):
      data = response[21:32]
      response = response[36:]
      if (data[0:11] == '7f ff ff ff'):
        return field_nr, '', response
      else:
        a = int(data[0:5].replace(' ','') , 16)
        b = int(data[6:11].replace(' ','') , 16)
        field_data = [a, b]
        return field_nr, field_data, response
  if (field_type == 4): # Text string
      response = response[21:]
      nextHex = response[0:2]
      word = ''
      while (nextHex != '00'):
        word += nextHex
        response = response[3:]
        nextHex = response[0:2]
      word = HexToByte(word)
      response = response[6:] # Strip seperator
      return field_nr, word, response
  debug( "Uknown field type " + str(field_type))

def parseResponse(response):
  dict = {}
  response = response[42:]
  while (len(response) > 6):
    field_nr, field_data, response = getNextField(response)
    dict[field_nr] = field_data
  return dict

def add_crc(message):
  fields=message.split()
  message_int=[int(x,16) for x in fields[1:]]
  crc_int = calc_rev_crc16(message_int[0:-1])
  return message + " " + hexdump(crc_int)

def send_receive(message):
  bytes = message.count(' ') + 1
  message = bytearray.fromhex(message)
  s.sendall(message)
  response = ''
  hex = ''
  for x in s.recv(1024):
    hex = format(x, '02x')
    response = response + hex + ' '
  return response

def open_tcp(pico_ip):
  try:
    serverport = 5001
    s.connect((pico_ip, serverport))
    return
  except:
    debug( "Connection to " + str(pico_ip) + ":5001 failed. Retrying in 1 sec.")
    time.sleep(5)
    return open_tcp(pico_ip)

def get_pico_config(pico_ip):
  config = {}
  open_tcp(pico_ip)
  response_list = []
  fluid = ['fresh water','diesel']
  fluid_type = ['freshWater','fuel']
  message = ('00 00 00 00 00 ff 02 04 8c 55 4b 00 03 ff')
  message = add_crc(message)
  response = send_receive(message)
  req_count = int(response.split()[19], 16) + 1

  for pos in range(req_count):
    message = ('00 00 00 00 00 ff 41 04 8c 55 4b 00 16 ff 00 01 00 00 00 ' + "%02x" % pos + ' ff 01 03 00 00 00 00 ff 00 00 00 00 ff')
    message = add_crc(message)
    response = send_receive(message)
    element = parseResponse(response)
    config[pos] = element

  s.close()
  return config

def toTemperature (temp):
  if temp > 32768:
      temp = temp - 65536
  temp2 = float(("%.2f" % round((temp * .18) + 32, 2)))
  return temp2

def createDeviceList (config):
  deviceList = {}
  fluid = ['Unknown', 'freshWater', 'fuel', 'wasteWater']  # Simarine fluid types
  # Fluidtype label
  for entry in config.keys():
#DEBUG deviceList
#    debug( config[entry])
    id = config[entry][0][1]
    type = config[entry][1][1]
    deviceList[id] = {}
    if (type == 1):
      type = 'voltmeter'
      deviceList[id].update ({'name': config[entry][3]})
    if (type == 2):
      type = 'ammeter'
      deviceList[id].update ({'name': config[entry][3]})
    if (type == 3):
      type = 'thermometer'
      deviceList[id].update ({'name': config[entry][3]})
    if (type == 5):
      type = 'barometer'
      deviceList[id].update ({'name': config[entry][3]})
    if (type == 6):
      type = 'ohmmeter'
      deviceList[id].update ({'name': config[entry][3]})
    if (type == 8):
      type = 'tank'
      deviceList[id].update ({'name': config[entry][3]})
      deviceList[id].update ({'capacity': round(float(config[entry][7][1]) / 10 * 0.26417,1)})
      deviceList[id].update ({'fluid': fluid[config[entry][6][1]]})
    if (type == 9):
      type = 'battery'
      deviceList[id].update ({'name': config[entry][3]})
      deviceList[id].update ({'capacity.nominal': config[entry][5][1] / 100 })
    if (type == 14):
      type = 'alarmRelay'
      deviceList[id].update ({'name': config[entry][3]})

    deviceList[id].update ({'type': type})
  return deviceList

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
client.bind(("", 43210))

# Assign pico address
message, addr = client.recvfrom(2048)
pico_ip = addr[0]
#debug("See Pico at " + str(pico_ip))

config = get_pico_config(pico_ip)
#debug(config)

deviceList = createDeviceList(config)
#debug(deviceList)

responseB = [''] * 50
responseC = []

old_pico = {}
counter = 0

# Main loop
while True:
    pico = []
    deviceListTmp = copy.deepcopy(deviceList)

    message = ''
    while True:
      message, addr = client.recvfrom(2048)
      if len(message) > 100 and len(message) < 1000:
        break

    response = BinToHex(message)

    if response[18] == 'b':
      if len(response) == 0:
        continue
      else:
        pos = 0

    element = parseResponse(response)
#    debug("Element: " + str(element) )

    old_element = copy.deepcopy(element)


# Built-in   --------------------------------------
# Barometer
    deviceListTmp_id = 5
    element_id = 3
    deviceListTmp[deviceListTmp_id].update({'pressure':((element[element_id][1] + 65536) / 100)})

# Voltmeter
    deviceListTmp_id = 6
    element_id = 5
    if (element[element_id][1] != 65535):
      deviceListTmp[deviceListTmp_id].update({'voltage':round(element[element_id][1] / 1000,1)})

# SC302T #1 --------------------------------------
# Ammeter
    deviceListTmp_id = 10
    element_id = 11
    current = element[element_id][1]
    if (current > 25000):
      current = (65535 - current) / float(100)
    else:
      current = current / float(100) * -1  # (Reversed)
    deviceListTmp[deviceListTmp_id].update({'current': current})

# U1 Voltmeter
    deviceListTmp_id = 11
    element_id = 13
    if (element[element_id][1] <= 65530):
      deviceListTmp[deviceListTmp_id].update({'voltage':round(element[element_id][1] / 1000,1)})
    else:
      deviceListTmp[deviceListTmp_id].update({'voltage':'0.0'})

# U2 Voltmeter
    deviceListTmp_id = 12
    element_id = 14
    if (element[element_id][1] <= 65530):
      deviceListTmp[deviceListTmp_id].update({'voltage':round(element[element_id][1] / 1000,1)})
    else:
      deviceListTmp[deviceListTmp_id].update({'voltage':'0.0'})

# R1 Ohmmeter
    deviceListTmp_id = 13
    element_id = 15
    if (element[element_id][1] == 65535):
      deviceListTmp[deviceListTmp_id].update({'ohms': "OPEN" })
    else:
      deviceListTmp[deviceListTmp_id].update({'ohms': element[element_id][1] })

# R2 Ohmmeter
    deviceListTmp_id = 14
    element_id = 16
    if (element[element_id][1] == 65535):
      deviceListTmp[deviceListTmp_id].update({'ohms': "OPEN" })
    else:
      deviceListTmp[deviceListTmp_id].update({'ohms': element[element_id][1] })


# SC302T #2 --------------------------------------
# Ammeter
    deviceListTmp_id = 15
    element_id = 17
    current = element[element_id][1]
    if (current > 25000):
      current = (65535 - current) / float(100)
    else:
      current = current / float(100) * -1  # (Reversed)
    deviceListTmp[deviceListTmp_id].update({'current': current})

# U1 Voltmeter
    deviceListTmp_id = 16
    element_id = 19
    if (element[element_id][1] <= 65530):
      deviceListTmp[deviceListTmp_id].update({'voltage':round(element[element_id][1] / 1000,1)})
    else:
      deviceListTmp[deviceListTmp_id].update({'voltage':'0.0'})

# U2 Voltmeter
    deviceListTmp_id = 17
    element_id = 20
    if (element[element_id][1] <= 65530):
      deviceListTmp[deviceListTmp_id].update({'voltage':round(element[element_id][1] / 1000,1)})
    else:
      deviceListTmp[deviceListTmp_id].update({'voltage':'0.0'})

# R1 Ohmmeter
    deviceListTmp_id = 18
    element_id = 21
    if (element[element_id][1] == 65535):
      deviceListTmp[deviceListTmp_id].update({'ohms': "OPEN" })
    else:
      deviceListTmp[deviceListTmp_id].update({'ohms': element[element_id][1] })

# R2 Ohmmeter
    deviceListTmp_id = 19
    element_id = 22
    if (element[element_id][1] == 65535):
      deviceListTmp[deviceListTmp_id].update({'ohms': "OPEN" })
    else:
      deviceListTmp[deviceListTmp_id].update({'ohms': element[element_id][1] })

# SCQ25T  ----------------------------
# Ammeter 1
    deviceListTmp_id = 20
    element_id = 23
    current = element[element_id][1]
    if (current > 25000):
      current = (65535 - current) / float(100)
    else:
      current = current / float(100) * -1
    deviceListTmp[deviceListTmp_id].update({'current': current})

# Ammeter 2
    deviceListTmp_id = 21
    element_id = 25
    current = element[element_id][1]
    if (current > 25000):
      current = (65535 - current) / float(100)
    else:
      current = current / float(100) * -1
    deviceListTmp[deviceListTmp_id].update({'current': current})

# Ammeter 3
    deviceListTmp_id = 22
    element_id = 27
    current = element[element_id][1]
    if (current > 25000):
      current = (65535 - current) / float(100)
    else:
      current = current / float(100) * -1
    deviceListTmp[deviceListTmp_id].update({'current': current})

# Ammeter 4
    deviceListTmp_id = 23
    element_id = 29
    current = element[element_id][1]
    if (current > 25000):
      current = (65535 - current) / float(100)
    else:
      current = current / float(100) * -1
    deviceListTmp[deviceListTmp_id].update({'current': current})

# U1 Voltmeter
    deviceListTmp_id = 24
    element_id = 31
    if (element[element_id][1] <= 65530):
      deviceListTmp[deviceListTmp_id].update({'voltage':round(element[element_id][1] / 1000,1)})
    else:
      deviceListTmp[deviceListTmp_id].update({'voltage':'0.0'})

# U2 Voltmeter
    deviceListTmp_id = 25
    element_id = 32
    if (element[element_id][1] <= 65530):
      deviceListTmp[deviceListTmp_id].update({'voltage':round(element[element_id][1] / 1000,1)})
    else:
      deviceListTmp[deviceListTmp_id].update({'voltage':'0.0'})

# U3 Voltmeter
    deviceListTmp_id = 26
    element_id = 33
    if (element[element_id][1] <= 65530):
      deviceListTmp[deviceListTmp_id].update({'voltage':round(element[element_id][1] / 1000,1)})
    else:
      deviceListTmp[deviceListTmp_id].update({'voltage':'0.0'})

# R1 Ohmmeter
    deviceListTmp_id = 27
    element_id = 34
    if (element[element_id][1] == 65535):
      deviceListTmp[deviceListTmp_id].update({'ohms': "OPEN" })
    else:
      deviceListTmp[deviceListTmp_id].update({'ohms': element[element_id][1] })

# R2 Ohmmeter
    deviceListTmp_id = 28
    element_id = 35
    if (element[element_id][1] == 65535):
      deviceListTmp[deviceListTmp_id].update({'ohms': "OPEN" })
    else:
      deviceListTmp[deviceListTmp_id].update({'ohms': element[element_id][1] })

# R3 Ohmmeter
    deviceListTmp_id = 29
    element_id = 36
    if (element[element_id][1] == 65535):
      deviceListTmp[deviceListTmp_id].update({'ohms': "OPEN" })
    else:
      deviceListTmp[deviceListTmp_id].update({'ohms': element[element_id][1] })

# R4 Ohmmeter
    deviceListTmp_id = 30
    element_id = 37
    if (element[element_id][1] == 65535):
      deviceListTmp[deviceListTmp_id].update({'ohms': "OPEN" })
    else:
      deviceListTmp[deviceListTmp_id].update({'ohms': element[element_id][1] })

# alarmRelay
    deviceListTmp_id = 31
    element_id = 38
    if (element[element_id][1] == 1):
      deviceListTmp[deviceListTmp_id].update({'alarmRelay': "ON" })
    else:
      deviceListTmp[deviceListTmp_id].update({'alarmRelay': "OFF" })

#   HOUSE Batt Thermometer
    deviceListTmp_id = 33
    element_id = 44
    deviceListTmp[deviceListTmp_id].update({'temperature':toTemperature(element[element_id][1])})

#-------------------------------------------
#   HOUSE battery
    deviceListTmp_id = 32
    element_id = 39
    if (element[element_id][0] != 65535):
      stateOfCharge = float("%.2f" % (element[element_id][1] / 100.0))
      deviceListTmp[deviceListTmp_id].update({'stateOfCharge': stateOfCharge })
      deviceListTmp[deviceListTmp_id].update({'capacity.remaining':round(deviceList[deviceListTmp_id]['capacity.nominal'] *(stateOfCharge /100 ),1)  })
    current = element[element_id + 1][1]
    if (current > 25000):
      current = (65535 - current) / float(100)
    else:
      current = current / float(100) * -1
    deviceListTmp[deviceListTmp_id].update({'current': current})
#Voltmeter
    deviceListTmp[deviceListTmp_id].update({'voltage':round(element[element_id + 2][1] / float(1000),1)})
#Temperature
    deviceListTmp[deviceListTmp_id].update({'temperature':toTemperature(element[element_id + 5][1])})

#-------------------------------------------

# Front tank
    deviceListTmp_id = 34
    element_id = 45
    deviceListTmp[deviceListTmp_id].update({'currentLevel':element[element_id][0] / float(10)})
    deviceListTmp[deviceListTmp_id].update({'currentVolume':round(float(element[element_id][1]) / 10 * 0.26417,1)})
# Rear tank
    deviceListTmp_id = 35
    element_id = 46
    deviceListTmp[deviceListTmp_id].update({'currentLevel':element[element_id][0] / float(10)})
    deviceListTmp[deviceListTmp_id].update({'currentVolume':round(float(element[element_id][1]) / 10 * 0.26417,1)})
# Diesel tank
    deviceListTmp_id = 36
    element_id = 47
    deviceListTmp[deviceListTmp_id].update({'currentLevel':element[element_id][0] / float(10)})
    deviceListTmp[deviceListTmp_id].update({'currentVolume':round(float(element[element_id][1]) / 10 * 0.26417,1)})

#-------------------------------------------

#   Inside Thermometer
    deviceListTmp_id = 37
    element_id = 48
    deviceListTmp[deviceListTmp_id].update({'temperature':toTemperature(element[element_id][1])})

#-------------------------------------------

#Calculations
# Engine runs if Voltmeter is > 13.5 volt
    if (float(deviceListTmp[26]['voltage']) > 13.5):
      pico.append({"topic": TOPIC + "van/power", "payload": "RUNNING"})
    else:
      pico.append({"topic": TOPIC + "van/power", "payload": "OFF"})

#-------------------------------------------

# Populate JSON
    for key, value in deviceListTmp.items():
      if (value['type'] == 'battery'):
#        pico.append({"topic": TOPIC + "electrical/batteries/" +value['name'] + "/name", "payload": value['name']})
        pico.append({"topic": TOPIC + "electrical/batteries/" +value['name'] + "/capacity/nominal", "payload": value['capacity.nominal']})
        if 'voltmeter' in value:
          pico.append({"topic": TOPIC + "electrical/batteries/" +value['name'] + "/voltage", "payload": value['voltage']})
        if 'temperature' in value:
          pico.append({"topic": TOPIC + "electrical/batteries/" +value['name'] + "/temperature", "payload": value['temperature']})
        if 'current' in value:
          pico.append({"topic": TOPIC + "electrical/batteries/" +value['name'] + "/current", "payload": value['current']})
        if 'capacity.remaining' in value:
          pico.append({"topic": TOPIC + "electrical/batteries/" +value['name'] + "/capacity/remaining", "payload": value['capacity.remaining']})
          pico.append({"topic": TOPIC + "electrical/batteries/" +value['name'] + "/stateOfCharge", "payload": value['stateOfCharge']})
        if 'capacity.timeRemaining' in value:
          pico.append({"topic": TOPIC + "electrical/batteries/" +value['name'] + "/capacity/timeRemaining", "payload": value['capacity.timeRemaining']})
      if (value['type'] == 'barometer'):
        pico.append({"topic": TOPIC + "environment/pressure", "payload": value['pressure']})
      if (value['type'] == 'thermometer'):
#        pico.append({"topic": TOPIC + "environment/temperature/" +value['name'] + "/name", "payload": value['name']})
        pico.append({"topic": TOPIC + "environment/temperature/" +value['name'] ,"payload": value['temperature']})
      if (value['type'] == 'tank'):
        pico.append({"topic": TOPIC + "tanks/" + value['fluid'] + "/" +value['name'] + "/currentLevel", "payload": value['currentLevel']})
        pico.append({"topic": TOPIC + "tanks/" + value['fluid'] + "/" +value['name'] + "/currentVolume", "payload": value['currentVolume']})
#        pico.append({"topic": TOPIC + "tanks/" + value['fluid'] + "/" +value['name'] + "/name", "payload": value['name']})
#        pico.append({"topic": TOPIC + "tanks/" + value['fluid'] + "/" +value['name'] + "/type", "payload": value['fluid']})
        pico.append({"topic": TOPIC + "tanks/" + value['fluid'] + "/" +value['name'] + "/capacity", "payload": value['capacity']})
      if (value['type'] == 'alarmRelay'):
        pico.append({"topic": TOPIC + "alarmRelay", "payload": value['alarmRelay']})
      if (value['type'] == 'voltmeter'):
        pico.append({"topic": TOPIC + "electrical/voltmeter/" +value['name'] + "/voltage", "payload": value['voltage']})
#        pico.append({"topic": TOPIC + "electrical/voltmeter/" +value['name'] + "/name", "payload": value['name']})
      if (value['type'] == 'ohmmeter'):
        pico.append({"topic": TOPIC + "electrical/ohmmeter/" +value['name'] + "/ohms", "payload": value['ohms']})
#        pico.append({"topic": TOPIC + "electrical/ohmmeter/" +value['name'] + "/name", "payload": value['name']})
      if (value['type'] == 'ammeter'):
        pico.append({"topic": TOPIC + "electrical/ammeter/" +value['name'] + "/current", "payload": value['current']})
#        pico.append({"topic": TOPIC + "electrical/ammeter/" +value['name'] + "/name", "payload": value['name']})



    old_pico_topics = {d["topic"]:d for d in old_pico}
    pico_topics = {d["topic"]:d for d in pico}

    assert len(old_pico_topics) == len(old_pico), "DUPLICATE TOPICS DETECTED"
    assert len(pico_topics) == len(pico), "DUPLICATE TOPICS DETECTED"

    diff = []

# for keys that are in both pico and old_pico, check if there's a payload difference
    for k in set(pico_topics) & set(old_pico_topics):
        if pico_topics[k]["payload"] != old_pico_topics[k]["payload"]:

            diff.append(pico_topics[k])

# for keys that are in pico but not in old_pico, just copy over
    for k in set(pico_topics) - set(old_pico_topics):
        diff.append(pico_topics[k])

    counter = counter + 1
    diff.append({"topic": TOPIC + "counter", "payload": counter})

    old_pico = copy.deepcopy(pico)

#Output for Node-Red use
    debug(str(diff))

    sys.stdout.flush()
    time.sleep (0.9)
    empty_socket(client)
