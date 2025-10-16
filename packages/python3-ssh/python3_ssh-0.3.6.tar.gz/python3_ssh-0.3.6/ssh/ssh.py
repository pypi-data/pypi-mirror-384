import os
import time
import socket
import paramiko
import subprocess
from datetime import datetime
from func_timeout import func_set_timeout
from func_timeout.exceptions import FunctionTimedOut
from paramiko import SSHException
import time
import functools
import logging
import traceback
import inspect
from typing import Callable, Any
from typing import List, Dict, Any, Optional

log=logging.getLogger(__name__)


class ExecResult():
    def __init__(self, exit_status_code, stdout="", stderr=""):
        self.__exit_status_code = exit_status_code
        self.__stdout = stdout
        self.__stderr = stderr

    @property
    def exit_status_code(self):
        return self.__exit_status_code

    @property
    def stdout(self):
        return self.__stdout

    @property
    def stderr(self):
        return self.__stderr

def enter_and_leave_function(func: Callable) -> Callable:
    """
    函数调用日志装饰器：
    1. 记录函数入参、调用位置
    2. 正常执行时记录返回值
    3. 异常时记录完整堆栈（含函数内具体报错行数）
    """

    @functools.wraps(func)  # 保留原函数元信息（如 __name__、__doc__）
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 获取函数定义的文件路径和行号（基础位置信息）
        func_def_file = inspect.getsourcefile(func) or "unknown_file"
        func_def_file = func_def_file.split("/")[-1]
        func_def_line = inspect.getsourcelines(func)[1] if func_def_file != "unknown_file" else "unknown_line"
        log.info(
            f"[{func_def_file}: {func_def_line}]"
            f"[{func.__name__}()]"
            f"| args={args}, kwargs={kwargs}"
        )

        try:
            result = func(*args, **kwargs)
            if isinstance(result, ExecResult):
                if result.exit_status_code == 0:
                    log.info(
                        f"[{func_def_file}: {func_def_line}]"
                        f" finish run function {func.__name__}(), stdout is: {result.stdout} "
                    )
                else:
                    log.error(
                        f"[{func_def_file}: {func_def_line}]"
                        f" failed to run function {func.__name__}(), stderr is: {result.stderr} "
                    )
            else:
                log.info(
                    f"[{func_def_file}: {func_def_line}]"
                    f" finish run function {func.__name__}(), return value is: {result} "
                )
            return result

        except Exception as e:
            error_traceback = traceback.format_exc()

            log.error(
                f"[{func_def_file}: {func_def_line}]"
                f"failed to run function {func.__name__}() :Failed. "
                f"| error_type：{type(e).__name__} "
                f"| error_message：{str(e)} "
                f"| full_stack_trace：\n{error_traceback}",
                exc_info=False  # 已手动捕获堆栈，避免 logging 重复打印
            )
            raise  # 重新抛出异常，不中断原异常链路

    return wrapper

class SSHClient(object):
    def __init__(self, ip="127.0.0.1", port=22, username="root", password="", connect_timeout=10):
        self.__ip = ip
        self.__port = port
        self.__username = username
        self.__password = password
        self.__connect_timeout = connect_timeout
        self.__ssh = None
        self.__sftp = None

    @property
    def ip(self):
        return self.__ip

    @property
    def port(self):
        return self.__port

    @property
    def is_sshable(self):
        ssh = None
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.__ip,
                port=self.__port,
                username=self.__username,
                password=self.__password,
                look_for_keys=False,
                allow_agent=False,
                timeout=self.__connect_timeout
            )
            return True
        except SSHException as e:
            log.warning(f"{self.__ip}:{self.__port} | cannot create ssh session, err msg is {str(e)}.")
            return False
        except Exception as e:
            log.warning(f"{self.__ip}:{self.__port} | server is not sshable.")
            return False
        finally:
            try:
                ssh.close()
            except Exception as e:
                pass

    @enter_and_leave_function
    def wait_for_sshable(self, timeout=60):
        count=0
        while True:
            count += 1
            if self.is_sshable:
                return True
            if count > int(timeout/self.__connect_timeout):
                return False
            time.sleep(self.__connect_timeout)

    @enter_and_leave_function
    def __connect(self):
        log.info(f" {self.__ip}:{self.__port} | begin to create ssh connect.")
        try:
            self.__ssh = paramiko.SSHClient()
            self.__ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.__ssh.connect(
                self.__ip,
                port=self.__port,
                username=self.__username,
                password=self.__password,
                look_for_keys=False,
                allow_agent=False,
                timeout=self.__connect_timeout
            )
            log.info(f"{self.__ip}:{self.__port} | ssh connect successfully.")
            return True
        except socket.timeout as e:
            log.warning(f"{self.__ip}:{self.__port} | failed to ssh connect. err msg is {str(e)}")
            return False
        except SSHException as e:
            log.warning(f"{self.__ip}:{self.__port} | failed to ssh connect. err msg is {str(e)}")
            return False
        except Exception as e:
            log.warning(f"{self.__ip}:{self.__port} | failed to ssh connect. err msg is {str(e)}")
            return False

    def reconnect(self):
        self.close()
        return self.__connect()

    def close(self):
        try:
            self.__sftp.close()
        except:
            pass
        try:
            self.__ssh.close()
        except:
            pass

    @enter_and_leave_function
    def _exec(self, cmd, promt_response,timeout=60):
        log.info(f" {self.__ip}:{self.__port} | begin to run cmd:{cmd}.")
        try:
            if promt_response:
                channel = self.__ssh.exec_command('bash', get_pty=True)[0].channel
                channel.set_window_size(200, 200)
                # channel = self.__ssh.get_transport().open_session()
                # channel.get_pty()  # 获取虚拟终端
                channel.exec_command(cmd)
                output = ""
                begin=datetime.now()
                stderr = ""
                while True:
                    end = datetime.now()
                    if (end-begin).total_seconds()>timeout:
                        output=""
                        stderr=f"timeout to run cmd.{cmd}"
                    if channel.recv_ready():
                        output_chunk  = channel.recv(1024).decode('utf-8', 'ignore')
                        output += output_chunk
                        print(output_chunk, end='')

                        # 检查输出是否包含预期的提示信息
                        for elem in promt_response:
                            prompt = elem["prompt"]
                            response = elem["response"]
                            if prompt in output:
                                # 发送相应的回答
                                channel.send(response)
                    if channel.recv_stderr_ready():
                        stderr_chunk =channel.recv_stderr(2024).decode('utf-8', 'ignore')
                        stderr += stderr_chunk
                        print(stderr_chunk, end='')
                    if channel.closed and not (channel.recv_ready() or channel.recv_stderr_ready()):
                        break
                return_code = channel.recv_exit_status()
                return ExecResult(return_code, output, stderr)
            else:
                stdin, stdout, stderr = self.__ssh.exec_command(cmd,timeout=timeout)
                exit_status = stdout.channel.recv_exit_status()
                std_output = stdout.read().decode()
                std_err = stderr.read().decode()
                if not std_err:
                    log.info(
                        f" {self.__ip}:{self.__port} | successful to run cmd {cmd}, exit_status_code is {exit_status}, output is:{std_output} and stderr:{std_err}.")
                else:
                    log.info(
                    f" {self.__ip}:{self.__port} | successful to run cmd {cmd}, exit_status_code is {exit_status}, output is:{std_output}.")
                return ExecResult(exit_status, std_output, std_err)
        except Exception as e:
            return ExecResult(1, "", str(e))

    @func_set_timeout(1800)
    @enter_and_leave_function
    def exec(self, cmd, promt_response=[], timeout=60):
        try:
            if not self.__ssh:
                if not self.reconnect():
                    raise RuntimeError("ssh transport is not active and failed to reconnect.")
            return self._exec(cmd,promt_response,timeout)
        except Exception as e:
            log.warning(f"when run cmd: {cmd}, meets exception, err msg is {str(e)}")
            return ExecResult(1, "", str(e))

    @enter_and_leave_function
    def _scp_to_remote(self, local_path, remote_path):
        log.info(
            f" {self.__ip}:{self.__port} | Begin to copy file from local {local_path} to remote host {remote_path}.")
        self.__sftp.put(local_path, remote_path)
        rs = self.exec(f"ls {remote_path}")
        if rs.exit_status_code == 0:
            log.info(
                f" {self.__ip}:{self.__port} | Success to copy file from local {local_path} to remote host{remote_path}: OK.")
            return True
        else:
            log.warning(
                f" {self.__ip}:{self.__port} | failed to copy file from local {local_path} to remote host{remote_path}:Error.")
            return False

    @enter_and_leave_function
    def scp_to_remote(self, local_path, remote_path,timeout=120):
        try:
            if not self.__ssh:
                if not self.reconnect():
                    raise RuntimeError("ssh transport is not active and failed to reconnect.")
            if not self.__sftp:
                self.__sftp = self.__ssh.open_sftp()
            return self._scp_to_remote(local_path, remote_path)
        except Exception:
            log.warning(f"when scp from local {local_path} to remote {remote_path}, meets exception.", exc_info=True)
            return False

    @enter_and_leave_function
    def _scp_file_to_local(self, remote_path, local_path):
        log.info(
            f" {self.__ip}:{self.__port} | Begin to copy file from remote {remote_path} to local host {local_path}.")
        if os.path.isfile(local_path):
            subprocess.run(['rm', '-rf', local_path], capture_output=True, text=True)
        self.__sftp.get(remote_path, local_path)
        log.info(
            f" {self.__ip}:{self.__port} | Success to copy file from remote {remote_path} to local host{local_path}:OK.")
        return True

    @enter_and_leave_function
    def scp_file_to_local(self, remote_path, local_path,timeout=120):
        try:
            if not self.__ssh:
                if not self.reconnect():
                    raise RuntimeError("ssh transport is not active and failed to reconnect.")
            if not self.__sftp:
                self.__sftp = self.__ssh.open_sftp()
            return self._scp_file_to_local(remote_path, local_path)
        except Exception:
            log.warning(f"when scp from remote {remote_path} to local {local_path}, meets exception.", exc_info=True)
            return False

    def __del__(self):
        self.close()
