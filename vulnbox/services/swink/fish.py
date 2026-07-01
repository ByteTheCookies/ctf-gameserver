class FISH:
    def __init__(self, key: bytes):
        if not isinstance(key, bytes):
            raise TypeError('key must be bytes')

        if len(key) != 32:
            raise ValueError('key must be 32 bytes long')

        self.a = list(key[:16])
        self.s = list(key[16:])

    def randbytes(self, n: int):
        if not isinstance(n, int):
            raise TypeError('n must be an integer')

        n = abs(n)

        val = bytearray(n)

        for i in range(n):
            ai = (self.a[0] + self.a[13]) & 0xff
            si = (self.s[1] + self.a[9]) & 0xff

            self.a = self.a[1:] + [ai ^ 1]
            self.s = self.s[1:] + [si ^ 1]

            val[i] = ai ^ si

        return val
