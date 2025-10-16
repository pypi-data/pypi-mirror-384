"""Module dedicated to identifiers. Identifiers allow to retrieve an object (scan or volume) from an url - identifier"""


class BaseIdentifier:
    TOMO_TYPE = None

    def __init__(self, object):
        self._dataset_builder = object.from_identifier

    @property
    def tomo_type(self):
        return self.TOMO_TYPE

    def recreate_object(self):
        """Recreate the dataset from the identifier"""
        return self._dataset_builder(self)

    def short_description(self) -> str:
        """short description of the identifier"""
        return ""

    @property
    def scheme(self) -> str:
        raise NotImplementedError("Base class")

    def to_str(self):
        return str(self)

    @staticmethod
    def from_str(identifier):
        raise NotImplementedError("base class")

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, BaseIdentifier):
            return __o.to_str() == self.to_str()
        elif isinstance(__o, str):
            return __o == self.to_str()
        else:
            return False


class ScanIdentifier(BaseIdentifier):
    TOMO_TYPE = "scan"


class VolumeIdentifier(BaseIdentifier):
    TOMO_TYPE = "volume"
