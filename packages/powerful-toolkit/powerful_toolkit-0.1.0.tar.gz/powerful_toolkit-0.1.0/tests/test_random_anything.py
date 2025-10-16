from src.powerful_toolkit.random_anything import *

def test():
    rand = RandAnything()
    print(rand.rand_list((None, None), (7, 10), int))