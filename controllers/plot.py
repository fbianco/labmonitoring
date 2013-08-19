#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GPL v.3 see master file

import time
from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt

DEBUG = False

class TimeScaleDraw(Qwt.QwtScaleDraw):

    def __init__(self, *args):
        Qwt.QwtScaleDraw.__init__(self, *args)

    def label(self, v):
        return Qwt.QwtText( time.strftime('%H:%M %d/%m',time.localtime(v)) )


class Plot( Qwt.QwtPlot ) :
    """Define a refined QwtPlot class with a nicer design, aligned label,... """

    def __init__( self, *args ) :
        """ Plot constructor, change axis, init curve """
        Qwt.QwtPlot.__init__( self, *args )

        self.setCanvasBackground( Qt.Qt.white )
        self.setAxisScaleDraw(Qwt.QwtPlot.xBottom, TimeScaleDraw() )
        self.initGrid()
        self.alignScales()
        self.initZoom()

        self.timer = None

        self.picker = Qwt.QwtPlotPicker(
            Qwt.QwtPlot.xBottom,
            Qwt.QwtPlot.yLeft,
            Qwt.QwtPicker.PointSelection | Qwt.QwtPicker.DragSelection,
            Qwt.QwtPlotPicker.CrossRubberBand,
            Qwt.QwtPicker.AlwaysOn,
            self.canvas())
        self.picker.setTrackerPen(Qt.QPen(Qt.Qt.blue))

        self.curve = None
        self.initCurve()

        self.makeAction()
        self.setContextMenuPolicy( Qt.Qt.CustomContextMenu )
        Qt.QObject.connect( self, Qt.SIGNAL( "customContextMenuRequested ( QPoint )"), self.contextMenu )

    def _tr(self, s ) :
        """Provide a way to add translation of the message strings.
            Not used now. """
        return s

    def contextMenu( self, point ) :
        """Display a context menu on the graph to let the user change the scaling and zooming."""

        m = Qt.QMenu('Context')
        m.addAction( self.zoomAct )
        m.addAction( self.logScaleAct )
        m.addSeparator()
        m.addAction( self.printAct )
        m.addAction( self.exportPdfAct )
        m.addAction( self.exportSvgAct )

        m.exec_( self.mapToGlobal(point) )


    def makeAction( self ) :
        """Create all the actions used on the toolbars and menus """

        self.zoomAct = Qt.QAction( Qt.QIcon('img/zoom-original.svg'),
            self._tr('&Autoscale'), self )
        Qt.QObject.connect( self.zoomAct, Qt.SIGNAL( "triggered()" ),
            self.clearZoomStack )

        self.logScaleAct = Qt.QAction( Qt.QIcon('img/log-scale.svg'),
            self._tr('Show &logarithmic scale'), self )
        self.logScaleAct.setCheckable( True )
        Qt.QObject.connect( self.logScaleAct, Qt.SIGNAL( "triggered()" ),
            self.toggleLogScale )

        self.printAct = Qt.QAction( Qt.QIcon('img/print.svg'),
            self._tr('Print...'), self )
        Qt.QObject.connect( self.printAct, Qt.SIGNAL( "triggered()" ),
            self.printPlot )

        self.exportPdfAct = Qt.QAction( Qt.QIcon('img/export-pdf.svg'),
            self._tr('Export to pdf...'), self )
        Qt.QObject.connect( self.exportPdfAct, Qt.SIGNAL( "triggered()" ),
            self.exportPDF )

        self.exportSvgAct = Qt.QAction( Qt.QIcon('img/export-svg.svg'),
            self._tr('Export to svg...'), self )
        Qt.QObject.connect( self.exportSvgAct, Qt.SIGNAL( "triggered()" ),
            self.exportSVG )


    def initGrid( self ) :
        """Create a grid on the plot """

        self.grid = Qwt.QwtPlotGrid()
        self.grid.setMajPen(Qt.QPen(Qt.Qt.black, 0, Qt.Qt.DotLine))
        self.grid.setMinPen(Qt.QPen(Qt.Qt.gray, 0 , Qt.Qt.DotLine))
        self.grid.attach(self)


    def initZoom( self ) :
        """Add zooming capabilities on the QwtPlot """

        self.zoomer = Qwt.QwtPlotZoomer(
                Qwt.QwtPlot.xBottom,
                Qwt.QwtPlot.yLeft,
                Qwt.QwtPicker.DragSelection,
                Qwt.QwtPicker.AlwaysOff,
                self.canvas() )
        self.zoomer.setRubberBandPen( Qt.QPen(Qt.Qt.black) )

        # FIXME : deactivate unzoom on right click
        self.zoomer.setMousePattern( [Qwt.QwtEventPattern.MousePattern( Qt.Qt.MidButton, Qt.Qt.NoModifier),] )
        self.zoomer.initMousePattern(0)


    def clearZoomStack( self ) :
        """Reset the zoom and autoscale plot"""

        self.setAxisAutoScale(Qwt.QwtPlot.xBottom)
        self.setAxisAutoScale(Qwt.QwtPlot.yLeft)
        self.zoomer.setZoomBase()

        self.replot()

    def toggleLogScale( self ) :
        """Change the scale to base 10 or log scale."""

        if self.logScaleAct.isChecked() :
            self.setAxisScaleEngine( Qwt.QwtPlot.yLeft, Qwt.QwtLog10ScaleEngine() )
            self.replot()
        else :
            self.setAxisScaleEngine( Qwt.QwtPlot.yLeft, Qwt.QwtLinearScaleEngine() )
            self.replot()


    def initCurve( self ) :
        """(Re)initialize the curve on the plot """

        # (re)Initialize data
        self.x = []
        self.y = []

        if self.curve is not None :
            self.curve.detach()
            del self.curve

        self.curve = Qwt.QwtPlotCurve()
        self.curve.attach( self )

        self.curve.setSymbol( Qwt.QwtSymbol(
                        Qwt.QwtSymbol.Ellipse,
                        Qt.QBrush(),
                        Qt.QPen( Qt.Qt.green ),
                        Qt.QSize(7, 7) ) )

        self.curve.setPen( Qt.QPen( Qt.Qt.red ) )


    def initTimer( self, interval ) :
        """Start a timer and save a pointer on it """

        self.timer = self.startTimer( interval )
        self.timerEvent() # Read a first value at time t = 0
        self.zoomer.setZoomBase()


    def stopTimer( self ) :
        """Stop the timer if it's running"""

        if self.timer:
            self.killTimer( self.timer )


    def alignScales( self ) :
        """Change some style parameters of the axis."""

        self.canvas().setFrameStyle( Qt.QFrame.Box | Qt.QFrame.Plain )
        self.canvas().setLineWidth( 1 )
        for i in range( Qwt.QwtPlot.axisCnt ) :
            scaleWidget = self.axisWidget( i )
            if scaleWidget:
                scaleWidget.setMargin( 0 )
            scaleDraw = self.axisScaleDraw( i )
            if scaleDraw:
                scaleDraw.enableComponent(
                    Qwt.QwtAbstractScaleDraw.Backbone, False)


    def setInterval( self, interval ) :
        """Store the interval of the timer event """

        self.interval = interval


    def printPlot(self):
        """Print the current plot."""

        printer = Qt.QPrinter(Qt.QPrinter.HighResolution)

        printer.setOutputFileName('bakeout-%s.ps' % qVersion())

        printer.setCreator('Bakeout Controller')
        printer.setOrientation(Qt.QPrinter.Landscape)
        printer.setColorMode(Qt.QPrinter.Color)

        docName = self.plot.title().text()
        if not docName.isEmpty():
            docName.replace(Qt.QRegExp(Qt.QString.fromLatin1('\n')), self.tr(' -- '))
            printer.setDocName(docName)

        dialog = Qt.QPrintDialog(printer)
        if dialog.exec_():
            filter = PrintFilter()
        if (Qt.QPrinter.GrayScale == printer.colorMode()):
            filter.setOptions(
            Qwt.QwtPlotPrintFilter.PrintAll
            & ~Qwt.QwtPlotPrintFilter.PrintBackground
            | Qwt.QwtPlotPrintFilter.PrintFrameWithScales)

            self.plot.print_(printer, filter)


    def exportPDF(self):
        """Export the current plot as a PDF file."""

        fileName = Qt.QFileDialog.getSaveFileName(
            self,
            'Export File Name',
            'plot.pdf',
            'PDF Documents (*.pdf)')

        if not fileName.isEmpty():
            printer = Qt.QPrinter()
            printer.setOutputFormat(Qt.QPrinter.PdfFormat)
            printer.setOrientation(Qt.QPrinter.Landscape)
            printer.setOutputFileName(fileName)

            printer.setCreator('Temperature and pressure controller')
            self.print_(printer)


    def exportSVG(self):
        """Export the current plot to a SVG file."""

        fileName = Qt.QFileDialog.getSaveFileName(
            self,
            'Export File Name',
            'plot.svg',
            'SVG Documents (*.svg)')

        if not fileName.isEmpty():
            generator = Qt.QSvgGenerator()
            generator.setFileName(fileName)
            generator.setSize(QSize(800, 600))
            self.plot.print_(generator)
