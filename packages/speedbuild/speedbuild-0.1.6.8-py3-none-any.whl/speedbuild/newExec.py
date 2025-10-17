import os
import sys
import time
import atexit
import signal
import threading
import subprocess


class PythonExecutor:
    def __init__(self, timeout=6):
        self.timeout = timeout
        self.stop_event = threading.Event()
        self.processes = []  # track all processes

        # Register cleanup at exit
        atexit.register(self.cleanup)

        # Handle Ctrl+C / kill signals
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)

    def read_stream(self, stream, stream_name):
        try:
            for line in stream:
                if self.stop_event.is_set():
                    break
                if stream_name == "stdout":
                    self.output[0].append(line)
                else:
                    self.output[1].append(line)
                # self.output.append((stream_name, line))
        finally:
            stream.close()

    def timeout_handler(self, process):
        time.sleep(self.timeout)
        if not self.stop_event.is_set():
            self.stop_event.set()
            self.kill_process(process)

    def kill_process(self, process):
        if process and process.poll() is None:
            try:
                # Kill the whole process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass  # already gone

    def executeSelfExitingCommand(self,command,env=None,cwd=None):

        process = subprocess.Popen(command,env=env,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        
        stdout, stderr = process.communicate()

        if stdout:
            lines = stdout.decode()
            lines = lines.split("\n")
            for line in lines:
                if len(line.strip()) > 0:
                    self.output[0].append(line)

        if stderr:
            lines = stderr.decode()
            lines = lines.split("\n")
            for line in lines:
                if len(line.strip()) > 0:
                    self.output[1].append(line)

    def runCommand(self, command, cwd,env=None, self_exit=True):
        self.output = [[],[]]
        self.stop_event = threading.Event()

        print("self exist ", "#"*5, self_exit)

        if self_exit:
            self.executeSelfExitingCommand(command,env,cwd)
        else:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                preexec_fn=os.setsid  # create new process group
            )
            self.processes.append(process)

            stdout_thread = threading.Thread(
                target=self.read_stream,
                args=(process.stdout, 'stdout'),
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=self.read_stream,
                args=(process.stderr, 'stderr'),
                daemon=True
            )
            timeout_thread = threading.Thread(
                target=self.timeout_handler,
                args=(process,),
                daemon=True
            )

            stdout_thread.start()
            stderr_thread.start()
            timeout_thread.start()

            process.wait()
            self.stop_event.set()

            stdout_thread.join(timeout=2)
            stderr_thread.join(timeout=2)
            timeout_thread.join(timeout=1)

            self.kill_process(process)

        return self.output

    def cleanup(self):
        """Kill all subprocesses at exit"""
        for process in self.processes:
            self.kill_process(process)

    def handle_exit(self, signum, frame):
        """Handle Ctrl+C or kill signals"""
        print(f"\nReceived signal {signum}, cleaning up...")
        self.cleanup()
        sys.exit(1)
