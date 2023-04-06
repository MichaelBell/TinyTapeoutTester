import tt_driver

tt_driver.send_byte_repeat(42, 50)
for i in range(50):
    print(tt_driver.send_byte(i))
    
print(tt_driver.send_byte(0, latch=True))
print(tt_driver.send_byte(0, scan=True))
for i in range(10):
    print(tt_driver.send_byte(0))
