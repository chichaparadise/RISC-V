from enum import Enum

# OP CODES
class OP:
    LUI    = 0b0110111
    AUIPC  = 0b0010111
    JAL    = 0b1101111
    JALR   = 0b1100111
    BRANCH = 0b1100011
    LOAD   = 0b0000011
    STORE  = 0b0100011
    REG    = 0b0110011
    IMM    = 0b0010011

# ALU
class ALU:
    ADD   = 0b0000
    SUB   = 0b1000
    SLT   = 0b0010
    SLTU  = 0b0011
    XOR   = 0b0100
    OR    = 0b0110
    AND   = 0b0111
    SLL   = 0b0001
    SRL   = 0b0101
    SRA   = 0b1101


class IType(Enum):
    ALU = 1
    LD = 2
    ST = 3
    J = 4
    JR = 5
    BR = 6
    AUIPC = 7


class Width:
    BYTE = 0b000
    HALF = 0b001
    WORD = 0b010
    BYTEU = 0b100
    HALFU = 0b101

# BRANCH
class BRANCH:
    BEQ  = 0b000
    BNE  = 0b001
    BLT  = 0b100
    BGE  = 0b101
    BLTU = 0b110
    BGEU = 0b111

def hexs( num ):
  if num >= 0:
    return "0x%08X"%( num )
  else:
    return "0x%08X"%( ( num + ( 1 << 32 ) ) % ( 1 << 32 ) )


# R-type operation: Rc = Ra ? Rb
# The '?' operation depends on the opcode, funct3, and funct7 bits.
def RV32I_R( op, f, ff, c, a, b ):
  return ( ( op & 0x7F ) |
         ( ( c  & 0x1F ) << 7  ) |
         ( ( f  & 0x07 ) << 12 ) |
         ( ( a  & 0x1F ) << 15 ) |
         ( ( b  & 0x1F ) << 20 ) |
         ( ( ff & 0x7C ) << 25 ) )
# I-type operation: Rc = Ra ? Immediate
# The '?' operation depends on the opcode and funct3 bits.
def RV32I_I( op, f, c, a, i ):
  return ( ( op & 0x7F  ) |
         ( ( c  & 0x1F  ) << 7  ) |
         ( ( f  & 0x07  ) << 12 ) |
         ( ( a  & 0x1F  ) << 15 ) |
         ( ( i  & 0xFFF ) << 20 ) )
# S-type operation: Store Rb in Memory[ Ra + Immediate ]
# The funct3 bits select whether to store a byte, half-word, or word.
def RV32I_S( op, f, a, b, i ):
  return ( ( op & 0x7F ) |
         ( ( i  & 0x1F ) << 7  ) |
         ( ( f  & 0x07 ) << 12 ) |
         ( ( a  & 0x1F ) << 15 ) |
         ( ( b  & 0x1F ) << 20 ) |
         ( ( ( i >> 5 ) & 0x7C ) ) )
# B-type operation: Branch to (PC + Immediate) if Ra ? Rb.
# The '?' compare operation depends on the funct3 bits.
# Note: the 12-bit immediate represents a 13-bit value with LSb = 0.
# This function accepts the 12-bit representation as an argument.
def RV32I_B( op, f, a, b, i ):
  return ( ( op & 0x7F ) |
         ( ( ( i >> 10 ) & 0x01 ) << 7  ) |
         ( ( ( i ) & 0x0F ) << 8 ) |
         ( ( f  & 0x07 ) << 12 ) |
         ( ( a  & 0x1F ) << 15 ) |
         ( ( b  & 0x1F ) << 20 ) |
         ( ( ( i >> 4  ) & 0x3F ) << 25 ) |
         ( ( ( i >> 11 ) & 0x01 ) << 31 ) )
# U-type operation: Load the 20-bit immediate into the most
# significant bits of Rc, setting the 12 least significant bits to 0.
# The opcode selects between LUI and AUIPC; AUIPC also adds the
# current PC address to the result which is stored in Rc.
def RV32I_U( op, c, i ):
  return ( ( op & 0x7F ) |
         ( ( c  & 0x1F ) << 7 ) |
         ( ( i & 0xFFFFF000 ) ) )
# J-type operation: In the base RV32I spec, this is only used by JAL.
# Jumps to (PC + Immediate) and stores (PC + 4) in Rc. The 20-bit
# immediate value represents a 21-bit value with LSb = 0; this
# function takes the 20-bit representation as an argument.
def RV32I_J( op, c, i ):
  return ( ( op & 0x7F ) |
         ( ( c  & 0x1F ) << 7 ) |
         ( ( ( i >> 11 ) & 0xFF ) << 12 ) |
         ( ( ( i >> 10 ) & 0x01 ) << 20 ) |
         ( ( ( i ) & 0x3FF ) << 21 ) |
         ( ( ( i >> 19 ) & 0x01 ) << 31 ) )

# Functions to assemble individual instructions.
# R-type operations:
def ADD( c, a, b ):
  return RV32I_R( OP.REG, ALU.ADD, 0b0, c, a, b )
def SUB( c, a, b ):
  return RV32I_R( OP.REG, ALU.SUB, 0b0100000, c, a, b )
def SLL( c, a, b ):
  return RV32I_R( OP.REG, ALU.SLL, 0b0000000, c, a, b )
def SLT( c, a, b ):
  return RV32I_R( OP.REG, ALU.SLT, 0b0000000, c, a, b )
def SLTU( c, a, b ):
  return RV32I_R( OP.REG, ALU.SLTU, 0b0000000, c, a, b )
def XOR( c, a, b ):
  return RV32I_R( OP.REG, ALU.XOR, 0b0000000, c, a, b )
def SRL( c, a, b ):
  return RV32I_R( OP.REG, ALU.SRL, 0b0000000, c, a, b )
def SRA( c, a, b ):
  return RV32I_R( OP.REG, ALU.SRA, 0b0100000, c, a, b )
def OR( c, a, b ):
  return RV32I_R( OP.REG, ALU.OR, 0b0000000, c, a, b )
def AND( c, a, b ):
  return RV32I_R( OP.REG, ALU.AND, 0b0000000, c, a, b )
# Special case: immediate shift operations use
# 5-bit immediates, structured as an R-type operation.
def SLLI( c, a, i ):
  return RV32I_R( OP.IMM, ALU.SLL, 0b0000000, c, a, i )
def SRLI( c, a, i ):
  return RV32I_R( OP.IMM, ALU.SRL, 0b0000000, c, a, i )
def SRAI( c, a, i ):
  return RV32I_R( OP.IMM, ALU.SRA, 0b0100000, c, a, i )
# I-type operations:
def JALR( c, a, i ):
  return RV32I_I( OP.JALR, 0b000, c, a, i )
# def LB( c, a, i ):
#   return RV32I_I( OP.LOAD, ALU.LB, c, a, i )
# def LH( c, a, i ):
#   return RV32I_I( OP.LOAD, ALU.LH, c, a, i )
# def LW( c, a, i ):
#   return RV32I_I( OP.LOAD, ALU.LW, c, a, i )
# def LBU( c, a, i ):
#   return RV32I_I( OP.LOAD, ALU.LBU, c, a, i )
# def LHU( c, a, i ):
#   return RV32I_I( OP.LOAD, ALU.LHU, c, a, i )
def ADDI( c, a, i ):
  return RV32I_I( OP.IMM, ALU.ADD, c, a, i )
def SLTI( c, a, i ):
  return RV32I_I( OP.IMM, ALU.SLT, c, a, i )
def SLTIU( c, a, i ):
  return RV32I_I( OP.IMM, ALU.SLTU, c, a, i )
def XORI( c, a, i ):
  return RV32I_I( OP.IMM, ALU.XOR, c, a, i )
def ORI( c, a, i ):
  return RV32I_I( OP.IMM, ALU.OR, c, a, i )
def ANDI( c, a, i ):
  return RV32I_I( OP.IMM, ALU.AND, c, a, i )
# S-type operations:
# def SB( a, b, i ):
#   return RV32I_S( OP.STORE, ALU.SB, a, b, i )
# def SH( a, b, i ):
#   return RV32I_S( OP.STORE, ALU.SH, a, b, i )
def SW( a, b, i ):
  return RV32I_S( OP.STORE, Width.WORD, a, b, i )
# B-type operations:
def BEQ( a, b, i ):
  return RV32I_B( OP.BRANCH, BRANCH.BEQ, a, b, i )
def BNE( a, b, i ):
  return RV32I_B( OP.BRANCH, BRANCH.BNE, a, b, i )
def BLT( a, b, i ):
  return RV32I_B( OP.BRANCH, BRANCH.BLT, a, b, i )
def BGE( a, b, i ):
  return RV32I_B( OP.BRANCH, BRANCH.BGE, a, b, i )
def BLTU( a, b, i ):
  return RV32I_B( OP.BRANCH, BRANCH.BLTU, a, b, i )
def BGEU( a, b, i ):
  return RV32I_B( OP.BRANCH, BRANCH.BGEU, a, b, i )
# U-type operations:
def LUI( c, i ):
  return RV32I_U( OP.LUI, c, i )
def AUIPC( c, i ):
  return RV32I_U( OP.AUIPC, c, i )
# J-type operation:
def JAL( c, i ):
  return RV32I_J( OP.JAL, c, i )


def LI( c, i ):
  if ( ( i & 0x0FFF ) & 0x0800 ):
    return LUI( c, ( ( i >> 12 ) + 1 ) << 12 ), \
           ADDI( c, c, ( i & 0x0FFF ) )
  else:
    return LUI( c, i ), ADDI( c, c, ( i & 0x0FFF ) )
def NOP():
  return ADDI( 0, 0, 0x000 )

def rom_img( arr ):
  a = []
  for i in arr:
    if type( i ) == tuple:
      for j in i:
        a.append( j )
    else:
      a.append( i )
  return a

def ram_img( arr ):
  a = []
  for i in arr:
    a.append( i )
  return a