#!/usr/bin/env python
#
# Copyright (c) 2012-2014 Poul-Henning Kamp <phk@phk.freebsd.dk>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

'''Lasat MultiCom modem controller

'''

from pyreveng import assy, mem, code, data, listing, discover, partition
from pyreveng import eyecandy
import pyreveng.cpu.i8086 as i8086
import pyreveng.cpu.i8086_switches as i8086_switches

NAME = "LaSat_2.50"

FILENAME = "CCU32_2.50.bin"

OUT_DIR = "/tmp/_" + NAME

SYMBOLS = {
    0x0266f: "pincode_buffer",
    0xe1f00: "?main()",
    0xe56ce: "?define_irq_vectors()",
    0xe58d4: "?ptr* get_init_msg(int)",
    0xe6d3e: "?serial_ansi_attrib(mode)",
    0xe6e12: "?serial_out(ptr*)",
    0xe6e64: "?serial_repeat(chr, count)",
    0xe6ea4: "?serial_out(count, ptr*)",
    0xf3420: "?config_80c188()",
    0xf3eb6: "?write_lcd(is_cmd, octet)",
    0xf3f1e: "?lcd_output(line, txt*)",
    0xf3fd4: "?lcd_show_cursor(line, pos)",
    0xf4294: "?seeprom(oper, nbit)",
    0xf443c: "?password_scrambler(len, ptr*)",
    0xf4906: "?putchar_port_A(chr)",
    0xf4c7a: "?putchar_port_B(chr)",
    0xf68c0: "?compare(len, ptr1*, ptr2*)",
    0xf6910: "?strlen(src*)",
    0xf6930: "?memcpy(dst*, src*, len)",
    0xf6960: "?strcpy(src*, dst*)",
    0xf6a40: "?fill(count, val, ptr*)",
    0xfff90: "?crt0(void)",
}

hack_desc = '''
les	x	| 2E		| C4		| 36		| lo		| hi		|
les	x	| 2E		| C4		| 1e		| lo		| hi		|
PUSHFAR	y	| B8		| lo		| hi		| 0E		| 50		|
PUSHFAR	z	| B8		| lo		| hi		| 1E		| 50		|
'''

hack_targets = set()
lcmt_targets = {}

class hack_ins(assy.Instree_ins):
    ''' ... '''

    def farref(self, seg, off):
        self.dstadr = (seg << 4) + off
        lcmt_targets[self.lo] = self.dstadr

    def assy_y(self):
        cs = self.lang.what_is_segment("cs", self.lo)
        if cs is not None:
            off = self['lo'] + (self['hi'] << 8)
            self.farref(cs, off)
        raise assy.Invalid("NO CS")

    def assy_z(self):
        ds = self.lang.what_is_segment("ds", self.lo)
        if ds is not None:
            off = self['lo'] + (self['hi'] << 8)
            self.farref(ds, off)
        raise assy.Invalid("NO DS")

    def assy_x(self):
        cs = self.lang.what_is_segment("cs", self.lo)
        if cs is not None:
            off = (self['hi'] << 8) | self['lo']
            dst = (cs << 4) + off
            z = list(self.lang.m.find(dst, dst+1))
            if len(z) == 0:
                y = FarPtr(self.lang.m, dst)
                if dst not in hack_targets:
                    hack_targets.add(dst)
                # print("LES", self, z, self.lang.what_is_segment("cs", self.lo), y)
            else:
                y = z[0]
            self.farref(cs, off)
        raise assy.Invalid("LES")

class FarPtr(data.Struct):

    def __init__(self, tree, lo):
        super().__init__(
            tree,
            lo,
            off_=data.Lu16,
            seg_=data.Lu16,
        )
        self.dstadr = (self.seg<<4) + self.off

    def render(self):
        yield "Far pointer 0x%04x:0x%04x = 0x%05x = %s" % (
            self.seg,
            self.off,
            self.dstadr,
            self.tree.adr(self.dstadr),
        )

def text_range(cx, lo, hi):
    while lo < hi:
        if cx.m[lo] == 0:
            lo += 1
            continue
        y = data.Text(cx.m, lo).insert()
        lo = y.hi
    return lo

def texts(cx, *args):
    for adr in args:
        data.Text(cx.m, adr).insert()

def manual(cx, *args):
    for adr in args:
        cx.disass(adr)
        cx.m.set_line_comment(adr, "Manual")

class CodeSegment():
    def __init__(self, cx, lo, hi, ds):
        assert (lo & 0xf) == 0
        assert (hi & 0xf) == 0
        self.cx = cx
        self.lo = lo
        self.hi = hi
        cx.m.set_block_comment(lo, "ASSUME CS 0x%04x" % (lo >> 4))
        cx.assume("cs", lo, hi, lo >> 4)
        if ds != 0:
            cx.assume("ds", lo, hi, ds)

    def __str__(self):
        return "<CS %05x-%05x>" % (self.lo, self.hi)

    def do_data(self):
        ''' ... '''

    def do_code(self):
        ''' ... '''

class CSe000(CodeSegment):

    def do_data(self):
        texts(self.cx, 0xe002c, 0xe003d)
        text_range(self.cx, 0xe0049, 0xe009c)
        FarPtr(self.cx.m, 0xe00fc).insert()
        FarPtr(self.cx.m, 0xe0100).insert()
        FarPtr(self.cx.m, 0xe0104).insert()

    def do_code(self):
        manual(
            self.cx,
            0xe01d8,
            0xe022e,
            0xe028a,
            0xe02d0,
            0xe03aa,
            0xe083d,
        )

class CSe215(CodeSegment):

    def do_data(self):
        data.Text(self.cx.m, 0xe219e).insert()
        data.Text(self.cx.m, 0xe21a2, 0xe21b2).insert()
        data.Text(self.cx.m, 0xe21b2, 0xe21b8).insert()
        data.Text(self.cx.m, 0xe21b8, 0xe21bc).insert()
        text_range(self.cx, 0xe2200, 0xe228e)
        FarPtr(self.cx.m, 0xe2394).insert()
        FarPtr(self.cx.m, 0xe239c).insert()
        FarPtr(self.cx.m, 0xe23a0).insert()
        FarPtr(self.cx.m, 0xe23a4).insert()

class CSe32b(CodeSegment):

    def do_data(self):
        FarPtr(self.cx.m, 0xe3386).insert()
        FarPtr(self.cx.m, 0xe338a).insert()

class CSe432(CodeSegment):

    def do_data(self):
        text_range(self.cx, 0xe4320, 0xe4348)

class CSe514(CodeSegment):

    def do_code(self):

        for where, vec, off, what in (
            (0xe56d7, 0x20, 0x9c, "TIMER0"),
            (0xe56eb, 0x28, 0x6c, "DMA0"),
            (0xe56ff, 0x2c, 0x84, "DMA1"),
            (0xe5713, 0x30, 0x2c6, "INT0"),
            (0xe5727, 0x34, 0x308, "INT1"),
            (0xe573b, 0x38, 0x452, "INT2"),
            (0xe574f, 0x3c, 0x4f0, "INT3"),
            (0xe5763, 0x48, 0xc6, "TIMER1"),
            (0xe5777, 0x4c, 0x124, "TIMER2"),
        ):
            fp = self.lo + off
            self.cx.m.set_label(where, "INIT_VECTOR_" + what)
            self.cx.disass(fp)
            self.cx.m.set_label(fp, "IRQ_" + what)

class CSe579(CodeSegment):

    def do_data(self):
        cs = self.lo
        #text_range(self.cx, 0xe5790, 0xe5858)
        y = data.Text(self.cx.m, cs + 0x1).insert()
        self.cx.m.set_label(y.lo, "init_msg_0")
        y = data.Text(self.cx.m, cs + 0x28).insert()
        self.cx.m.set_label(y.lo, "init_msg_1")
        y = data.Text(self.cx.m, cs + 0x4c).insert()
        self.cx.m.set_label(y.lo, "init_msg_2")
        y = data.Text(self.cx.m, cs + 0x76).insert()
        self.cx.m.set_label(y.lo, "init_msg_5")
        y = data.Text(self.cx.m, cs + 0x8b).insert()
        self.cx.m.set_label(y.lo, "init_msg_6")
        y = data.Text(self.cx.m, cs + 0xa3).insert()
        self.cx.m.set_label(y.lo, "init_msg_7")

        FarPtr(self.cx.m, 0xe58c4).insert()
        FarPtr(self.cx.m, 0xe58c8).insert()
        FarPtr(self.cx.m, 0xe58cc).insert()
        FarPtr(self.cx.m, 0xe58d0).insert()

class CSe5cb(CodeSegment):

    def do_code(self):
        manual(
            self.cx,
            0xe5ddc,
            0xe5efc,
            0xe60a0,
        )

class CSe612(CodeSegment):

    def do_data(self):
        data.Text(self.cx.m, 0xe6131).insert()

    def do_code(self):
        manual(
            self.cx,
            0xe615e,
        )

class CSe61c(CodeSegment):

    def do_data(self):
        text_range(self.cx, 0xe61c0, 0xe675b)
        text_range(self.cx, 0xe67a3, 0xe6bed)
        FarPtr(self.cx.m, 0xe6cda).insert()

    def do_code(self):
        manual(
            self.cx,
            0xe701a,
            0xe7cee,
            0xe8160,
            0xe84f6,
        )

class CSea44(CodeSegment):

    def do_data(self):
        text_range(self.cx, 0xea530, 0xeaf80)
        text_range(self.cx, 0xeafd1, 0xeb174)
        text_range(self.cx, 0xeb197, 0xeb1d1)
        text_range(self.cx, 0xeb1e2, 0xeb40d)
        text_range(self.cx, 0xeb44d, 0xeb5de)
        FarPtr(self.cx.m, 0xeb68e).insert()
        FarPtr(self.cx.m, 0xeb692).insert()

class CSeee8(CodeSegment):

    def do_data(self):
        text_range(self.cx, 0xeef38, 0xef19f)
        text_range(self.cx, 0xef1cf, 0xef36e)

class CSf053(CodeSegment):

    def do_data(self):
        text_range(self.cx, 0xf0530, 0xf05b8)

class CSf131(CodeSegment):

    def do_data(self):
        text_range(self.cx, 0xf16e0, 0xf1e78)
        FarPtr(self.cx.m, 0xf1fae).insert()
        FarPtr(self.cx.m, 0xf1fb2).insert()

class CSf342(CodeSegment):

    def do_data(self):
        self.cx.m.set_line_comment(0xf342c, "RELOCATION")
        self.cx.m.set_line_comment(0xf3433, "EDRAM")
        self.cx.m.set_line_comment(0xf3437, "CDRAM")
        self.cx.m.set_line_comment(0xf343b, "MDRAM")
        self.cx.m.set_line_comment(0xf343f, "POWER SAVE")
        self.cx.m.set_line_comment(0xf3446, "MID RANGE MEMORY SIZE")
        self.cx.m.set_line_comment(0xf344d, "MID RANGE MEMORY BASE")
        self.cx.m.set_line_comment(0xf3454, "PERIPHERAL BASE")
        self.cx.m.set_line_comment(0xf345b, "LOWER MEMORY SIZE")
        self.cx.m.set_line_comment(0xf3462, "UPPER MEMORY SIZE")
        self.cx.m.set_line_comment(0xf3469, "DMA 1 CONTROL WORD")
        self.cx.m.set_line_comment(0xf346d, "DMA 1 TRANSFER COUNT")
        self.cx.m.set_line_comment(0xf3471, "DMA 1 DST POINTER 1")
        self.cx.m.set_line_comment(0xf3475, "DMA 1 DST POINTER 2")
        self.cx.m.set_line_comment(0xf3479, "DMA 1 SRC POINTER 1")
        self.cx.m.set_line_comment(0xf347d, "DMA 1 SRC POINTER 2")
        self.cx.m.set_line_comment(0xf3481, "DMA 0 CONTROL WORD")
        self.cx.m.set_line_comment(0xf3485, "DMA 0 TRANSFER COUNT")
        self.cx.m.set_line_comment(0xf3489, "DMA 0 DST POINTER 1")
        self.cx.m.set_line_comment(0xf348d, "DMA 0 DST POINTER 2")
        self.cx.m.set_line_comment(0xf3491, "DMA 0 SRC POINTER 1")
        self.cx.m.set_line_comment(0xf3495, "DMA 0 SRC POINTER 2")
        self.cx.m.set_line_comment(0xf349c, "TIMER 2 CONTROL")
        self.cx.m.set_line_comment(0xf34a3, "TIMER 2 MAX COUNT")
        self.cx.m.set_line_comment(0xf34aa, "TIMER 2 COUNT")
        self.cx.m.set_line_comment(0xf34b1, "TIMER 1 CONTROL")
        self.cx.m.set_line_comment(0xf34b8, "TIMER 1 MAX COUNT B")
        self.cx.m.set_line_comment(0xf34bc, "TIMER 1 MAX COUNT A")
        self.cx.m.set_line_comment(0xf34c0, "TIMER 1 COUNT")
        self.cx.m.set_line_comment(0xf34c7, "TIMER 0 CONTROL")
        self.cx.m.set_line_comment(0xf34ce, "TIMER 0 MAX COUNT B")
        self.cx.m.set_line_comment(0xf34d2, "TIMER 0 MAX COUNT A")
        self.cx.m.set_line_comment(0xf34d6, "TIMER 0 COUNT")
        self.cx.m.set_line_comment(0xf34dd, "INT3 CONTROL")
        self.cx.m.set_line_comment(0xf34e1, "INT2 CONTROL")
        self.cx.m.set_line_comment(0xf34e5, "INT1 CONTROL")
        self.cx.m.set_line_comment(0xf34e9, "INT0 CONTROL")
        self.cx.m.set_line_comment(0xf34f0, "DMA1 CONTROL")
        self.cx.m.set_line_comment(0xf34f4, "DMA0 CONTROL")
        self.cx.m.set_line_comment(0xf34fb, "TIMER")
        self.cx.m.set_line_comment(0xf3502, "INTERRUPT STATUS")
        self.cx.m.set_line_comment(0xf3509, "INTERRUPT REQUEST")
        self.cx.m.set_line_comment(0xf350d, "IN-SERVICE")
        self.cx.m.set_line_comment(0xf3514, "PRIORITY MASK")
        self.cx.m.set_line_comment(0xf351b, "MASK")
        self.cx.m.set_line_comment(0xf3522, "EOI")

class CSf353(CodeSegment):

    def do_code(self):
        manual(
            self.cx,
            0xf3734,
            0xf375e,
            0xf36c6,
            0xf3c44,
        )

class CSf3d4(CodeSegment):

    def do_data(self):
        text_range(self.cx, 0xf3d4b, 0xf3d68)
        self.cx.m.set_line_comment(0xf3f46, "Disable LCD Cursor")
        self.cx.m.set_line_comment(0xf4013, "Enable LCD Cursor")

class CSf451(CodeSegment):

    def do_data(self):
        FarPtr(self.cx.m, 0xf4510).insert()
        
    def do_code(self):
        manual(
            self.cx,
            0xf4950,
            0xf4ae4,
            0xf4c36,
            0xf4cc4,
            0xf4dec,
        )

class CSf4fb(CodeSegment):

    def do_data(self):
        text_range(self.cx, 0xf5000, 0xf5024)

class CSfff9(CodeSegment):

    def do_data(self):
        self.cx.m.set_line_comment(0xfff90, "PCB.UMCS - upper memory")
        self.cx.m.set_line_comment(0xfff93, "128K, no wait states")
        self.cx.m.set_line_comment(0xfff97, "PCB.LMCS - lower memory")
        self.cx.m.set_line_comment(0xfff9a, "128K, no wait states")
        self.cx.m.set_line_comment(0xfff9e, "PCB.PACS - peripherals")
        self.cx.m.set_line_comment(0xfffa1, "IO at 0x400+N*0x80 (?)")
        self.cx.m.set_line_comment(0xfffa5, "PCB.MPCS - middle memory")
        self.cx.m.set_line_comment(0xfffa8, "512K total, 128K blocks")

class CSfffd(CodeSegment):

    def do_data(self):
        y = data.Lu16(self.cx.m, 0xfffd0).insert()
        self.cx.m.set_label(y.lo, "STACK_SEGMENT")
        y = data.Lu16(self.cx.m, 0xfffd2).insert()
        self.cx.m.set_label(y.lo, "DATA_SEGMENT")

class CSffff(CodeSegment):

    def do_code(self):
        self.cx.m.set_block_comment(0xffff0, "RESET VECTOR")


def example():
    m = mem.Stackup((FILENAME,))
    cx = i8086.i80186()
    i8086_switches.i8086_switches(cx)
    cx.add_ins(hack_desc, hack_ins)
    # cx.has_8087()
    cx.m.map(m, 0xe0000)

    for i, j in SYMBOLS.items():
        cx.m.set_label(i, j)

    seglist = []
    segs = [
        (0xe000, 0x0020, CSe000),
        (0xe215, 0x0266, CSe215),
        (0xe32b, 0x0266, CSe32b),
        (0xe432, 0x0266, CSe432),
        (0xe514, 0x0268, CSe514),
        (0xe579, 0x0268, CSe579),
        (0xe5cb, 0x0268, CSe5cb),
        (0xe612, 0x0269, CSe612),
        (0xe61c, 0x0269, CSe61c),
        (0xea44, 0x0272, CSea44),
        (0xeee8, 0x0276, CSeee8),
        (0xf053, 0x0277, CSf053),
        (0xf131, 0x0278, CSf131),
        (0xf342, 0x0290, CSf342),
        (0xf353, 0x0290, CSf353),
        (0xf385, 0x0291, CodeSegment),
        (0xf3bc, 0x0293, CodeSegment),
        (0xf3d4, 0x0295, CSf3d4),
        (0xf403, 0x029b, CodeSegment),
        (0xf415, 0x029b, CodeSegment),
        (0xf429, 0x029c, CodeSegment),
        (0xf451, 0x029d, CSf451),
        (0xf4fb, 0x04b7, CSf4fb),
        (0xf685, 0x0000, CodeSegment),
        (0xf68c, 0x0000, CodeSegment),
        (0xf691, 0x0000, CodeSegment),
        (0xf693, 0x0000, CodeSegment),
        (0xf696, 0x0000, CodeSegment),
        (0xf699, 0x0780, CodeSegment),
        (0xf69f, 0x0780, CodeSegment),
        (0xf6a4, 0x0000, CodeSegment),
        (0xfff9, 0x0000, CSfff9),
        (0xfffd, 0x0000, CSfffd),
        (0xffff, 0x0000, CSffff),
        (0x10000, 0x0000, CodeSegment),
    ]
    for n in range(len(segs) - 1):
        cs, ds, cls = segs[n]
        s = cls(cx, cs << 4, segs[n+1][0] << 4, ds)
        seglist.append(s)

    for seg in seglist:
        seg.do_data()

    cx.disass(0xffff0)

    for seg in seglist:
        seg.do_code()

    # discover.Discover(cx)
    #code.lcmt_flows(cx.m)

    for adr in sorted(hack_targets):
        z = list(cx.m.find(adr, adr+1))
        if len(z) == 0:
            FarPtr(cx.m, adr).insert()

    for adr,dst in sorted(lcmt_targets.items()):
        t = ["=> 0x%05x" % dst]
        for e in cx.m.find(dst, dst + 1):
            t += list(e.render())
        cx.m.set_line_comment(adr, " ".join(t))

    p = partition.Partition(cx.m)
    eyecandy.GraphVzPartition(p, output_dir=OUT_DIR)
    eyecandy.AddBlockComments(p)

    return NAME, (cx.m,)


if __name__ == '__main__':
    listing.Example(example, fn=OUT_DIR + "/disass.txt", ncol=8)
