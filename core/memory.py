from math import ceil, log2
from nmigen import *
from nmigen.sim import *
from nmigen_soc.wishbone.bus import Arbiter, Interface, MemoryMap


class MemoryUnit(Elaboratable):
    def __init__(self, size_words, data=[]):
        self.size = size_words * 4
        self.mem = Memory(
            width=32,
            depth=size_words,
            init=data
        )
        self.read_port = self.mem.read_port()
        self.write_port = self.mem.write_port()
        self.arb = Arbiter(addr_width=ceil(log2(self.size + 1)),
                           data_width=32)
        self.arb.bus.memory_map = MemoryMap(
            addr_width = self.arb.bus.addr_width,
            data_width = self.arb.bus.data_width,
            alignment = 0 )

    def new_bus( self ):
        bus = Interface( addr_width = self.arb.bus.addr_width,
                     data_width = self.arb.bus.data_width )
        bus.memory_map = MemoryMap( addr_width = bus.addr_width,
                                data_width = bus.data_width,
                                alignment = 0 )
        self.arb.add( bus )
        return bus

    def elaborate(self, platform):
        m = Module()

        m.submodules.read_port = self.read_port
        m.submodules.write_port = self.write_port
        m.submodules.arb = self.arb

        m.d.sync += self.arb.bus.ack.eq(0)
        with m.If(self.arb.bus.cyc):
            m.d.sync += self.arb.bus.ack.eq(self.arb.bus.stb)
        m.d.comb += [
            self.read_port.addr.eq(self.arb.bus.adr >> 2),
            self.write_port.addr.eq(self.arb.bus.adr >> 2),
            self.arb.bus.dat_r.eq(self.read_port.data),
            self.write_port.data.eq(self.arb.bus.dat_w),
            self.write_port.en.eq(self.arb.bus.we),
        ]

        return m
