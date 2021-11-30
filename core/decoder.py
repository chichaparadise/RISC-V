from nmigen import *
from nmigen.hdl.ast import Switch
from isa import *


class Decoder(Elaboratable):
    def __init__(self):
        self.instruction = Signal(32)
        self.rs1 = Signal(5)
        self.rs2 = Signal(5)
        self.rd = Signal(5)
        self.funct3 = Signal(3)
        self.imm = Signal(32)
        self.funct7 = Signal(1, reset=0)


    def elaborate(self, platfrom):
        m = Module()

        i_imm = Signal(32)
        s_imm = Signal(32)
        b_imm = Signal(32)
        u_imm = Signal(32)
        j_imm = Signal(32)

        m.d.comb += [
            i_imm.eq(Cat(self.instruction[20], self.instruction[21:25], self.instruction[25:31], Repl(self.instruction[31], 21))),
            s_imm.eq(Cat(self.instruction[7], self.instruction[8:12], self.instruction[25:31], Repl(self.instruction[31], 21))),
            b_imm.eq(Cat(0, self.instruction[8:12], self.instruction[25:31], self.instruction[7], Repl(self.instruction[31], 20))),
            u_imm.eq(Cat(Repl(0, 12), self.instruction[12:20], self.instruction[20:31], self.instruction[31])),
            j_imm.eq(Cat(0, self.instruction[21:25], self.instruction[25:31], self.instruction[20], self.instruction[12:20], Repl(self.instruction[31], 12))),
        ]

        with m.Switch(self.instruction[:7]):
            with m.Case(OP_IMM):
                with m.Switch(self.instruction[12:15]):
                    with m.Case(ALU_SLL, ALU_SRL, ALU_SRA):
                        m.d.comb += self.imm.eq(self.instruction[20:25])
                        m.d.comb += self.funct7.eq(self.instruction[30])
                    with m.Default():
                        m.d.comb += self.imm.eq(i_imm)
                m.d.comb += [
                    self.rs1.eq(self.instruction[15:20]),
                    self.rs2.eq(0),
                    self.rd.eq(self.instruction[7:12]),
                    self.funct3.eq(self.instruction[12:15])
                ]
            with m.Case(OP_REG):
                m.d.comb += [
                    self.imm.eq(0),
                    self.rs1.eq(self.instruction[15:20]),
                    self.rs2.eq(self.instruction[20:25]),
                    self.rd.eq(self.instruction[7:12]),
                    self.funct3.eq(self.instruction[12:15]),
                    self.funct7.eq(self.instruction[30])
                ]
            with m.Case(OP_LUI, OP_AUIPC):
                m.d.comb += [
                    self.imm.eq(u_imm),
                    self.rs1.eq(0),
                    self.rs2.eq(0),
                    self.rd.eq(self.instruction[7:12])
                ]
            with m.Case(OP_JAL):
                m.d.comb += [
                    self.imm.eq(j_imm),
                    self.rs1.eq(0),
                    self.rs2.eq(0),
                    self.rd.eq(self.instruction[7:12]),
                    self.funct3.eq(0)
                ]
            with m.Case(OP_JALR):
                m.d.comb += [
                    self.imm.eq(i_imm),
                    self.rs1.eq(self.instruction[15:20]),
                    self.rs2.eq(0),
                    self.rd.eq(self.instruction[7:12]),
                    self.funct3.eq(0)
                ]
            with m.Case(OP_BRANCH):
                m.d.comb += [
                    self.imm.eq(b_imm),
                    self.rs1.eq(self.instruction[15:20]),
                    self.rs2.eq(self.instruction[20:25]),
                    self.rd.eq(0),
                    self.funct3.eq(self.instruction[12:15])
                ]

        return m