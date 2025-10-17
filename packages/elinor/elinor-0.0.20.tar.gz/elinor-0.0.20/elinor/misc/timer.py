import time
import functools
import asyncio
from typing import Callable, Any

def timer(func: Callable) -> Callable:
    """
    极简版计时装饰器，支持同步和异步函数
    """
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            end = time.perf_counter()
            print(f"函数 {func.__name__} 执行耗时: {end - start:.4f} 秒")
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            end = time.perf_counter()
            print(f"函数 {func.__name__} 执行耗时: {end - start:.4f} 秒")
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


if __name__ == "__main__":
    @timer
    def sync_function(x: int) -> int:
        time.sleep(x)
        return x * 2

    @timer
    async def async_function(x: int) -> int:
        await asyncio.sleep(x)
        return x * 3

    # 测试同步函数
    print(sync_function(2))

    # 测试异步函数
    print(asyncio.run(async_function(2)))
    
