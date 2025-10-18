import asyncio

class Sender:
    def __init__(self,q: asyncio.Queue):
        self.q = q

    async def send(self, msg):
        return await self.q.put(msg)


class Receiver:
    def __init__(self, q: asyncio.Queue):
        self.q = q

    async def recv(self):
        return await self.q.get()


class Duplex:

    def __init__(self, rx: asyncio.Queue, tx: asyncio.Queue):
        self.rx = Receiver(rx)
        self.tx = Sender(tx)

    async def send(self,msg):
        return await self.tx.send(msg)

    async def recv(self):
        return await self.rx.recv()


def duplex():
    
    A = asyncio.Queue()
    B = asyncio.Queue()
    
    return Duplex(A,B), Duplex(B,A)

def simplex():
    Q = asyncio.Queue()
    return Receiver(Q), Sender(Q)