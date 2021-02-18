import asyncio
import json
import RPi.GPIO as GPIO
from datetime import datetime
import serial
import requests
from gpiozero import MotionSensor
ser = serial.Serial('/dev/ttyACM1', baudrate=9600)
pir = MotionSensor(4)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)
GATE_CONFIG = {
    "gate_name": "gate1",
    "gate_availability": "available",
    "gate_is_busy" : False,
    "car_passed": False,
    "car_detected": False
    }

async def scan_id():
    print('Tap ID')
    id = str(ser.readline().decode("utf-8"))
    print(id)
    await asyncio.sleep(1)
    return id

async def is_verified(result):
    if (result == 'verified'):
        return True
    await asyncio.sleep(1)
    return False

async def unlift():
    GPIO.output(17,True)
    await asyncio.sleep(0.2)
    GPIO.output(17,False)
    
async def lift():
    GPIO.output(16,True)
    await asyncio.sleep(1.8)
    GPIO.output(16,False)
    print("Barrier is lifted")    
        
async def car_detection():
    pir.wait_for_motion()
    GATE_CONFIG['car_detected'] =  True
    print("car detected")
    pir.wait_for_no_motion()
    GATE_CONFIG['car_passed'] =  True
    print("car passed")
    print(GATE_CONFIG['car_passed'])
    await asyncio.sleep(1)
async def main():
           
        while True:        
            school_id = await scan_id()
            trueId = school_id[0:8:1]
            response = requests.get('https://agcs-serverless-function.vercel.app/api/iot/verifyId',params={'uid':trueId})
            print(response.url)
            ver = response.json()
            verResult = ver['data']
            print(verResult)
            if verResult == 'verified':    
                GATE_CONFIG['gate_is_busy'] = True
                print("gate is busy?",GATE_CONFIG['gate_is_busy'])
                await lift()
                await car_detection()
                if(GATE_CONFIG['car_detected']  and GATE_CONFIG['car_passed']):
                    await asyncio.sleep(1)   
                    await unlift()
                    await asyncio.sleep(1)
                    
                    query = {'gate':GATE_CONFIG['gate_name']}
                    payload = {'gate_availability':GATE_CONFIG['gate_availability'],
                               'gate_is_busy': GATE_CONFIG['gate_is_busy'],
                               }
                    statusRes = requests.post('https://agcs-serverless-function.vercel.app/api/iot/gates/updateGate',params=query,json=payload)
                    traffic ={'UID':trueId,
                              'date': datetime.now,
                              }
                    statusRes = requests.post('https://agcs-serverless-function.vercel.app/api/iot/data/insertTraffic', json=traffic)
asyncio.get_event_loop().run_until_complete(main())
