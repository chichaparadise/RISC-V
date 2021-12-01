import sys

from nmigen import *
from nmigen.sim import *


OP_STORE = 0b0100011
OP_LOAD = 0b0000011

sys.setrecursionlimit(4*1024)


class RV_Memory(Elaboratable):
    def __init__(self):
        self.mem = Memory(
            width=32,
            depth=32*4*1024,
        )
        self.waddress = Signal(32)
        self.raddress = Signal(32)
        self.write_val = Signal(32)
        self.read_val = Signal(32)
        self.we = Signal(1)

    def elaborate(self, platform):
        m = Module()

        m.submodules.rport = rport = self.mem.read_port()
        m.submodules.wport = wport = self.mem.write_port()

        m.d.comb += [
            rport.addr.eq(self.raddress),
            self.read_val.eq(rport.data)
        ]

        m.d.comb += [
            wport.addr.eq(self.waddress),
            wport.data.eq(self.write_val),
            wport.en.eq(self.we)
        ]

        return m


if __name__ == '__main__':

    dut = RV_Memory()

    sim = Simulator(dut)
     
    def proc():
        yield dut.waddress.eq(12)
        yield dut.write_val.eq(23)
        yield dut.we.eq(1)

        yield dut.raddress.eq(12)
        Tick()
        Settle()
        val = yield dut.read_val
        print(val)
    
    sim.add_clock(1e-6)
    sim.add_sync_process(proc)
    sim.run()
