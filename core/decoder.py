from nmigen import *
from nmigen.sim import *


class Opcode:
    LUI    = 0b0110111
    AUIPC  = 0b0010111
    JAL    = 0b1101111
    JALR   = 0b1100111
    BRANCH = 0b1100011
    LOAD   = 0b0000011
    STORE  = 0b0100011
    IMM    = 0b0010011
    REG    = 0b0110011

class IType:
    ALU   = 0b000
    BR    = 0b001
    J     = 0b010
    JR    = 0b011
    LD    = 0b100
    ST    = 0b101

class Decoder(Elaboratable):
    def __init__(self):
        self.inst = Signal(32)

        self.rs1 = Signal(5)
        self.rs1_en = Signal()

        self.rs2 = Signal(5)
        self.rs2_en = Signal()

        self.rd = Signal(5)
        self.rd_en = Signal()

        self.itype = Signal(3)
        self.mem_op_en = Signal()
        self.mem_op_store = Signal()
        self.funct3 = Signal(3)
        self.funct1 = Signal()

        self.imm = Signal(32)

    def elaborate(self, platform):
        m = Module()
        inst = self.inst
        opcode = inst[:7]
        rd = inst[7:12]
        rs1 = inst[15:20]
        rs2 = inst[20:25]
        funct3 = inst[12:15]
        funct7 = inst[25:32]

        imm_i = Signal(32)
        imm_s = Signal(32)
        imm_b = Signal(32)
        imm_u = Signal(32)
        imm_j = Signal(32)
        m.d.comb += [
            imm_i.eq(Cat(self.inst[20], self.inst[21:25], self.inst[25:31], Repl(self.inst[31], 21))),
            imm_s.eq(Cat(self.inst[7], self.inst[8:12], self.inst[25:31], Repl(self.inst[31], 21))),
            imm_b.eq(Cat(0, self.inst[8:12], self.inst[25:31], self.inst[7], Repl(self.inst[31], 20))),
            imm_u.eq(Cat(Repl(0, 12), self.inst[12:20], self.inst[20:31], self.inst[31])),
            imm_j.eq(Cat(0, self.inst[21:25], self.inst[25:31], self.inst[20], self.inst[12:20], Repl(self.inst[31], 12))),
        ]

        funct1 = Signal()
        funct1_valid = Signal()
        m.d.comb += [
            self.itype.eq(IType.ALU),
            self.rs1.eq(Mux(self.rs1_en, rs1, 0)),
            self.rs2.eq(Mux(self.rs2_en, rs2, 0)),
            self.rd.eq(Mux(self.rd_en, rd, 0)),
            self.funct3.eq(funct3),
        ]

        with m.Switch(funct7):
            with m.Case('0100000'):
                m.d.comb += [
                    funct1.eq(1),
                    funct1_valid.eq(1),
                ]
            with m.Case('0000000'):
                m.d.comb += [
                    funct1.eq(0),
                    funct1_valid.eq(1),
                ]
            with m.Default():
                m.d.comb += [
                    funct1.eq(0),
                    funct1_valid.eq(0),
                ]

        with m.Switch(opcode):
            with m.Case(Opcode.LUI):
                m.d.comb += [
                    self.rs1_en.eq(1),
                    self.rs1.eq(0),
                    self.rs2_en.eq(0),
                    self.rd_en.eq(1),
                    self.funct3.eq(0),
                    self.imm.eq(imm_u),
            ]
            with m.Case(Opcode.AUIPC):
                m.d.comb += [
                    self.rs1_en.eq(0),
                    self.rs2_en.eq(0),
                    self.rd_en.eq(1),
                    self.funct3.eq(0),
                    self.imm.eq(imm_u),
                ]
            with m.Case(Opcode.JAL):
                m.d.comb += [
                    self.rs1_en.eq(0),
                    self.rs2_en.eq(0),
                    self.rd_en.eq(1),
                    self.itype.eq(IType.J),
                    self.funct3.eq(0),
                    self.imm.eq(imm_j),
                ]
            with m.Case(Opcode.JALR):
                m.d.comb += [
                    self.rs1_en.eq(1),
                    self.rs2_en.eq(0),
                    self.rd_en.eq(1),
                    self.itype.eq(IType.JR),
                    self.funct3.eq(0),
                    self.imm.eq(imm_i),
                ]
            with m.Case(Opcode.BRANCH):
                m.d.comb += [
                    self.rs1_en.eq(1),
                    self.rs2_en.eq(1),
                    self.rd_en.eq(0),
                    self.itype.eq(IType.BR),
                    self.imm.eq(imm_b),
                ]
            with m.Case(Opcode.LOAD):
                m.d.comb += [
                    self.rs1_en.eq(1),
                    self.rs2_en.eq(0),
                    self.rd_en.eq(1),
                    self.imm.eq(imm_i),
                    self.mem_op_en.eq(1),
                    self.itype.eq(IType.LD)
                ]
            with m.Case(Opcode.STORE):
                m.d.comb += [
                    self.rs1_en.eq(1),
                    self.rs2_en.eq(1),
                    self.rd_en.eq(0),
                    self.imm.eq(imm_s),
                    self.mem_op_en.eq(1),
                    self.mem_op_store.eq(1),
                    self.itype.eq(IType.ST)
                ]
            with m.Case(Opcode.IMM):
                with m.Switch(Cat(funct1_valid, funct3)):
                    with m.Case('-011'):
                        m.d.comb += [
                            self.imm.eq(rs2),
                            self.funct1.eq(funct1),
                        ]
                    with m.Default():
                        m.d.comb += self.imm.eq(imm_i)
                m.d.comb += [
                    self.rs1_en.eq(1),
                    self.rs2_en.eq(0),
                    self.rd_en.eq(1),
                ]
            with m.Case(Opcode.REG):
                m.d.comb += [
                    self.rs1_en.eq(1),
                    self.rs2_en.eq(1),
                    self.rd_en.eq(1),
                    self.imm.eq(0),
                    self.funct1.eq(funct1),
                ]

        return m
