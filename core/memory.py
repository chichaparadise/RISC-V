from nmigen import *
from nmigen.sim import *


class RAM(Elaboratable):
    def __init__(self, init=None):
        self.mem = Memory(
            width=32,
            depth=2*1024,
            init=init if init else 0
        )
        self.read_address = Signal(32)
        self.read_value = Signal(32)
        self.write_address = Signal(32)
        self.write_value = Signal(32)
        self.we = Signal(1, reset=0)

    def elaborate(self, platform):
        m = Module()

        m.submodules.pread = pread = self.mem.read_port()
        m.submodules.pwrite = pwrite = self.mem.write_port()

        m.d.comb += [
            pread.addr.eq(self.read_address),
            self.read_value.eq(pread.data),
        ]

        m.d.comb += [
            pwrite.addr.eq(self.write_address),
            pwrite.data.eq(self.write_value),
            pwrite.en.eq(self.we)
        ]

        return m


def test_regs(reg, data, res):
    dut = RAM()
    sim = Simulator(dut)

    def proc():
        yield dut.write_address.eq(reg)
        yield dut.write_value.eq(data)
        yield dut.we.eq(1)

        yield dut.read_address.eq(reg)
        yield Tick()
        yield Settle()
        rs1_data = yield dut.read_value
        print(rs1_data)
        if rs1_data != res:
            raise ValueError('rs1_data: %s expected %s but got %s' % (reg, res, rs1_data))

    sim.add_clock(1e-6)
    sim.add_sync_process(proc)
    sim.run()

if __name__ == '__main__':
    test_regs(0x0000FF1E, 0x00003456, 0x00003456)
    