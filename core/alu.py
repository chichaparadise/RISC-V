from nmigen import *
from nmigen.sim import *


ALU_ADD   = 0b0000
ALU_SUB   = 0b1000
ALU_SLT   = 0b0010
ALU_SLTU  = 0b0011
ALU_XOR   = 0b0100
ALU_OR    = 0b0110
ALU_AND   = 0b0111
ALU_SLL   = 0b0001
ALU_SRL   = 0b0101
ALU_SRA   = 0b1101


class Alu(Elaboratable):

    def __init__(self):
        self.rs1_val = Signal(32, reset=0x0000000)
        self.rs2_val = Signal(32, reset=0x0000000)
        self.funct = Signal(4, reset=0b0000)
        self.rd_val = Signal(32, reset=0x00000000)

    def elaborate(self, platform):
        m = Module()

        with m.Switch(self.funct[:4]):
            with m.Case(ALU_ADD):
                m.d.comb += self.rd_val.eq(self.rs1_val.as_signed() + self.rs2_val.as_signed())
            with m.Case(ALU_SUB):
                m.d.comb += self.rd_val.eq(self.rs1_val.as_signed() - self.rs2_val.as_signed())
            with m.Case(ALU_AND):
                m.d.comb += self.rd_val.eq(self.rs1_val & self.rs2_val)
            with m.Case(ALU_OR):
                m.d.comb += self.rd_val.eq(self.rs1_val | self.rs2_val)
            with m.Case(ALU_XOR):
                m.d.comb += self.rd_val.eq(self.rs1_val ^ self.rs2_val)
            with m.Case(ALU_SLT):
                m.d.comb += self.rd_val.eq(self.rs1_val.as_signed() < self.rs2_val.as_signed())
            with m.Case(ALU_SLTU):
                m.d.comb += self.rd_val.eq(self.rs1_val < self.rs2_val)
            with m.Case(ALU_SLL):
                m.d.comb += self.rd_val.eq(self.rs1_val << self.rs2_val[:5])
            with m.Case(ALU_SRL):
                m.d.comb += self.rd_val.eq(self.rs1_val >> self.rs2_val[:5])
            with m.Case(ALU_SRA):
                m.d.comb += self.rd_val.eq(self.rs1_val.as_signed() >> self.rs2_val[:5])

        return m
        

ALU_STRS = {
  ALU_ADD:  "+", ALU_SLT:  "<", ALU_SLTU: "<",
  ALU_XOR:  "^", ALU_OR:   "|", ALU_AND:  "&",
  ALU_SLL: "<<", ALU_SRL: ">>", ALU_SRA: ">>",
  ALU_SUB:  "-"
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
    if hexs(expected) != hexs(result):
        failed += 1
        print( "\033[31mFAIL:\033[0m %s %s %s = %s (got: %s)"
           %( hexs( val1 ), ALU_STRS[ funct ], hexs( val2 ),
              hexs( expected ), hexs( result ) ) )
    else:
        passed += 1
        print( "\033[32mPASS:\033[0m %s %s %s = %s"
           %( hexs( val1 ), ALU_STRS[ funct ],
              hexs( val2 ), hexs( expected ) ) )


def alu_test(alu):

    yield Settle()

    print( "AND (&) tests:" )

    yield from alu_ut( alu, 0xCCCCCCCC, 0xCCCC0000, ALU_AND, 0xCCCC0000 )
    yield from alu_ut( alu, 0x00000000, 0x00000000, ALU_AND, 0x00000000 )
    yield from alu_ut( alu, 0xFFFFFFFF, 0xFFFFFFFF, ALU_AND, 0xFFFFFFFF )
    yield from alu_ut( alu, 0x00000000, 0xFFFFFFFF, ALU_AND, 0x00000000 )
    yield from alu_ut( alu, 0xFFFFFFFF, 0x00000000, ALU_AND, 0x00000000 )
    # Test the bitwise 'OR' operation.
    print( "OR  (|) tests:" )
    yield from alu_ut( alu, 0xCCCCCCCC, 0xCCCC0000, ALU_OR, 0xCCCCCCCC )
    yield from alu_ut( alu, 0x00000000, 0x00000000, ALU_OR, 0x00000000 )
    yield from alu_ut( alu, 0xFFFFFFFF, 0xFFFFFFFF, ALU_OR, 0xFFFFFFFF )
    yield from alu_ut( alu, 0x00000000, 0xFFFFFFFF, ALU_OR, 0xFFFFFFFF )
    yield from alu_ut( alu, 0xFFFFFFFF, 0x00000000, ALU_OR, 0xFFFFFFFF )
    # Test the bitwise 'XOR' operation.
    print( "XOR (^) tests:" )
    yield from alu_ut( alu, 0xCCCCCCCC, 0xCCCC0000, ALU_XOR, 0x0000CCCC )
    yield from alu_ut( alu, 0x00000000, 0x00000000, ALU_XOR, 0x00000000 )
    yield from alu_ut( alu, 0xFFFFFFFF, 0xFFFFFFFF, ALU_XOR, 0x00000000 )
    yield from alu_ut( alu, 0x00000000, 0xFFFFFFFF, ALU_XOR, 0xFFFFFFFF )
    yield from alu_ut( alu, 0xFFFFFFFF, 0x00000000, ALU_XOR, 0xFFFFFFFF )
    # Test the addition operation.
    print( "ADD (+) tests:" )
    yield from alu_ut( alu, 0, 0, ALU_ADD, 0 )
    yield from alu_ut( alu, 0, 1, ALU_ADD, 1 )
    yield from alu_ut( alu, 1, 0, ALU_ADD, 1 )
    yield from alu_ut( alu, 0xFFFFFFFF, 1, ALU_ADD, 0 )
    yield from alu_ut( alu, 29, 71, ALU_ADD, 100 )
    yield from alu_ut( alu, 0x80000000, 0x80000000, ALU_ADD, 0 )
    yield from alu_ut( alu, 0x7FFFFFFF, 0x7FFFFFFF, ALU_ADD, 0xFFFFFFFE )
    # Test the subtraction operation.
    print( "SUB (-) tests:" )
    yield from alu_ut( alu, 0, 0, ALU_SUB, 0 )
    yield from alu_ut( alu, 0, 1, ALU_SUB, -1 )
    yield from alu_ut( alu, 1, 0, ALU_SUB, 1 )
    yield from alu_ut( alu, -1, 1, ALU_SUB, -2 )
    yield from alu_ut( alu, 1, -1, ALU_SUB, 2 )
    yield from alu_ut( alu, 29, 71, ALU_SUB, -42 )
    yield from alu_ut( alu, 0x80000000, 1, ALU_SUB, 0x7FFFFFFF )
    yield from alu_ut( alu, 0x7FFFFFFF, -1, ALU_SUB, 0x80000000 )
    # Test the signed '<' comparison operation.
    print( "SLT (signed <) tests:" )
    yield from alu_ut( alu, 0, 0, ALU_SLT, 0 )
    yield from alu_ut( alu, 1, 0, ALU_SLT, 0 )
    yield from alu_ut( alu, 0, 1, ALU_SLT, 1 )
    yield from alu_ut( alu, -1, 0, ALU_SLT, 1 )
    yield from alu_ut( alu, -42, -10, ALU_SLT, 1 )
    yield from alu_ut( alu, -10, -42, ALU_SLT, 0 )
    # Test the unsigned '<' comparison operation.
    print( "SLTU (unsigned <) tests:" )
    yield from alu_ut( alu, 0, 0, ALU_SLTU, 0 )
    yield from alu_ut( alu, 1, 0, ALU_SLTU, 0 )
    yield from alu_ut( alu, 0, 1, ALU_SLTU, 1 )
    yield from alu_ut( alu, -1, 0, ALU_SLTU, 0 )
    yield from alu_ut( alu, -42, -10, ALU_SLTU, 1 )
    yield from alu_ut( alu, -10, -42, ALU_SLTU, 0 )
    yield from alu_ut( alu, -42, 42, ALU_SLTU, 0 )
    # Test the shift right operation.
    print ( "SRL (>>) tests:" )
    yield from alu_ut( alu, 0x00000001, 0, ALU_SRL, 0x00000001 )
    yield from alu_ut( alu, 0x00000001, 1, ALU_SRL, 0x00000000 )
    yield from alu_ut( alu, 0x00000011, 1, ALU_SRL, 0x00000008 )
    yield from alu_ut( alu, 0x00000010, 1, ALU_SRL, 0x00000008 )
    yield from alu_ut( alu, 0x80000000, 1, ALU_SRL, 0x40000000 )
    yield from alu_ut( alu, 0x80000000, 4, ALU_SRL, 0x08000000 )
    # Test the shift left operation.
    print ( "SLL (<<) tests:" )
    yield from alu_ut( alu, 0x00000001, 0, ALU_SLL, 0x00000001 )
    yield from alu_ut( alu, 0x00000001, 1, ALU_SLL, 0x00000002 )
    yield from alu_ut( alu, 0x00000011, 1, ALU_SLL, 0x00000022 )
    yield from alu_ut( alu, 0x00000010, 1, ALU_SLL, 0x00000020 )
    yield from alu_ut( alu, 0x80000000, 1, ALU_SLL, 0x00000000 )
    yield from alu_ut( alu, 0x00800000, 4, ALU_SLL, 0x08000000 )
    # Test the shift right with sign extension operation.
    print ( "SRA (>> + sign extend) tests:" )
    yield from alu_ut( alu, 0x00000001, 0, ALU_SRA, 0x00000001 )
    yield from alu_ut( alu, 0x00000001, 1, ALU_SRA, 0x00000000 )
    yield from alu_ut( alu, 0x00000011, 1, ALU_SRA, 0x00000008 )
    yield from alu_ut( alu, 0x00000010, 1, ALU_SRA, 0x00000008 )
    yield from alu_ut( alu, 0x80000000, 1, ALU_SRA, 0xC0000000 )
    yield from alu_ut( alu, 0x80000000, 4, ALU_SRA, 0xF8000000 )
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
