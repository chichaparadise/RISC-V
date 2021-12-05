from nmigen import *
from nmigen.hdl.ir import DriverConflict
from nmigen.sim import *
import warnings

from alu import Alu
from branch import Branch
from decoder import Decoder
from isa import *
from memory import RAM
from registers import Registers


class CPU(Elaboratable):
    def __init__(self, reset_adress=0x00000000, ram_size=1024, init=None):
        self.clk_rst = Signal( reset = 0b0, reset_less = True )
        self.pc = Signal(32, reset=reset_adress)
        self.init = init
        self.decoder = Decoder()
        self.alu = Alu()
        self.branch = Branch()
        self.registers = Registers()
        self.ram = RAM(ram_size, self.init)

    def elaborate(self, platform):
        m = Module()

        m.submodules.decoder = decoder = self.decoder
        m.submodules.alu = alu = self.alu
        m.submodules.branch = branch = self.branch
        m.submodules.registers = registers = self.registers
        m.submodules.ram = ram = self.ram

        iws = Signal(2, reset=0)

        pc = Signal(32)
        next_pc = Signal(32)
        data = Signal(32)
        addr = Signal(32)

        instruction = Signal(32)
        
        m.d.sync += [
            pc.eq(self.pc),
            ram.arb.bus.adr.eq(self.pc),
            instruction.eq(ram.arb.bus.dat_r)
        ]

        with m.If( self.ram.arb.bus.ack ):
            # Increment the wait-state counter.
            # (This also lets the instruction bus' 'cyc' signal fall.)
            m.d.sync += iws.eq( 1 )

        with m.If( iws != 0 ):
            # Increment the PC and reset the wait-state unless
            # otherwise specified.
            m.d.sync += [
                # self.pc.eq( self.pc + 4 ),
                iws.eq( 0 )
            ]

        m.d.comb += next_pc.eq(self.pc + 4)

        m.d.comb += [
            decoder.instruction.eq(instruction),
            registers.rs1_addr.eq(decoder.rs1),
            registers.rs2_addr.eq(decoder.rs2),
            registers.rd_addr.eq(decoder.rd),
            alu.rs1_val.eq(Mux(decoder.rs1_has_value, registers.rs1_val, pc)),
            alu.rs2_val.eq(Mux(decoder.rs2_has_value, registers.rs2_val, decoder.imm)),
            alu.funct.eq(Cat(decoder.funct3, decoder.funct7)),
            branch.funct.eq(Cat(decoder.funct3, decoder.funct7)),
            branch.src1.eq(decoder.rs1),
            branch.src2.eq(decoder.rs2),
        ]

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
                m.d.sync += [
                    ram.arb.bus.adr.eq(addr),
                ]
                m.d.comb += data.eq(ram.arb.bus.dat_r)
                # m.d.comb += [
                #     # add logic to load b, h, w
                #     ram.read_address.eq(addr),
                #     data.eq(ram.read_value)
                # ]
            with m.Case(IType.ST):
                # m.d.comb += [
                #     # add logic to store b, h, w
                #     ram.write_address.eq(addr),
                #     ram.write_value.eq(data),
                #     ram.we.eq(1)
                # ]
                m.d.sync += [
                    ram.arb.bus.adr.eq(addr),
                    ram.arb.bus.dat_w.eq(data),
                    ram.arb.bus.we.eq(1)
                ]

        # write to registers here
        with m.If(decoder.rd_has_value):
            m.d.comb += registers.rd_val.eq(data)
            m.d.comb += registers.we.eq(1)

        m.d.sync += [
            self.pc.eq(next_pc), # -> next loop
        ]

        return m


##################
# CPU testbench: #
##################
# Keep track of test pass / fail rates.
p = 0
f = 0

# Import test programs and expected runtime register values.
from programs import *

# Helper method to check expected CPU register / memory values
# at a specific point during a test program.
def check_vals( expected, ni, cpu ):
  global p, f
  if ni in expected:
    for j in range( len( expected[ ni ] ) ):
      ex = expected[ ni ][ j ]
      # Special case: program counter.
      if ex[ 'r' ] == 'pc':
        cpc = yield cpu.pc
        if hexs( cpc ) == hexs( ex[ 'e' ] ):
          p += 1
          print( "  \033[32mPASS:\033[0m pc  == %s"
                 " after %d operations"
                 %( hexs( ex[ 'e' ] ), ni ) )
        else:
          f += 1
          print( "  \033[31mFAIL:\033[0m pc  == %s"
                 " after %d operations (got: %s)"
                 %( hexs( ex[ 'e' ] ), ni, hexs( cpc ) ) )
      # Special case: RAM data (must be word-aligned).
      elif type( ex[ 'r' ] ) == str and ex[ 'r' ][ 0:3 ] == "RAM":
        rama = int( ex[ 'r' ][ 3: ] )
        if ( rama % 4 ) != 0:
          f += 1
          print( "  \033[31mFAIL:\033[0m RAM == %s @ 0x%08X"
                 " after %d operations (mis-aligned address)"
                 %( hexs( ex[ 'e' ] ), rama, ni ) )
        else:
          cpd = yield cpu.ram.mem[ rama // 4 ]
          if hexs( cpd ) == hexs( ex[ 'e' ] ):
            p += 1
            print( "  \033[32mPASS:\033[0m RAM == %s @ 0x%08X"
                   " after %d operations"
                   %( hexs( ex[ 'e' ] ), rama, ni ) )
          else:
            f += 1
            print( "  \033[31mFAIL:\033[0m RAM == %s @ 0x%08X"
                   " after %d operations (got: %s)"
                   %( hexs( ex[ 'e' ] ), rama, ni, hexs( cpd ) ) )
      # Numbered general-purpose registers.
      elif ex[ 'r' ] >= 0 and ex[ 'r' ] < 32:
        cr = yield cpu.registers.mem[ ex[ 'r' ] ]
        if hexs( cr ) == hexs( ex[ 'e' ] ):
          p += 1
          print( "  \033[32mPASS:\033[0m r%02d == %s"
                 " after %d operations"
                 %( ex[ 'r' ], hexs( ex[ 'e' ] ), ni ) )
        else:
          f += 1
          print( "  \033[31mFAIL:\033[0m r%02d == %s"
                 " after %d operations (got: %s)"
                 %( ex[ 'r' ], hexs( ex[ 'e' ] ),
                    ni, hexs( cr ) ) )

# Helper method to run a CPU device for a given number of cycles,
# and verify its expected register values over time.
def cpu_run( cpu, expected ):
  global p, f
  # Record how many CPU instructions have been executed.
  ni = -1
  # Watch for timeouts if the CPU gets into a bad state.
  timeout = 0
  instret = 0
  # Let the CPU run for N instructions.
  while ni <= expected[ 'end' ]:
    # Let combinational logic settle before checking values.
    yield Settle()
    timeout = timeout + 1
    # Only check expected values once per instruction.
    # ninstret = yield cpu.csr.minstret_instrs
    # if ninstret != instret:
    ni += 1
    #   instret = ninstret
    timeout = 0
      # Check expected values, if any.
    yield from check_vals( expected, ni, cpu )
    # elif timeout > 1000:
    #   f += 1
    #   print( "\033[31mFAIL: Timeout\033[0m" )
    #   break
    # Step the simulation.
    yield Tick()

# Helper method to simulate running a CPU with the given ROM image
# for the specified number of CPU cycles. The 'name' field is used
# for printing and generating the waveform filename: "cpu_[name].vcd".
def cpu_sim( test ):
  print( "\033[33mSTART\033[0m running '%s' program:"%test[ 0 ] )
  # Create the CPU device.
  dut = CPU( init= test[ 2 ]  )
  cpu = ResetInserter( dut.clk_rst )( dut )

  # Run the simulation.
  sim_name = "%s.vcd"%test[ 1 ]
  sim = Simulator(cpu)
  def proc():
      # Initialize RAM values.
      for i in range( len( test[ 3 ] ) ):
        yield cpu.mem.ram.data[ i ].eq( test[ 3 ][ i ]  )
      # Run the program and print pass/fail for individual tests.
      yield from cpu_run( cpu, test[ 4 ] )
      print( "\033[35mDONE\033[0m running %s: executed %d instructions"
             %( test[ 0 ], test[ 4 ][ 'end' ] ) )
  sim.add_clock( 1e-6 )
  sim.add_sync_process( proc )
  sim.run()

# # Helper method to simulate running a CPU from simulated SPI
# # Flash which contains a given ROM image.
# # def cpu_spi_sim( test ):
# #   print( "\033[33mSTART\033[0m running '%s' program (SPI):"%test[ 0 ] )
# #   # Create the CPU device.
# #   sim_spi_off = ( 2 * 1024 * 1024 )
# #   dut = CPU( SPI_ROM( sim_spi_off, sim_spi_off + 1024, test[ 2 ] ) )
# #   cpu = ResetInserter( dut.clk_rst )( dut )

# #   Run the simulation.
# #   sim_name = "%s_spi.vcd"%test[ 1 ]
# #   with Simulator( cpu, vcd_file = open( sim_name, 'w' ) ) as sim:
# #     def proc():
# #       for i in range( len( test[ 3 ] ) ):
# #         yield cpu.mem.ram.data[ i ].eq( test[ 3 ][ i ] )
# #       yield from cpu_run( cpu, test[ 4 ] )
# #       print( "\033[35mDONE\033[0m running %s: executed %d instructions"
# #              %( test[ 0 ], test[ 4 ][ 'end' ] ) )
# #     sim.add_clock( 1 / 6000000 )
# #     sim.add_sync_process( proc )
# #     sim.run()

# 'main' method to run a basic testbench.
# if __name__ == "__main__":
#   # Run testbench simulations.
#   with warnings.catch_warnings():
#     warnings.filterwarnings( "ignore", category = DriverConflict )
#     print( '--- CPU Tests ---' )
#     # Simulate the 'infinite loop' ROM to screen for syntax errors.
#     # cpu_sim( loop_test )
#     # cpu_spi_sim( loop_test )
#     cpu_sim( ram_pc_test )
#     # cpu_spi_sim( ram_pc_test )
#     # Done; print results.
#     print( "CPU Tests: %d Passed, %d Failed"%( p, f ) )


if __name__ == '__main__':
    dut = CPU(init=[0xdeadc0b7, 0xeef08093])
    cpu = ResetInserter( dut.clk_rst )( dut )
    sim = Simulator(cpu)

    def proc():
        Settle()
        a = yield cpu.pc
        print(a)
        Tick()
        Settle()
        b = yield cpu.pc
        print(b)
        Tick()

    sim.add_clock(1e-6)
    sim.add_sync_process(proc)
    sim.run()