#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GPL v.3 see master file

import serial
from plot import *

DEBUG = False

class Controller( Plot ) :
    """Create a plot for displaying the pressure measurments.

        It provide a method to read the pressure from the serial port
        on a MVC-3 pressure controller.
    """

    def __init__( self, deviceName, deviceAddress = None, deviceChannel = 1, serialPort = 0, serial = None, *args ) :
        """PressurePlot constructor it only add axis titles."""

        Plot.__init__( self, *args )

        self.curve.setTitle( self._tr('Pressure data') )
        self.setAxisTitle( Qwt.QwtPlot.xBottom, self._tr('Time (min)') )
        self.setAxisTitle( Qwt.QwtPlot.yLeft, self._tr('Pressure %s (mBar)') % deviceName )

        self.serial = serial
        self.serialPort = serialPort

        """
        MVC-3 Manual p. 51
        Address <,> Command <CR>
        Address <,> <TAB>   Command <,> <TAB>   [Parameter] <CR>

        RPV[a]<CR>
        b[,][TAB]x.xxxxE±xx
        """

        self.queryMsg = ''
        # Device adress only needed for RS485
        if (not deviceAddress == None):
            self.queryMsg += deviceAddress + ','

        self.queryMsg += "RPV"
        self.queryMsg += str(deviceChannel) # [a] = 1,2,3 for channel number
        self.queryMsg += '\r'


    def timerEvent( self, e = None ) :
        """ This method is called after a startTimer occured
            it will read the temperature on the controller
            with a serial connection.
        """

        if not self.serial.isOpen() :
            return

        self.serial.write(self.queryMsg)
        reply = self.serial.readline()

        # Check status
        #0   =   Measuring   value   OK
        #1   =   Measuring   value   <   Measuring   range
        #2   =   Measuring   value   >   Measuring   range
        #3   =   Measuring   range   undershooting   (Err    Lo)
        #4   =   Measuring   range   overstepping    (Err    Hi)
        #5   =   Sensor  off (oFF)
        #6   =   HV  on  (HU on)
        #7   =   Sensor  error   (Err    S)
        #8   =   BA  error   (Err    bA)
        #9   =   No  Sensor  (no Sen)
        #10  =   No  switch  on  or  switch  off point   (notriG)
        #11  =   Pressure    value   overstepping    (   Err P)
        #12  =   Pirani  error   ATMION  (Err    Pi)
        #13  =   Breakdown   of  operational voltage (Err    24)
        #14  =   Filament    defectively (FiLbr)

        reply = split(',')
        status = int(reply[0])

        if (status == 0):
            self.x.append( time.time() )
            self.y.append( float(reply[1]) )

            self.curve.setData( self.x, self.y )
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
