# -*- coding: utf-8 -*-

#
# References: 
#   https://docs.python.org/3/howto/unicode.html
#
# Mnemonic:
#
#        ---encode-->
#    str               bytes 
#        <--decode---
# 
# Tips:
#
#   * stay with the default utf-8 encoding (because utf-8 is endian agnostic)
#   

import sys, os

if sys.version_info < (3, 5):
    this_file = __file__.split(os.path.sep)[-1]
    this_python = "%s.%s.%s" % tuple(list(sys.version_info)[:3])
    raise Exception("'%s' needs a mature Python 3 engine, got %s" % \
                    (this_file, this_python))


street_as_str = "Hans-Bunte-Straße 19"
name_as_str = "Tom Hören"

arrows = "←↑→↓↔↕↨"
accents = "àáâãäçèéêëö"
greek = "ABΓΔEZHΘIKΛMNΞOΠPΣTϒΦXΨΩ αβγδϵζηθικλμνξoπρστυϕχψω"
fractions = "½ ⅓ ⅔ ¼ ¾ ⅕ ⅖ ⅗ ⅘ ⅙ ⅚ ⅛ ⅜ ⅝ ⅞"
symbols = "~ ≈ ≠ ≤ ≥ « » ‹ › ‰ ∞ № º ÷ ± ° € § Ø ø Œ © ®"
boxdraw = "─ │ ┌ ┐└ ┘"
bell = '\x07' # depends on console if you hear this one

if __name__ == '__main__':
    print("-" * 79)
    print("u'%s' holds %s characters" % (street_as_str(street_as_str)))
    print("u'%s' holds %s characters" % (street_as_str.casefold(), len(street_as_str.casefold())))
    print("u'%s' holds %s characters" % (name_as_str, len(name_as_str)))
    print("u'%s' holds %s characters" % (name_as_str.casefold(), len(name_as_str.casefold())))
    street_as_bytes = street_as_str.encode()
    street_as_bytes_casefolded = street_as_str.casefold().encode()
    name_as_bytes = name_as_str.encode()
    name_as_bytes_casefolded = name_as_str.casefold().encode()
    print("-" * 79)
    print("%s holds %s bytes" % (street_as_bytes, len(street_as_bytes)))
    print("%s holds %s bytes" % (street_as_bytes_casefolded, len(street_as_bytes_casefolded)))
    print("%s holds %s bytes" % (name_as_bytes, len(name_as_bytes)))
    print("%s holds %s bytes" % (name_as_bytes_casefolded, len(name_as_bytes_casefolded)))
    street_as_str_from_bytes = street_as_bytes.decode('utf-8')
    street_as_str_from_bytes_casefolded = street_as_bytes_casefolded.decode('utf-8')
    name_as_str_from_bytes = name_as_bytes.decode('utf-8')
    name_as_str_from_bytes_casefolded = name_as_bytes_casefolded.decode('utf-8')
    print("-" * 79)
    print("u'%s' holds %s characters" % (street_as_str_from_bytes, len(street_as_str_from_bytes)))
    print("u'%s' holds %s characters" % (street_as_str_from_bytes_casefolded, len(street_as_str_from_bytes_casefolded)))
    print("u'%s' holds %s characters" % (name_as_str_from_bytes, len(name_as_str_from_bytes)))
    print("u'%s' holds %s characters" % (name_as_str_from_bytes_casefolded, len(name_as_str_from_bytes_casefolded)))
    assert street_as_str == street_as_str_from_bytes
    assert street_as_str.casefold() == street_as_str_from_bytes_casefolded
    assert name_as_str == name_as_str_from_bytes
    assert name_as_str.casefold() == name_as_str_from_bytes_casefolded
    print("-" * 79)
    print("u'%s'.isascii() = %s" % (street_as_str, street_as_str.isascii()))
    print("u'%s'.isascii() = %s" % (street_as_str.casefold(), street_as_str.casefold().isascii()))
    print("%s.isascii() = %s" % (street_as_bytes, street_as_bytes.isascii()))
    print("%s.isascii() = %s" % (street_as_bytes_casefolded, street_as_bytes_casefolded.isascii()))
    print("-" * 79)
    print("ΔT = 23.5°C")
    print("1.55 ± 0.01 V")
    print("3‰")
    print(fractions)
    print(arrows)
    print(accents)
    print(greek)
    print(symbols)
    print(boxdraw)
    print(bell)
    
    
    