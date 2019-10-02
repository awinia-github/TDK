'''
Created on Oct 2, 2019

@author: hoeren
'''
from math import pi
import struct

little_endian = '<'
big_endian = '>'

#                              C-type                 Bytes       range
c = b'c'                     # char                   1           0..255
b = -127                     # singed char            1           -128..127
B = 254                      # unsigned char          1           0..255
h = -32767                   # short signed integer   2           -32768..32767 
H = 65534                    # short unsigned integer 2           0..65535
i = -2147483647              # signed integer         4           -2147483648..2147483647
I = 4294967294               # unsinged integer       4           0..4294967295
l = -2147483647              # signed long            4           -2147483648..2147483647
L = 4294967294               # unsigned long          4           0..4294967295 
q = -36028797018963967       # signed long long       8           -36028797018963968..36028797018963967
Q = 18446744073709551614     # unsigned long long     8           0..18446744073709551615
f = pi                       # float                  4           N/A
d = pi                       # double (long float)    8           N/A
s = b' whatever in 25 bytes' # char[]                 /           N/A

fmt = "cbBhHiIlLqQfd25s"
le_fmt = little_endian + fmt
be_fmt = big_endian + fmt

if __name__ == '__main__':
    le_raw = struct.pack(le_fmt, c, b, B, h, H, i, I, l, L, q, Q, f, d, s)
    print("little endian raw data = '%s'\n" % le_raw)
    (c_ ,b_ ,B_ ,h_ ,H_, i_, I_, l_, L_, q_, Q_, f_, d_, s_) = struct.unpack(le_fmt, le_raw)
    (c__ ,b__ ,B__ ,h__ ,H__, i__, I__, l__, L__, q__, Q__, f__, d__, s__) = struct.unpack(be_fmt, le_raw)
    print('c : ', c, c_, c__)
    print('b : ', b, b_, b__)
    print('B : ', B, B_, B__)
    print('h : ', h, h_, h__)
    print('H : ', H, H_, H__)
    print('i : ', i, i_, i__)
    print('I : ', I, I_, I__)
    print('l : ', l, l_, l__)
    print('L : ', L, L_, L__)
    print('q : ', q, q_, q__)
    print('Q : ', Q, Q_, Q__)
    print('f : ', f, f_, f__)
    print('d : ', d, d_, d__)
    print('s : ', s, s_, s__)
    print('s : ', s, s_.decode('utf8').strip(), s__.decode('utf8').strip())

    