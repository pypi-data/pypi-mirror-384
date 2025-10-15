from typing import final

from .interfaces import IBaseModel, IBaseView


class CustomBaseView(IBaseView):
    @final
    def refresh(self, model: IBaseModel) -> None:
        #view_log.debug('inicio:'+ type model)
        self.update(model)
        #view_log.debug('fim:'+comando)
