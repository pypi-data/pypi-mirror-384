import time
import os
import mlog
from mlog import LogManager
from multiprocessing import Pool

log_file = "logs/a1.log"

log_manager = LogManager()
logger_a1 = log_manager.get_logger("a1", log_file=log_file, add_console=False)
# logger_a2 = log_manager.get_logger("a2", log_file=log_file, add_console=False)
# logger_a3 = log_manager.get_logger("a3", log_file=log_file, add_console=False)


# 测试 num 个 日志耗时
def test_speed_time(num = 500):
    import time
    _st = time.time()
    for i in range(num):
        logger_a1.info(i)
    logger_a1.info(f"{num} --- {time.time() - _st}")

# 测试多进程
# 1000 个日志有没有
def test_logger(x):
    _pid = os.getpid()
    logger_a1.info(f"{_pid} -- {x}")


if __name__ == "__main__":
    with open(log_file, "w") as f:
        pass
    with Pool(2) as pool:
        pool.map(test_logger, range(0, 5000))



