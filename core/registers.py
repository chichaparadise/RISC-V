from nmigen import *
from nmigen.sim import *


class Registers(Elaboratable):
    def __init__(self):
        self.mem = Memory(
            width=32,
            depth=32
        )
        self.rs1_addr = Signal(5)
        self.rs1_val = Signal(32)
        self.rs2_addr = Signal(5)
        self.rs2_val = Signal(32)
        self.rd_addr = Signal(5)
        self.rd_val = Signal(32)
        self.we = Signal(1, reset=0)

    def elaborate(self, platform):
        m = Module()

        m.submodules.rs1 = rs1 = self.mem.read_port()
        m.submodules.rs2 = rs2 = self.mem.read_port()
        m.submodules.rd = rd = self.mem.write_port()

        m.d.comb += [
            rs1.addr.eq(self.rs1_addr),
            self.rs1_val.eq(rs1.data),
            rs2.addr.eq(self.rs2_addr),
            self.rs2_val.eq(rs2.data)
        ]

        with m.If(self.rd_addr != 0):
            m.d.comb += [
                rd.addr.eq(self.rd_addr),
                rd.data.eq(self.rd_val),
                rd.en.eq(self.we)
            ]

        return m


def test_regs(reg, data, res):
    dut = Registers()
    sim = Simulator(dut)

    def proc():
        yield dut.rd_addr.eq(reg)
        yield dut.rd_val.eq(data)
        yield dut.we.eq(1)
        #yield Tick()
        yield dut.rs1_addr.eq(reg)
        yield dut.rs2_addr.eq(reg)
        yield Tick()
        yield Settle()
        rs1_data = yield dut.rs1_val
        rs2_data = yield dut.rs2_val
        print(rs1_data, rs2_data)
        if rs1_data != res:
            raise ValueError('rs1_data: %s expected %s but got %s' % (reg, res, rs1_data))
        if rs2_data != res:
            raise ValueError('rs2_data: %s expected %s but got %s' % (reg, res, rs2_data))

    sim.add_clock(1e-6)
    sim.add_sync_process(proc)
    sim.run()

if __name__ == '__main__':
    for reg in range(32):
        if reg == 0:
            test_regs(reg, 0xffff_ffff, 0)
        else:
            test_regs(reg, 0x00000023, 0x00000023)