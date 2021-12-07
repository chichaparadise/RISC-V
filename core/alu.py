from nmigen import *
from nmigen.sim import *


class AluFunc:
    ADD  = 0b0000
    SUB  = 0b0001
    SLL  = 0b0010
    SLT  = 0b0100
    SLTU = 0b0110
    XOR  = 0b1000
    SRL  = 0b1010
    SRA  = 0b1011
    OR   = 0b1100
    AND  = 0b1110


class ALU(Elaboratable):

    def __init__(self):
        self.rs1_val = Signal(32, reset=0x0000000)
        self.rs2_val = Signal(32, reset=0x0000000)
        self.funct = Signal(4, reset=0b0000)
        self.rd_val = Signal(32, reset=0x00000000)
        self.rd_has_val = Signal(1, reset=1)

    def elaborate(self, platform):
        m = Module()

        with m.Switch(self.funct[:4]):
            with m.Case(AluFunc.ADD):
                m.d.comb += self.rd_val.eq(self.rs1_val.as_signed() + self.rs2_val.as_signed())
            with m.Case(AluFunc.SUB):
                m.d.comb += self.rd_val.eq(self.rs1_val.as_signed() - self.rs2_val.as_signed())
            with m.Case(AluFunc.AND):
                m.d.comb += self.rd_val.eq(self.rs1_val & self.rs2_val)
            with m.Case(AluFunc.OR):
                m.d.comb += self.rd_val.eq(self.rs1_val | self.rs2_val)
            with m.Case(AluFunc.XOR):
                m.d.comb += self.rd_val.eq(self.rs1_val ^ self.rs2_val)
            with m.Case(AluFunc.SLT):
                m.d.comb += self.rd_val.eq(self.rs1_val.as_signed() < self.rs2_val.as_signed())
            with m.Case(AluFunc.SLTU):
                m.d.comb += self.rd_val.eq(self.rs1_val < self.rs2_val)
            with m.Case(AluFunc.SLL):
                m.d.comb += self.rd_val.eq(self.rs1_val << self.rs2_val[:5])
            with m.Case(AluFunc.SRL):
                m.d.comb += self.rd_val.eq(self.rs1_val >> self.rs2_val[:5])
            with m.Case(AluFunc.SRA):
                m.d.comb += self.rd_val.eq(self.rs1_val.as_signed() >> self.rs2_val[:5])
            with m.Default():
                m.d.comb += self.rd_has_val.eq(0)

        return m
