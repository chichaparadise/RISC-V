from math import ceil, log2
from nmigen import *
from nmigen.sim import *
from nmigen_soc.wishbone.bus import Arbiter, Interface, MemoryMap


class RAM(Elaboratable):
    def __init__(self, size_words, data=None):
        self.size = size_words * 4
        self.mem = Memory(
            width=32,
            depth=size_words,
            init=data if data else ( 0x00000000 for i in range( size_words ) )
        )
        self.read_port = self.mem.read_port()
        self.write_port = self.mem.write_port()
        self.arb = Arbiter(addr_width=ceil(log2(self.size + 1)),
                           data_width=32)
        self.arb.bus.memory_map = MemoryMap(
            addr_width = self.arb.bus.addr_width,
            data_width = self.arb.bus.data_width,
            alignment = 0 )
        self.funct3 = Signal(3)

    def elaborate(self, platform):
        m = Module()

        # bus = Interface(addr_width=self.arb.bus.addr_width,
        #                 data_width=self.arb.bus.data_width)
        # self.arb.add(bus)

        m.submodules.read_port = self.read_port
        m.submodules.write_port = self.write_port
        m.submodules.arb = self.arb

        rws = Signal(1, reset=0)
        m.d.sync += rws.eq(self.arb.bus.cyc)
        m.d.sync += self.arb.bus.ack.eq(self.arb.bus.cyc & rws)

        m.d.comb += [
            self.read_port.addr.eq(self.arb.bus.adr >> 2),
            self.write_port.addr.eq(self.arb.bus.adr >> 2),
            self.write_port.en.eq(self.arb.bus.we)
        ]

        # with m.Switch(self.funct3):
        #     with m.Case(Width.BYTE):
        #         m.d.sync += self.arb.bus.dat_r.eq(self.read_port.data >> 4)


        m.d.sync += self.arb.bus.dat_r.eq(self.read_port.data)
        m.d.comb += self.write_port.data.eq(self.arb.bus.dat_w)

        return m


p = 0
f = 0

# Perform an individual RAM write unit test.


def ram_write_ut(ram, address, data, dw, success):
    global p, f
    # Set addres, 'din', and 'wen' signals.
    yield ram.arb.bus.adr.eq(address)
    yield ram.arb.bus.dat_w.eq(data)
    yield ram.arb.bus.we.eq(1)
    # yield ram.dw.eq( dw )
    # Wait three ticks, and un-set the 'wen' bit.
    yield Tick()
    yield Tick()
    yield Tick()
    yield ram.arb.bus.we.eq(0)
    # Done. Check that the 'din' word was successfully set in RAM.
    yield Settle()
    actual = yield ram.arb.bus.dat_r
    if success:
        if data != actual:
            f += 1
            print("\033[31mFAIL:\033[0m RAM[ 0x%08X ]  = "
                  "0x%08X (got: 0x%08X)"
                  % (address, data, actual))
        else:
            p += 1
            print("\033[32mPASS:\033[0m RAM[ 0x%08X ]  = 0x%08X"
                  % (address, data))
    else:
        if data != actual:
            p += 1
            print("\033[32mPASS:\033[0m RAM[ 0x%08X ] != 0x%08X"
                  % (address, data))
        else:
            f += 1
            print("\033[31mFAIL:\033[0m RAM[ 0x%08X ] != "
                  "0x%08X (got: 0x%08X)"
                  % (address, data, actual))
    yield Tick()

    # Perform an inidividual RAM read unit test.


def ram_read_ut(ram, address, expected):
    global p, f
    # Set address.
    yield ram.arb.bus.adr.eq(address)
    # Wait three ticks.
    yield Tick()
    yield Tick()
    yield Tick()
    # Done. Check the 'dout' result after combinational logic settles.
    yield Settle()
    actual = yield ram.arb.bus.dat_r
    if expected != actual:
        f += 1
        print("\033[31mFAIL:\033[0m RAM[ 0x%08X ] == "
              "0x%08X (got: 0x%08X)"
              % (address, expected, actual))
    else:
        p += 1
        print("\033[32mPASS:\033[0m RAM[ 0x%08X ] == 0x%08X"
              % (address, expected))

    # Top-level RAM test method.


def ram_test(ram):
    global p, f

    # Print a test header.
    print("--- RAM Tests ---")

    # Assert 'cyc' to activate the bus.
    yield ram.arb.bus.cyc.eq(1)
    yield Tick()
    yield Settle()

    # Test writing data to RAM.
    # yield from ram_write_ut(ram, 0x00, 0x01234567, RAM_DW_32, 1)
    # yield from ram_write_ut(ram, 0x0C, 0x89ABCDEF, RAM_DW_32, 1)
    # # Test reading data back out of RAM.
    # yield from ram_read_ut(ram, 0x00, 0x01234567)
    # yield from ram_read_ut(ram, 0x04, 0x00000000)
    # yield from ram_read_ut(ram, 0x0C, 0x89ABCDEF)
    # Test byte-aligned and halfword-aligend reads.
    # yield from ram_read_ut(ram, 0x01, 0x00012345)
    # yield from ram_read_ut(ram, 0x02, 0x00000123)
    # yield from ram_read_ut(ram, 0x03, 0x00000001)
    # yield from ram_read_ut(ram, 0x07, 0x00000000)
    # yield from ram_read_ut(ram, 0x0D, 0x0089ABCD)
    # yield from ram_read_ut(ram, 0x0E, 0x000089AB)
    # yield from ram_read_ut(ram, 0x0F, 0x00000089)
    # # Test byte-aligned and halfword-aligned writes.
    # yield from ram_write_ut(ram, 0x01, 0xDEADBEEF, RAM_DW_32, 0)
    # yield from ram_write_ut(ram, 0x02, 0xDEC0FFEE, RAM_DW_32, 0)
    # yield from ram_write_ut(ram, 0x03, 0xFABFACEE, RAM_DW_32, 0)
    # yield from ram_write_ut(ram, 0x00, 0xAAAAAAAA, RAM_DW_32, 1)
    # yield from ram_write_ut(ram, 0x01, 0xDEADBEEF, RAM_DW_8, 0)
    # yield from ram_read_ut(ram, 0x00, 0xAAAAEFAA)
    # yield from ram_write_ut(ram, 0x00, 0xAAAAAAAA, RAM_DW_32, 1)
    # yield from ram_write_ut(ram, 0x02, 0xDEC0FFEE, RAM_DW_16, 0)
    # yield from ram_read_ut(ram, 0x00, 0xFFEEAAAA)
    # yield from ram_write_ut(ram, 0x00, 0xAAAAAAAA, RAM_DW_32, 1)
    # yield from ram_write_ut(ram, 0x01, 0xDEC0FFEE, RAM_DW_16, 0)
    # yield from ram_read_ut(ram, 0x00, 0xAAFFEEAA)
    # yield from ram_write_ut(ram, 0x00, 0xAAAAAAAA, RAM_DW_32, 1)
    # yield from ram_write_ut(ram, 0x03, 0xDEADBEEF, RAM_DW_8, 0)
    # yield from ram_read_ut(ram, 0x00, 0xEFAAAAAA)
    # yield from ram_write_ut(ram, 0x03, 0xFABFACEE, RAM_DW_32, 0)
    # # Test byte and halfword writes.
    # yield from ram_write_ut(ram, 0x00, 0x0F0A0B0C, RAM_DW_32, 1)
    # yield from ram_write_ut(ram, 0x00, 0xDEADBEEF, RAM_DW_8, 0)
    # yield from ram_read_ut(ram, 0x00, 0x0F0A0BEF)
    # yield from ram_write_ut(ram, 0x60, 0x00000000, RAM_DW_32, 1)
    # yield from ram_write_ut(ram, 0x10, 0x0000BEEF, RAM_DW_8, 0)
    # yield from ram_read_ut(ram, 0x10, 0x000000EF)
    # yield from ram_write_ut(ram, 0x20, 0x000000EF, RAM_DW_8, 1)
    # yield from ram_write_ut(ram, 0x40, 0xDEADBEEF, RAM_DW_16, 0)
    # yield from ram_read_ut(ram, 0x40, 0x0000BEEF)
    # yield from ram_write_ut(ram, 0x50, 0x0000BEEF, RAM_DW_16, 1)
    # # Test reading from the last few bytes of RAM.
    # yield from ram_write_ut(ram, ram.size - 4, 0x01234567, RAM_DW_32, 1)
    # yield from ram_read_ut(ram, ram.size - 4, 0x01234567)
    # yield from ram_read_ut(ram, ram.size - 3, 0x00012345)
    # yield from ram_read_ut(ram, ram.size - 2, 0x00000123)
    # yield from ram_read_ut(ram, ram.size - 1, 0x00000001)
    # # Test writing to the end of RAM.
    # yield from ram_write_ut(ram, ram.size - 4, 0xABCDEF89, RAM_DW_32, 1)
    # yield from ram_write_ut(ram, ram.size - 3, 0x00000012, RAM_DW_8, 0)
    # yield from ram_read_ut(ram, ram.size - 4, 0xABCD1289)
    # yield from ram_write_ut(ram, ram.size - 4, 0xABCDEF89, RAM_DW_32, 1)
    # yield from ram_write_ut(ram, ram.size - 3, 0x00003412, RAM_DW_16, 0)
    # yield from ram_read_ut(ram, ram.size - 4, 0xAB341289)
    # yield from ram_write_ut(ram, ram.size - 4, 0xABCDEF89, RAM_DW_32, 1)
    # yield from ram_write_ut(ram, ram.size - 1, 0x00000012, RAM_DW_8, 1)
    # yield from ram_read_ut(ram, ram.size - 4, 0x12CDEF89)
    # yield from ram_write_ut(ram, ram.size - 4, 0xABCDEF89, RAM_DW_32, 1)

    # Done.
    yield Tick()
    print("RAM Tests: %d Passed, %d Failed" % (p, f))

    # 'main' method to run a basic testbench.
if __name__ == "__main__":
    # Instantiate a test RAM module with 128 bytes of data.
    dut = RAM(1024)
    # Run the RAM tests.
    sim = Simulator(dut)

    def proc():
        yield from ram_test(dut)
    sim.add_clock(1e-6)
    sim.add_sync_process(proc)
    sim.run()
