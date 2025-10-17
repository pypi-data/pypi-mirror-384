import time
import os
import getpass
import glob
import errno
import logging
import portalocker
from abc import ABC, abstractmethod


# 常量：锁文件最大存活时间（秒）
LOCK_TIMEOUT = 120  # 2 minutes


class MultiProcessSafeRotatingHandlerBase(logging.Handler, ABC):
    """
    日志轮转 Handler 基类
    """
    def __init__(self, filename, backupCount=3):
        super().__init__()
        self.filename = filename
        self.backupCount = backupCount
        self.lockfile = filename + ".lock"

        # 本进程临时文件
        pid = os.getpid()
        user = getpass.getuser()
        self.tmp_file = f"{filename}.tmp.{user}.{pid}"

        self.stream = None

    def emit(self, record):
        try:
            # ✅ 检查锁文件
            if os.path.exists(self.lockfile):
                if self._is_lock_expired():
                    # 清理过期锁
                    try:
                        os.remove(self.lockfile)
                        print(f"[MPLog] Removed stale lock: {self.lockfile}")
                    except Exception as e:
                        print(f"[MPLog] Failed to remove stale lock {self.lockfile}: {e}")
                        self._write_to_tmp(record)
                        return
                else:
                    # 有效锁，写临时文件
                    self._write_to_tmp(record)
                    return

            # ✅ 尝试写主文件
            try:
                self._open_log()
                msg = self.format(record) + '\n'
                self.stream.write(msg)
                self.stream.flush()
            except Exception:
                self._write_to_tmp(record)
                return

            # ✅ 子类决定是否需要轮转
            if self._should_rollover(record):
                self.doRollover()

        except Exception:
            self.handleError(record)

    def _write_to_tmp(self, record):
        """写入本进程临时文件"""
        msg = self.format(record) + '\n'
        try:
            with open(self.tmp_file, 'a', encoding='utf-8') as f:
                f.write(msg)
        except Exception as e:
            print(f"Failed to write tmp: {e}")

    @abstractmethod
    def _should_rollover(self, record) -> bool:
        """子类实现：判断是否需要轮转"""
        pass

    @abstractmethod
    def _do_rollover_impl(self):
        """子类实现：具体的轮转归档逻辑"""
        pass

    def _open_log(self):
        """打开主日志文件"""
        if self.stream is None:
            try:
                self.stream = open(self.filename, 'a', encoding='utf-8')
            except Exception as e:
                print(f"Failed to open {self.filename}: {e}")
                raise

    def _get_file_size(self, filepath):
        """安全获取文件大小"""
        try:
            return os.path.getsize(filepath)
        except (OSError, IOError) as e:
            if e.errno == errno.ENOENT:
                return 0
            raise

    def _is_lock_expired(self):
        """检查锁文件是否存在且是否超时"""
        try:
            st = os.stat(self.lockfile)
            return time.time() - st.st_mtime > LOCK_TIMEOUT
        except (OSError, IOError) as e:
            if e.errno == errno.ENOENT:
                return False
            return False   

    def doRollover(self):
        """执行轮转（跨平台安全）"""
        # ✅ 使用 portalocker 获取独占锁（非阻塞）
        try:
            lock_fd = os.open(self.lockfile, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        except Exception as e:
            return  # 无法创建锁文件

        try:
            # 尝试立即获得独占锁（非阻塞）
            portalocker.lock(lock_fd, portalocker.LOCK_EX | portalocker.LOCK_NB)
            # 加锁成功 → 写入锁信息（可选）
            os.write(lock_fd, f"{os.getpid()}\n{time.time()}".encode())
            os.close(lock_fd)
            lock_fd = None  # 已关闭
        except portalocker.LockException:
            # 无法获得锁 → 其他进程正在轮转
            if lock_fd is not None:
                os.close(lock_fd)
            return
        except Exception as e:
            # 其他异常
            if lock_fd is not None:
                os.close(lock_fd)
            return

        try:
            # ✅ 关闭主文件流
            if self.stream:
                self.stream.close()
                self.stream = None

            # ✅ 执行子类的具体轮转逻辑
            self._do_rollover_impl()

            # ✅ 合并所有临时文件
            self._merge_temp_files()

        finally:
            # ✅ 删除锁文件（释放锁）
            try:
                if os.path.exists(self.lockfile):
                    os.remove(self.lockfile)
            except Exception:
                pass

    def _merge_temp_files(self):
        """合并所有临时文件到主日志"""
        tmp_pattern = f"{self.filename}.tmp.*"
        for tmp_path in glob.glob(tmp_pattern):
            try:
                with open(tmp_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                if data.strip():
                    with open(self.filename, 'a', encoding='utf-8') as logf:
                        logf.write(data)
                os.remove(tmp_path)
            except Exception as e:
                print(f"Merge failed {tmp_path}: {e}")


# ========================================
# 子类：按文件大小轮转
# ========================================
def parse_bytes_size(size_str: str) -> int:
    """
    将表示大小的字符串（如 '1 M', '5K', '2 G'）解析为字节数。
    支持单位：K (KB), M (MB), G (GB)
    不区分大小写，空格可选。
    """
    size_str = size_str.strip().upper()
    
    # 定义单位到字节数的映射（以 1024 为基数）
    units = {
        'K': 1024,
        'M': 1024 * 1024,
        'G': 1024 * 1024 * 1024,
    }

    # 默认单位是字节（无单位时）
    unit = 'B'
    num_part = size_str

    # 从后往前找单位
    for u in units:
        if size_str.endswith(u):
            unit = u
            num_part = size_str[:-len(u)].strip()
            break

    # 解析数值（支持整数和小数）
    try:
        value = float(num_part)
    except ValueError:
        raise ValueError(f"无法解析大小字符串: {size_str}")

    # 计算总字节数
    if unit == 'B':
        return int(value)  # 假设单位是字节
    else:
        return int(value * units[unit])
    
class MultiProcessSafeSizeRotatingHandler(MultiProcessSafeRotatingHandlerBase):
    """
    使用案例
    >>> handler = MultiProcessSafeSizeRotatingHandler(filename="a1.log", maxBytes="1 M")
    >>> get_logger(custom_handler=handler)
    """
    def __init__(self, filename, maxBytes=5 * 1024 * 1024, backupCount=3):
        super().__init__(filename, backupCount)
        if isinstance(maxBytes, str):
            maxBytes = parse_bytes_size(maxBytes)

        if maxBytes <= 0:
            raise ValueError("maxBytes must be positive")
        
        self.maxBytes = maxBytes

    def _should_rollover(self, record) -> bool:
        return self._get_file_size(self.filename) >= self.maxBytes

    def _do_rollover_impl(self):
        # 轮转备份文件
        for i in range(self.backupCount - 1, 0, -1):
            sfn = f"{self.filename}.{i}"
            dfn = f"{self.filename}.{i+1}"
            if os.path.exists(sfn):
                if os.path.exists(dfn):
                    os.remove(dfn)
                os.rename(sfn, dfn)
        if os.path.exists(self.filename):
            dfn = f"{self.filename}.1"
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.filename, dfn)

        # 重新创建空的日志文件
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                pass
        except Exception as e:
            print(f"Failed to recreate log file {self.filename}: {e}")


# ========================================
# 子类：按时间轮转
# ========================================
class MultiProcessSafeTimeRotatingHandler(MultiProcessSafeRotatingHandlerBase):
    """
    使用案例
    >>> handler = MultiProcessSafeTimeRotatingHandler(filename="a2.log", when='H')
    >>> get_logger(custom_handler=handler)
    """
    def __init__(self, filename, when='D', interval= 1, backupCount=7):
        super().__init__(filename, backupCount)
        self.when = when.upper()
        self.interval = max(1, int(interval))  # 至少为 1
        self.last_rollover = int(time.time())

        # 支持的单位映射
        self.when_to_seconds = {
            'S': 10,      # 最少 10s
            'M': 60,      # 分钟
            'H': 3600,    # 小时
            'D': 86400,   # 天
        }

    def _should_rollover(self, record) -> bool:
        now = int(time.time())

        if self.when not in self.when_to_seconds:
            return False

        seconds_per_unit = self.when_to_seconds[self.when]
        total_interval_seconds = seconds_per_unit * self.interval

        # 计算当前属于第几个周期（从 0 开始）
        current_cycle = now // total_interval_seconds
        last_cycle = self.last_rollover // total_interval_seconds

        return current_cycle > last_cycle

    def _do_rollover_impl(self):
        # 按日期重命名，如 log.txt -> log.txt.2025-09-16
        date_str = time.strftime(self._get_rollover_format())
        dfn = f"{self.filename}.{date_str}"
        if os.path.exists(self.filename):
            os.rename(self.filename, dfn)
        with open(self.filename, 'w'): pass
        self.last_rollover = int(time.time())

    def _get_rollover_format(self):
        """
        根据 when 和 interval 返回时间格式字符串
        """
        if self.when == 'S':
            return "%Y-%m-%d-%H:%M:%S"   # 精确到分钟
        if self.when == 'M':
            return "%Y-%m-%d-%H:%M"   # 精确到分钟
        elif self.when == 'H':
            if self.interval >= 24:
                return "%Y-%m-%d"     # 每N小时但N>=24 → 按天
            else:
                return "%Y-%m-%d-%H"  # 按小时
        elif self.when == 'D':
            if self.interval == 1:
                return "%Y-%m-%d"     # 每天
            else:
                return "%Y-%m-%d"     # 每N天，仍用日期表示（如 2025-09-16）
        else:
            return "%Y-%m-%d"         # 默认按天