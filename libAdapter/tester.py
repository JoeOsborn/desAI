# type check: MYPYPATH=../../mypy-data/numpy-mypy mypy --py2 tester.py
# run: python tester.py
from __future__ import print_function
import subprocess
import atexit
import struct
import io
import numpy as np
from typing import cast, Iterable, Dict, Tuple, List, Optional
from driver import Driver, Infos
import driver


def dump_ppm(buf, fl):
    header = bytearray(b"P6\n {} {}\n 255\n".format(buf.shape[0], buf.shape[1]))
    ppmfile = open(fl, 'wb')
    ppmfile.write(header)

    for y in range(len(buf)):
        for x in range(len(buf[y])):
            ppmfile.write(bytearray([buf[y, x, 2], buf[y, x, 1], buf[y, x, 0]]))
    ppmfile.flush()
    ppmfile.close()


mario_controls = driver.read_fm2('Illustrative.fm2')

remo = Driver("./driver", "../cores/bnes-libretro/bnes_libretro.dylib", "mario.nes")
#remo = Driver("./driver", "../cores/nestopia/libretro/nestopia_libretro.dylib", "mario.nes")

startup = 500
results = remo.step([mario_controls[0][:startup]], Infos(framebuffer=False))
results = remo.step([mario_controls[0][startup:startup + 1]], Infos(framebuffer=True))

print("Steps done")

i = 0
for pf in results:
    if pf.framebuffer is not None:
        dump_ppm(pf.framebuffer, "out/out_" + str(i) + ".ppm")
    i += 1

# TODO: test save and load
