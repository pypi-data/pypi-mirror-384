from abc import ABC, abstractmethod
from collections.abc import Collection
from typing import Callable, Literal, TypeAlias

import numpy as np


class Strategy(ABC):
    @abstractmethod
    def __call__(
        self,
        left_texts: Collection[str],
        right_texts: Collection[str],
    ) -> np.ndarray:
        """
        Abstract Base Class for all similarity strategy classes.
        """
        pass


# function signatures
StrategyCallable: TypeAlias = Callable[[Collection[str], Collection[str]], np.ndarray]
SimilarityCallable: TypeAlias = Callable[[str, str], float]
PreprocessorCallable: TypeAlias = Callable[[str], str]

# Lists of things that can be coerced into specific types
SimilarityLike: TypeAlias = str | SimilarityCallable | None
StrategyLike: TypeAlias = str | Strategy | StrategyCallable | None

# types used by join
HowLiteral = Literal["inner", "left", "right", "outer"]
AllowManyLiteral = Literal["neither", "left", "right", "both"]
