from nmigen import *
from nmigen.hdl.rec import *
from nmigen.sim import *
from core.alu import ALU
from core.branch import Branch
from core.decoder import Decoder, IType
from core.registers import Registers
from core.memory import MemoryUnit


class CPU(Elaboratable):
    def __init__(self, reset_address=0x0000_0000, data=[]):
        self.reset_address = reset_address

        self.ram = MemoryUnit(256)
        self.rom = MemoryUnit(len(data), data=data)
        self.ibus = self.rom.new_bus()
        self.dbus = self.ram.new_bus()
        self.pc = Signal(32, reset=reset_address)
        self.instruction = Signal(32)
        self.decoder = Decoder()
        self.regs = Registers()
        self.alu = ALU()
        self.branch = Branch()
        self.valid = Signal(1, reset=0)

    def elaborate(self, platform):
        m = Module()

        m.submodules.decoder = decoder = self.decoder
        m.submodules.regs    = regs    = self.regs
        m.submodules.alu     = alu     = self.alu
        m.submodules.branch  = branch  = self.branch
        m.submodules.ram = self.ram
        m.submodules.rom = self.rom

        pc_next = Signal(32)
        pc_next_temp = Signal(32)
        pc_4 = Signal(32)
        inst = self.instruction
        m.d.comb += pc_4.eq(self.pc + 4)
        rs1_en = Signal()
        rs2_en = Signal()

        valid = self.valid

        m.d.comb += [
            self.ibus.adr.eq(self.pc),
            self.ibus.cyc.eq(1)
        ]

        m.d.comb += decoder.inst.eq(self.ibus.dat_r),

        m.d.comb += [
            regs.rs1_addr.eq(decoder.rs1),
            regs.rs2_addr.eq(decoder.rs2),
            regs.rd_addr.eq(decoder.rd),
        ]

        m.d.comb += [
            alu.rs1_val.eq(Mux(rs1_en, regs.rs1_data, self.pc)),
            alu.rs2_val.eq(Mux(rs2_en, regs.rs2_data, decoder.imm)),
        ]

        m.d.comb += [
            branch.funct.eq(decoder.funct3),
            branch.src1.eq(regs.rs1_data),
            branch.src2.eq(regs.rs2_data),
        ]

        m.d.comb += [
            self.dbus.adr.eq(Mux(decoder.mem_op_en, alu.rd_val, 0)),
            self.dbus.dat_w.eq(Mux(decoder.mem_op_store, regs.rs2_data, self.dbus.dat_r)),
            self.dbus.cyc.eq(1),
            pc_next.eq(pc_next_temp),
        ]

        with m.Switch(decoder.itype):
            with m.Case(IType.ALU):
                m.d.comb += [
                    alu.funct.eq(Cat(decoder.funct1, decoder.funct3)),
                    rs1_en.eq(decoder.rs1_en),
                    rs2_en.eq(decoder.rs2_en),
                    pc_next_temp.eq(pc_4),
                    regs.rd_data.eq(alu.rd_val),
                ]
                with m.If(decoder.mem_op_en):
                    m.d.comb += [
                        alu.funct.eq(0),
                        rs2_en.eq(0),
                    ]
            with m.Case(IType.J):
                m.d.comb += [
                    rs1_en.eq(0),
                    rs2_en.eq(0),
                    pc_next_temp.eq(alu.rd_val),
                    regs.rd_data.eq(pc_4),
                ]
            with m.Case(IType.JR):
                m.d.comb += [
                    rs1_en.eq(1),
                    rs2_en.eq(0),
                    pc_next_temp.eq(alu.rd_val),
                    regs.rd_data.eq(pc_4),
                ]
            with m.Case(IType.BR):
                m.d.comb += [
                    alu.funct.eq(0),
                    rs1_en.eq(0),
                    rs2_en.eq(0),
                    pc_next_temp.eq(Mux(branch.res, alu.rd_val, pc_4)),
                ]
            with m.Case(IType.ST):
                m.d.comb += [
                    alu.funct.eq(0),
                    rs1_en.eq(1),
                    rs2_en.eq(0),
                    pc_next_temp.eq(pc_4)
                ]
            with m.Case(IType.LD):
                m.d.comb += [
                    alu.funct.eq(0),
                    rs1_en.eq(1),
                    rs2_en.eq(0),
                    pc_next_temp.eq(pc_4),
                ]

        with m.FSM():
            with m.State('FETCH'):
                m.d.comb += self.ibus.stb.eq(1)
                with m.If(self.ibus.ack):
                    m.next = 'EXECUTE'
                    m.d.sync += inst.eq(self.ibus.dat_r)
                    m.d.comb += decoder.inst.eq(self.ibus.dat_r)
            with m.State('EXECUTE'):
                m.d.comb += decoder.inst.eq(inst)
                with m.If(decoder.mem_op_en):
                    m.next = 'WRITE'
                with m.Else():
                    m.next = 'FETCH'
                    m.d.comb += [
                        regs.rd_we.eq(1),
                        valid.eq(1),
                    ]
                    m.d.sync += self.pc.eq(pc_next)
            with m.State('WRITE'):
                m.d.comb += [
                    decoder.inst.eq(inst),
                    self.dbus.we.eq(decoder.mem_op_store),
                    self.dbus.stb.eq(1),
                ]
                with m.If(self.dbus.ack):
                    m.next = 'FETCH'
                    m.d.comb += [
                        valid.eq(1),
                        regs.rd_we.eq(~decoder.mem_op_store),
                        regs.rd_data.eq(self.dbus.dat_r),
                    ]
                    m.d.sync += self.pc.eq(pc_next)

        return m
