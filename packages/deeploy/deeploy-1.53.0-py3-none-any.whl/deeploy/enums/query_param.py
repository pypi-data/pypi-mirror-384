from enum import Enum, EnumMeta


class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True


class BaseEnum(Enum, metaclass=MetaEnum):
    pass


class SortDirection(BaseEnum):
    ASC = "asc"
    DESC = "desc"


class RHSQuery(BaseEnum):
    EQ = "eq"
    IN = "in"
    LIKE = "like"
