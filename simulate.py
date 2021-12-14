from nmigen.sim import *
from core.cpu import CPU


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
    ]

    cpu = CPU(reset_address=0x8000_0000, data=prog)
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
        print('Instr'.rjust(10), 'PC'.rjust(10), 'RS1 Addr'.rjust(10), 
        'RS1 Data'.rjust(10), 'RS2 Addr'.rjust(10), 'RS2 Data'.rjust(10), 'RD Addr'.rjust(10), 'RD Data'.rjust(10))
        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        rs1_addr = yield cpu.regs.rs1_addr
        rs1_data = yield cpu.regs.rs1_data
        rs2_addr = yield cpu.regs.rs2_addr
        rs2_data = yield cpu.regs.rs2_data
        rd_addr = yield cpu.regs.rd_addr
        rd_data = yield cpu.regs.rd_data
        print(hex(instr).rjust(10), hex(pc).rjust(10), hex(rs1_addr).rjust(10), 
        hex(rs1_data).rjust(10), hex(rs2_addr).rjust(10), hex(rs2_data).rjust(10), hex(rd_addr).rjust(10), hex(rd_data).rjust(10),)

        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        rs1_addr = yield cpu.regs.rs1_addr
        rs1_data = yield cpu.regs.rs1_data
        rs2_addr = yield cpu.regs.rs2_addr
        rs2_data = yield cpu.regs.rs2_data
        rd_addr = yield cpu.regs.rd_addr
        rd_data = yield cpu.regs.rd_data
        print(hex(instr).rjust(10), hex(pc).rjust(10), hex(rs1_addr).rjust(10), 
        hex(rs1_data).rjust(10), hex(rs2_addr).rjust(10), hex(rs2_data).rjust(10), hex(rd_addr).rjust(10), hex(rd_data).rjust(10),)

        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        rs1_addr = yield cpu.regs.rs1_addr
        rs1_data = yield cpu.regs.rs1_data
        rs2_addr = yield cpu.regs.rs2_addr
        rs2_data = yield cpu.regs.rs2_data
        rd_addr = yield cpu.regs.rd_addr
        rd_data = yield cpu.regs.rd_data
        print(hex(instr).rjust(10), hex(pc).rjust(10), hex(rs1_addr).rjust(10), 
        hex(rs1_data).rjust(10), hex(rs2_addr).rjust(10), hex(rs2_data).rjust(10), hex(rd_addr).rjust(10), hex(rd_data).rjust(10),)

        print('Instr'.rjust(10), 'PC'.rjust(10), 'RS2 Addr'.rjust(10), 'RS2 Data'.rjust(10), 'Bus Addr'.rjust(10), 'Bus RData')
        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        rs2_addr = yield cpu.regs.rs2_addr
        rs2_data = yield cpu.regs.rs2_data
        addr = yield cpu.dbus.adr
        data = yield cpu.dbus.dat_w
        print(hex(instr).rjust(10), hex(pc).rjust(10), hex(rs2_addr).rjust(10), hex(rs2_data).rjust(10),hex(addr).rjust(10), hex(data).rjust(10),)

        print('Instr'.rjust(10), 'PC'.rjust(10), 'RS1 Addr'.rjust(10), 
        'RS1 Data'.rjust(10), 'RS2 Addr'.rjust(10), 'RS2 Data'.rjust(10), 'RD Addr'.rjust(10), 'RD Data'.rjust(10))
        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        rs1_addr = yield cpu.regs.rs1_addr
        rs1_data = yield cpu.regs.rs1_data
        rs2_addr = yield cpu.regs.rs2_addr
        rs2_data = yield cpu.regs.rs2_data
        rd_addr = yield cpu.regs.rd_addr
        rd_data = yield cpu.regs.rd_data
        print(hex(instr).rjust(10), hex(pc).rjust(10), hex(rs1_addr).rjust(10), 
        hex(rs1_data).rjust(10), hex(rs2_addr).rjust(10), hex(rs2_data).rjust(10), hex(rd_addr).rjust(10), hex(rd_data).rjust(10),)

        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        rd_addr = yield cpu.regs.rd_addr
        rd_data = yield cpu.regs.rd_data
        addr = yield cpu.dbus.adr
        data = yield cpu.dbus.dat_r
        print(hex(instr).rjust(10), hex(pc).rjust(10), hex(rd_addr).rjust(10), hex(rd_data).rjust(10),hex(addr).rjust(10), hex(data).rjust(10),)

        print('Instr'.rjust(10), 'PC'.rjust(10), 'RS2 Addr'.rjust(10), 'RS2 Data'.rjust(10), 'Bus Addr'.rjust(10), 'Bus RData')
        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        rs1_addr = yield cpu.regs.rs1_addr
        rs1_data = yield cpu.regs.rs1_data
        rs2_addr = yield cpu.regs.rs2_addr
        rs2_data = yield cpu.regs.rs2_data
        rd_addr = yield cpu.regs.rd_addr
        rd_data = yield cpu.regs.rd_data
        print(hex(instr).rjust(10), hex(pc).rjust(10), hex(rs1_addr).rjust(10), 
        hex(rs1_data).rjust(10), hex(rs2_addr).rjust(10), hex(rs2_data).rjust(10), hex(rd_addr).rjust(10), hex(rd_data).rjust(10),)

        yield from step()
        instr = yield cpu.instruction
        pc = yield cpu.pc
        print(hex(instr).rjust(10), hex(pc).rjust(10))

        yield Tick()
        yield Tick()
        yield Tick()
        yield Tick()
        yield Settle()

    sim.add_clock(1e-6, domain='sync')
    sim.add_sync_process(proc)
    with sim.write_vcd("cpu.vcd", "cpu.gtkw"):
        sim.run()
