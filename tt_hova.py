import time

design_num = 9
chain_len = 34

class TT_Hova:
    def __init__(self, tt_pio, pin_seg_latch):
        self.tt = tt_pio
        self.seg_latch = pin_seg_latch
        self.reset()
    
    @micropython.native
    def clock_byte(self, d):
        self.tt.send_bytes_blocking(((d & 0xFE), (d | 1)))
        
    @micropython.native
    def clock_hbyte(self, d, scan=False):
        self.tt.send_bytes_blocking(((((d & 0x3F) << 2) | 2), (((d & 0x3F) << 2) | 3)), scan=scan)
        
    @micropython.native
    def send_instr(self, instr):
        d = []
        for i in range(4):
            d.append(((instr & 0x3F) << 2) | 2)
            d.append(((instr & 0x3F) << 2) | 3)
            instr >>= 6
        d.append(((instr & 0x3F) << 2) | 2)
        self.tt.send_bytes_blocking(d)
        d.clear()
        d.append(((instr & 0x3F) << 2) | 3)
        instr >>= 6
        d.append(((instr & 0x3F) << 2) | 2)
        d.append(((instr & 0x3F) << 2) | 3)
        d.extend((0,)*9)
        self.tt.send_bytes_blocking(d, latch=True)

    def reset(self):    
        # Reset: 3 clocks of 8b0000_010C
        for i in range(3):
            self.clock_byte(0b0000_0100)
        self.tt.send_zeroes_blocking(design_num - 6)
        self.tt.send_zeroes_blocking(6, latch=True)

    @micropython.native
    def execute_instr(self, instr, in1=[], in2=[], latch_seg=True):
        self.send_instr(instr)
        status = self.tt.send_zeroes_blocking(chain_len - design_num, scan=True)

        if (status & 0x1) != 0 and len(in1) > 0:
            in1.pop(0)
        if (status & 0x2) != 0 and len(in2) > 0:
            in2.pop(0)
            
        in1_val = 0
        in2_val = 0
        if len(in1) > 0: in1_val = in1[0]
        if len(in2) > 0: in2_val = in2[0]    
        out = 0

        # Read new PC
        self.clock_hbyte(in1_val)
        self.tt.send_zeroes_blocking(design_num - 2)
        self.tt.send_zeroes_blocking(2, latch=True)
        if (status & 0xC) == 0:
            # Complete hovalaag cycle
            self.tt.send_zeroes_blocking(chain_len - (2*design_num + 6), scan=True)
            self.clock_hbyte(in1_val >> 6)
            self.clock_hbyte(in2_val)
            self.clock_hbyte(in2_val >> 6)
            self.tt.send_zeroes_blocking(design_num - 6)
            pc = self.tt.send_zeroes_blocking(6, latch=True)
        else:
            pc = self.tt.send_zeroes_blocking(chain_len - design_num, scan=True)
            
            self.clock_hbyte(in1_val >> 6)
            self.tt.send_zeroes_blocking(design_num - 2)
            self.tt.send_zeroes_blocking(2, latch=True)
            out = self.tt.send_zeroes_blocking(chain_len - design_num, scan=True) >> 2
            
            self.clock_hbyte(in2_val)
            self.tt.send_zeroes_blocking(design_num - 2)
            self.tt.send_zeroes_blocking(2, latch=True)
            out = ((self.tt.send_zeroes_blocking(chain_len - design_num, scan=True) & 0xFC) << 4) | out
            out = (out ^ 0x800) - 0x800 # Sign extend
            
            self.clock_hbyte(in2_val >> 6)
            self.tt.send_zeroes_blocking(design_num - 2)
            self.tt.send_zeroes_blocking(2, latch=True)
        #print("PC={:02x}".format(pc))
        
        if latch_seg:
            self.tt.send_zeroes_blocking(chain_len - design_num, scan=True)
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
            pc, status, out = self.execute_instr(prog[pc], in1, in2, False)
            if (status & 0x4) != 0:
                out1.append(out)
            if (status & 0x8) != 0:
                in2.append(out)
            count += 1
        
        print("Executed {} instructions".format(count))
        return out1
