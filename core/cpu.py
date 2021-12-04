from collections import Counter
from nmigen import *

from alu import Alu
from branch import Branch
from decoder import Decoder
from isa import *
from memory import RAM
from registers import Registers


class CPU(Elaboratable):
    def __init__(self, reset_adress=0x00000000, init=None, instruction=0x00000000):
        self.pc = Signal(32, reset=reset_adress)
        self.init = init
        self.cycles = Signal(8, reset=0x00000000)
        self.instruction = Signal(32, reset=instruction)

        self.decoder = Decoder()
        self.alu = Alu()
        self.branch = Branch()
        self.registers = Registers()
        self.ram = RAM(self.init)

    def elaborate(self, platform):
        m = Module()

        m.submodules.decoder = decoder = self.decoder
        m.submodules.alu = alu = self.alu
        m.submodules.branch = branch = self.branch
        m.submodules.registers = registers = self.registers
        m.submodules.ram = ram = self.ram

        pc = Signal(32)
        next_pc = Signal(32)
        data = Signal(32)
        addr = Signal(32)

        instruction = Signal(32)

        m.d.comb += [
            pc.eq(self.pc),
            ram.read_address.eq(self.pc),
            # instruction.eq(ram.read_value)
            instruction.eq(self.instruction)
        ]

        m.d.comb += [
            decoder.instruction.eq(instruction),
            registers.rs1_addr.eq(decoder.rs1),
            registers.rs2_addr.eq(decoder.rs2),
            registers.rd_addr.eq(decoder.rd),
            alu.rs1_val.eq(Mux(decoder.rs1_has_value, registers.rs1_val, pc)),
            alu.rs2_val.eq(Mux(decoder.rs2_has_value, registers.rs2_val, decoder.imm)),
            branch.funct.eq(Cat(decoder.funct3, decoder.funct7)),
            branch.src1.eq(decoder.rs1),
            branch.src2.eq(decoder.rs2),
        ]

        m.d.comb += next_pc.eq(pc + 4)

        with m.Switch(decoder.itype):
            # proc main functions against opcode && itype
            with m.Case(IType.J):
                m.d.comb += data.eq(pc+4)
                with m.If(decoder.imm_has_value):
                    m.d.comb += next_pc.eq(decoder.imm + pc)
            with m.Case(IType.JR):
                m.d.comb += data.eq(pc+4)
                with m.If(decoder.imm_has_value):
                    with m.If(decoder.rs1_has_value):
                        m.d.comb += next_pc.eq(decoder.imm + registers.rs1_val)    
            with m.Case(IType.BR):
                with m.If(decoder.imm_has_value):
                    m.d.comb += next_pc.eq(decoder.imm + pc)
            with m.Case(IType.AUIPC):
                with m.If(decoder.imm_has_value):
                    m.d.comb += data.eq(pc + decoder.imm)
            with m.Case(IType.ST):
                with m.If(decoder.rs2_has_value):
                    m.d.comb += data.eq(registers.rs2_val)
                with m.If(alu.rd_has_val):
                    m.d.comb += addr.eq(alu.rd_val)
            with m.Case(IType.LD):
                with m.If(alu.rd_has_val):
                    m.d.comb += addr.eq(alu.rd_val)
            with m.Case(IType.ALU):
                with m.If(alu.rd_has_val):
                    m.d.comb += data.eq(alu.rd_val)

        with m.Switch(decoder.itype):
            with m.Case(IType.LD):
                m.d.comb += [
                    # add logic to load b, h, w
                    ram.read_address.eq(addr),
                    data.eq(ram.read_value)
                ]
            with m.Case(IType.ST):
                m.d.comb += [
                    # add logic to store b, h, w
                    ram.write_address.eq(addr),
                    ram.write_value.eq(data),
                    ram.we.eq(1)
                ]

        # write to registers here
        with m.If(decoder.rd_has_value):
            m.d.comb += registers.rd_val.eq(data)
            m.d.comb += registers.we.eq(1)


        m.d.comb += [
            self.pc.eq(next_pc), # -> next loop
            self.cycles.eq(self.cycles + 1)
        ]

        return m


if __name__ == '__main__':
    from nmigen.sim import *
    dut = CPU(init=[0xeef08093], instruction=0xeef08093)
    
    sim = Simulator(dut)

    def proc():
        # yield Tick()
        yield Settle()
        pc = yield dut.registers.rd_val
        print(pc)

    # sim.add_clock(1e-6)
    # sim.add_sync_process(proc)
    sim.add_process(proc)
    sim.run()
