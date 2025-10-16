from src.powerful_toolkit.IO_test import *

def test():
    restart_monitoring()
    print("test")
    iprint("test")
    iprint(get_captured_output())
    restore_stdout()
    @monitor_print()
    def a():
        print("a")
        print('b')
    a()
    iprint(get_captured_output())
    iprint(get_captured_output())
