from nmigen import *
from nmigen.sim import *


class Registers(Elaboratable):
    def __init__(self):
        self.mem = Memory(width = 32, depth = 32)
        self.rs1_addr = Signal(5)
        self.rs1_data = Signal(32)
        self.rs2_addr = Signal(5)
        self.rs2_data = Signal(32)
        self.rd_addr = Signal(5)
        self.rd_data = Signal(32)
        self.rd_we = Signal()

    def elaborate(self, platform):
        m = Module()

        rs1 = m.submodules.rs1 = self.mem.read_port()
        rs2 = m.submodules.rs2 = self.mem.read_port()
        rd  = m.submodules.rd  = self.mem.write_port()

        m.d.comb += [
            rs1.addr.eq(self.rs1_addr),
            self.rs1_data.eq(rs1.data),
            rs2.addr.eq(self.rs2_addr),
            self.rs2_data.eq(rs2.data),
        ]

        with m.If(self.rd_addr != 0):
            m.d.comb += [
                rd.addr.eq(self.rd_addr),
                rd.data.eq(self.rd_data),
                rd.en.eq(self.rd_we),
            ]

        return m
