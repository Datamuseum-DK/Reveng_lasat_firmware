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

'''II Morrow Apollo 618C Loran - Navigation Processor
'''

from pyreveng import assy, mem, code, data, listing, discover, partition
from pyreveng import eyecandy
import pyreveng.cpu.i8086 as i8086
import pyreveng.cpu.i8086_switches as i8086_switches

NAME = "LaSat_2.50"

FILENAME = "CCU32_2.50.bin"

OUT_DIR = "/tmp/_" + NAME

SYMBOLS = {
    0xf6910: "?strlen(src*)",
    0xf6930: "?memcpy(dst*, src*, len)",
    0xf6960: "?strcpy(dst*, src*)",
}

les_desc = '''
les	x	| 2E		| C4		| 36		| lo		| hi		|
les	x	| 2E		| C4		| 1e		| lo		| hi		|
'''

les_targets = set()

class les_ins(assy.Instree_ins):
    ''' ... '''

    def assy_x(self):
        cs = self.lang.what_is_segment("cs", self.lo)
        if cs is not None:
            off = (self['hi'] << 8) | self['lo']
            dst = (cs << 4) + off
            z = list(self.lang.m.find(dst, dst+1))
            if len(z) == 0:
                if dst not in les_targets:
                    self.lang.m.set_line_comment(dst, "LES target")
                    les_targets.add(dst)
                y = FarPtr(self.lang.m, dst)
                # print("LES", self, z, self.lang.what_is_segment("cs", self.lo), y)
            else:
                y = z[0]
            self.lang.m.set_line_comment(self.lo, " ".join(y.render()))
        raise assy.Invalid("LES")

class FarPtr(data.Struct):

    def __init__(self, tree, lo):
        super().__init__(
            tree,
            lo,
            off_=data.Lu16,
            seg_=data.Lu16,
        )

def text_range(cx, lo, hi):
    while lo < hi:
        if cx.m[lo] == 0:
            lo += 1
            continue
        y = data.Text(cx.m, lo).insert()
        lo = y.hi
    return lo

def manual(cx, *args):
    for adr in args:
        cx.disass(adr)
        cx.m.set_line_comment(adr, "Manual")

def seg_e000(cx):
    text_range(cx, 0xe0049, 0xe009c)
    manual(
        cx,
        0xe01d8,
        0xe022e,
        0xe028a,
        0xe02d0,
        0xe03aa,
        0xe083d,
    )

def seg_e215(cx):
    text_range(cx, 0xe220a, 0xe228e)

def seg_e432(cx):
    text_range(cx, 0xe4320, 0xe4348)

    if False:
        cx.disass(0xe43d6)
        y = data.Array(7, data.Lu16, vertical=True)(cx.m, 0xe4402).insert()
        # y = data.Lu16(cx.m, 0xe4402).insert()
        cx.disass(0xe4410)
        cx.disass(0xe4495)
        cx.disass(0xe4506)
        cx.disass(0xe4535)

        cx.disass(0xe4579)

        cx.m.set_label(0xe4c8c, "L_e432:096c")
        cx.disass(0xe4c8c)

        cx.m.set_label(0xe4912, "L_e432:05f2")
        cx.disass(0xe4912)
        y = data.Array(7, data.Lu16, vertical=True)(cx.m, 0xe4946).insert()
        for i in y:
            cx.disass(0xe4320 + i.val)

        cx.m.set_label(0xe45b2, "L_e432:0292")
        cx.disass(0xe45b2)
        y = data.Array(7, data.Lu16, vertical=True)(cx.m, 0xe45e6).insert()
        for i in y:
            cx.disass(0xe4320 + i.val)


def seg_e514(cx):
    manual(
        cx,
        0xe51ac,
        0xe51c4,
        0xe51dc,
        0xe520c,
        0xe5264,
        0xe5264,
        0xe5406,
        0xe5448,
        0xe548a,
        0xe5592,
        0xe5630,
    )

def seg_e579(cx):
    text_range(cx, 0xe5790, 0xe5858)

def seg_e5cb(cx):
    for adr in (
        0xe5ddc,
        0xe5efc,
        0xe60a0,
    ):
        cx.disass(adr)
        cx.m.set_line_comment(adr, "Manual")

def seg_e612(cx):
    for adr in (
        0xe615e,
    ):
        cx.disass(adr)
        cx.m.set_line_comment(adr, "Manual")

def seg_e61c(cx):
    text_range(cx, 0xe61c0, 0xe675b)
    text_range(cx, 0xe67a3, 0xe6bed)
    for adr in (
        0xe701a,
        0xe7cee,
        0xe8160,
        0xe84f6,
    ):
        cx.disass(adr)
        cx.m.set_line_comment(adr, "Manual")

def seg_ea44(cx):
    text_range(cx, 0xea530, 0xeaf80)
    text_range(cx, 0xeafd1, 0xeb174)
    text_range(cx, 0xeb1e2, 0xeb40d)
    #text_range(cx, 0xeb44d, 0xeb511)
    text_range(cx, 0xeb44d, 0xeb5de)

def seg_eee8(cx):
    text_range(cx, 0xeef38, 0xef19f)
    text_range(cx, 0xef1d5, 0xef362)

def seg_f053(cx):
    text_range(cx, 0xf0530, 0xf05b8)

def seg_f131(cx):
    text_range(cx, 0xf16e0, 0xf1e78)

def seg_f353(cx):
    manual(
        cx,
        0xf3734,
        0xf36c6,
    )

def seg_f3d4(cx):
    text_range(cx, 0xf3d4b, 0xf3d68)

def seg_f451(cx):
    manual(
        cx,
        0xf4950,
        0xf4ae4,
        0xf4c36,
        0xf4cc4,
        0xf4dec,
    )

def seg_f4fb(cx):
    text_range(cx, 0xf5000, 0xf5024)

def example():
    m = mem.Stackup((FILENAME,))
    cx = i8086.i80186()
    i8086_switches.i8086_switches(cx)
    cx.add_ins(les_desc, les_ins)
    # cx.has_8087()
    cx.m.map(m, 0xe0000)

    segs = [
        0xe000,
        0xe215,
        0xe432,
        0xe514,
        0xe579,
        0xe5cb,
        0xe612,
        0xe61c,
        0xea44,
        0xeee8,
        0xf053,
        0xf131,
        0xf342,
        0xf353,
        0xf385,
        0xf3bc,
        0xf3d4,
        0xf403,
        0xf415,
        0xf429,
        0xf451,
        0xf4fb,
        0xf68c,
        0xf691,
        0xf693,
        0xf696,
        0xf699,
        0xf6a4,
        0x10000,
    ]
    for n in range(len(segs) - 1):
        seg = segs[n]
        cx.m.set_block_comment(seg << 4, "ASSUME CS 0x%04x" % seg)
        cx.assume("cs", seg << 4, segs[n+1] << 4, seg)

    cx.disass(0xffff0)

    seg_e000(cx)
    seg_e215(cx)
    seg_e432(cx)
    seg_e514(cx)
    seg_e579(cx)
    seg_e5cb(cx)
    seg_e612(cx)
    seg_e61c(cx)
    seg_ea44(cx)
    seg_eee8(cx)
    seg_f053(cx)
    seg_f131(cx)
    seg_f353(cx)
    seg_f3d4(cx)
    seg_f451(cx)
    seg_f4fb(cx)

    for i, j in SYMBOLS.items():
        cx.m.set_label(i, j)

    #discover.Discover(cx)
    #code.lcmt_flows(cx.m)

    for adr in sorted(les_targets):
        z = list(cx.m.find(adr, adr+1))
        if len(z) == 0:
            FarPtr(cx.m, adr).insert()

    p = partition.Partition(cx.m)
    eyecandy.GraphVzPartition(p, output_dir=OUT_DIR)
    eyecandy.AddBlockComments(p)

    return NAME, (cx.m,)


if __name__ == '__main__':
    listing.Example(example, fn=OUT_DIR + "/disass.txt", ncol=8)
