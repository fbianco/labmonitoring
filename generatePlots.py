#!/usr/bin/env python
# -*- coding: utf-8 -*-

#!/usr/bin/env python

"""

    \mainpage


    \section Infos

     Written by François Bianco, University of Geneva - francois.bianco@unige.ch

     Automatic plots generation for bakeout files.

    \section Copyright

    Copyright (C) 2011 François Bianco, University of Geneva - francois.bianco@unige.ch

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


    \section Updates

    2011-06-27 fbianco :
        first version, really rough to produce graphs of data

"""

import os
import re
import time
from optparse import OptionParser
from pylab import *
from matplotlib.ticker import Formatter

font = {'size'   : 10}
matplotlib.rc('font', **font)  # pass in the font dict as kwargs


def cleanReadingError(x):
    if 1e-15 < x < 1e-1:
        return x
    else:
        return None


class DateFormatter(Formatter):
    def __init__(self, dates, dateFormat='%Y-%m-%d'):
        self.dates = dates
        self.dateFormat = dateFormat

    def __call__(self, x, pos=0):
        """Return the label for time x at position pos"""
        ind = int(round(x))
        if ind>=len(self.dates) or ind<0: return ''

        return time.strftime(self.dateFormat,
                            time.localtime(float(self.dates[ind])))


def generatePlot(filename, quiet=True):
    if not quiet : print '--> Processing file ' + filename,

    f = open( filename, 'r')
    lines = f.readlines()
    header = lines[0]

    data = {}
    timeaxis = []
    timeInTimestamp = False # i.e time in seconds

    # Old file types
    if re.match("^Time\tTemperature\tPressure",header):
    ## Old file types with 2 pressures, inclueded in same reading pattern
    #if re.match("^Time\tTemperature\tPressure (LT|Prep)",header):
        labels = header.rstrip().split('\t')
        for label in labels:
            data[label] = []

        for line in lines[1:] :
            x = line.rstrip().split()
            for i,label in enumerate(labels):
                data[label].append(x[i])

    # New file types, faster to read
    elif re.match("^Time;",header) :
        timeInTimestamp = True
        for line in lines:
            content = line.rstrip().split(';')
            label = content[0]
            data[label] = content[1:]

    else:
        f.close()
        if not quiet : print ' unknown format, dropped'
        return

    timeaxis = data.pop('Time')
    figure, axarr = subplots(len(data), sharex=True)

    if timeInTimestamp:
        dates = timeaxis
        timeaxis = range(len(timeaxis))
        formatter = DateFormatter(dates, dateFormat='%d %H:%M')
        year = time.strftime('%Y/%m/',
                time.localtime(float(dates[0])))

    for i,label in enumerate(data):
        if len(data) == 1 :
            p = axarr
        else:
            p = axarr[i]
        y = map(float, data[label])
        if label == "Temperature":
            p.set_ylabel(r"Temperature [$^o$C]")
        elif re.match("^Pressure",label):
            y = map(cleanReadingError, y)
            p.set_yscale('log')
            p.set_ylabel(label + " [mbar]")

        p.plot(timeaxis[:min(len(y),len(timeaxis))],
               y[:min(len(y),len(timeaxis))],'g-',linewidth=2)
        p.grid('on')

    if timeInTimestamp:
        p.xaxis.set_major_formatter(formatter)
        figure.autofmt_xdate()
        p.set_xlabel("%s" % year)
    else:
        p.set_xlabel("Time [min]")

    savefig(filename+".png")
    f.close()

    if not quiet : print ' finished'
    return timeaxis,data

def main() :
    """Allow to use this script as a *nix command line program."""

    parser = OptionParser(usage="usage: %prog [options] [filename(s)]")
    parser.add_option("-q", "--quiet", action="store_true", default=False, dest="quiet", help="Be quiet")
    (options, args) = parser.parse_args()

    if not args :
        parser.error("No file specified")

    fileslist = args

    for filename in fileslist :
        generatePlot(filename, quiet = options.quiet)

if __name__ == "__main__":
    try :
        main()
    except (KeyboardInterrupt) :
        print "Goodbye world !"
