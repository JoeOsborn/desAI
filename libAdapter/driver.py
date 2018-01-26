# type check: MYPYPATH=../../mypy-data/numpy-mypy mypy --py2 tester.py

from __future__ import print_function
import sys
import subprocess
import atexit
import struct
import io
import numpy as np
from typing import cast, Iterable, Dict, Tuple, List, Optional
from collections import namedtuple

# "Framebuffers" are always 256*240*4 rgb bytes for now

CmdStep = 0  # , //Infos NumPlayers NumMovesMSB NumMovesLSB MOVES
#           // -> steps emu. One FB, Audio per move
CmdGetState = 1  # , // -> state length, state
CmdLoadState = 2  # , //LoadState, infos, statelen, statebuf
#                // -> loads state; if infos & FB, sends framebuffer, if infos & Audio sends audio samples

InfoNone = 0
InfoFB = 1 << 0
InfoAudio = 1 << 1


class Move(object):
    B = 0
    Y = 1
    SELECT = 2
    START = 3
    UP = 4
    DOWN = 5
    LEFT = 6
    RIGHT = 7
    A = 8
    X = 9
    L = 10
    R = 11
    L2 = 12
    R2 = 13
    L3 = 14
    R3 = 15
    __slots__ = ("mask")

    def __init__(self, mask=0):
        self.mask = mask

    @classmethod
    def from_button_names(cls, **kwargs):
        btns = []
        for k, v in kwargs.items():
            if v:
                btns.append(getattr(cls, k))
        return cls.from_buttons(btns)

    @classmethod
    def from_buttons(cls, btns):
        mask = 0
        for b in btns:
            assert(0 <= b <= 15)
            mask = mask | (1 << b)
        return cls(mask)


def from_uint32(byte_slice):
    return struct.unpack("@I", byte_slice)[0]


def to_uint8(num):
    return struct.pack("@B", num)


def to_uint16(num):
    return struct.pack("@H", num)


def to_uint32(num):
    return struct.pack("@I", num)


PerFrame = namedtuple("PerFrame", ["framebuffer", "audio_samples"])
Infos = namedtuple("Infos", ["framebuffer", "audio"])
Infos.__new__.__defaults__ = (None,) * len(Infos._fields)


def infos_to_byte(infos):
    # type: (Infos) -> int
    mask = InfoNone
    if infos.framebuffer:
        mask |= InfoFB
    if infos.audio:
        mask |= InfoAudio
    return mask


def fm2_input_to_move(fm2_data):
    return Move.from_button_names(
        A='A' in fm2_data,
        B='B' in fm2_data,
        START='T' in fm2_data,
        SELECT='S' in fm2_data,
        UP='U' in fm2_data,
        DOWN='D' in fm2_data,
        LEFT='L' in fm2_data,
        RIGHT='R' in fm2_data)


def read_fm2(fm2_file):
    player_controls = {}
    with open(fm2_file, 'rb') as fm2_file:
        for line in fm2_file:
            line.rstrip()
            if line[0] == '|':
                controls = line.split('|')[2:-2]
                controls = [x for x in controls if x]
                for player, control in enumerate(controls):
                    if player not in player_controls:
                        player_controls[player] = []
                    player_controls[player].append(fm2_input_to_move(control))
    return [player_controls[player] for player in sorted(player_controls)]


class Driver(object):
    __slots__ = ("driver", "core", "rom", "process", "inp", "outp", "readbuf", "writebuf",
                 "num_players", "bytes_per_player", "framebuffer_length",
                 "framebuffer_height", "framebuffer_width", "framebuffer_depth")
    # TODO: type the above

    def __init__(self, driver, corefile, romfile, num_players=1, bytes_per_player=2, framebuffer_height=240, framebuffer_width=256, framebuffer_depth=4):
        # type: (str, str, int, int, int, int, int) -> None
        self.driver = driver
        self.core = corefile
        self.rom = romfile
        self.num_players = num_players
        assert self.num_players > 0
        self.bytes_per_player = bytes_per_player
        assert self.bytes_per_player == 2
        self.framebuffer_height = framebuffer_height
        self.framebuffer_width = framebuffer_width
        self.framebuffer_depth = framebuffer_depth
        self.framebuffer_length = self.framebuffer_height * self.framebuffer_width * self.framebuffer_depth
        assert self.framebuffer_height == 240
        assert self.framebuffer_width == 256
        assert self.framebuffer_depth == 4
        self.process = subprocess.Popen([self.driver, self.core, self.rom],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=sys.stdout,
                                        bufsize=0)
        self.inp = cast(io.BufferedWriter, io.open(self.process.stdin.fileno(), 'wb', closefd=False))
        self.outp = cast(io.BufferedReader, io.open(self.process.stdout.fileno(), 'rb', closefd=False))
        self.readbuf = memoryview(bytearray([0] * 1024 * 1024 * 32))
        self.writebuf = memoryview(bytearray([0] * 1024 * 1024))
        self.wait_ready()

    def __del__(self):
        # type: () -> None
        self.process.kill()

    def wait_ready(self):
        # type: () -> None
        assert self.outp.readinto(cast(bytearray, self.readbuf[:1])) == 1
        assert ord(self.readbuf[0]) == 0

    def step(self, move_gen, infos):
        # type: (Iterable[Iterable[Move]], Infos) -> Iterable[PerFrame]
        move_gens = list(move_gen)
        assert len(move_gens) == self.num_players
        moves = map(lambda m: list(m), move_gens)  # type: List[List[Move]]
        move_count = len(moves[0])
        move_bytes = move_count * self.num_players * self.bytes_per_player
        assert move_bytes < (len(self.writebuf) - 6)
        assert move_count < 2**16
        for move_list in moves:
            assert len(move_list) == move_count
        self.writebuf[0] = chr(CmdStep)
        self.writebuf[1] = chr(infos_to_byte(infos))
        self.writebuf[2] = chr(self.num_players)
        self.writebuf[4:6] = to_uint16(move_count)
        for i in range(move_count):
            for p in range(self.num_players):
                move_mask_bytes = to_uint16(moves[p][i].mask)
                player_start = 6 + i * self.num_players * self.bytes_per_player + p * self.bytes_per_player
                self.writebuf[player_start:player_start + self.bytes_per_player] = move_mask_bytes[0:self.bytes_per_player]
        self.inp.write(cast(bytearray, self.writebuf[:6 + move_bytes]))
        self.inp.flush()
        # read outputs from self.outp
        per_frames = []
        read_idx = 0
        for m in range(move_count):
            framebuffer = None  # type: Optional[np.ndarray[int]]
            audio = None  # type: Optional[np.ndarray[int]]
            if infos.framebuffer:
                assert self.outp.readinto(cast(bytearray, self.readbuf[:self.framebuffer_length])) == self.framebuffer_length
                framebuffer = cast(np.ndarray, np.array(self.readbuf[:self.framebuffer_length], copy=True, dtype=np.uint8).reshape((self.framebuffer_height, self.framebuffer_width, self.framebuffer_depth)))
            if infos.audio:
                # TODO audio buffers
                pass
            per_frames.append(PerFrame(framebuffer, audio))
        # read summary statistics if infos have them
        print("wait")
        self.wait_ready()
        print("ready")
        return per_frames
