from core.cpu import CPU
import os
from nmigen.sim import *

BIN_FILE = os.environ.get('mem_file')


def read_prog(path):
    prog = []
    with open(path, 'rb') as f:
        while True:
            b = f.read(4)
            if b == b'':
                break
            i = int.from_bytes(b, byteorder='little', signed=False)
            prog.append(i)
    return prog

prog = read_prog(BIN_FILE)
cpu = CPU(reset_address=0x0000_0200, data=prog)
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
    for _ in range(len(prog)):
        yield from step()

    res = yield cpu.regs.mem[28]
    pc = yield cpu.pc
    print('-'*20, '\n')
    if res == 0:
        print('PASSED')
    else:
        print('FAILED')
    print(f'STEPS: {pc}')
    print('\n', '-'*20)

sim.add_clock(1e-6)
sim.add_sync_process(proc)
sim.run()