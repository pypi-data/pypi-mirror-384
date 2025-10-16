import random
from types import NoneType
from typing import (
    Optional,
    Any,
    Union,
    Tuple,
    Dict,
    Type,
)


AvailableType = Union[int, float, bytes, str]
Interval = Tuple[Any, Any]
_TYPE_RANGES: Dict[Type[Any], tuple[Any, Any]] = {
    int: (-2147483648, 2147483647),  # 32位有符号整数
    float: (0.0, 100.0),
    bytes: (b'', b'\xff\xff'),  # 空字节到全 ff
    str: ('\u0000', '\U0010FFFF'),
}


class _RandIvl:
    # 有效 rand_type 集合（快速校验）
    _VALID_RAND_TYPES: set[Type[Any]] = set(_TYPE_RANGES.keys())


    def __init__(
            self,
            start: Union[AvailableType, None] = None,
            end: Union[AvailableType, None] = None,
            rand_type: Type[Any] = None,
    ) -> None:
        self.start = None
        self.end = None

        self.rand_type: Type[*_TYPE_RANGES] = self._infer_rand_type(start, end) if rand_type is None else rand_type
        self.min, self.max = _TYPE_RANGES[self.rand_type]

        params = [
            (f"{start=}".split('=')[0], start, 'min'),  # start 为 None 时，默认取 self.min
            (f"{end=}".split('=')[0], end, 'max')  # end 为 None 时，默认取 self.max
        ]
        for attr, value, default_attr in params:
            self._validate_and_set(attr, value, default_attr)


    def _infer_rand_type(self, start: Optional[object], end: Optional[object]) -> Type:
        """
        根据start/end的类型推断rand_type（仅当rand_type为None时调用）
        :return: 推断出的rand_type
        :raise TypeError: 如果start/end类型不一致且都不为None
        """

        start_type = type(start) if start is not None else None
        end_type = type(end) if end is not None else None

        # 检查类型一致性：两者不能不同且都不为None
        if start_type == end_type == NoneType and self.rand_type is not NoneType:
            return self.rand_type
        elif start_type != end_type and NoneType not in (start_type, end_type):
            raise TypeError(f"start和end类型不一致：{start_type.__name__} vs {end_type.__name__}")

        # 确定rand_type：优先取非None的类型
        return end_type if start_type is None else start_type

    def _validate_and_set(self, attr: str, value: Any, default_attr: str) -> None:
        """验证参数类型并设置实例属性"""
        type_converters = {
            int: lambda val: int(val),
            float: lambda val: float(val),
            bytes: lambda val: bytes(val),
            str: lambda val: str(val),
        }

        default_value = getattr(self, default_attr)  # 获取默认值

        if value is None:
            setattr(self, attr, default_value)
        elif self.rand_type in self._VALID_RAND_TYPES:  # 严格匹配类型
            setattr(self, attr, type_converters[self.rand_type](value))
        else:  # 类型无效
            raise TypeError(
                f"{attr.capitalize()} must be of type {self.rand_type.__name__} or None. "
                f"Got {type(value).__name__} instead."
            )

    def __iter__(self):
        yield self.start
        yield self.end

    def set_range(self, start: AvailableType = None, end: AvailableType = None) -> None:
        if start is not None:
            self.start = start
        elif type(start) is not self.rand_type:
            raise TypeError(f"start must be of type {self.rand_type.__name__}")
        if end is not None:
            self.end = end
        elif type(end) is not self.rand_type:
            raise TypeError(f"end must be of type {self.rand_type.__name__}")


class RandAnything:
    def __init__(
            self,
            seed: int = random.randint(-2147483648, 2147483647),
    ) -> None:
        self._seed = seed
        self._rand = random.Random(self._seed)
        self._type_ranges = _TYPE_RANGES.copy()

        self._types_of_randoms = {
            int: lambda rng: self._rand.randint(*rng),
            float: lambda rng: self._rand.uniform(*rng),
            bytes: lambda rng: bytes(self.rand_bytes(*rng)),
            str: lambda rng: str(self.rand_char(*rng)),
        }

    def rand_bytes(self, start: bytes, end: bytes) -> bytes:
        start = int.from_bytes(start, byteorder='little')
        end = int.from_bytes(end, byteorder='little')

        return self._rand.randint(start, end).to_bytes(2, byteorder='little')

    def rand_char(self, start: str, end: str) -> str:
        start = ord(start)
        end = ord(end)

        return chr(self._rand.randint(start, end))

    def rand_list(
            self, value_range: Interval | str, size: Interval | int = (0, 20), rand_type: Type[Any] = None) -> list:
        value_range = _RandIvl(value_range[0], value_range[1], rand_type=rand_type)
        size_range = _RandIvl(*size) if type(size) in (list, tuple) else _RandIvl(size, size)
        length = self._rand.randint(*size_range)

        return [self._types_of_randoms[value_range.rand_type](value_range) for _ in range(length)]

    def rand_tuple(
            self, value_range: Interval | str, size: Interval | int, rand_type: Type[Any] = None) -> tuple:
        return tuple(self.rand_list(value_range, size, rand_type))

    def rand_set(
            self, value_range: Interval | str, size: Interval | int, rand_type: Type[Any] = None) -> set:
        return set(self.rand_list(value_range, size, rand_type))

    def rand_string(self, value_range: Interval | str, size: Interval | int):
        return ''.join(self.rand_list(value_range, size, str))

__all__ = [
    'RandAnything',
]