import time
import tt_driver

design_num = 9
fifo_design_num = 28
chain_len = 34

class TT_Hova:
    def __init__(self, pin_seg_latch):
        self.seg_latch = pin_seg_latch
        self.reset()
    
    @micropython.native
    def clock_byte(self, d):
        tt_driver.send_bytes(((d & 0xFE), (d | 1)))
        
    @micropython.native
    def clock_hbyte(self, d, scan=False):
        tt_driver.send_bytes(((((d & 0x3F) << 2) | 2), (((d & 0x3F) << 2) | 3)), scan=scan)
        
    @micropython.native
    def send_instr(self, instr):
        tt_driver.send_byte_repeat(0, fifo_design_num - design_num)
        d = []
        for i in range(4):
            d.append(((instr & 0x3F) << 2) | 2)
            d.append(((instr & 0x3F) << 2) | 3)
            instr >>= 6
        d.append(((instr & 0x3F) << 2) | 2)
        tt_driver.send_bytes(d)
        d.clear()
        d.append(((instr & 0x3F) << 2) | 3)
        instr >>= 6
        d.append(((instr & 0x3F) << 2) | 2)
        d.append(((instr & 0x3F) << 2) | 3)
        d.extend((0,)*9)
        tt_driver.send_bytes(d, latch=True)

    def reset(self):    
        # Reset FIFO: 3 clocks of 8b0000_000C
        for i in range(3):
            self.clock_byte(0)
        tt_driver.send_byte_repeat(0, fifo_design_num - design_num - 6)

        # Reset Hovalaag: 3 clocks of 8b0000_010C
        for i in range(3):
            self.clock_byte(0b0000_0100)
        tt_driver.send_byte_repeat(0, design_num - 6)
        tt_driver.send_byte_repeat(0, 6, latch=True)

    def execute_instr(self, instr, in1=[], latch_seg=True):
        self.send_instr(instr)
        status = tt_driver.send_byte_repeat(0, chain_len - design_num, scan=True, read=True)

        if (status & 0x1) != 0 and len(in1) > 0:
            in1.pop(0)
        in2_pop = (status & 0x2) != 0
        
        in1_val = 0
        if len(in1) > 0: in1_val = in1[0]
        out = 0

        # Read in2 from FIFO and new PC, send in1
        if in2_pop:
            self.clock_byte(0b0010_1100)
        else:
            self.clock_byte(0b0000_0100)
        tt_driver.send_byte_repeat(0, fifo_design_num - design_num - 2)
        self.clock_hbyte(in1_val)
        tt_driver.send_byte_repeat(0, design_num - 2)
        tt_driver.send_byte_repeat(0, 2, latch=True)
        in2_low = tt_driver.send_byte_repeat(0, chain_len - fifo_design_num, scan=True, read=True) >> 2
        pc = tt_driver.send_byte_repeat(0, fifo_design_num - design_num, read=True)

        if in2_pop:
            self.clock_byte(0b0010_1100)
        else:
            self.clock_byte(0b0001_0100)
        if (status & 0x8) != 0:
            tt_driver.send_byte_repeat(0, fifo_design_num - 2)
            tt_driver.send_byte_repeat(0, 2, latch=True)
            in2_high = tt_driver.send_byte_repeat(0, chain_len - fifo_design_num, scan=True, read=True) >> 2
            tt_driver.send_byte_repeat(0, 2*fifo_design_num - design_num - chain_len)
        else:
            tt_driver.send_byte_repeat(0, fifo_design_num - design_num - 2)
            self.clock_hbyte(in1_val >> 6)
            tt_driver.send_byte_repeat(0, design_num - 2)
            tt_driver.send_byte_repeat(0, 2, latch=True)
            in2_high = tt_driver.send_byte_repeat(0, chain_len - fifo_design_num, scan=True, read=True) >> 2
            out = tt_driver.send_byte_repeat(0, fifo_design_num - design_num, read=((status & 0x4) != 0)) >> 2
        
        if (status & 0xC) == 0:
            # Complete hovalaag cycle
            self.clock_hbyte(in2_low)
            self.clock_hbyte(in2_high)
            tt_driver.send_byte_repeat(0, design_num - 4)
            tt_driver.send_byte_repeat(0, 4, latch=True)
        elif (status & 0x8) != 0:
            data_for_hova = ((in1_val >> 4) & 0xFC) | 2
            tt_driver.send_byte(data_for_hova)
            tt_driver.send_byte_repeat(0, design_num - 1)
            tt_driver.send_byte(0, latch=True)
            tt_driver.send_byte_repeat(data_for_hova, fifo_design_num - design_num - 1, scan=True)
            tt_driver.send_byte(0, latch=True)

            tt_driver.send_byte_repeat(0, fifo_design_num - design_num)
            data_for_hova = ((in1_val >> 4) & 0xFC) | 3
            tt_driver.send_byte(data_for_hova)
            tt_driver.send_byte_repeat(0, design_num - 1)
            tt_driver.send_byte(0, latch=True)
            tt_driver.send_byte_repeat(data_for_hova, fifo_design_num - design_num - 1, scan=True)
            tt_driver.send_byte(0, latch=True)
            
            tt_driver.send_byte_repeat(0, fifo_design_num - design_num)
            data_for_hova = (in2_low << 2) | 2
            tt_driver.send_byte(data_for_hova)
            tt_driver.send_byte_repeat(0, design_num - 1)
            tt_driver.send_byte(0, latch=True)
            tt_driver.send_byte_repeat(data_for_hova, fifo_design_num - design_num - 1, scan=True)
            tt_driver.send_byte(0, latch=True)

            tt_driver.send_byte_repeat(0, fifo_design_num - design_num)
            data_for_hova = (in2_low << 2) | 3
            tt_driver.send_byte(data_for_hova)
            tt_driver.send_byte_repeat(0, design_num - 1)
            tt_driver.send_byte(0, latch=True)
            tt_driver.send_byte_repeat(data_for_hova, fifo_design_num - design_num - 2, scan=True)
            tt_driver.send_byte(0)
            tt_driver.send_byte(0, latch=True)
            
            self.clock_hbyte(in2_high)
            tt_driver.send_byte_repeat(0, design_num - 2)
            tt_driver.send_byte_repeat(0, 2, latch=True)

        else:
            self.clock_hbyte(in2_low)
            tt_driver.send_byte_repeat(0, design_num - 2)
            tt_driver.send_byte_repeat(0, 2, latch=True)
            out = ((tt_driver.send_byte_repeat(0, chain_len - design_num, scan=True, read=True) & 0xFC) << 4) | out
            out = (out ^ 0x800) - 0x800 # Sign extend
            
            self.clock_hbyte(in2_high)
            tt_driver.send_byte_repeat(0, design_num - 2)
            tt_driver.send_byte_repeat(0, 2, latch=True)
            #print("OUT={}".format(out))
        #print("PC={:02x}".format(pc))
        
        if latch_seg:
            tt_driver.send_byte_repeat(0, chain_len - design_num, scan=True)
            self.seg_latch.on()
            time.sleep(0.00001)
            self.seg_latch.off()
            
        return (pc, status, out)

    def run_program(self, prog, in1, target_len):
        out1 = []
        in2 = []
        
        # JMP 0
        pc, status, out = self.execute_instr(0b0000_00_00_00_0_00_00_01_0_0_0_000000_000000, in1)
        
        count = 1
        while len(out1) < target_len:
            pc, status, out = self.execute_instr(prog[pc], in1, False)
            if (status & 0x4) != 0:
                out1.append(out)
            if (status & 0x8) != 0:
                in2.append(out)
            count += 1
        
        print("Executed {} instructions".format(count))
        return out1
