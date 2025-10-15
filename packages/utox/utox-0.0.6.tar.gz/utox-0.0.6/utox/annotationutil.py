import cProfile
import io
import pstats


def profile(is_enabled=True):
    """是否profile的装饰器"""

    def main(func):
        def wrapper(*args, **kwargs):
            pr = cProfile.Profile()
            pr.enable()
            func(*args, **kwargs)
            pr.disable()
            s = io.StringIO()
            sortby = "cumtime"
            ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            ps.print_stats()
            print(s.getvalue())

        return wrapper if is_enabled else func

    return main


def time_it(func):
    """统计某个函数的执行时间的装饰器"""

    def wrapper(*args, **kwargs):
        import time

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"函数[{func.__name__}]执行时间:{(end_time - start_time)*1000} ms")
        return result

    return wrapper
