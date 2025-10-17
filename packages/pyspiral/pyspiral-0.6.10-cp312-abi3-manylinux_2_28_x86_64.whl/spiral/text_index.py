from spiral.core.client import TextIndex as CoreTextIndex
from spiral.expressions import Expr


class TextIndex(Expr):
    def __init__(self, core: CoreTextIndex, *, name: str | None = None):
        super().__init__(core.__expr__)
        self.core = core
        self._name = name

    @property
    def index_id(self) -> str:
        return self.core.id

    @property
    def name(self) -> str:
        return self._name or self.index_id
