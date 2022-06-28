
'''

'''
import spidev
import time
from time import sleep
from datetime import datetime
from firebase import firebase
import RPi.GPIO as GPIO
from csv import writer
import csv
import smtplib

GPIO.setmode(GPIO.BCM)

fb = firebase.FirebaseApplication('https://water-quality-42101-default-rtdb.firebaseio.com/',None)

#Open SPI bus
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

#define custom chip select this is done so we can use dozens of SPI devices on 1 bus
CS_ADC = 12
GPIO.setup(CS_ADC, GPIO.OUT)

#function to store data to csv file
def store_data(time,fb_ph,fb_turb,value):
    append = [time,fb_ph,fb_turb,value]
    with open('sensor_output.csv', 'a') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(append)
    csvFile.close()

# Function to read SPI data from MCP3008 chip Channel must be an integer 0-7
def ReadChannel3008(channel):
    #below sends 00000001 1xxx0000 00000000 to the chip and records the response
    #xxx encodes 0-7, the channel selected for the transfer.
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

#same thing but for the 12-bit MCP3208
def ReadChannel3208(channel):
    adc = spi.xfer2([6|(channel>>2),channel<<6,0]) #0000011x,xx000000,00000000
    data = ((adc[1]&15) << 8) + adc[2]
    return data

def ConvertToVoltage(value, bitdepth, vref):
    return vref*(value/(2**bitdepth-1))

# Define delay between readings
delay = 10
 
while True:
    GPIO.output(CS_ADC, GPIO.LOW)

    phvalue = ReadChannel3208(2)
    turbvalue = ReadChannel3208(0)

    GPIO.output(CS_ADC, GPIO.HIGH)

    #voltage = ConvertToVoltage(value, 12, 3.3) #for MCP3208 at 3.3V
    fb_ph=phvalue/300
    fb_turb=turbvalue/1024

    print("pH is" ,fb_ph)
    print("turbidity is" ,fb_turb)

    
    res="out of range" 
    value=0
    if fb_turb<=1.5 or fb_turb>4.5 or fb_ph<=6.5 or fb_ph>=8:
        message = "Turbidity (should be 1.5-4.5NTU) sensor value : "+str(fb_turb)+"\npH (should be 6.5-7.5)  sensor value : "+str(fb_turb)+" \n one of the above is out of range \n Please take measures immediately!!"
        smtpUser="project.be.jnn@gmail.com"
        smtpPass="SSVP@2021"
        toAdd = "project.b3.jnn@gmail.com"
        fromAdd = smtpUser
        subject="water quality in your area"
        header= "Take action Fast on your water"
        body="values of ph and turbidity are: "

        s=smtplib.SMTP("smtp.gmail.com",587)
        s.ehlo()
        s.starttls()
        s.ehlo()

        s.login(smtpUser,smtpPass)
        s.sendmail(fromAdd,toAdd , body)
        s.quit()

        print("Water is not safe")
        value=1
        #call store_data function to store data in csv
        #in csv there will be 3 columns date_time,ph and turbidity value
        store_data(datetime.now().strftime('%Y-%m-%d,%H:%M:%S,'),fb_ph,fb_turb,value)

    else:
        print("Water is safe")
        store_data(datetime.now().strftime('%Y-%m-%d,%H:%M:%S,'),fb_ph,fb_turb,value)

    #using post to send data to firebase branch sensor
    fb.post('/sensor',
                  { 'date': datetime.now().strftime('%Y-%m-%d,%H:%M:%S,'),
                    'ph':fb_ph,
                    'turbidity':fb_turb
                  })


    # Wait before repeating loop
    time.sleep(delay)
