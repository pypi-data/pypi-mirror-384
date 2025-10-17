from src.common_things.random_anything import *


def test():
    rand = RandAnything()

    print(rand.rand_list((100, 500), 10, int))
    print(rand.rand_list((1, 100), 10, float))
    print(rand.rand_list((' ', 'z'), 10, str))
    print(rand.rand_list((1, 10), 10, bytes))
    print(rand.rand_string((' ', '啊'), 10))