import time
import random
import hashlib

class Algo:
    @staticmethod
    def calc_seqid():
        return round(time.time() * 4096 - 7201519810322) * 2048 + random.randint(0, 4095)
    @staticmethod
    def calc_hash(*args: str):
        p = b"\x00".join([ n.encode("utf-8") for n in args ])
        c = int.from_bytes(hashlib.md5(p).digest()[2:9], 'little')
        c = c & 0x7fff_ffff_ffff_ffff
        return c

algo = Algo()