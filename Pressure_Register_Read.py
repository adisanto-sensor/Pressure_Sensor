' ******Rev History*****'
'I2C_Write working using sleep command Date 12/18/2019'

import time
import sys
import signal
import matplotlib.pyplot as plt
import numpy
from PyMata.pymata import PyMata

# Digital pin 13 is connected to an LED. If you are running this script with
# an Arduino UNO no LED is needed (Pin 13 is connected to an internal LED).
BOARD_LED = 13

# some global sensor registers variables
sensor_operation_mode = 0x04
sensor_i2c_addr = 0x6C
sensor_hw_version_reg = 0x38
corrected_pressure = 0x30
corrected_temp_register = 0x2E

Config_Mode_List =['Sensor Signal Correction Enabled',\
                'Temp Compensation of Bridge and Internal Temp Sensor' ,\
                'Temp Sensor',\
                'Post Coarse Correction Eanbled',\
                'AODO Scale/Offset Enabled',\
                'AOD0 Limiting Enabled',\
                'Error Signaling Enabled',\
                'Ratio Analog Output, DAC Output Temp Correction Coeff Set 0',\
                'Absolute Temp Signal Correction',\
                'Sensor Acq. Diags Chain Disabled', \
                'DSP Post scaling Alarm Disabled']

# Dict of Registers
Main_Registers = {0:{'Reg':hex(0x50),'Name':'SER0'},
        1:{'Reg':hex(0x52),'Name':'SER1'},
        2:{'Reg':hex(0x54),'Name':'RATIO_DAC0'}, 
        3:{'Reg':hex(0x56),'Name':'RATIO_DAC23'},
        4:{'Reg':hex(0x58),'Name':'RATIO_DAC45'},
        5:{'Reg':hex(0x5A),'Name':'ABS_V_DAC01'},
        6:{'Reg':hex(0x5A),'Name':'ABS_V_DAC01'},
        7:{'Reg':hex(0x5C),'Name': 'ABS_V_DAC23'}, 
        8:{'Reg':hex(0x5E),'Name':'ABS_V_DAC45'}, 
        9:{'Reg':hex(0x60),'Name':'ABS_I_DAC01'}, 
        10:{'Reg':hex(0x62),'Name':'BS_I_DAC23'},
        11:{'Reg':hex(0x64),'Name':'ABS_I_DAC45'}, 
        12:{'Reg':hex(0x66) ,'Name' :'G01 IC'},
        13:{'Reg':hex(0x68),'Name':'G2OFF'}, 
        14:{'Reg':hex(0x00), 'Name':'CFG_CAL0 I'},
        15:{'Reg':hex(0x02), 'Name':'CFG_CAL1'}, 
        16:{'Reg':hex(0x06), 'Name':'CFG_SPI_I2C'},
        17:{'Reg':hex(0x08), 'Name':'CFG_PADS0'},
        18:{'Reg':hex(0x0A), 'Name':'CFG_PADS1'},
        19:{'Reg':hex(0x0C0),'Name': 'CFG_PADS2'},
        20:{'Reg':hex(0x0E), 'Name':'CFG_PERIOD'}, 
        21:{'Reg':hex(0x10), 'Name': 'CFG_AODO'},
        22:{'Reg':hex(0x12), 'Name':'CFG_SBC_INTF'}, 
        23:{'Reg':hex(0x14), 'Name': 'CFG_ADC'}, 
        24:{'Reg':hex(0x16), 'Name': 'CFG_LP0'}, 
        25:{'Reg':hex(0x18), 'Name': 'CFG_LP1'},
        26:{'Reg':hex(0x1A), 'Name': 'CFG_AFE0'},
        27:{'Reg':hex(0x1C), 'Name': 'CFG_AFE1'},
        28:{'Reg':hex(0x1E), 'Name': 'CFG_AFE2'},
        29:{'Reg':hex(0x6A), 'Name': 'USER'}}

DSP_Registers = {0:{'Reg': hex(0x6C), 'Name' : 'Temp prescale offset coeff'},
        1:{'Reg':hex(0x6E), 'Name':'Temp prescaling gain coefficient'},
        2:{'Reg':hex(0x70), 'Name':'Pressure prescaling offset coeff'},
        3:{'Reg':hex(0x72), 'Name':'Pressure prescaling gain coeff'},
        4:{'Reg':hex(0x74), 'Name': 'S0 pressure sensor coeff'},
        5:{'Reg':hex(0x76), 'Name':'S1 pressure sensor coeff'},
        6:{'Reg':hex(0x78), 'Name':'S2 pressure sensor coeff'},
        7:{'Reg':hex(0x7A), 'Name':'S3 pressure sensor coeff'},
        8:{'Reg':hex(0x7C), 'Name':'S4 pressure sensor coeff'},
        9:{'Reg':hex(0x7E), 'Name':'S5 pressure sensor coeff'},
        10:{'Reg':hex(0x80), 'Name':'S6 pressure sensor coeff'},
        11:{'Reg':hex(0x82), 'Name':'S7 pressure sensor coeff'}}
 
Results_Registers = {0:{'Reg': hex(0x26), 'Name' :'Chip temp ADC'},
        1:{'Reg':hex(0x28), 'Name':'Temp ADC value for signal correction'},
        2:{'Reg':hex(0x2A), 'Name':'Pressure sensor ADC value'},
        3:{'Reg':hex(0x2C), 'Name':'A0D0 output value'},
        4:{'Reg':hex(0x2E), 'Name':'Corrected temp value'},
        5:{'Reg':hex(0x30), 'Name':'Corrected pressure value'}}

# Create a PyMata instance
board = PyMata("COM3", verbose=True)

print ("Board", board)


######################################


# Main Menu Function
def mainMenu():
    while True:
        print("\n\n")
        print("\t*****************************")
        print("\t MAIN MENU")
        print("\t Ctrl+C to Exit Selection")
        print("\t*****************************")
        print("\t 0. Test Board Communication / Blink LED on UNO board")
        print("\t 1. Read IC Version and Sensor Configuration")
        print("\t 2. Dump DSP Registers")
        print("\t 3. Dump Main Registers")
        print("\t 4. Read Corrected Pressure")
        print("\t 5. Read Corrected Temperature")
        print("\t 6. Dump Results Registers")
        print("\t 7. Read Single Register")
        print("\t 8. Quit/Test Function")
        print("\n")
        selection=(input("Enter Choice:" ))
        
        if selection.isalpha():
            print("ERROR: You entered a letter, Enter valid number:")
            mainMenu()
            
        elif selection == '0':
                count=int(input("Enter number of times:"))
                print("LED 13 will blink on the Uno board")
                blink(count)

        elif selection == '1':
                read_HW_Version()

        elif selection == '2':
                #Call function (func) and pass dictionary holding registers into it 
                func(DSP_Registers)

        elif selection == '3':
                func(Main_Registers)

        elif selection == '4':
                count = int(input("Enter number of times to Loop: "))
                print("Enter Ctrl+C to Exit")
                pressure_register_read(corrected_pressure,count)

        elif selection == '5':
                count = int(input("Enter number of times to Loop: "))
                print("Enter Ctrl+C to Exit")
                temp_register_read(corrected_temp_register,count)
                
        # Read Results Registers
        elif selection == '6':
                func(Results_Registers)
                
        # Read single Register
        elif selection == '7':
                register = (input("Enter Register 0x:"))
                count = int(input("Enter number of times to Loop: "))
                print("Enter Ctrl+C to Exit")
                single_register_read(register,count,Main_Registers)

        elif selection == '8':
                #board.reset()
                #sys.exit(0)
                i2c_write()

        else:
                print("Enter a valid selection number:")
                mainMenu()

# Working.... I2C

def i2c_write():
    # (device addr, register addr, lowbyte, highbyte)
    board.i2c_write(0x6c,0x22,0x32,0x6C)

# Read Sensor hw version via I2C interface
def read_HW_Version():
    board.i2c_read(sensor_i2c_addr, sensor_hw_version_reg, 2, board.I2C_READ)
    time.sleep(1)
    data = board.i2c_get_read_data(sensor_i2c_addr)
    word = data[2] << 8 | data[1]
    print("IC Version --->" , hex(word))

    # Read Sensor Configuration
    board.i2c_read(sensor_i2c_addr, sensor_operation_mode, 2, board.I2C_READ)
    time.sleep(1)
    data = board.i2c_get_read_data(sensor_i2c_addr)
    word = data[2] << 8 | data[1]
    if word == 0x13da:
        print("\n")
        print("\t *** Operational Mode for Sensor *** ")
        for List in Config_Mode_List:
            print('\t' , List)
    else:
        print("Operational Configuration of Sensor has changed")

def single_register_read(register, count, Main_Registers):
    #Need to convert hex 'string' to int, 16 determines base
    register=int(register,16)
    #Convert stupid thing back to a string so that we can add name to the register read 
    register_back_hex_string=hex(register)
    for key, reg in Main_Registers.items():
        # Get register number from dict that and do string compare from the register read requested
        get_register_number = Main_Registers[key]['Reg'] 
        if (get_register_number == register_back_hex_string):
            print(" *** Reading from Main Register Bank ***" , Main_Registers[key]['Name'])
    # Do the register read as requested
    for x in range(count):
        board.i2c_read(sensor_i2c_addr, register, 2, board.I2C_READ)
        time.sleep(1)
        data = board.i2c_get_read_data(sensor_i2c_addr)
        data = data[2] << 8 | data[1]
        print(hex(register), "Data--> Hex", hex(data), "Binary", (format(data, '#018b')))
    
def func(Registers):      
    for key, reg in Registers.items():
        # reg variable above is place holder for .items method, value is used as the index into dict
        print("\nDictionary ID:" , key)
        r_register_str_address = (Registers[key]['Reg'])
        r_register_hex_address = int(r_register_str_address, 16)
        register_name = (Registers[key]['Name'])
        board.i2c_read(sensor_i2c_addr, r_register_hex_address, 2, board.I2C_READ)
        time.sleep(1)
        data = board.i2c_get_read_data(sensor_i2c_addr)
        data = data[2] << 8 | data[1]
        print("Register Name:", register_name, "\nRegister--> ", r_register_str_address, "\nData-->", hex(data))

# Blink Function
def blink(count):
    for x in range(count):
        print(x + 1)
        # Set the output to 1 = High
        board.digital_write(BOARD_LED, 1)
        # Wait a half second between toggles.
        time.sleep(1)
        # Set the output to 0 = Low
        board.digital_write(BOARD_LED, 0)
        time.sleep(1)

# Read Pressure Register
def pressure_register_read(register,count):
    # Plot stuff
    p_delta = 0
    ydata = []
    xdata = []
    #plt.show()
    plt.title('ChemHost Sensor', loc='center',color='b')
    plt.suptitle('Enter Crtl+C to Kill Plot',color='r')
    plt.ylabel('mmHg', color='r')
    plt.xlabel('Counts', color='b')
    fig = plt.gca()
    fig.set_xlim(0, 100)
    fig.set_ylim(720, 760)
    line, = fig.plot(xdata,ydata, 'r-')
        
    for x in range(count):
        board.i2c_read(sensor_i2c_addr, register, 2, board.I2C_READ)
        time.sleep(1)
        data = board.i2c_get_read_data(sensor_i2c_addr)
        # data[2] = byte 4 of pressure data
        # data[1] = byte 3 of pressure data
        # shift both bytes into a word (i.e) 0x[E5][68]
        pressure_counts = data[2] << 8 | data[1]
        print("Pressure Counts", pressure_counts)
        b = pressure_counts
        if  b >= 1 << 15:
            b -= 1 << 16
        print("Pressure 2's Complement", (b))
        P_DOUT_max = 26214
        P_DOUT_min = -26214
        PMax = 1260 
        PMin = 460
        P0 = 760
        Delta_P_DOUT = 52428
        p_read = PMin + ((b - P_DOUT_min) / (Delta_P_DOUT )) *(PMax - PMin)
        print("Pressure in mmHg            ", p_read)
        xdata.append(x)
        ydata.append(p_read)
        line.set_xdata(xdata)
        line.set_ydata(ydata)
        plt.draw()
        plt.pause(1e-17)
        # Tony
        time.sleep(.1)
        p_delta += p_read
        # if (p_delta > 10000):
        #    i2c_write()
        
   
# Read Temp Register
def temp_register_read(register,count):
    # Plot stuff 
    ydata = []
    xdata = []
    #plt.show()
    plt.title('ChemHost Sensor', loc='center',color='r')
    plt.ylabel('Temperature  C', color='r')
    plt.xlabel('Counts', color='b')
    fig = plt.gca()
    fig.set_xlim(0, 100)
    fig.set_ylim(0, 40)
    line, = fig.plot(xdata,ydata, 'r-')
        
    for x in range(count):
        board.i2c_read(sensor_i2c_addr, register, 2, board.I2C_READ)
        time.sleep(1)
        data = board.i2c_get_read_data(sensor_i2c_addr)
        # data[2] = byte 4 of temp data
        # data[1] = byte 3 of temp data
        # shift both bytes into a word (i.e) 0x[E5][68]
        temp_counts = data[2] << 8 | data[1]
        print("Temp Counts", temp_counts)
        b = temp_counts
        if  b >= 1 << 15:
            b -= 1 << 16
        print("Temp 2's Complement", (b))
        t_read = (b * .002578 + 42.5)
        print("Temperature =           ", t_read)
        xdata.append(x)
        ydata.append(t_read)
        line.set_xdata(xdata)
        line.set_ydata(ydata)
        plt.draw()
        plt.pause(1e-17)
        time.sleep(0.1)
        
# Event Handler
def signal_handler(sig, frame):
    print('You pressed Ctrl+C')
    # Close graph
    if board is not None:
        plt.close()
        mainMenu()

signal.signal(signal.SIGINT, signal_handler)

version = board.get_firmata_version()
print("Firmata Version....", version) 

# Set digital pin 13 to be an output port
board.set_pin_mode(BOARD_LED, board.OUTPUT, board.DIGITAL)

time.sleep(2)
print("Blinking LED on pin 13 for 10 times ...")

# Configure firmata for i2c on an UNO, call just once####
board.i2c_config(0, board.ANALOG, 4, 5)
 
# call main menu

mainMenu()

# Close PyMata when we are done
board.close()
