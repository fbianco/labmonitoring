#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GPL v.3 see master file

import serial
from plot import Plot

DEBUG = False

class Controller( Plot ) :
    """Create a plot for displaying the Liquid Helium Level measurements.

        It provide a method to read the temperature from the serial port
        on a Twickenham Scientific Instrument He Depth Indicator.

    """

    def __init__( self, serial = None, *args ) :
        """TemperaturePlot constructor it add axis titles."""

        Plot.__init__( self, *args )

        self.curve.setTitle( self._tr('LHe level data') )
        self.setAxisTitle( Qwt.QwtPlot.xBottom, self._tr('Time (min)') )
        self.setAxisTitle( Qwt.QwtPlot.yLeft, self._tr('LHe level (mm)') )

        self.serial = serial


    def timerEvent( self, e = None ) :
        """ This method is called after a startTimer occured
            it will read the temperature on the controller
            with a serial connection.
        """

        if not self.serial.isOpen() :
            return

        # Query message :
        #     T = Trigger a reading, no read back
        #     G return current reading : as abcdefg
        #       a = channel A, B
        #       fg = [mm]
        #       where cdef are the LHe Level
        #     Terminators are <CR><LF>
        self.serial.write( "T \r\n" )
        self.serial.write( "G \r\n" )
        reply = self.serial.readline()

        self.x.append( time.time() )
        self.y.append( float(reply[2:5]) )

        self.curve.setData( self.x, self.y )
        self.replot()


    def connect( self ) :
        """Connect and open the serial port."""

        if DEBUG:
            print "connecting"

        if not self.serial :
            self.serial = serial.Serial( serialPortTemp, 9600, serial.EIGHTBITS,
                serial.PARITY_NONE, serial.STOPBITS_ONE, xonxoff=True  )

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

