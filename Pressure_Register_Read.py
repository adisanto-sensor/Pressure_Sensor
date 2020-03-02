' ******Rev History*****'
'I2C_Write working using sleep command Date 12/18/2019'
'added simple test to unlock and read nvm area.  12/23/2019'
'added cmd dict access and cmds  1/6/2020'
'added lambda function and ub menu commands 1/13/2020'
'fixed i2c_write_register  1/20/2020'
'added CMD command idel, sleep, reset and start 1/20/2020'


import time
import sys
import signal
import matplotlib.pyplot as plt
import numpy
from PyMata.pymata import PyMata
from crccheck.crc import Crc8

# Digital pin 13 is connected to an LED. If you are running this script with
# an Arduino UNO no LED is needed (Pin 13 is connected to an internal LED).
BOARD_LED = 13

# sensor registers variables
sensor_operation_mode = 0x04
sensor_i2c_addr = 0x6C
sensor_hw_version_reg = 0x38
corrected_pressure = 0x30
corrected_temp_register = 0x2E

# Configuration Memory (CM) Access 
# Address and command access to CM area
cm_status_reg = 0x46
cm_rdata_reg  = 0x48
cm_wdata_reg = 0x4A
cm_cmd_reg = 0x4E

# Commands for CM_CMD
cm_read_cmd = 0x4C
cm_crc_cmd = 0x88

# lamda byte extraction
extract_lowb = lambda a: (a & 0xFF)
extract_highb = lambda a: (a >> 8)

# Command Register (CMD)
cmd_Addr =  0x22

# CMD Cookies
cmd_cookie = {1: 0xF75A, 
              2: 0x0CC7,
              3: 0xD21E}

# cmd cookie flag to see if cookies were send once to enable CM reads

cmd_cookie_flag = False 

Config_Mode_List =['Sensor Signal Correction Enabled',
                'Temp Compensation of Bridge and Internal Temp Sensor' ,
                'Temp Sensor',
                'Post Coarse Correction Eanbled',
                'AODO Scale/Offset Enabled',
                'AOD0 Limiting Enabled',
                'Error Signaling Enabled',
                'Ratio Analog Output, DAC Output Temp Correction Coeff Set 0',
                'Absolute Temp Signal Correction',
                'Sensor Acq. Diags Chain Disabled', 
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

#data = (0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39)
#crc = Crc8.calc(data)
#print ("Test new CRC", hex(crc))

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
        print("\t 2. Read Sensor DSP Registers")
        print("\t 3. Read Sensor Main Registers")
        print("\t 4. Plot Corrected Pressure")
        print("\t 5. Plot Corrected Temperature")
        print("\t 6. Read Sensor Results Registers")
        print("\t 7. Read Single Address Register")
        print("\t 8. CMD Modes Idle - Start - Reset - Sleep")
        print("\t 9. Read CM Address Offsets ex: CM-->0x00 = 0x50 ")
        print("\t 10. Read CM factory calibration area 0x00 to 0x1E and display checksum")
        print("\t 99. Quit/Exit")
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
                sub_Menu()
        #main menu command
                
        elif selection == '9':
                cm_addr_offset = (input("Enter to CM location to Read: "))
                i2c_cm_register_access(cm_addr_offset)

        elif selection == '10':
                'Do unlock of CM memory'
                read_calibration()

        elif selection == '99':
                board.reset()
                sys.exit(0)
        else:
                print("Enter a valid selection number:")
                mainMenu()


def sub_Menu():
    sub_sel = input("CMD modes available"
                    "\n\t"
                    "0: Idle"
                    "\n\t"
                    "1: Start Measurement"
                    "\n\t"
                    "2: Reset"
                    "\n\t"
                    "3: Power Sleep State (Untested)"
                    "\n"
                    "Enter Command:")

    if sub_sel.isalpha():
        print("ERROR: You entered a letter, Enter valid number:")
        sub_Menu()

    elif sub_sel == '0':
        print("Idle") #Idle
        cmd_Idle = 0x7BBA
        _mode(cmd_Idle)

    elif sub_sel == '1':
        print("Start") # Start
        cmd_Start = 0x8B93
        _mode(cmd_Start)

    elif sub_sel == '2': #Reset
        print("Reset")
        cmd_Reset = 0xB169
        _mode(cmd_Reset)
        
    elif sub_sel == '3': #Sleep
        print("Sleep")
        cmd_Sleep = 0x6C32
        _mode(cmd_Sleep)

    else:
        print("Enter a valid selection number:")
        mainMenu()

#CRC working area 
def crc8(buff):
    crc = 0
    print ('Buffer', buff)
    for b in buff:
        # print('Buff = ' , b)
        # bitwise xor
        crc ^= b
       # print('crc1=', bin(crc))
        for i in range(8):
            # print('i=' , i)
            if ((crc & 0x80) != 0):
                crc = (crc << 1) ^ 0x7
                #print (      '       CRC2 = ', bin(crc))
            else:
                crc <<= 1
    print ('Final CRC8  =', bin(crc))
    print ('Final CRC8 = ', hex(crc & 0xFF))
    return crc

#buff = [0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39]
#crcc = crc8(buff)
#print('Sub =', hex(crcc))
#hex(crcc >> 8)
#print('Final', hex(crcc & 0xFF))


# CMD modes writes
def _mode(cmd):
        _unlock_1()
        board.i2c_write(sensor_i2c_addr, cmd_Addr , extract_lowb(cmd), extract_highb(cmd) )
        print("Command Sent") 

# Unlock to enable system register write access 
def _unlock_1():
    for key , cmd in cmd_cookie.items():
        print('Sending Unlock ''CMD'' Cookies = ' , hex(cmd_cookie[key]))
        #low_byte = extract_lowb(cmd)
        #high_byte = extract_highb(cmd)
        #print(hex(a))
        #print(hex(b))
        board.i2c_write(sensor_i2c_addr, cmd_Addr, extract_lowb(cmd), extract_highb(cmd))
    global cmd_cookie_flag 
    cmd_cookie_flag = True 

 
# unlock CM area with the cookie sequence 0xf75A, 0x0cc7, 0xd21e
# 0x22 = register address to write cookie
def _unlock():
    board.i2c_write(0x6c, 0x22, 0x5A, 0xF7)
    board.i2c_write(0x6c, 0x22, 0xc7, 0x0c)
    board.i2c_write(0x6c, 0x22, 0x1e, 0xd2)

# Read the CM registers related to calibration 0x0 to 0x1E
def read_calibration():
    # Do CRC check for a test 
    board.i2c_write(sensor_i2c_addr, cm_cmd_reg, 0x0, 0x88)
    print ('Read CM area from locations 0x00 to 0x1E CRC8 Check')
    cm_addr_lower = 0  # CM 0x00 
    cm_addr_upper = 31 # CM 0x1F 
    cal_array = [None] * 32 
    #do unlock
    if cmd_cookie_flag == False:  # Just want to unlock cm area once so test this flag to ensure it got unlock once. 
        _unlock_1()
    # write CM_CMD register --> command register 0x4C and register to read.
    for x in range (cm_addr_lower, cm_addr_upper , 2):
        print ('CM Address = ', hex(x))
        board.i2c_write(sensor_i2c_addr, cm_cmd_reg, x , cm_read_cmd)
        time.sleep(1)
        # cmd read register location = 0x48
        board.i2c_read(sensor_i2c_addr, cm_rdata_reg, 2, board.I2C_READ)
        time.sleep(1)
        data = board.i2c_get_read_data(sensor_i2c_addr)
        # need sleep for some reason on NVM read, maybe timing to memory
        word = data[2] << 8 | data[1]
        print("Read Cal Area --->" , hex(word))
        cal_array[x] = data[1]
        # x + 1 fills the odd locations into the cal array like 1, 3,5,7 
        cal_array[x+1] = data[2]

    #crc_results = crc8(cal_array)

    crc_results = Crc8.calc(cal_array)
    print ("Using new CRC package", hex(crc_results))
                
        
# Setup access to configuration memory area
# Need to perform special payttern of an I2C write and I2C read for CM access
# I2C Addr, CMD, byte address to read, 4C read command
# 0x20 CM area CMD register = 0x04 Register address space
def i2c_cm_register_access(cm_addr_):
    # first unlock CM area
    _unlock_1()
    register =int(cm_addr_,16)
    # write CM_CMD register --> command register 0x4C and register to read.
    board.i2c_write(sensor_i2c_addr, cm_cmd_reg, register, cm_read_cmd)  
    time.sleep(1)   
    # cmd read register location = 0x48
    board.i2c_read(sensor_i2c_addr, cm_rdata_reg, 2, board.I2C_READ)
    # need sleep for some reason on NVM read, maybe timing to memory
    time.sleep(1)
    data = board.i2c_get_read_data(sensor_i2c_addr)
    value0 = data[0]
    value1 = data[1]
    value2 = data[2]
    word = data[2] << 8 | data[1]
    print("Read Command Area --->" , hex(word))

"""
# Write to configuration area access
# I2C Addr, CMD, byte address to read, 4C read command
# 0x20 CM area CMD register = 0x04 Register address space
def i2c_write_register():
    # first unlock CM area
    _unlock()
    data = 0
    board.i2c_write(0x6c, 0x4e, 0x20, 0x4C)  
    time.sleep(1)   
    # cmd read register location = 0x48
    board.i2c_read(0x6C, 0x48, 2, board.I2C_READ)
    # need sleep for some reason on NVM read, maybe timing to memory
    time.sleep(1)
    data = board.i2c_get_read_data(0x6C)
    value0 = data[0]
    value1 = data[1]
    value2 = data[2]
    word = data[2] << 8 | data[1]
    print("Read Command Area --->" , hex(word))
"""

#Read Sensor hw version via I2C interface
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
        # print("Pressure Counts", pressure_counts)
        b = pressure_counts
        if  b >= 1 << 15:
            b -= 1 << 16
        # print("Pressure 2's Complement", (b))
        P_DOUT_max = 26214
        P_DOUT_min = -26214
        PMax = 1260 
        PMin = 460
        P0 = 760
        Delta_P_DOUT = 52428
        p_read = PMin + ((b - P_DOUT_min) / (Delta_P_DOUT )) *(PMax - PMin)
        # print("Pressure in mmHg            ", p_read)
        xdata.append(x)
        ydata.append(p_read)
        line.set_xdata(xdata)
        line.set_ydata(ydata)
        plt.draw()
        plt.pause(1e-17)
        # Tony
        time.sleep(.1)
        # p_delta += p_read
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
