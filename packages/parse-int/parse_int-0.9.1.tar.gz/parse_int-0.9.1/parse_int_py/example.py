#!/usr/bin/env python3

from parse_int_py import parse_int, parse_num, format_hex, format_dec

print(" === parsing === ")
print(parse_int("-0x42_00"))

print(parse_num("42"))
print(parse_num("-0x42_00.3"))
print(parse_num("-16896.3"))

print(" === formatting === ")
print(format_hex(10000))
print(format_dec(-10000))
print(format_dec(-10000.300001))
