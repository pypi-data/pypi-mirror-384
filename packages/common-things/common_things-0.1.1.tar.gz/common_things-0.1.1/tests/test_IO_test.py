from src.common_things.IO_test import *
from src.common_things.data_structures import EmptyCollectionError


om = output_monitor


def test_base():
    try:
        om.get_output
    except EmptyCollectionError as e:
        print(e)


def test_capture():
    # 不推荐的方式
    om.__enter__()
    print("testcase1")
    om.__exit__()
    print(f"test1_capture: {om.get_output}")

    with om:
        print("testcase2")
        print("testcase3")
    print(f"test2_capture: {om.get_output}, {om.get_output}")

    @monitor_print()
    def test_func():
        print("testcase4")
    test_func()
    print(f"test3_capture: {om.get_output}")
