class Method:
    def __getattr__(self, method):
        return Method2(method)


class Method2:
    def __init__(self, method):
        self.methods = [method]
        self.args = []
        self.kwargs = {}

    def __getattr__(self, method):
        self.methods.append(method)
        return self

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return Method3(self)


class Method3:
    def __init__(self, m2):
        self.m2 = m2

    def __getattr__(self, method):
        getattr(self.m2, method)
        return self

    def __call__(self, instance):
        cursor = instance
        for method in self.m2.methods:
            cursor = getattr(cursor, method)
        return cursor(*self.m2.args, **self.m2.kwargs)


class MethodSimple:
    def __getattr__(self, method):
        return Method3(Method2(method))
