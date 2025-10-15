from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from tqdm import tqdm

from .logger import logger


def submit_task(func, item, use_args=False, use_kwargs=False):
    """根据item的类型决定如何调用函数
    
    Args:
        func: 要执行的函数
        item: 输入项
        use_args: 当item是元组或列表时，是否按位置参数传递（True）；
            为 False 时将元组或列表整体作为一个位置参数传递
        use_kwargs: 当item是字典时，是否按关键字参数传递（True）；
            为 False 时将字典整体作为一个位置参数传递
    """
    if isinstance(item, dict):
        # 检查是否是混合格式 {'args': (...), 'kwargs': {...}}
        if "args" in item and "kwargs" in item:
            return func(*item["args"], **item["kwargs"])
        elif "args" in item:
            return func(*item["args"])
        elif "kwargs" in item:
            return func(**item["kwargs"])
        else:
            # 纯字典
            if use_kwargs:
                # 作为关键字参数传递
                return func(**item)
            else:
                # 将字典整体作为单个位置参数传递
                return func(item)
    elif isinstance(item, (tuple, list)) and not isinstance(item, str):
        # 元组或列表
        if use_args:
            # 作为位置参数传递
            return func(*item)
        else:
            # 将元组或列表整体作为单个位置参数传递
            return func(item)
    else:
        # 单个值
        return func(item)


def sequential_map(
    func, items, description=None, log_level="none", progress_type="rich", use_args=False, use_kwargs=False
):
    """
    顺序执行函数，用于单线程场景（如调试）

    Args:
        func: 要执行的函数
        items: 输入数据列表
        description: 进度条描述，默认为函数名
        log_level: 日志级别
        progress_type: 进度条类型，可选值：
            - "rich": 使用 rich 进度条（默认）
            - "tqdm": 使用 tqdm 进度条
            - "none": 无进度条
        use_args: 当items中的元素是元组或列表时，是否按位置参数传递（True）；
            为 False 时将元组或列表整体作为一个位置参数传递
        use_kwargs: 当items中的元素是字典时，是否按关键字参数传递（True）；
            为 False 时将字典整体作为一个位置参数传递

    Returns:
        按输入顺序排列的结果列表
    """
    results = []

    # 检查是否支持len，如果不支持则转换为列表
    if not hasattr(items, "__len__"):
        logger.info("Converting iterator to list for map processing...")
        items = list(items)

    total = len(items)

    # 使用函数名
    if description is None:
        func_name = getattr(func, "__name__", "task")
        description = f"<{func_name}>"

    if progress_type == "rich":
        # 使用 rich 进度条，显示数量和进度
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            total_task = progress.add_task(f"[green]{description}[/green]", total=total)
            for i, item in enumerate(items):
                try:
                    result = submit_task(func, item, use_args, use_kwargs)
                    logger.log(log_level, f"index: {i}, result: {result}")
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in sequential_map: {e}")
                    results.append(e)
                progress.update(total_task, advance=1)

    elif progress_type == "tqdm":
        # 使用 tqdm 进度条
        with tqdm(total=total, desc=description, unit="item") as pbar:
            for i, item in enumerate(items):
                try:
                    result = submit_task(func, item, use_args, use_kwargs)
                    logger.log(log_level, f"index: {i}, result: {result}")
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in sequential_map: {e}")
                    results.append(e)
                pbar.update(1)

    else:  # progress_type == "none"
        # 无进度条
        for i, item in enumerate(items):
            try:
                result = submit_task(func, item, use_args, use_kwargs)
                logger.log(log_level, f"index: {i}, result: {result}")
                results.append(result)
            except Exception as e:
                logger.error(f"Error in sequential_map: {e}")
                results.append(e)

    return results


def parallel_map(
    func, items, description=None, log_level="none", max_workers=5, progress_type="rich", use_args=False, use_kwargs=False
):
    """
    并行执行函数，保证输出顺序与输入顺序一致

    Args:
        func: 要执行的函数
        items: 输入数据列表，支持以下格式：
            - 单个值的列表: [1, 2, 3]
            - 元组列表（位置参数）: [(1, 2), (3, 4), (5, 6)]
            - 字典列表（关键字参数）: [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
            - 混合格式：[{'args': (...), 'kwargs': {...}}, ...]
        description: 进度条描述，默认为函数名
        log_level: 日志级别
        max_workers: 最大工作线程数，默认为 5
        progress_type: 进度条类型，可选值：
            - "rich": 使用 rich 进度条（默认）
            - "tqdm": 使用 tqdm 进度条
            - "none": 无进度条
        use_args: 当items中的元素是元组或列表时，是否按位置参数传递（True）；
            为 False 时将元组或列表整体作为一个位置参数传递
        use_kwargs: 当items中的元素是字典时，是否按关键字参数传递（True）；
            为 False 时将字典整体作为一个位置参数传递

    Returns:
        按输入顺序排列的结果列表

    Examples:
        # 单个参数
        parallel_map(lambda x: x * 2, [1, 2, 3])

        # 多个位置参数
        parallel_map(lambda x, y: x + y, [(1, 2), (3, 4), (5, 6)])

        # 关键字参数
        parallel_map(lambda a, b: a + b, [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}])

        # 字典作为单个位置参数（适用于形参是一个dict的函数）
        parallel_map(lambda d: (d['a'] + d['b']), [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}], use_kwargs=False)

        # 混合参数
        parallel_map(lambda x, y, z=0: x + y + z,
                    [{'args': (1, 2), 'kwargs': {'z': 3}},
                     {'args': (4, 5), 'kwargs': {'z': 6}}])

    Problem:
        Process上下文中会导致icecream不可用,因为
        # icecream的ic()函数默认将输出写入stderr（标准错误流），而不是stdout（标准输出流）。这会导致：
        # 输出缓冲问题: stderr和stdout有不同的缓冲策略
        # 输出顺序混乱: 当使用map等函数时，多个ic()调用的输出可能交错
        需要手动配置输出函数为print
        ic.configureOutput(outputFunction=print)

    """
    # 如果只有一个worker或更少，使用顺序执行，避免线程开销
    if max_workers <= 1:
        return sequential_map(func, items, description, log_level, progress_type, use_args, use_kwargs)

    # 检查是否支持len，如果不支持则转换为列表
    if not hasattr(items, "__len__"):
        logger.info("Converting iterator to list for map processing...")
        items = list(items)

    # 使用函数名
    if description is None:
        func_name = getattr(func, "__name__", "task")
        description = f"<{func_name}>"

    results = [None] * len(items)
    
    # 创建包装函数来传递 use_kwargs 参数
    def submit_task_wrapper(func, item):
        return submit_task(func, item, use_args, use_kwargs)

    if progress_type == "rich":
        # 使用 rich 进度条，显示数量和进度
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            total_task = progress.add_task(
                f"[green]{description}[/green]", total=len(items)
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务，并保存任务和索引的映射
                future_to_index = {
                    executor.submit(submit_task_wrapper, func, item): i
                    for i, item in enumerate(items)
                }

                # 按完成顺序获取结果，但保存到正确的位置
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        logger.log(
                            log_level, f"index: {index}, result: {future.result()}"
                        )
                        results[index] = future.result()
                    except Exception as e:
                        logger.error(f"Error in parallel_map: {e}")
                        results[index] = e
                    progress.update(total_task, advance=1)

    elif progress_type == "tqdm":
        # 使用 tqdm 进度条
        if tqdm is None:
            logger.warning("tqdm not available, falling back to no progress bar")
            progress_type = "none"
        else:
            with tqdm(total=len(items), desc=description, unit="item") as pbar:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # 提交所有任务，并保存任务和索引的映射
                    future_to_index = {
                        executor.submit(submit_task_wrapper, func, item): i
                        for i, item in enumerate(items)
                    }

                    # 按完成顺序获取结果，但保存到正确的位置
                    for future in as_completed(future_to_index):
                        index = future_to_index[future]
                        try:
                            logger.log(
                                log_level, f"index: {index}, result: {future.result()}"
                            )
                            results[index] = future.result()
                        except Exception as e:
                            logger.error(f"Error in parallel_map: {e}")
                            results[index] = e
                        pbar.update(1)

    else:  # progress_type == "none"
        # 无进度条
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务，并保存任务和索引的映射
            future_to_index = {
                executor.submit(submit_task_wrapper, func, item): i
                for i, item in enumerate(items)
            }

            # 按完成顺序获取结果，但保存到正确的位置
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    logger.log(log_level, f"index: {index}, result: {future.result()}")
                    results[index] = future.result()
                except Exception as e:
                    logger.error(f"Error in parallel_map: {e}")
                    results[index] = e

    return results


def auto_map(
    func, items, description=None, log_level="none", max_workers=1, progress_type="rich", use_args=False, use_kwargs=False
):
    """
    智能映射函数，根据max_workers自动选择执行方式

    Args:
        func: 要执行的函数
        items: 输入数据列表
        description: 进度条描述，默认为函数名
        log_level: 日志级别
        max_workers: 最大工作线程数，默认为 1（顺序执行）
        progress_type: 进度条类型，可选值：
            - "rich": 使用 rich 进度条（默认）
            - "tqdm": 使用 tqdm 进度条
            - "none": 无进度条
        use_args: 当items中的元素是元组或列表时，是否按位置参数传递（True）；
            为 False 时将元组或列表整体作为一个位置参数传递
        use_kwargs: 当items中的元素是字典时，是否按关键字参数传递（True）；
            为 False 时将字典整体作为一个位置参数传递

    Returns:
        按输入顺序排列的结果列表
    """
    return parallel_map(func, items, description, log_level, max_workers, progress_type, use_args, use_kwargs)
