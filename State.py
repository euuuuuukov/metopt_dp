class State:
    def __init__(self, zb1: float, zb2: float, dep: float, free: float, step: int) -> None:
        self.zb1, self.zb2, self.dep = zb1, zb2, dep
        self.free = free
        self.step = step