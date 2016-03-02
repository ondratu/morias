#!/usr/bin/env python
"""Generate bcrypt hash."""

from bcrypt import hashpw, gensalt
from argparse import ArgumentParser


if __name__ == "__main__":
    parser = ArgumentParser(
        description=__doc__,
        usage="%(prog)s [options] PASSWORD [ROUNDS]")
    parser.add_argument(
        "password", type=str, metavar="PASSWORD",
        help="Password from which you want to generate hash.")
    parser.add_argument(
        "rounds", default=12, type=int, nargs='?', metavar="ROUNDS",
        help="How many rounds to create hash. (Default 12)")
    args = parser.parse_args()

    hs = hashpw(args.password, gensalt(args.rounds))
    print hs
    print "UPDATE logins SET passwd='%s' WHERE email='your@login';" % hs
