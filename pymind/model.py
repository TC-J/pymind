from abc import ABC, abstractmethod
from typing import Any, Literal, override

class Model(ABC):
    backend : Literal["tf"] | Literal["pt"] | None = None
    nn : Any | None = None
    epochs = 0

    def __init__(
        self,
        backend: Literal["tf", "pt", "keras"],
        **hyperparams
    ) -> None:
        self.backend = backend
        self.hyperparams = hyperparams


    @abstractmethod
    def __train__(self, X_train, y_train) -> Any:
        pass

    @abstractmethod
    def __test__(self, X_test, y_test) -> Any:
        pass

    @abstractmethod
    def __predict__(self, X) -> Any:
        pass

    @abstractmethod
    def parameters(self) -> Any:
        pass

    def train(self, X_train, y_train) -> Any:
        self.epochs += 1
        return self.__train__(X_train, y_train)
    
    def test(self, X_test, y_test) -> Any:
        return self.__test__(X_test, y_test)
    
    def predict(self, X) -> Any:
        return self.__predict__(X)