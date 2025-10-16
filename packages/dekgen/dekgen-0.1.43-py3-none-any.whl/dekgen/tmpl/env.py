class EnvExtend:
    def __init__(self):
        self._filters = {}
        self._globals = {}

    @staticmethod
    def mark(context, func_or_name):
        def func_wrapper(func):
            context[func_or_name] = func
            return func

        if isinstance(func_or_name, str):
            return func_wrapper
        else:
            context[func_or_name.__name__] = func_or_name
            return func_or_name

    def filters(self, func_or_name):
        return self.mark(self._filters, func_or_name)

    def globals(self, func_or_name):
        return self.mark(self._globals, func_or_name)

    @property
    def context(self):
        return dict(
            filters=self._filters,
            globals=self._globals
        )
