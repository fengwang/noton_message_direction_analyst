from abc import ABCMeta, abstractmethod

class Module(metaclass=ABCMeta):

    @abstractmethod
    def forward(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)

