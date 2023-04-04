from machine import Pin
from tt_pio import TT_PIO

chain_len = 34

class TT:
    def __init__(self):
        # Pin mapping - names from FPGA's point of view
        clk = Pin(12, Pin.OUT)
        data_in = Pin(13, Pin.OUT)
        latch_en = Pin(11, Pin.OUT)
        scan_select = Pin(10, Pin.OUT)

        clk_out = Pin(9, Pin.IN)
        data_out = Pin(8, Pin.IN)

        seg_latch = Pin(7, Pin.OUT)

        clk.off()
        data_in.off()
        latch_en.off()
        scan_select.off()
        seg_latch.off()

        self.tt = TT_PIO(0, data_in, data_out, scan_select)

    def send_receive_byte(self, byte_in, design_num):
        self.tt.send_byte_blocking(byte_in)
        self.tt.send_zeroes_blocking(design_num - 1)
        self.tt.send_byte_blocking(0, latch=True)
        return self.tt.send_zeroes_blocking(chain_len - design_num, scan=True)
