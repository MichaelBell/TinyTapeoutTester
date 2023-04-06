import time
import random

from machine import Pin
import hova_asm

#from tt_pio import TT_PIO
from tt_hova_fifo import TT_Hova
import tt_driver

seg_latch = Pin(7, Pin.OUT)
seg_latch.off()

chain_len = 34

def send_byte(d, read=False, latch=False, scan=False):
    return tt_driver.send_byte(d, latch=latch, scan=scan)
    
def send_bytes(d, read=False, latch=False, scan=False):
    return tt_driver.send_bytes(d, read=read, latch=latch, scan=scan)
    
def send_zeroes(num, read=False, latch=False, scan=False):
    return tt_driver.send_byte_repeat(0, num, read=read, latch=latch, scan=scan)
    
# Test invert
if True:
    for i in range(chain_len):
        send_byte(i)

    send_byte(0xAA)
    send_byte(0, latch=True)
    #send_byte(0, scan=True)
    #for i in range(chain_len-3):
    #    print("{:02x}".format(send_byte(0, read=True)))
    #    
    #print("{:02x}".format(send_byte(0, read=True)))
    print("{:02x} (expected 55)".format(send_zeroes(chain_len-1, read=True, scan=True)))

# Test Hovalaag
hova = TT_Hova(seg_latch)

#NOP
hova.execute_instr(0)
hova.execute_instr(0)
hova.execute_instr(0)

# Repeatedly add one to A
if False:
    for i in range(50):
        #                    ALU- A- B- C- D W- F- PC O I X K----- L-----
        hova.execute_instr(0b0101_01_11_00_0_01_00_00_1_0_0_000001_000000) # A=A+B,B=1,W=A+B,OUT1=W,JMP 0
        time.sleep(0.1)
    
# Example loop 1:
example_loop1 = [
    0b0000_11_00_00_0_00_00_00_0_0_0_000000_000000,  # A=IN1
    0b0000_00_10_00_0_00_00_00_0_0_0_000000_000000,  # B=A
    0b0101_01_01_00_0_00_00_00_0_0_0_000000_000000,  # A=B=A+B
    0b0101_01_01_00_0_00_00_00_0_0_0_000000_000000,  # A=B=A+B
    0b0101_00_00_00_0_01_00_00_0_0_0_000000_000000,  # W=A+B
    0b0000_00_00_00_0_00_00_00_1_0_0_000000_000000,  # OUT1=W
    0b0000_00_00_00_0_00_00_01_0_0_0_000000_000000,  # JMP 0
]

if True:
    print("Running example loop 1")
    NUM_VALUES = 14
    in1 = [random.randint(-2048 // 8,2047 // 8) for x in range(NUM_VALUES)]
    print(in1)
    correct = [8*x for x in in1]
    start = time.ticks_ms()
    result = hova.run_program(example_loop1, in1, NUM_VALUES)
    runtime = time.ticks_diff(time.ticks_ms(), start)
    for i in range(NUM_VALUES):
        if result[i] != correct[i]:
            print("Got {}, expected {}".format(result[i], correct[i]))
    print(result)
    print("Took {}ms".format(runtime))
    print()

# Loop via IN2
in2_test = [
#     ALU- A- B- C- D W- F- PC O I X K----- L-----
    0b0000_11_00_00_0_00_00_00_0_0_0_000000_000000,  # A=IN1
    0b0000_00_00_00_0_10_00_00_0_0_0_000000_000000,  # W=A
    0b0000_00_00_00_0_00_00_00_1_1_0_000000_000000,  # OUT2=W
    0b0000_00_00_00_0_00_00_00_0_0_0_000000_000000,  # NOP
    0b0000_11_00_00_0_00_00_00_0_1_0_000000_000000,  # A=IN2
    0b0000_00_00_00_0_10_00_00_0_0_0_000000_000000,  # W=A
    0b0000_00_00_00_0_00_00_01_1_0_0_000000_000000,  # OUT1=W, JMP 0
]

print("Running test of IN2")
NUM_VALUES = 14
in1 = [random.randint(0,2047) for x in range(NUM_VALUES)]
print(in1)
correct = [x for x in in1]
start = time.ticks_ms()
result = hova.run_program(in2_test, in1, NUM_VALUES)
runtime = time.ticks_diff(time.ticks_ms(), start)
for i in range(NUM_VALUES):
    if result[i] != correct[i]:
        print("Got {}, expected {}".format(result[i], correct[i]))
print(result)
print("Took {}ms".format(runtime))
print()

test_prog = """
; compute B earlier to get a 4-cycle loop

   A=IN1
   B=A
loop5:
   A=B=A+B
   A=B=A+B
   W=A+B,A=IN1
   OUT1=W,B=A,JMP loop5
"""
tprog = hova_asm.assemble(test_prog)

print("Running example loop 5")
NUM_VALUES = 14
in1 = [random.randint(-2048 // 8,2047 // 8) for x in range(NUM_VALUES)]
print(in1)
correct = [8*x for x in in1]
start = time.ticks_ms()
result = hova.run_program(tprog, in1, NUM_VALUES)
runtime = time.ticks_diff(time.ticks_ms(), start)
for i in range(NUM_VALUES):
    if result[i] != correct[i]:
        print("Got {}, expected {}".format(result[i], correct[i]))
print(result)
print("Took {}ms".format(runtime))
print()

aoc2020_1_1_asm = """
; Advent of Code Day 1.1
;
; IN1 is a sequence of positive numbers, two of which sum to 2020
; Output those two numbers to OUT1
; Any output to OUT2 is looped back to IN2

 A=IN1,B=2020
 B=B-A,A=IN1
 OUT2=W,F=ZERO(B-A),W=A
 A=IN1

; First loop reading values from IN1 and checking against very first input
firstloop:
 F=ZERO(-A),JMPT found
 F=ZERO(B-A),OUT2=W,W=A,JMPT firstnext
 A=IN1,JMP firstloop

; Initialize subsequent loop reading values from IN2
firstnext:
 A=IN2
 A=IN2
next:
 B=2020
 B=B-A,A=IN2,W=0
 OUT2=W,F=ZERO(B-A),W=A
 A=IN2,JMPT found
 F=ZERO(-A)

loop:
 F=ZERO(B-A),OUT2=W,W=A,A=IN2,JMPT next
 F=ZERO(-A),JMPT found
 JMP loop

found:
 OUT1=W,A=B,B=2020
 W=B-A
 OUT1=W"""

tprog = hova_asm.assemble(aoc2020_1_1_asm)

print("Running AOC 2020 1_1")
in1 = [
#        2000, 50, 1984, 1648, 32, 1612, 1992, 1671, 1955, 1658, 1592, 1596, 1888, 1540, 239, 1677, 1602, 1877, 1481, 2004, 1985, 1829, 1980, 1500, 1120, 1849, 1941, 1403, 1515, 1915, 1862, 2002, 1952, 1893, 1494, 1610, 1432, 1547, 1488, 1642, 1982, 1666, 1856, 1889, 1691, 1976, 1962, 2005, 1611, 1665, 1816, 1880, 1896, 1552, 1809, 1844, 1553, 1841, 1785, 1968, 1491, 1498, 1995, 1748, 1533, 1988, 2001, 1917, 0
        2000,   50, 1984, 1648,   32, 1612, 1992, 1671, 1955, 1658,
        1592, 1596, 1888, 1540,  239, 1677, 1602, 1877, 1481, 2004,
        1849, 1941, 1403, 1515, 1915, 1862, 2002, 1995, 1748, 1533,
        1988, 2001, 1917, 0
    ]

start = time.ticks_ms()
result = hova.run_program(tprog, in1, 2)
runtime = time.ticks_diff(time.ticks_ms(), start)
print(result)
print("Took {}ms".format(runtime))
print()
