from nmigen import *
from nmigen.sim import *
from isa import *


class Alu(Elaboratable):

    def __init__(self):
        self.rs1_val = Signal(32, reset=0x0000000)
        self.rs2_val = Signal(32, reset=0x0000000)
        self.funct = Signal(4, reset=0b0000)
        self.rd_val = Signal(32, reset=0x00000000)
        self.rd_has_val = Signal(1, reset=1)

    def elaborate(self, platform):
        m = Module()

        with m.Switch(self.funct[:4]):
            with m.Case(ALU.ADD):
                m.d.comb += self.rd_val.eq(self.rs1_val.as_signed() + self.rs2_val.as_signed())
            with m.Case(ALU.SUB):
                m.d.comb += self.rd_val.eq(self.rs1_val.as_signed() - self.rs2_val.as_signed())
            with m.Case(ALU.AND):
                m.d.comb += self.rd_val.eq(self.rs1_val & self.rs2_val)
            with m.Case(ALU.OR):
                m.d.comb += self.rd_val.eq(self.rs1_val | self.rs2_val)
            with m.Case(ALU.XOR):
                m.d.comb += self.rd_val.eq(self.rs1_val ^ self.rs2_val)
            with m.Case(ALU.SLT):
                m.d.comb += self.rd_val.eq(self.rs1_val.as_signed() < self.rs2_val.as_signed())
            with m.Case(ALU.SLTU):
                m.d.comb += self.rd_val.eq(self.rs1_val < self.rs2_val)
            with m.Case(ALU.SLL):
                m.d.comb += self.rd_val.eq(self.rs1_val << self.rs2_val[:5])
            with m.Case(ALU.SRL):
                m.d.comb += self.rd_val.eq(self.rs1_val >> self.rs2_val[:5])
            with m.Case(ALU.SRA):
                m.d.comb += self.rd_val.eq(self.rs1_val.as_signed() >> self.rs2_val[:5])
            with m.Default():
                m.d.comb += self.rd_has_val.eq(0)

        return m
        

ALU.STRS = {
  ALU.ADD:  "+", ALU.SLT:  "<", ALU.SLTU: "<",
  ALU.XOR:  "^", ALU.OR:   "|", ALU.AND:  "&",
  ALU.SLL: "<<", ALU.SRL: ">>", ALU.SRA: ">>",
  ALU.SUB:  "-"
}

def hexs( num ):
  if num >= 0:
    return "0x%08X"%( num )
  else:
    return "0x%08X"%( ( num + ( 1 << 32 ) ) % ( 1 << 32 ) )


passed, failed = 0, 0

def alu_ut(alu: Alu, val1: Signal, val2: Signal, funct: Signal, expected: Signal):
    global passed, failed

    yield alu.rs1_val.eq(val1)
    yield alu.rs2_val.eq(val2)
    yield alu.funct.eq(funct)

    yield Settle()

    result = yield alu.rd_val
    has_val = yield alu.rd_has_val
    print(hex(has_val))
    if hexs(expected) != hexs(result):
        failed += 1
        print( "\033[31mFAIL:\033[0m %s %s %s = %s (got: %s)"
           %( hexs( val1 ), ALU.STRS[ funct ], hexs( val2 ),
              hexs( expected ), hexs( result ) ) )
    else:
        passed += 1
        print( "\033[32mPASS:\033[0m %s %s %s = %s"
           %( hexs( val1 ), ALU.STRS[ funct ],
              hexs( val2 ), hexs( expected ) ) )


def alu_test(alu):

    yield Settle()

    print( "AND (&) tests:" )

    yield from alu_ut( alu, 0xCCCCCCCC, 0xCCCC0000, ALU.AND, 0xCCCC0000 )
    yield from alu_ut( alu, 0x00000000, 0x00000000, ALU.AND, 0x00000000 )
    yield from alu_ut( alu, 0xFFFFFFFF, 0xFFFFFFFF, ALU.AND, 0xFFFFFFFF )
    yield from alu_ut( alu, 0x00000000, 0xFFFFFFFF, ALU.AND, 0x00000000 )
    yield from alu_ut( alu, 0xFFFFFFFF, 0x00000000, ALU.AND, 0x00000000 )
    # Test the bitwise 'OR' operation.
    print( "OR  (|) tests:" )
    yield from alu_ut( alu, 0xCCCCCCCC, 0xCCCC0000, ALU.OR, 0xCCCCCCCC )
    yield from alu_ut( alu, 0x00000000, 0x00000000, ALU.OR, 0x00000000 )
    yield from alu_ut( alu, 0xFFFFFFFF, 0xFFFFFFFF, ALU.OR, 0xFFFFFFFF )
    yield from alu_ut( alu, 0x00000000, 0xFFFFFFFF, ALU.OR, 0xFFFFFFFF )
    yield from alu_ut( alu, 0xFFFFFFFF, 0x00000000, ALU.OR, 0xFFFFFFFF )
    # Test the bitwise 'XOR' operation.
    print( "XOR (^) tests:" )
    yield from alu_ut( alu, 0xCCCCCCCC, 0xCCCC0000, ALU.XOR, 0x0000CCCC )
    yield from alu_ut( alu, 0x00000000, 0x00000000, ALU.XOR, 0x00000000 )
    yield from alu_ut( alu, 0xFFFFFFFF, 0xFFFFFFFF, ALU.XOR, 0x00000000 )
    yield from alu_ut( alu, 0x00000000, 0xFFFFFFFF, ALU.XOR, 0xFFFFFFFF )
    yield from alu_ut( alu, 0xFFFFFFFF, 0x00000000, ALU.XOR, 0xFFFFFFFF )
    # Test the addition operation.
    print( "ADD (+) tests:" )
    yield from alu_ut( alu, 0, 0, ALU.ADD, 0 )
    yield from alu_ut( alu, 0, 1, ALU.ADD, 1 )
    yield from alu_ut( alu, 1, 0, ALU.ADD, 1 )
    yield from alu_ut( alu, 0xFFFFFFFF, 1, ALU.ADD, 0 )
    yield from alu_ut( alu, 29, 71, ALU.ADD, 100 )
    yield from alu_ut( alu, 0x80000000, 0x80000000, ALU.ADD, 0 )
    yield from alu_ut( alu, 0x7FFFFFFF, 0x7FFFFFFF, ALU.ADD, 0xFFFFFFFE )
    # Test the subtraction operation.
    print( "SUB (-) tests:" )
    yield from alu_ut( alu, 0, 0, ALU.SUB, 0 )
    yield from alu_ut( alu, 0, 1, ALU.SUB, -1 )
    yield from alu_ut( alu, 1, 0, ALU.SUB, 1 )
    yield from alu_ut( alu, -1, 1, ALU.SUB, -2 )
    yield from alu_ut( alu, 1, -1, ALU.SUB, 2 )
    yield from alu_ut( alu, 29, 71, ALU.SUB, -42 )
    yield from alu_ut( alu, 0x80000000, 1, ALU.SUB, 0x7FFFFFFF )
    yield from alu_ut( alu, 0x7FFFFFFF, -1, ALU.SUB, 0x80000000 )
    # Test the signed '<' comparison operation.
    print( "SLT (signed <) tests:" )
    yield from alu_ut( alu, 0, 0, ALU.SLT, 0 )
    yield from alu_ut( alu, 1, 0, ALU.SLT, 0 )
    yield from alu_ut( alu, 0, 1, ALU.SLT, 1 )
    yield from alu_ut( alu, -1, 0, ALU.SLT, 1 )
    yield from alu_ut( alu, -42, -10, ALU.SLT, 1 )
    yield from alu_ut( alu, -10, -42, ALU.SLT, 0 )
    # Test the unsigned '<' comparison operation.
    print( "SLTU (unsigned <) tests:" )
    yield from alu_ut( alu, 0, 0, ALU.SLTU, 0 )
    yield from alu_ut( alu, 1, 0, ALU.SLTU, 0 )
    yield from alu_ut( alu, 0, 1, ALU.SLTU, 1 )
    yield from alu_ut( alu, -1, 0, ALU.SLTU, 0 )
    yield from alu_ut( alu, -42, -10, ALU.SLTU, 1 )
    yield from alu_ut( alu, -10, -42, ALU.SLTU, 0 )
    yield from alu_ut( alu, -42, 42, ALU.SLTU, 0 )
    # Test the shift right operation.
    print ( "SRL (>>) tests:" )
    yield from alu_ut( alu, 0x00000001, 0, ALU.SRL, 0x00000001 )
    yield from alu_ut( alu, 0x00000001, 1, ALU.SRL, 0x00000000 )
    yield from alu_ut( alu, 0x00000011, 1, ALU.SRL, 0x00000008 )
    yield from alu_ut( alu, 0x00000010, 1, ALU.SRL, 0x00000008 )
    yield from alu_ut( alu, 0x80000000, 1, ALU.SRL, 0x40000000 )
    yield from alu_ut( alu, 0x80000000, 4, ALU.SRL, 0x08000000 )
    # Test the shift left operation.
    print ( "SLL (<<) tests:" )
    yield from alu_ut( alu, 0x00000001, 0, ALU.SLL, 0x00000001 )
    yield from alu_ut( alu, 0x00000001, 1, ALU.SLL, 0x00000002 )
    yield from alu_ut( alu, 0x00000011, 1, ALU.SLL, 0x00000022 )
    yield from alu_ut( alu, 0x00000010, 1, ALU.SLL, 0x00000020 )
    yield from alu_ut( alu, 0x80000000, 1, ALU.SLL, 0x00000000 )
    yield from alu_ut( alu, 0x00800000, 4, ALU.SLL, 0x08000000 )
    # Test the shift right with sign extension operation.
    print ( "SRA (>> + sign extend) tests:" )
    yield from alu_ut( alu, 0x00000001, 0, ALU.SRA, 0x00000001 )
    yield from alu_ut( alu, 0x00000001, 1, ALU.SRA, 0x00000000 )
    yield from alu_ut( alu, 0x00000011, 1, ALU.SRA, 0x00000008 )
    yield from alu_ut( alu, 0x00000010, 1, ALU.SRA, 0x00000008 )
    yield from alu_ut( alu, 0x80000000, 1, ALU.SRA, 0xC0000000 )
    yield from alu_ut( alu, 0x80000000, 4, ALU.SRA, 0xF8000000 )
    # Done.

    print( "ALU Tests: %d Passed, %d Failed"%( passed, failed ) )


if __name__ == '__main__':

    m = Module()
    m.submodules.alu = alu = Alu()

    sim = Simulator(m)
    
    def proc():
        yield from alu_test(alu)
    
    sim.add_process(proc)

    sim.run()
