from rushdata.data import BaseData


class IlBuilderData(BaseData):
    def is_file(self):
        return self.path.exists()