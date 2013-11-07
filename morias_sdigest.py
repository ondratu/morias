#!/usr/bin/env python

from hashlib import sha1
from sys import exit, argv

def sha1_sdigest(text, salt):
    return sha1(salt + text + "0nb\xc5\x99e!\xc5\xa4\xc5\xafm@").hexdigest()

if __name__ == "__main__":
    if len(argv) < 3:
        print "Usage:"
        print " %s passwordstring salt" % argv[0]
        exit(1)

    print sha1_sdigest(argv[1], argv[2])
#endif
