#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    \package This program read, display and store the bakeout temperature
        and pressure.


    \file bakeoutController.py
    \author François Bianco, UniGE - francois.bianco@unige.ch
    \date 2008.09.09


    \mainpage Bakeout Temperature Controller

    \section Copyright

    Copyright (C) 2008 François Bianco, UniGE - francois.bianco@unige.ch

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    \section Version
    2013.08 : v1.00
        fbianco - Cleaned the progamm structure to make it more flexible
                  Controllers are now separated from main source file and
                  stored as a module.
    2011.03 : v0.04
        fbianco - Added LHe Depth reader

    2009.03 : v0.03
        fbianco - Dual pressure plot

    2008.12.11 : v0.02
        fbianco - grid added, data picker added

    2008.09.09 : v0.01
        fbianco - first version

"""

import sys
import os
import time
from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt
import serial

from controllers import *

DEBUG = False

def _tr( s ) :
    """Provide a way to add translation of the message strings.
       Not used now. """
    return s

class BakeoutControllerWindow( Qt.QMainWindow ) :
    """ Implement a GUI window showing the temperature and pressure plots based on Qwt library
        with some toolbars and menus.
    """

    def __init__( self, *args ) :
        """Constructor, put the widgets together and launch method for creating menubars and toolbars """

        Qt.QMainWindow.__init__( self, *args )

        # FIXME add a GUI way to change the available controllers.
        #
        # For now, you simply have to edit the list below to add, remove or change controllers
        # In case the same serial port is used (daisy chaining like on the IGC3, refer to the right
        # serial port from the other controller with something like as 3rd argument:
        #
        #       self.plots[_tr('Pressure LT')] = IGC3( '\x01', 'LT' )
        #       self.plots[_tr('Pressure Prep')] = IGC3( '\x02', 'Prep', self.plots[_tr('Pressure LT')].initSerial() )
        #
        # On Windows it seems that the port 0 is unused, or it might depends on our own configuration.
        #
        self.plots = {}

        # Do a basic kind of switch for the possible configuration in our lab
        which = 'LT-STM'
        
        # NOTE This is a special case for our Omicron STM lab, as exemple
        if 'LT-STM' == which:
            self.plots[_tr('Temperature')] = Lakeshore331.Controller( serialPort = 'COM15')
            self.plots[_tr('Pressure LT')] = IGC3.Controller( '\x01', 'LT', serialPort = 'COM14')
            self.plots[_tr('Pressure Prep')] = IGC3.Controller( '\x02', 'Prep', self.plots[_tr('Pressure LT')].initSerial() )

        # NOTE This is a special case for our JT-STM lab, as exemple
        elif 'JT-STM' == which:
            self.plots[_tr('Pressure JT')] = MVC3.Controller( 'JT', serialPort = 1 )
            self.plots[_tr('Pressure JT')].initSerial()

        # NOTE This is an example to use this program with a LHe meter, as exemple
        elif 'LHeMeter' == which:
            self.plots[_tr('Liquid Helium Depth')] = HeLevelPlot.Controller( serialPort = 1)

        else:
            print 'Woups... no plots defined or wrong name selected ? are you sure.'
            return

        # Store if we need to clean the plot on next run
        self.clearPlots = False
        self.autoSaveTimer = None

        widget = Qt.QWidget( self )
        layout = Qt.QVBoxLayout()

        for p in self.plots.values() :
            layout.addWidget( p )

        widget.setLayout( layout )
        self.setCentralWidget( widget )

        self.makeConfigWidget()
        self.makeAction()
        self.makeMenuBars()
        self.makeToolBars()

        self.setWindowTitle( _tr('Lab monitoring[*]') )
        self.setWindowIcon( Qt.QIcon("img/app.svg") )
        self.statusBar().showMessage( _tr('Ready') )

        self.resize(600, 500)


    def makeConfigWidget( self ) :
        """Create the configuration dock with all the options for the controllers and autosave """

        self.configDock = Qt.QDockWidget()
        self.addDockWidget( Qt.Qt.LeftDockWidgetArea, self.configDock )
        configWidget = Qt.QWidget()
        configLayout = Qt.QFormLayout()

        self.intervalSpinBox = Qt.QDoubleSpinBox()
        Qt.QObject.connect( self.intervalSpinBox, Qt.SIGNAL( "valueChanged(double)" ), self.setInterval )
        self.intervalSpinBox.setSuffix( _tr(' min') )
        self.intervalSpinBox.setDecimals( 1 )
        self.intervalSpinBox.setValue( 1 )
        configLayout.addRow( _tr('&Readout interval'), self.intervalSpinBox )

        self.autoSaveCheckBox = Qt.QCheckBox()
        self.autoSaveCheckBox.setCheckState(Qt.Qt.Checked)
        configLayout.addRow( _tr('&Autosave enabled'), self.autoSaveCheckBox )

        self.autoSaveSpinBox = Qt.QDoubleSpinBox()
        self.autoSaveSpinBox.setSuffix( _tr(' min') )
        self.autoSaveSpinBox.setDecimals( 1 )
        self.autoSaveSpinBox.setValue( 5 )
        configLayout.addRow( _tr('&Autosave interval'), self.autoSaveSpinBox )

        self.autoSaveDirEdit = Qt.QLineEdit( Qt.QDir.home().path() )
        configLayout.addRow( _tr('Autosave &directory'), self.autoSaveDirEdit )

        configWidget.setLayout( configLayout )
        self.configDock.setWidget( configWidget )
        self.configDock.setVisible( False )


    def makeAction( self ) :
        """Create all the actions used on the toolbars and menus """

        self.openAct = Qt.QAction( Qt.QIcon('img/open.svg'),
            _tr('&Open...'), self )
        self.openAct.setShortcut( _tr('Ctrl+o') )
        Qt.QObject.connect( self.openAct, Qt.SIGNAL( "triggered()" ),
            self.openFile )


        self.saveAsAct = Qt.QAction( Qt.QIcon('img/saveas.svg'),
            _tr('&Save as...'), self )
        self.saveAsAct.setShortcut( _tr('Ctrl+S') )
        Qt.QObject.connect( self.saveAsAct, Qt.SIGNAL( "triggered()" ),
            self.saveAs )


        self.quitAct = Qt.QAction( Qt.QIcon('img/quit.svg'),
            _tr('&Quit'), self )
        self.quitAct.setShortcut( _tr('Ctrl+Q') )
        Qt.QObject.connect( self.quitAct, Qt.SIGNAL( "triggered()" ),
            self, Qt.SLOT( "close()" ) )


        self.startAct = Qt.QAction( Qt.QIcon('img/start.svg'),
            _tr('Start'), self )
        Qt.QObject.connect( self.startAct, Qt.SIGNAL( "triggered()" ),
            self.startMeasurement )
        self.startAct.setCheckable( True )


        self.clearAct = Qt.QAction( Qt.QIcon('img/stop.svg'),
            _tr('Stop'), self )
        Qt.QObject.connect( self.clearAct, Qt.SIGNAL( "triggered()" ),
            self.clearMeasurement )


        self.pauseAct = Qt.QAction( Qt.QIcon('img/pause.svg'),
            _tr('Pause'), self )
        Qt.QObject.connect( self.pauseAct, Qt.SIGNAL( "triggered()" ),
            self.pauseMeasurement )
        self.pauseAct.setCheckable( True )


        self.configureAct = self.configDock.toggleViewAction()
        self.configureAct.setIcon( Qt.QIcon('img/config.svg') )
        self.configureAct.setText( _tr('Show options') )


    def makeToolBars( self ) :
        """Create the toolbars """

        self.fileToolBar = Qt.QToolBar( _tr( "File" ) )
        self.fileToolBar.setObjectName( "FileToolBar" )
        self.fileToolBar.addAction( self.openAct )
        self.fileToolBar.addAction( self.saveAsAct )

        self.addToolBar( Qt.Qt.TopToolBarArea, self.fileToolBar )

        self.measurementToolBar = Qt.QToolBar( _tr( "Measurement" ) )
        self.measurementToolBar.setObjectName( "MeasurementToolBar" )
        self.measurementToolBar.addAction( self.startAct )
        self.measurementToolBar.addAction( self.pauseAct )
        self.measurementToolBar.addSeparator()
        self.measurementToolBar.addAction( self.clearAct )

        self.addToolBar( Qt.Qt.TopToolBarArea, self.measurementToolBar )


        self.configToolBar = Qt.QToolBar( _tr( "Configuration") )
        self.configToolBar.setObjectName( "ConfigToolBar" )
        self.configToolBar.addAction( self.configureAct )

        self.addToolBar( Qt.Qt.TopToolBarArea, self.configToolBar )


    def makeMenuBars( self ) :
        """Create the windows menus """

        self.fileMenu = self.menuBar().addMenu( _tr( "&File" ) )
        self.fileMenu.addAction( self.openAct )
        self.fileMenu.addAction( self.saveAsAct )
        self.fileMenu.addSeparator()
        self.fileMenu.addAction( self.quitAct )

        self.measurementMenu = self.menuBar().addMenu( _tr('&Measurements') )
        self.measurementMenu.addAction( self.startAct )
        self.measurementMenu.addAction( self.pauseAct )
        self.measurementMenu.addSeparator()
        self.measurementMenu.addAction( self.clearAct )

        self.configMenu = self.menuBar().addMenu( _tr('&Configuration') )
        self.configMenu.addAction( self.configureAct )

    def openFile( self ) :

        filename = Qt.QFileDialog.getSaveFileName( self, _tr('Open file'), Qt.QDir.home().path() )

        if filename == '' :
            return

        f = open( filename, 'r')
        lines = f.readlines()

        if "Time\tTemperature\tPressure" == lines[0] :
            # old style file
            pass

        #elif Time

    def saveAs( self ) :
        """Ask where to save and then call self.save() """

        filename = Qt.QFileDialog.getSaveFileName( self, _tr('Open file'), Qt.QDir.home().path() )

        if filename == '' :
            return

        self.save( filename )


    def save( self, filename ) :
        """Save the measured value in .csv format """

        f = open( filename, 'w')

        for name,plot in self.plots.items() :
            # ';'.join(map(str,list)) --> Functionnal way to convert all integer
            # item in list to string and join them with a comma.
            f.write( name + ' Time' + ';' )
            f.write( ';'.join(map(str,self.plots.values()[0].x)) + '\n' )
            f.write( name + ';' )
            f.write( ';'.join(map(str,plot.y))  + '\n' )

        f.close()

        self.setWindowModified( False )


    def startMeasurement( self ) :
        """Start the timer on the plots """

        if not self.startAct.isChecked() :
            # if the user try to unset action wile running
            self.startAct.setChecked( True )

        else :
            # Do not allow to change settings while running
            self.configDock.setEnabled( False )
            self.pauseAct.setChecked( False )

            if self.clearPlots :
                if ( self.isWindowModified() ) :
                    r = Qt.QMessageBox.warning( self, _tr('Save current plots ?'), _tr( "The current plots were not saved." ), Qt.QMessageBox.Save | Qt.QMessageBox.Discard | Qt.QMessageBox.Cancel, Qt.QMessageBox.Save )

                    if r == Qt.QMessageBox.Save :
                        self.saveAs()
                    elif r == Qt.QMessageBox.Cancel :
                        return

                for p in self.plots.values() :
                    p.initCurve()

                self.clearPlots = False

            try :

                for p in self.plots.values() :
                    p.connect()

            except serial.serialutil.SerialException :

                Qt.QMessageBox.critical( self, _tr( "Critical error" ), _tr( "Serial connection error :\n\n%s" ) % sys.exc_info()[1] , Qt.QMessageBox.Ok )

                for p in self.plots.values() :
                    p.disconnect()

                self.startAct.setChecked( False )
                self.configDock.setEnabled( True )

            else :

                #  * 60000 to convert interval from [min] to [ms]
                if self.autoSaveCheckBox.isChecked() :
                    self.filename = 'bakeout_' + time.strftime('%Y-%m-%d-%H-%M',time.localtime()) + '.csv'
                    self.autoSaveTimer = self.startTimer(
                        self.autoSaveSpinBox.value() * 60000 )

                interval = self.intervalSpinBox.value()

                for p in self.plots.values() :
                    p.initTimer( interval * 60000 )

                self.statusBar().showMessage( _tr('Measuring') )
                self.setWindowModified( True )


    def clearMeasurement( self ) :
        """Set the clear plot to true for next run and kill the timer on the plots """

        self.configDock.setEnabled( True )

        self.clearPlots = True
        self.statusBar().showMessage( _tr('Stopped') )

        self.startAct.setChecked( False )
        self.pauseAct.setChecked( False )

        for p in self.plots.values() :
            p.stopTimer()
            p.disconnect()


    def pauseMeasurement( self ) :
        """Stop the measurement, which can be restarted by calling startMeasurement again """

        if not self.pauseAct.isChecked() :
            # if the user try to unset action while in pause
            self.pauseAct.setChecked( True )

        elif self.startAct.isChecked() :

            self.startAct.setChecked( False )
            self.configDock.setEnabled( True )

            for p in self.plots.values() :
                p.stopTimer()
                p.disconnect()

            self.statusBar().showMessage( _tr('Paused') )

        else :

            self.pauseAct.setChecked( False )


    def setInterval( self ) :
        """Inform the plots of the new interval """

        for p in self.plots.values() :
            p.setInterval( self.intervalSpinBox.value() )


    def timerEvent( self, e ) :
        """This method is called after a startTimer occured it will save
        the measured value at regular interval.
        """

        filepath = os.path.join( str(self.autoSaveDirEdit.text()), self.filename)

        self.save( filepath )
        self.setWindowModified( True )


#Only start an application if we are __main__
if __name__ == '__main__':

    app = Qt.QApplication( sys.argv )
    Qt.QObject.connect( app, Qt.SIGNAL("lastWindowClosed()"), app, Qt.SLOT("quit()") )
    mainWindow = BakeoutControllerWindow()
    mainWindow.show()
    sys.exit( app.exec_() )
