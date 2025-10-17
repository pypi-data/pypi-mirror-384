import pytest
import random
from src.common_things.random_anything import *
from src.common_things.random_anything import _RandIvl


class TestRandIvl:
    """_RandIvl 类测试"""

    def test_init_with_valid_types(self):
        """测试有效类型初始化"""
        # 测试整数区间
        ivl = _RandIvl(1, 100, int)
        assert ivl.rand_type == int
        assert ivl.start == 1
        assert ivl.end == 100

        # 测试浮点数区间
        ivl = _RandIvl(0.5, 99.9, float)
        assert ivl.rand_type == float
        assert ivl.start == 0.5
        assert ivl.end == 99.9

        # 测试字符串区间
        ivl = _RandIvl("a", "z", str)
        assert ivl.rand_type == str
        assert ivl.start == "a"
        assert ivl.end == "z"

    def test_init_with_none_values(self):
        """测试None值处理"""
        # start为None，使用默认最小值
        ivl = _RandIvl(None, 100, int)
        assert ivl.start == -2147483648  # int默认最小值
        assert ivl.end == 100

        # end为None，使用默认最大值
        ivl = _RandIvl(1, None, int)
        assert ivl.start == 1
        assert ivl.end == 2147483647  # int默认最大值

        # 两者都为None
        ivl = _RandIvl(None, None, float)
        assert ivl.start == 0.0  # float默认最小值
        assert ivl.end == 100.0  # float默认最大值

    def test_type_inference(self):
        """测试类型推断"""
        # 从start推断类型
        ivl = _RandIvl(10, None)
        assert ivl.rand_type == int

        # 从end推断类型
        ivl = _RandIvl(None, 3.14)
        assert ivl.rand_type == float

        # 从两者推断（类型一致）
        ivl = _RandIvl(b"a", b"z")
        assert ivl.rand_type == bytes

    def test_type_inference_error(self):
        """测试类型推断错误"""
        with pytest.raises(TypeError, match="Inconsistent types between start and end"):
            _RandIvl(1, "string")  # int和str类型不一致

    def test_both_none_error(self):
        """测试start和end都为None的错误"""
        with pytest.raises(ValueError, match="Both start and end cannot be None"):
            _RandIvl(None, None)  # 无法推断类型

    def test_invalid_rand_type(self):
        """测试无效的rand_type"""
        with pytest.raises(TypeError, match="rand_type must be a type"):
            _RandIvl(1, 100, "not_a_type")  # rand_type不是类型

    def test_iteration(self):
        """测试迭代功能"""
        ivl = _RandIvl(1, 10, int)
        start, end = list(ivl)
        assert start == 1
        assert end == 10

    def test_set_range(self):
        """测试设置范围"""
        ivl = _RandIvl(1, 100, int)
        ivl.reset_range(5, 50)
        assert ivl.start == 5
        assert ivl.end == 50

        # 测试部分设置
        ivl.reset_range(start=10)
        assert ivl.start == 10
        assert ivl.end == 50

        ivl.reset_range(end=80)
        assert ivl.start == 10
        assert ivl.end == 80


class TestRandAnything:
    """RandAnything 类测试"""

    def test_init_with_seed(self):
        """测试带种子初始化"""
        ra = RandAnything(seed=42)
        assert ra._seed == 42
        assert isinstance(ra._rand, random.Random)

    def test_init_without_seed(self):
        """测试无种子初始化"""
        ra = RandAnything()
        assert isinstance(ra._seed, int)
        assert isinstance(ra._rand, random.Random)

    def test_rand_bytes(self):
        """测试随机字节生成"""
        ra = RandAnything(seed=42)

        # 测试字节范围
        result = ra.rand_bytes(b"a", b"z")
        assert isinstance(result, bytes)

        # 测试整数范围（转换为字节）
        result = ra.rand_bytes(97, 122)  # 'a'到'z'的ASCII码
        assert isinstance(result, bytes)

    def test_rand_char(self):
        """测试随机字符生成"""
        ra = RandAnything(seed=42)

        # 测试基本字符范围
        result = ra.rand_char("a", "z")
        assert isinstance(result, str)
        assert len(result) == 1
        assert "a" <= result <= "z"

        # 测试Unicode字符
        result = ra.rand_char("一", "龟")  # 中文字符范围
        assert isinstance(result, str)
        assert len(result) == 1

    def test_rand_char_empty_error(self):
        """测试空字符错误"""
        ra = RandAnything(seed=42)
        with pytest.raises(ValueError, match="cannot be empty"):
            ra.rand_char("", "z")
        with pytest.raises(ValueError, match="cannot be empty"):
            ra.rand_char("a", "")

    def test_rand_list_basic(self):
        """测试基本随机列表生成"""
        ra = RandAnything(seed=42)

        # 测试整数列表
        result = ra.rand_list((1, 10), 5)  # 5个1-10的整数
        assert isinstance(result, list)
        assert len(result) == 5
        assert all(isinstance(x, int) for x in result)
        assert all(1 <= x <= 10 for x in result)

        # 测试浮点数列表
        result = ra.rand_list((0.0, 1.0), 3, float)
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(x, float) for x in result)
        assert all(0.0 <= x <= 1.0 for x in result)

    def test_rand_list_variable_size(self):
        """测试可变大小列表"""
        ra = RandAnything(seed=42)

        # 测试大小区间
        result = ra.rand_list((1, 100), (3, 7))  # 3-7个元素
        assert isinstance(result, list)
        assert 3 <= len(result) <= 7
        assert all(1 <= x <= 100 for x in result)

    def test_rand_list_type_inference(self):
        """测试列表类型推断"""
        ra = RandAnything(seed=42)

        # 从值范围推断类型
        result = ra.rand_list(("a", "z"), 5)  # 推断为str类型
        assert isinstance(result, list)
        assert all(isinstance(x, str) for x in result)
        assert all("a" <= x <= "z" for x in result)

    def test_rand_tuple(self):
        """测试随机元组生成"""
        ra = RandAnything(seed=42)

        result = ra.rand_tuple((1, 10), 5)
        assert isinstance(result, tuple)
        assert len(result) == 5
        assert all(isinstance(x, int) for x in result)
        assert all(1 <= x <= 10 for x in result)

    def test_rand_set(self):
        """测试随机集合生成"""
        ra = RandAnything(seed=42)

        result = ra.rand_set((1, 10), 10)  # 可能包含重复值，但集合会去重
        assert isinstance(result, set)
        assert len(result) <= 10  # 去重后长度可能小于10
        assert all(isinstance(x, int) for x in result)
        assert all(1 <= x <= 10 for x in result)

    def test_rand_string(self):
        """测试随机字符串生成"""
        ra = RandAnything(seed=42)

        result = ra.rand_string(("a", "z"), 10)
        assert isinstance(result, str)
        assert len(result) == 10
        assert all("a" <= char <= "z" for char in result)

    def test_reproducibility(self):
        """测试随机数可重现性（相同种子产生相同结果）"""
        ra1 = RandAnything(seed=123)
        ra2 = RandAnything(seed=123)

        # 测试多个方法的重现性
        list1 = ra1.rand_list((1, 100), 5)
        list2 = ra2.rand_list((1, 100), 5)
        assert list1 == list2

        tuple1 = ra1.rand_tuple((1, 10), 3)
        tuple2 = ra2.rand_tuple((1, 10), 3)
        assert tuple1 == tuple2

        str1 = ra1.rand_string(("a", "z"), 5)
        str2 = ra2.rand_string(("a", "z"), 5)
        assert str1 == str2


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_range(self):
        """测试空范围"""
        ra = RandAnything(seed=42)

        # 单元素范围
        result = ra.rand_list((5, 5), 3)  # 始终生成5
        assert all(x == 5 for x in result)

        # 字符单元素范围
        result = ra.rand_string(("a", "a"), 5)
        assert result == "aaaaa"

    def test_zero_size(self):
        """测试零大小集合"""
        ra = RandAnything(seed=42)

        result = ra.rand_list((1, 10), 0)
        assert result == []

        result = ra.rand_tuple((1, 10), 0)
        assert result == ()

        result = ra.rand_set((1, 10), 0)
        assert result == set()

    def test_large_size(self):
        """测试大尺寸集合"""
        ra = RandAnything(seed=42)

        # 测试较大尺寸（性能测试）
        result = ra.rand_list((1, 1000), 1000)
        assert len(result) == 1000
        assert all(1 <= x <= 1000 for x in result)

    def test_unicode_characters(self):
        """测试Unicode字符生成"""
        ra = RandAnything(seed=42)

        # 测试基本多文种平面字符
        result = ra.rand_char("\u0000", "\uFFFF")
        assert isinstance(result, str)
        assert len(result) == 1

        # 测试补充平面字符（需要代理对）
        result = ra.rand_char("\U00010000", "\U0010FFFF")
        assert isinstance(result, str)
        assert len(result) == 1  # 或2（代理对）


class TestIntegration:
    """集成测试"""

    def test_chained_operations(self):
        """测试链式操作"""
        ra = RandAnything(seed=42)

        # 生成列表后转换为其他结构
        numbers = ra.rand_list((1, 100), 10)
        unique_numbers = set(numbers)  # 去重
        sorted_numbers = tuple(sorted(numbers))  # 排序

        assert len(unique_numbers) <= 10
        assert len(sorted_numbers) == 10
        assert all(isinstance(x, int) for x in sorted_numbers)

    def test_multiple_data_types(self):
        """测试多种数据类型混合使用"""
        ra = RandAnything(seed=42)

        # 同时测试多种类型
        int_list = ra.rand_list((1, 10), 5)
        float_list = ra.rand_list((0.0, 1.0), 5, float)
        str_list = ra.rand_list(("a", "z"), 5)

        assert all(isinstance(x, int) for x in int_list)
        assert all(isinstance(x, float) for x in float_list)
        assert all(isinstance(x, str) for x in str_list)

    def test_randomness_quality(self):
        """测试随机性质量（统计测试）"""
        ra = RandAnything(seed=42)

        # 生成大量随机数测试分布
        numbers = ra.rand_list((1, 10), 1000)

        # 简单统计测试：每个数字应该出现大约100次（±20%）
        from collections import Counter
        counts = Counter(numbers)

        for i in range(1, 11):
            assert 80 <= counts.get(i, 0) <= 120, f"数字{i}出现次数异常: {counts.get(i, 0)}"
