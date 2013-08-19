#!/usr/bin/env python
# -*- coding: utf-8 -*-

def modbusCRC16( st ) :
	crc = 0xFFFF
	for ch in st :
		crc ^= ord( ch ) # convert char to int
		for i in range( 8 ) :
			carry = crc & 0x0001
			crc >>= 1
			if ( carry ) :
				crc ^= 0xA001
	return crc