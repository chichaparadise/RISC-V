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

# BRANCH
class BRANCH:
    BEQ  = 0b000
    BNE  = 0b001
    BLT  = 0b100
    BGE  = 0b101
    BLTU = 0b110
    BGEU = 0b111