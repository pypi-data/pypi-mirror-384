from .core_utils import ArgTypes


class Args:
    LOAD_TEST: bool = ArgTypes.Bool("--load-test")
    DOCS: bool = ArgTypes.Bool("--docs")
