# Pico-NR
Pico to NodeRed for use in Home Assistant

Simarine Pico to NodeRed blatantly ripped from https://github.com/htool/Pico2SignalK. I had to combine brainsmoke.py since I kept forgetting to keep both files together.

This requires a lot of manual preparation.

Still hardcoded to my devices. I added 1x 302 shunt and figured out the addresses. Then added the second 302, then the SCQ. Adding a battery, thermometers, and tanks will add new registers also... If devices are added, but not given IDs then the script bombs, because it sees a thermometer and doesn't know what to do (for instance). To fix, it's all got to be done manually right now, but maybe someone smarter than I can probably figure out how to automate it.

Use the debugs to determine the sensorlist for IDs (Line 208 or 255), then element registers for values (Line 282).

I diff the json and only upload changes. Every 10 minutes I kill the script in NodeRed and restart, since old values which don't change will never be updated, in the case of a Home Assistant restart.

I'd suggest you fix your device names in the Pico first, since the MQTT topics are based on device names. I haven't done that in this example yet, but it would require changing the pico.yaml for Home Assistant also. Save yourself time and do it first, or don't, since you can name it whatever you want in Home Assistant.

Produces json, which is processed by NodeRed:
[{'topic': '/pico/van/power', 'payload': 'OFF'}, 
{'topic': '/pico/environment/pressure', 'payload': 1025.72}, 
{'topic': '/pico/electrical/voltmeter/PICO INTERNAL/voltage', 'payload': 12.554}, 
{'topic': '/pico/electrical/voltmeter/PICO INTERNAL/name', 'payload': 'PICO INTERNAL'}, 
{'topic': '/pico/electrical/ammeter/SC302T [6573]/current', 'payload': 0.03}, 
{'topic': '/pico/electrical/ammeter/SC302T [6573]/name', 'payload': 'SC302T [6573]'}, 
{'topic': '/pico/electrical/voltmeter/SC302T [6573] U1/voltage', 'payload': 0.0}, 
{'topic': '/pico/electrical/voltmeter/SC302T [6573] U1/name', 'payload': 'SC302T [6573] U1'}, 
{'topic': '/pico/electrical/voltmeter/SC302T [6573] U2/voltage', 'payload': 12.686}, 
{'topic': '/pico/electrical/voltmeter/SC302T [6573] U2/name', 'payload': 'SC302T [6573] U2'}, 
{'topic': '/pico/electrical/ohmmeter/SC302T [6573] R1/ohms', 'payload': 'OPEN'}, 
{'topic': '/pico/electrical/ohmmeter/SC302T [6573] R1/name', 'payload': 'SC302T [6573] R1'}, 
{'topic': '/pico/electrical/ohmmeter/SC302T [6573] R2/ohms', 'payload': 10952}, 
{'topic': '/pico/electrical/ohmmeter/SC302T [6573] R2/name', 'payload': 'SC302T [6573] R2'}, 
{'topic': '/pico/electrical/ammeter/SC302T [7065]/current', 'payload': -0.0}, 
{'topic': '/pico/electrical/ammeter/SC302T [7065]/name', 'payload': 'SC302T [7065]'}, 
{'topic': '/pico/electrical/voltmeter/SC302T [7065] U1/voltage', 'payload': 0.0}, 
{'topic': '/pico/electrical/voltmeter/SC302T [7065] U1/name', 'payload': 'SC302T [7065] U1'}, 
{'topic': '/pico/electrical/voltmeter/SC302T [7065] U2/voltage', 'payload': 0.0}, 
{'topic': '/pico/electrical/voltmeter/SC302T [7065] U2/name', 'payload': 'SC302T [7065] U2'}, 
{'topic': '/pico/electrical/ohmmeter/SC302T [7065] R1/ohms', 'payload': 'OPEN'}, 
{'topic': '/pico/electrical/ohmmeter/SC302T [7065] R1/name', 'payload': 'SC302T [7065] R1'}, 
{'topic': '/pico/electrical/ohmmeter/SC302T [7065] R2/ohms', 'payload': 'OPEN'}, 
{'topic': '/pico/electrical/ohmmeter/SC302T [7065] R2/name', 'payload': 'SC302T [7065] R2'}, 
{'topic': '/pico/electrical/ammeter/SCQ25T [2172] 1/current', 'payload': 0.03}, 
{'topic': '/pico/electrical/ammeter/SCQ25T [2172] 1/name', 'payload': 'SCQ25T [2172] 1'}, 
{'topic': '/pico/electrical/ammeter/SCQ25T [2172] 2/current', 'payload': -0.0}, 
{'topic': '/pico/electrical/ammeter/SCQ25T [2172] 2/name', 'payload': 'SCQ25T [2172] 2'}, 
{'topic': '/pico/electrical/ammeter/SCQ25T [2172] 3/current', 'payload': -0.0}, 
{'topic': '/pico/electrical/ammeter/SCQ25T [2172] 3/name', 'payload': 'SCQ25T [2172] 3'}, 
{'topic': '/pico/electrical/ammeter/SCQ25T [2172] 4/current', 'payload': -0.0}, 
{'topic': '/pico/electrical/ammeter/SCQ25T [2172] 4/name', 'payload': 'SCQ25T [2172] 4'}, 
{'topic': '/pico/electrical/voltmeter/SCQ25T [2172] U1/voltage', 'payload': '0.0'}, 
{'topic': '/pico/electrical/voltmeter/SCQ25T [2172] U1/name', 'payload': 'SCQ25T [2172] U1'}, 
{'topic': '/pico/electrical/voltmeter/SCQ25T [2172] U2/voltage', 'payload': 0.0}, 
{'topic': '/pico/electrical/voltmeter/SCQ25T [2172] U2/name', 'payload': 'SCQ25T [2172] U2'}, 
{'topic': '/pico/electrical/voltmeter/SCQ25T [2172] U3/voltage', 'payload': '0.0'}, 
{'topic': '/pico/electrical/voltmeter/SCQ25T [2172] U3/name', 'payload': 'SCQ25T [2172] U3'}, 
{'topic': '/pico/electrical/ohmmeter/SCQ25T [2172] R1/ohms', 'payload': 'OPEN'}, 
{'topic': '/pico/electrical/ohmmeter/SCQ25T [2172] R1/name', 'payload': 'SCQ25T [2172] R1'}, 
{'topic': '/pico/electrical/ohmmeter/SCQ25T [2172] R2/ohms', 'payload': 'OPEN'}, 
{'topic': '/pico/electrical/ohmmeter/SCQ25T [2172] R2/name', 'payload': 'SCQ25T [2172] R2'}, 
{'topic': '/pico/electrical/ohmmeter/SCQ25T [2172] R3/ohms', 'payload': 'OPEN'}, 
{'topic': '/pico/electrical/ohmmeter/SCQ25T [2172] R3/name', 'payload': 'SCQ25T [2172] R3'}, 
{'topic': '/pico/electrical/ohmmeter/SCQ25T [2172] R4/ohms', 'payload': 'OPEN'}, 
{'topic': '/pico/electrical/ohmmeter/SCQ25T [2172] R4/name', 'payload': 'SCQ25T [2172] R4'}, 
{'topic': '/pico/electrical/batteries/HOUSE/name', 'payload': 'HOUSE'}, 
{'topic': '/pico/electrical/batteries/HOUSE/capacity/nominal', 'payload': 100.0}, 
{'topic': '/pico/electrical/batteries/HOUSE/temperature', 'payload': 73.4}, 
{'topic': '/pico/electrical/batteries/HOUSE/current', 'payload': 0.03}, 
{'topic': '/pico/electrical/batteries/HOUSE/capacity/remaining', 'payload': 97.6}, 
{'topic': '/pico/electrical/batteries/HOUSE/stateOfCharge', 'payload': 97.62}, 
{'topic': '/pico/environment/temperature/HOUSE/name', 'payload': 'HOUSE'}, 
{'topic': '/pico/environment/temperature/HOUSE', 'payload': 73.4}]
