#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GPL v.3 see master file

import serial
from plot import *

DEBUG = False

class Controller( Plot ) :
    """Create a plot for displaying the temperature measurements.

        It provide a method to read the temperature from the serial port
        on a LakeShore 331 temperature controller.

    """

    def __init__( self, serialPort = 0, serial = None, *args ) :
        """TemperaturePlot constructor it add axis titles."""

        Plot.__init__( self, *args )

        self.curve.setTitle( self._tr('Temperature data') )
        self.setAxisTitle( Qwt.QwtPlot.xBottom, self._tr('Time (min)') )
        self.setAxisTitle( Qwt.QwtPlot.yLeft, self._tr('Temperature (C)') )

        self.serial = serial
        self.serialPort = serialPort


    def timerEvent( self, e = None ) :
        """ This method is called after a startTimer occured
            it will read the temperature on the controller
            with a serial connection.
        """

        if not self.serial.isOpen() :
            return

        # Query message :
        #     CRDG = Celsius Reading Query
        #     A is the input can be A or B
        #     Terminators are <CR><LF>
        self.serial.write( "CRDG? A \r\n" )
        reply = self.serial.readline()

        self.x.append( time.time() )
        self.y.append( float(reply) )

        self.curve.setData( self.x, self.y )
        self.replot()


    def connect( self ) :
        """Connect and open the serial port."""

        if DEBUG:
            print "connecting"

        if not self.serial :
            self.serial = serial.Serial( self.serialPort, 9600, serial.SEVENBITS,
                serial.PARITY_ODD, serial.STOPBITS_ONE )

        if not self.serial.isOpen():
            self.serial.open()

        return self.serial


    def disconnect( self ) :
        """Safe way to close the serial port."""

        if not self.serial :
            return

        if self.serial.isOpen() :
            if DEBUG:
                print "disconnecting"
            self.serial.close()

