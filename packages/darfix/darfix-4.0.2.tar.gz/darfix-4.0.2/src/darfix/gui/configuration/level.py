from silx.utils.enum import Enum as _Enum


class ConfigurationLevel(_Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    ADVANCED = "advanced"

    def _get_num_value(self) -> int:
        if self is self.REQUIRED:
            return 0
        elif self is self.OPTIONAL:
            return 1
        elif self is self.ADVANCED:
            return 2

    def __le__(self, other):
        if not isinstance(other, ConfigurationLevel):
            raise TypeError(
                f"other is expected to be an instance of ConfigurationLevel. {type(other)} provided"
            )
        return self._get_num_value() <= other._get_num_value()

    def __lt__(self, other):
        if not isinstance(other, ConfigurationLevel):
            raise TypeError(
                f"other is expected to be an instance of ConfigurationLevel. {type(other)} provided"
            )
        return self._get_num_value() < other._get_num_value()
