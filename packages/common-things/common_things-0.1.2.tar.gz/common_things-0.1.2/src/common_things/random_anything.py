import random
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
    """区间，用于合理化各种 Type"""
    # 有效 rand_type 集合（快速校验）
    _VALID_RAND_TYPES: set[Type[Any]] = set(_TYPE_RANGES.keys())

    def __init__(
            self,
            start: Optional[AvailableType] = None,
            end: Optional[AvailableType] = None,
            rand_type: Type[Any] = None,
    ) -> None:
        self.start = None
        self.end = None

        self.rand_type: Type[*_RandIvl._VALID_RAND_TYPES] = self._infer_rand_type(start, end) if rand_type is None else rand_type

        if not isinstance(self.rand_type, type):
            raise TypeError("rand_type must be a type")

        self.min, self.max = _TYPE_RANGES[self.rand_type]

        params = [
            (f"{start=}".split('=')[0], start, 'min'),  # start 为 None 时，默认取 self.min
            (f"{end=}".split('=')[0], end, 'max')  # end 为 None 时，默认取 self.max
        ]
        for attr, value, default_attr in params:
            self._validate_and_set(attr, value, default_attr)


    def _infer_rand_type(self, start: Optional[Any], end: Optional[Any]) -> Type:
        """
        根据 start/end 的类型推断 rand_type（仅当 rand_type 为 None 时调用），用于区间初始化
        :return: 推断出的 rand_type
        :raise TypeError: 如果 start/end 类型不一致且都不为 None
        """

        if start is not None and end is not None:
            if type(start) != type(end):
                raise TypeError("Inconsistent types between start and end")
            return type(start)
        elif start is not None:
            return type(start)
        elif end is not None:
            return type(end)
        else:  # start != end != None
            raise ValueError("Both start and end cannot be None")

    def _validate_and_set(self, attr: str, value: Any, default_attr: str) -> None:
        """验证参数类型并设置实例属性，用于初始化"""
        type_converters = {
            int: lambda val: int(val),
            float: lambda val: float(val),
            bytes: lambda val: bytes(val),
            str: lambda val: str(val),
        }

        default_value = getattr(self, default_attr)  # 获取默认值

        if value is None:
            setattr(self, attr, default_value)
        elif self.rand_type in self._VALID_RAND_TYPES:
            setattr(self, attr, type_converters[self.rand_type](value))
        else:  # 类型无效
            raise TypeError(
                f"{attr.capitalize()} must be of type {self.rand_type.__name__} or None. "
                f"Got {type(value).__name__} instead."
            )

    def __iter__(self):
        yield self.start
        yield self.end

    def reset_range(self, start: AvailableType = None, end: AvailableType = None) -> None:
        self._validate_and_set("start", start, "start")
        self._validate_and_set("end", end, "end")


class RandAnything:
    """随机生成器"""
    def __init__(
            self,
            seed: int = random.randint(-2147483648, 2147483647),
    ) -> None:
        self._seed = seed
        self._rand = random.Random(self._seed)

        self._types_of_randoms = {
            int: lambda rng: self._rand.randint(*rng),
            float: lambda rng: self._rand.uniform(*rng),
            bytes: lambda rng: bytes(self.rand_bytes(*rng)),
            str: lambda rng: str(self.rand_char(*rng)),
        }

    def rand_bytes(self, start: bytes | int, end: bytes | int) -> bytes:
        """随机字节"""
        if type(start) is bytes:
            start, end = [int.from_bytes(v, byteorder='little') for v in (start, end)]
        return self._rand.randint(start, end).to_bytes(2, byteorder='little')

    def rand_char(self, start: str, end: str) -> str:
        """随机字符"""
        if start == '' or end == '':
            raise ValueError(f"'{start}' or '{end}' cannot be empty")
        start, end = ord(start), ord(end)
        return chr(self._rand.randint(start, end))

    def rand_list(
            self,
            value_range: Interval | str,
            size: Interval | int = (0, 20),
            rand_type: Type[Any] = None
    ) -> list:
        """随机列表"""
        value_range = _RandIvl(value_range[0], value_range[1], rand_type=rand_type)
        size_rng = _RandIvl(size[0], size[1]) if isinstance(size, (list, tuple)) else _RandIvl(size, size)
        length = self._rand.randint(*size_rng)

        random_values = [self._types_of_randoms[value_range.rand_type](value_range) for _ in range(length)]
        return random_values

    def rand_tuple(
            self,
            value_range: Interval | str,
            size: Interval | int,
            rand_type: Type[Any] = None
    ) -> tuple:
        """随机元组"""
        return tuple(self.rand_list(value_range, size, rand_type))

    def rand_set(
            self,
            value_range: Interval | str,
            size: Interval | int,
            rand_type: Type[Any] = None
    ) -> set:
        """随机集合（会生成重复值）"""
        return set(self.rand_list(value_range, size, rand_type))

    def rand_string(
            self,
            value_range: Interval | str,
            size: Interval | int
    ):
        """随机字符串"""
        return ''.join(self.rand_list(value_range, size, str))

__all__ = [
    'RandAnything',
]