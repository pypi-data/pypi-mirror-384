from typing import final

from .interfaces import IBaseController


class CustomBaseController(IBaseController):
    @final
    def run(self) -> None:
        self.execute()



