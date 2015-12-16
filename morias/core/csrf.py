
from hashlib import sha256
from base64 import encodestring
from time import time
from random import randrange, seed

seed()


def random_string(length=24):
    """Return `length` long random string."""
    return ''.join(chr(randrange(256)) for c in range(24))


def get_token(secret, user_hash, references, timeout=None, expired=0):
    """Create token from secret key, user_hash hash and references.

    If timeout (in minutes) is set, token contains time align to minutes with
    twice of timeout. That is if time of creating is near to computed timeout.
    Argument variable is for internal use, when function is called from
    check_token.
    """
    if timeout is None:
        text = "%s%s%s" % (secret, user_hash, references)
    else:
        shift = 60 * timeout
        if expired == 0:
            now = time()
            now = int(now / shift) * shift     # shift to timeout
            expired = now + 2 * shift
        expired = sha256(str(expired)).hexdigest()
        text = "%s%s%s%s" % (secret, user_hash, references, expired)
    return encodestring(sha256(text).digest()).strip()


def check_token(token, secret, user_hash, references, timeout=None):
    """Check token with generated one.

    If timeout is set, than two token are generated. One for time before
    twice timeout, one before timeout. That is because time is aligned.
    """
    if timeout is None:
        return token == get_token(secret, user_hash, references)
    else:
        now = time()
        shift = 60 * timeout
        now = int(now / shift) * shift      # shift to timeout
        expired = now + 2 * shift
        if token == get_token(secret, user_hash, references, timeout, expired):
            return True

        expired = now + shift
        return token == get_token(secret, user_hash, references, timeout,
                                  expired)
