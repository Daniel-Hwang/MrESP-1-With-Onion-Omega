#!/usr/bin/python
# coding=utf-8

# modified by Daniel Hwang at 2017.8.24

import sys,threading,time; 
import serial; 
#import binascii,encodings; 
import json

#import binascii
import urllib2

import math

#Omega 2 relayExp
from OmegaExpansion import relayExp
# check initialization
#	should return 0 if the Expansion has just been plugged in
addr = 7
ret 	= relayExp.checkInit(addr)
print "checking if initialized: ", ret
# initialize the relay-exp
ret 	= relayExp.driverInit(addr)
print "Result from relayDriverInit: ", ret
if (ret != 0):
	exit()
# check initialization
#	should return 1 since the Expansion was initialized above
ret 	= relayExp.checkInit(addr)
print "checking if initialized: ", ret
time.sleep(1)
print "Init Done"

class ReadThread: 
    def __init__(self, Output="", Port="/dev/tty", Log="", Baudrate=9600, Com_timeout = 0.1, Dispstate = 0): 
        self.l_serial = None;   # used for serial
        self.alive = False;     # used for whether the com is open
        self.waitEnd = None;    # waitEnd = threading.Event();
        self.sendport = '';     # used for read config file
        self.log = Log;         # used for save Log, for logfile
        self.output = Output;   # used for save output, for print
        self.com_switch = "OFF";       # used for Com Port switch
        self.port = Port;       # used for Com Port
        self.baudrate = Baudrate;          # used for Com Baudrate
        self.com_timeout = Com_timeout;    # used for Com timeout
        self.connection_falg = False;      # used for child thread
        self.com_continurous_falg = False;      # used for child thread
        self.connect_senddata =b'';
        self.connect_receive_len = 40;
        self.connect_confirmdata =b'';
        self.continue_senddata =b'';
        self.continue_receive_len = 40;
        self.continue_confirmdata =b'';
        self.stop_senddata =b''; 

    def start(self): 
        self.l_serial = serial.Serial(self.port,self.baudrate,timeout=self.com_timeout);  

        try: 
            if not self.output is None: 
                self.output+=u'Open Com Port\r\n'; 
            if not self.log is None: 
                self.log+=u'Open Com Port';
            self.l_serial.close(); 
            self.l_serial.open(); 
        except Exception as ex: 
            if not self.output is None: 
                self.output+=u'oops!!!ERROR!!!\r\n   %s\r\n' % ex; 
            if not self.log is None: 
                self.log+=u'%s' % ex; 
            return False; 

        if self.l_serial.isOpen():             
            # use multi threading
            self.waitEnd = threading.Event(); 
            self.alive = True; 
            self.thread_read = None; 
            # inheritant threading, the ReaderLoop() work in the thread. 
            self.thread_read = threading.Thread(target=self.ReaderLoop); 
            # This must be set before start() is called, otherwise RuntimeError is raised
            self.thread_read.daemon=True; 
            # Start the thread's activity.
            self.thread_read.start();             
            return True; 
        else: 
            if not self.output is None: 
                self.output+=u'Com port not open\r\n'; 
            if not self.log is None: 
                self.log+=u'Com port not open'; 
            return False; 

    def InitHead(self): 
        global Mainboard

        if Mainboard == "EEG-MrESP1":
            self.connect_receive_len = 100;
            self.continue_receive_len =43;


    def EEG_MrESP1_ACQ(self):    
        STATE_IDLE=0
        STATE_FIRST=1
        STATE_SECOND=2
        STATE_LEN=3
        STATE_DATA=4
        state=0
        print("EEG_MrESP1_ACQ")

        dispstate=0
        dataindex=0
        
        # code:time
        x = time.localtime();
        flocaltime = time.strftime('BLueBCI_MrESP1_BP_%Y-%m-%d_%H-%M-%S',x)
        print(flocaltime)
        f = open("/root/DATA/"+flocaltime+".hs2f", "wb")
        f.write("####### EEG_BlueBCI_MrESPV1 \r\n");
        f.write("####### Made By Daniel Hwang \r\n");
        f.close();
        f = open("/root/DATA/"+flocaltime+".hs2f", "a")
        
        #self.l_serial.write(self.connect_senddata)
        receive_stack = []
        while True:
            
            # use file to COM_OBplot, (fake data)
            while True:
                ans = self.l_serial.read(self.connect_receive_len)
                receive_stack+=ans
                #print(len(ans))
                while(ans):
                    
                    ans=self.l_serial.read(self.continue_receive_len)
                    #print(ans.encode('hex'))  

                    receive_stack+=ans
                    while len(receive_stack)!=0:
                        tmp=receive_stack[0]
                        receive_stack=receive_stack[1:];
                        #print (hex(ord(tmp)))
                        if state==STATE_IDLE:
                            if ord(tmp)==170:   #0xAA
                                state=STATE_FIRST
                                #print "first"
                        elif state==STATE_FIRST:
                            if ord(tmp)==170:   #0xAA
                                state=STATE_SECOND
                                lencnt=0
                                lenstr=""
                                #print "second"
                        elif state==STATE_SECOND: #record 4 indax
                            if ord(tmp)==32:   #0x20
                                state=STATE_SECOND
                                lencnt=0
                                lenstr=""
                                #print "second"
                                state=STATE_LEN
                                datapt=0
                                datastr=""
                                
                        elif state==STATE_LEN:
                            if len(datastr)<32:  #
                                datastr+=tmp
                                datapt+=1
                                if len(datastr)==30:  #the 29 for the focus value
                                    #since the datastr++, the 30 for that
                                    if ord(datastr[28])==4:   #0x04   the Attention protocal
                                        print (hex(ord(datastr[28])))
                                        print (ord(datastr[29]))   
                                        if ord(datastr[29])<50 :
                                            # set channel 1 to off
                                            ret 	= relayExp.setChannel(addr, 1, 0)
                                            print "Result from relaySetChannel: ", ret
                                            if (ret != 0):
                                            	exit()
                                        else:
                                            # set channel 1 to on
                                            ret 	= relayExp.setChannel(addr, 1, 1)
                                            print "Result from relaySetChannel: ", ret
                                            if (ret != 0):
                                            	exit()
                                                
                                    else:
                                        state=STATE_IDLE;
                                elif len(datastr)==32:
                                    dataindex+=1
                                    print(datastr.encode('hex')) 
                                    if ord(datastr[30])==5:  #the 30 is fixed 5
                                        print (hex(ord(datastr[30])))
                                        print (ord(datastr[31]))
                                        self.s2f_switch = 1;
                                        if self.s2f_switch == 1: 
                                            global s2f_buffer
                                            s2f_buffer.append(str(dataindex));
                                            s2f_buffer.append(', ')
                                            s2f_buffer.append(str(datastr.encode('hex')))
                                            s2f_buffer.append('\r')
                                            print (len(s2f_buffer));
                                            if len(s2f_buffer) >= 20:    #4*5    #record every 5s data
                                                #print(len(s2f_buffer))
                                                #f = open("/root/DATA/"+flocaltime+".hs2f", "a")
                                                for i in range(len(s2f_buffer)):
                                                    f.write(str(s2f_buffer[i]));
                                                #f.close();
                                                s2f_buffer = [];       #20171120 why need???
                                                #datastr="";
                                                print("s2f successful!!! \r\n")
                                    else:
                                        state=STATE_IDLE;
                            elif len(datastr)>=32:
                                #print (datastr.encode('hex'))
                                state=STATE_IDLE;    
                                                                
    # Com port Threading method
    def ReaderLoop(self): 
        #read Head Infor content 
        self.InitHead();

        if Mainboard == "EEG-MrESP1":
            self.EEG_MrESP1_ACQ();
                        

#test part

if __name__ == '__main__':
    # load class
    rt = ReadThread(); 

    # load config file from local
    f = open("/root/config/4MrESP1_Omega.cfg", "r") 
    fread=f.read();
    f.close() 
    json_data = json.loads(fread);
    # get info to COMPORT
    rt.port = json_data['COM'][0]['PORT'];       # used for Com Port
    rt.baudrate = json_data['COM'][0]['BAUDRATE'];          # used for Com Baudrate
    rt.com_timeout = json_data['COM'][0]['TIMEOUT'];    # used for Com timeout
    print(rt.port,rt.baudrate,rt.com_timeout)

    # get info to MAINBOARD-PROTOCOL
    global Mainboard 
    global Version
    global Type
    Mainboard = json_data['MAINBOARD'][0]['PROTOCOL'];  # used for MAINBOARD-PROTOCOL
    Version = json_data['MAINBOARD'][0]['VERSION'];       # used for MAINBOARD-VERSION
    Type = json_data['MAINBOARD'][0]['TYPE'];          # used for MAINBOARD-TYPE
    print(Mainboard,Version,Type)

    global s2f_buffer
    s2f_buffer = [] 
    global Save2file_dataindex
    Save2file_dataindex = 0    
    
    try: 
        if rt.start() : 
            while 1: 



                time.sleep(2)
                
                '''
                there are a lot of things to do in the mother thread!
                TO DO 1: serial COM device abnormal taking out error, no way to write
                '''
            
        else: 
            pass;             
    except Exception as se: 
        print(str(se)); 

    # exit handle!
    if rt.alive: 
        rt.alive = False;
        print("rt.alive!rt.stop!Finish\r\n") 
    print(rt.output);
    print('End OK .'); 
    del rt; 