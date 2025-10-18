from IPython import get_ipython
from sparkmagic.kernels.kernelmagics import KernelMagics


class SparkMagic:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = KernelMagics(get_ipython())
        return cls._instance
