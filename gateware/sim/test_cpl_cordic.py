from myhdl import *
import os
import numpy as np
import spectrum
from scipy import signal

module = 'cpl_cordic'
testbench = 'test_%s' % module

srcs = []

srcs.append("../rtl/radio_openhpsdr1/%s.v" % module)
srcs.append("%s.v" % testbench)

src = ' '.join(srcs)

build_cmd = "iverilog -g2012 -o %s.vvp %s" % (testbench, src)

cosa = np.zeros(16384)

verilogtb = """
module test_cpl_cordic;

    reg clk;
    reg signed [31:0] phase;
    wire signed [15:0] cos;

    initial begin
        $from_myhdl(clk, phase);
        $to_myhdl(cos);
        $dumpfile("test_cpl_cordic.lxt");
        $dumpvars(0, test_cpl_cordic);
    end


cpl_cordic #(.OUT_WIDTH(16)) UUT (
    .clock(clk), 
    .frequency(phase), 
    .in_data_I(16'h4c9a),           
    .in_data_Q(16'h0000), 
    .out_data_I(cos), 
    .out_data_Q()
);

endmodule
"""
f = open(testbench+".v","w")
f.write(verilogtb)
f.close()



def bench():
    global cosa

    # Inputs
    clk = Signal(bool(0))
 
    maxv = 2**31
    phase = Signal(intbv(0,min=-maxv,max=maxv))
    maxv = 2**15
    cos = Signal(intbv(0,min=-maxv,max=maxv))

    # DUT
    if os.system(build_cmd):
        raise Exception("Error running build command")

    dut = Cosimulation(
        "vvp -m myhdl %s.vvp -lxt2" % testbench,
        clk=clk,
        phase=phase,
        cos=cos
    )

    @always(delay(5))
    def clkgen():
        clk.next = not clk


    @instance
    def check():

        phase.next = 0x18a9c71c
        for i in range(32):
            yield negedge(clk)

        for i in range(16384):
            cosa[i] = cos ## >> 2
            yield clk.negedge
 
        raise StopSimulation

    return dut, clkgen, check

def test_bench():
    sim = Simulation(bench())
    sim.run()

    dt = 1.0/76.8e6
    print("MinMax",np.min(cosa),np.max(cosa))
    s = spectrum.Spectrum(cosa,dt,window=signal.flattop)
    peaks = s.findPeaks(order=4,clipdb=90)
    s.printPeaks(peaks)
    s.plot()


if __name__ == '__main__':
    print("Running test...")
    test_bench()

    
        


                

        

