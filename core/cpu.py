from nmigen import *
from nmigen.hdl.rec import *
from nmigen.sim import *
# from alu import ALU
# from branch import Branch
# from decoder import Decoder, IType
# from registers import Registers
# from ram import RAM
from core.alu import ALU
from core.branch import Branch
from core.decoder import Decoder, IType
from core.registers import Registers
from core.ram import RAM


class CPU(Elaboratable):
    def __init__(self, reset_address=0x8000_0000, data=[]):
        self.reset_address = reset_address

        self.ram = RAM(1024)
        self.rom = RAM(len(data), data=data)
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

        decoder   = m.submodules.decoder   = self.decoder
        regs      = m.submodules.regs      = self.regs
        alu       = m.submodules.alu       = self.alu
        branch    = m.submodules.branch    = self.branch
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


if __name__ == '__main__':
    prog = [
        0xdead_c0b7, # lui   x1, 0xdeadc
        0xeef0_8093, # addi  x1, x1,-273
        0x8000_4197, # auipc x3,0x80004
        0xfe11_ac23, # sw    x1,-8(x3) # 0x4000
        0x8000_4117, # auipc x2,0x80004
        0xff01_2103, # lw    x2,-16(x2) # 0x4000
        0x0011_0463, # beq   x2,x1,80000020
        0x0000_0073, # ecall
        0x0000_0013, # addi x0,x0,0
        # 0x0060_8113,
        # 0x0420_a023,
        # 0x0400_a083         	
    ]

    cpu = CPU(reset_address=0x200, data=prog)
    sim = Simulator(cpu)
    def step():
        clock = 0
        yield Tick()
        yield Settle()
        while (yield cpu.valid) != 1 and clock < 5:
            clock += 1
            yield Tick()
            yield Settle()
        assert(clock < 8)

    def proc():

        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        rs1_addr = yield cpu.regs.rs1_addr
        rs1_data = yield cpu.regs.rs1_data
        rs2_addr = yield cpu.regs.rs2_addr
        rs2_data = yield cpu.regs.rs2_data
        rd_addr = yield cpu.regs.rd_addr
        rd_data = yield cpu.regs.rd_data
        print(hex(instr), hex(pc), hex(rs1_addr), hex(rs1_data), hex(rs2_addr), hex(rs2_data),hex(rd_addr), hex(rd_data),)


        yield from step()

        instr = yield cpu.instruction
        pc = yield cpu.pc
        rs1_addr = yield cpu.regs.rs1_addr
        rs1_data = yield cpu.regs.rs1_data
        rs2_addr = yield cpu.regs.rs2_addr
        rs2_data = yield cpu.regs.rs2_data
        rd_addr = yield cpu.regs.rd_addr
        rd_data = yield cpu.regs.rd_data
        print(hex(instr), hex(pc), hex(rs1_addr), hex(rs1_data), hex(rs2_addr), hex(rs2_data),hex(rd_addr), hex(rd_data),)

        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        rs1_addr = yield cpu.regs.rs1_addr
        rs1_data = yield cpu.regs.rs1_data
        rs2_addr = yield cpu.regs.rs2_addr
        rs2_data = yield cpu.regs.rs2_data
        rd_addr = yield cpu.regs.rd_addr
        rd_data = yield cpu.regs.rd_data
        print(hex(instr), hex(pc), hex(rs1_addr), hex(rs1_data), hex(rs2_addr), hex(rs2_data),hex(rd_addr), hex(rd_data),)

        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        rs2_addr = yield cpu.regs.rs2_addr
        rs2_data = yield cpu.regs.rs2_data
        addr = yield cpu.dbus.adr
        data = yield cpu.dbus.dat_w
        print(hex(instr), hex(pc), hex(rs2_addr), hex(rs2_data),hex(addr), hex(data),)

        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        rs1_addr = yield cpu.regs.rs1_addr
        rs1_data = yield cpu.regs.rs1_data
        rs2_addr = yield cpu.regs.rs2_addr
        rs2_data = yield cpu.regs.rs2_data
        rd_addr = yield cpu.regs.rd_addr
        rd_data = yield cpu.regs.rd_data
        print(hex(instr), hex(pc), hex(rs1_addr), hex(rs1_data), hex(rs2_addr), hex(rs2_data),hex(rd_addr), hex(rd_data),)

        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        rd_addr = yield cpu.regs.rd_addr
        rd_data = yield cpu.regs.rd_data
        addr = yield cpu.dbus.adr
        data = yield cpu.dbus.dat_r
        print(hex(instr), hex(pc), hex(rd_addr), hex(rd_data),hex(addr), hex(data),)

        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        rs1_addr = yield cpu.regs.rs1_addr
        rs1_data = yield cpu.regs.rs1_data
        rs2_addr = yield cpu.regs.rs2_addr
        rs2_data = yield cpu.regs.rs2_data
        rd_addr = yield cpu.regs.rd_addr
        rd_data = yield cpu.regs.rd_data
        print(hex(instr), hex(pc), hex(rs1_addr), hex(rs1_data), hex(rs2_addr), hex(rs2_data),hex(rd_addr), hex(rd_data),)

        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        print(hex(instr), hex(pc))

        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Settle()

    sim.add_clock(1e-6, domain='sync')
    sim.add_sync_process(proc)
    sim.run()
