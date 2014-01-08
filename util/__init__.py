__author__ = 'zifnab'

import string

def random_string(size=10, chars=string.ascii_letters + string.digits):
    import random
    return ''.join(random.choice(chars) for x in range(size))