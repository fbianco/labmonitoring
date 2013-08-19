#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GPL v.3 see master file

import serial
import struct
from struct import unpack
from modbusCRC16 import modbusCRC16
from plot import *

DEBUG = False

class Controller( Plot ) :
    """Create a plot for displaying the pressure measurments.

        It provide a method to read the pressure from the serial port
        on a IGC3 pressure controller.
    """

    def __init__( self, deviceAddress, deviceName, serialPort = 0, serial = None, *args ) :
        """PressurePlot constructor it only add axis titles."""

        Plot.__init__( self, *args )

        self.curve.setTitle( self._tr('Pressure data') )
        self.setAxisTitle( Qwt.QwtPlot.xBottom, self._tr('Time (min)') )
        self.setAxisTitle( Qwt.QwtPlot.yLeft, self._tr('Pressure %s (mBar)') % deviceName )

        # Device address 0x01, 0x02, ... (hex)
        self.initMsg( deviceAddress )

        self.serial = serial
        self.serialPort = serialPort


    def initMsg( self, address ) :
        """Generate the message for the IGC3 according to modbus protocol."""

        # Query Message to IGC3 with MODBUS protocol
        #
        # Device address : 0x01, to 0x99
        # Function code for IGC3 : 0x17
        # Parameter to be read (in this case the pressure value ) : 0x00 0x9a
        # Number of word (=2 Bytes) to read : 0x00 0x02
        # Five words with only zeros to say that no parameters have to be written
        #
        # And then the two CRC bytes
        #
        self.queryMsg = address
        self.queryMsg += "\x17\x00\x9a\x00\x02\x00\x00\x00\x00\x00"
        queryMsgCRC = modbusCRC16( self.queryMsg )
        self.queryMsg += chr( queryMsgCRC % 0x0100 )    # append the lowest byte of the CRC to the msg
        self.queryMsg += chr( queryMsgCRC >> 8 )    # append the upper byte of the CRC to the msg


    def timerEvent( self, e = None ) :
        """This method is called after a startTimer occured
            it will read the pressure on the controller
            with a serial connection.
        """
        #return

        if not self.serial.isOpen() :
            return

        if 0 != self.serial.inWaiting() :
            time.sleep(1)

        self.serial.write( self.queryMsg )
        reply = self.serial.read(9)
        #print "Reply : " + reply

        # FIXME Ugly workaround for avoiding empty answer
        # FIXME should use CRC for message validation
        if len( reply ) == 0 :
            self.serial.write( self.queryMsg )
            reply = self.serial.read(9)
            #print "Reply : " + reply
            if len( reply ) == 0 :
                return

        #FIXME retry to read if exception occured
        try :
            pressure = unpack('f', reply[3:7] )[0] # Convert char 3 to 6 to a float (f)
        except struct.error :
            print "Reading error on the pressure controller."

        self.x.append( time.time() )
        self.y.append( pressure )

        self.curve.setData( self.x, self.y )
        self.zoomer.setZoomBase()
        self.replot()


    def initSerial( self ) :
        """Create the serial port object only if not already existing,
        i.e. it was already created by the previous pressure plot."""

        if not self.serial :
            self.serial = serial.Serial( self.serialPort, 19200, serial.EIGHTBITS,
                serial.PARITY_NONE, serial.STOPBITS_ONE, 1 )

        return self.serial


    def connect( self ) :
        """Connect and open the serial port."""

        if not self.serial.isOpen() :
            self.serial.open()


    def disconnect( self ) :
        """Safe way to close the serial port."""

        if not self.serial :
            return

        if self.serial.isOpen() :
            self.serial.close()
