import functools
import os
import re
import shutil
import traceback
import asyncio
from typing import Callable, Any
from time import sleep
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pixelarraylib.monitor.feishu import Feishu
import inspect


def catch_exception(
    exception_return: Any = None,
    alert_params: bool = True,
    addtional_alert: str = "",
    alert_channel: str = "devtoolkit服务报警",
):
    feishu_alert = Feishu(alert_channel)
    def get_caller_function_name():
        """
        description:
            获取调用当前函数的函数名
        return:
            str: 函数名
        """
        return inspect.getframeinfo(inspect.currentframe().f_back.f_back).function

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                alert_params_str = f"参数：{args, kwargs}" if alert_params else ""
                alert_message = f"文件{os.path.relpath(inspect.getfile(func))}中的函数{get_caller_function_name()}执行失败，{alert_params_str}，错误信息如下:\n {traceback.format_exc()}"
                if addtional_alert:
                    alert_message += f"\n{addtional_alert}"
                feishu_alert.send(alert_message)
                return exception_return

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                alert_params_str = f"参数：{args, kwargs}" if alert_params else ""
                alert_message = f"文件{os.path.relpath(inspect.getfile(func))}中的函数{get_caller_function_name()}执行失败，{alert_params_str}，错误信息如下:\n {traceback.format_exc()}"
                if addtional_alert:
                    alert_message += f"\n{addtional_alert}"
                feishu_alert.send(alert_message)
                return exception_return

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def with_retry(
    retry_times: int = 3,
    retry_interval: int = 1,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(retry_times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < retry_times - 1:
                        print(f"第{attempt + 1}次尝试失败，{retry_interval}秒后重试...")
                        sleep(retry_interval)
                    else:
                        print(f"操作失败，已重试{retry_times}次，执行失败")
                        raise e

        return wrapper

    return decorator


def with_timeout(seconds):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=seconds)
                except TimeoutError:
                    raise TimeoutError(
                        f"Function {func.__name__} timed out after {seconds} seconds"
                    )

        return wrapper

    return decorator


def avoid_chinese_filename(func):
    def contains_chinese(text):
        if not text:
            return False
        chinese_pattern = re.compile(r"[\u4e00-\u9fff]")
        return bool(chinese_pattern.search(text))

    def create_temp_path(original_path):
        if not contains_chinese(original_path):
            return original_path

        dir_path = os.path.dirname(original_path)
        filename = os.path.basename(original_path)
        name, ext = os.path.splitext(filename)

        import uuid

        temp_name = f"temp_{uuid.uuid4().hex[:8]}{ext}"
        temp_path = os.path.join(dir_path, temp_name)

        try:
            shutil.copy2(original_path, temp_path)
            return temp_path
        except Exception as e:
            return original_path

    def restore_original_files(path_mapping):
        for temp_path, original_path in path_mapping.items():
            try:
                if os.path.exists(temp_path):
                    os.makedirs(os.path.dirname(original_path), exist_ok=True)

                    if not os.path.exists(original_path):
                        os.rename(temp_path, original_path)
                    else:
                        os.remove(original_path)
                        os.rename(temp_path, original_path)
            except Exception as e:
                pass

    def cleanup_temp_files(temp_files):
        for temp_path in temp_files:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                pass

    def wrapper(*args, **kwargs):
        path_mapping = {}
        temp_files = []

        try:
            new_args = list(args)
            for i, arg in enumerate(args):
                if isinstance(arg, str):
                    is_file_path = os.path.exists(arg)
                    if is_file_path:
                        temp_path = create_temp_path(arg)
                        if temp_path != arg:
                            path_mapping[temp_path] = arg
                            new_args[i] = temp_path
                            temp_files.append(temp_path)

            new_kwargs = kwargs.copy()
            for key, value in kwargs.items():
                if isinstance(value, str):
                    if os.path.exists(value):
                        temp_path = create_temp_path(value)
                        if temp_path != value:
                            path_mapping[temp_path] = value
                            new_kwargs[key] = temp_path
                            temp_files.append(temp_path)

            result = func(*new_args, **new_kwargs)

            restore_original_files(path_mapping)

            return result

        except Exception as e:
            try:
                restore_original_files(path_mapping)
            except:
                pass
            raise e
        finally:
            cleanup_temp_files(temp_files)

    return wrapper
