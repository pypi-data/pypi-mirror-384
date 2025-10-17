# -*- coding: utf-8 -*-

import os
import time
import ctypes

class PidFile(object):
    def __init__(self, file=None, timeout=0, exit_code=0, raise_except=False):
        self.file = file
        self.timeout = timeout
        self.exit_code = exit_code
        self.raise_except = raise_except
        self.os_win = 1 if os.sep == '\\' else 0

    def __enter__(self):
        self.lock()
        return self

    def __exit__(self, exc_type=None, exc_value=None, exc_tb=None):
        self.unlock()

    def _is_process_running(self, pid):
        """
        Check if a process with given PID is running.
        
        Args:
            pid: Process ID to check
            
        Returns:
            bool: True if process is running, False otherwise
        """
        if not pid:
            return False
        
        try:
            if self.os_win:
                # On Windows, use Windows API to check process
                PROCESS_QUERY_INFORMATION = 0x0400
                PROCESS_VM_READ = 0x0010
                
                # Open process
                handle = ctypes.windll.kernel32.OpenProcess(
                    PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
                    False, pid
                )
                
                if handle:
                    # Close handle
                    ctypes.windll.kernel32.CloseHandle(handle)
                    return True
                return False
            else:
                # On Unix/Linux, use os.kill to check process
                os.kill(pid, 0)  # Signal 0 doesn't send actual signal, but checks if process exists
                return True
        except OSError:
            # Process doesn't exist or no permission to access
            return False
        except Exception:
            # Other exception cases, return False by default
            return False

    def _kill_process(self, pid):
        """
        Kill a process with given PID.
        
        Args:
            pid: Process ID to kill
        """
        try:
            if self.os_win:
                # Force terminate process on Windows
                PROCESS_TERMINATE = 0x0001
                handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
                if handle:
                    ctypes.windll.kernel32.TerminateProcess(handle, -1)
                    ctypes.windll.kernel32.CloseHandle(handle)
            else:
                # Force kill process on Unix/Linux
                os.kill(pid, 9)  # SIGKILL signal
        except Exception:
            pass  # Ignore exceptions when terminating process

    def lock(self):
        if not self.file:
            return
        if os.path.exists(self.file):
            pid = 0
            with open(self.file, 'r') as f:
                pid = int(f.read())
            if pid:
                # Use new process checking method
                if self._is_process_running(pid):
                    c = 1
                    if self.timeout:
                        mtime = os.path.getmtime(self.file)
                        if time.time() - mtime > self.timeout:
                            self._kill_process(pid)
                            c = 0
                    if c:
                        s = "Already running, pid: " + str(pid)
                        if self.raise_except:
                            raise Exception(s)
                        else:
                            print(s)
                            exit(self.exit_code)

                os.unlink(self.file)
        with open(self.file, 'w') as f:
            f.write(str(os.getpid()))

    def unlock(self):
        if not self.file:
            return
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:
                pid = int(f.read())
            if pid == os.getpid():
                os.unlink(self.file)
