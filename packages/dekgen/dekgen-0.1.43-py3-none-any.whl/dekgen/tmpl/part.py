class Repr:
    def __init__(self, value, delay=False):
        self.value = value
        self.delay = delay

    def final_value(self):
        return self.value

    def __repr__(self):
        value = self.final_value()
        return f'lambda: {value}' if self.delay else value

    def __copy__(self):
        return self.__class__(self.value, self.delay)

    def __deepcopy__(self, memo):
        return self.__class__(self.value, self.delay)


class ReprTuple(Repr):
    def __init__(self, value, delay=False):
        super().__init__(list(value), delay)

    def final_value(self):
        return repr(tuple(self.value))

    def __getattr__(self, item):
        return getattr(self.value, item)
