from nmigen import *
from nmigen.sim import *


class BRANCH:
    BEQ  = 0b000
    BNE  = 0b001
    BLT  = 0b100
    BGE  = 0b101
    BLTU = 0b110
    BGEU = 0b111


class Branch(Elaboratable):
    def __init__(self):
        self.funct = Signal(3)
        self.src1 = Signal(signed(32))
        self.src2 = Signal(signed(32))
        self.res = Signal(1)
        self.res_has_val = Signal(1, reset=1)

    def elaborate(self, platform):
        m = Module()

        with m.Switch(self.funct):
            with m.Case(BRANCH.BEQ):
                m.d.comb += self.res.eq(self.src1 == self.src2)
            with m.Case(BRANCH.BNE):
                m.d.comb += self.res.eq(self.src1 != self.src2)
            with m.Case(BRANCH.BGE):
                m.d.comb += self.res.eq(self.src1 >= self.src2)
            with m.Case(BRANCH.BLT):
                m.d.comb += self.res.eq(self.src1 < self.src2)
            with m.Case(BRANCH.BGEU):
                m.d.comb += self.res.eq(self.src1.as_unsigned() >= self.src2.as_unsigned())
            with m.Case(BRANCH.BLTU):
                m.d.comb += self.res.eq(self.src1.as_unsigned() < self.src2.as_unsigned())
            with m.Default():
                m.d.comb += self.res_has_val.eq(0)

        return m
        