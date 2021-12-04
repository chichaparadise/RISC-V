from nmigen import *
from nmigen.sim import *
from alu import Alu
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
        self.opcode = Signal(7)
        self.itype = Signal(4)
        self.rs1_has_value = Signal(1)
        self.rs2_has_value = Signal(1)
        self.rd_has_value = Signal(1)
        self.imm_has_value = Signal(1)

    def elaborate(self, platfrom):
        m = Module()

        i_imm = Signal(32)
        s_imm = Signal(32)
        b_imm = Signal(32)
        u_imm = Signal(32)
        j_imm = Signal(32)

        m.d.comb += self.opcode.eq(self.instruction[:7])

        m.d.comb += [
            i_imm.eq(Cat(self.instruction[20], self.instruction[21:25], self.instruction[25:31], Repl(self.instruction[31], 21))),
            s_imm.eq(Cat(self.instruction[7], self.instruction[8:12], self.instruction[25:31], Repl(self.instruction[31], 21))),
            b_imm.eq(Cat(0, self.instruction[8:12], self.instruction[25:31], self.instruction[7], Repl(self.instruction[31], 20))),
            u_imm.eq(Cat(Repl(0, 12), self.instruction[12:20], self.instruction[20:31], self.instruction[31])),
            j_imm.eq(Cat(0, self.instruction[21:25], self.instruction[25:31], self.instruction[20], self.instruction[12:20], Repl(self.instruction[31], 12))),
        ]

        with m.Switch(self.opcode):
            with m.Case(OP.IMM):
                with m.Switch(self.instruction[12:15]):
                    with m.Case(ALU.SLL & 0b111, ALU.SRL & 0b111, ALU.SRA & 0b111):
                        m.d.comb += self.imm.eq(self.instruction[20:25])
                        m.d.comb += self.funct7.eq(self.instruction[30])
                    with m.Default():
                        m.d.comb += self.imm.eq(i_imm)
                m.d.comb += [
                    self.rs1.eq(self.instruction[15:20]),
                    self.rs2.eq(0),
                    self.rd.eq(self.instruction[7:12]),
                    self.funct3.eq(self.instruction[12:15]),
                    self.itype.eq(IType.ALU),
                    self.rs1_has_value.eq(1),
                    self.rs2_has_value.eq(0),
                    self.rd_has_value.eq(1),
                    self.imm_has_value.eq(1)
                ]
            with m.Case(OP.REG):
                m.d.comb += [
                    self.imm.eq(0),
                    self.rs1.eq(self.instruction[15:20]),
                    self.rs2.eq(self.instruction[20:25]),
                    self.rd.eq(self.instruction[7:12]),
                    self.funct3.eq(self.instruction[12:15]),
                    self.funct7.eq(self.instruction[30]),
                    self.itype.eq(IType.ALU),
                    self.rs1_has_value.eq(1),
                    self.rs2_has_value.eq(1),
                    self.rd_has_value.eq(1),
                    self.imm_has_value.eq(0)
                ]
            with m.Case(OP.LUI):
                m.d.comb += [
                    self.imm.eq(u_imm),
                    self.rs1.eq(0),
                    self.rs2.eq(0),
                    self.rd.eq(self.instruction[7:12]),
                    self.itype.eq(IType.ALU),
                    self.rs1_has_value.eq(1),
                    self.rs2_has_value.eq(0),
                    self.rd_has_value.eq(1),
                    self.imm_has_value.eq(1)
                ]
            with m.Case(OP.AUIPC):
                m.d.comb += [
                    self.imm.eq(u_imm),
                    self.rs1.eq(0),
                    self.rs2.eq(0),
                    self.rd.eq(self.instruction[7:12]),
                    self.itype.eq(IType.AUIPC),
                    self.rs1_has_value.eq(0),
                    self.rs2_has_value.eq(0),
                    self.rd_has_value.eq(1),
                    self.imm_has_value.eq(1)
                ]
            with m.Case(OP.JAL):
                m.d.comb += [
                    self.imm.eq(j_imm),
                    self.rs1.eq(0),
                    self.rs2.eq(0),
                    self.rd.eq(self.instruction[7:12]),
                    self.funct3.eq(0),
                    self.itype.eq(IType.J),
                    self.rs1_has_value.eq(0),
                    self.rs2_has_value.eq(0),
                    self.rd_has_value.eq(1),
                    self.imm_has_value.eq(1)
                ]
            with m.Case(OP.JALR):
                m.d.comb += [
                    self.imm.eq(i_imm),
                    self.rs1.eq(self.instruction[15:20]),
                    self.rs2.eq(0),
                    self.rd.eq(self.instruction[7:12]),
                    self.funct3.eq(0),
                    self.itype.eq(IType.JR),
                    self.rs1_has_value.eq(1),
                    self.rs2_has_value.eq(0),
                    self.rd_has_value.eq(1),
                    self.imm_has_value.eq(1)
                ]
            with m.Case(OP.BRANCH):
                m.d.comb += [
                    self.imm.eq(b_imm),
                    self.rs1.eq(self.instruction[15:20]),
                    self.rs2.eq(self.instruction[20:25]),
                    self.rd.eq(0),
                    self.funct3.eq(self.instruction[12:15]),
                    self.itype.eq(IType.BR),
                    self.rs1_has_value.eq(1),
                    self.rs2_has_value.eq(1),
                    self.rd_has_value.eq(0),
                    self.imm_has_value.eq(1)
                ]

        return m


def test_decoder(inst, funct4, type: ALU):
    dut = Decoder()
    sim = Simulator(dut)

    def proc():
        yield dut.instruction.eq(inst)
        yield Settle()
        itype = yield dut.itype
        out = yield Cat(dut.funct3, dut.funct7)
        if hex(itype) != hex(type.value):
            raise ValueError('expected %s but got %s' % (hex(type.value), hex(itype)))
        if hex(out) != hex(funct4):
            raise ValueError('expected %s but got %s' % (hex(funct4), hex(out)))

    sim.add_process(proc)
    sim.run()


if __name__ == '__main__':
    inst = 0b00000000000100000000000010010011 # addi x1, x0, 1
    test_decoder(inst, ALU.ADD, IType.ALU)
    print('ok')
    inst = 0b00000000000000000111000010110011 # and x1, x0, x0
    test_decoder(inst, ALU.AND, IType.ALU)
    print('ok')
