import threading
import time
import subprocess
import select
import sys


class PythonExecutor:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.output = [[],[]] #stdout stderror

    def kill_after_timeout(self):
        """Kill process after timeout if still running"""
        time.sleep(self.timeout)
        if not self.stop_event.is_set():
            try:
                if self.process and self.process.poll() is None:
                    print("Terminating due to timeout Jumbo")
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait(timeout=1)
                    finally:
                        self.stop_event.set()
            except Exception as err:
                print(f"Error in timeout handler: {err}")
                self.stop_event.set()

    def executeCommand(self, command,env=None,cwd=None):
        """Execute command and capture output"""
        try:
            self.process = subprocess.Popen(
                command,
                stderr=subprocess.PIPE,stdout=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                env=env,
                cwd=cwd,
            )

            # Read output until process finishes or stop event is set
            while not self.stop_event.is_set() and self.process.poll() is None:
                # Check if there's data to read from stdout
                if self.process.stdout:
                    line = self.process.stdout.readline()
                    # print("our line ",line.strip())
                    if line:
                        self.output[0].append(line)
                
                # Check if there's data to read from stderr
                if self.process.stderr:
                    line = self.process.stderr.readline()
                    if line:
                        # print(f"ERROR: {line.strip()}")
                        self.output[1].append(line)
                
                # Small sleep to prevent busy waiting
                time.sleep(0.01)

            # Read any remaining output after process finishes
            if self.process.stdout:
                remaining_stdout = self.process.stdout.read()
                if remaining_stdout:
                    for line in remaining_stdout.splitlines(keepends=True):
                        # print(line.strip())
                        self.output[0].append(line)

            if self.process.stderr:
                remaining_stderr = self.process.stderr.read()
                if remaining_stderr:
                    for line in remaining_stderr.splitlines(keepends=True):
                        # print(f"ERROR bingo : {line.strip()}")
                        self.output[1].append(line)

            print("Process finished")
            self.stop_event.set()

        except Exception as err:
            print(f"Error in executeCommand: {err}")
            self.stop_event.set()
    
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

    def runCommand(self, command, self_exit=False,env=None,cwd=None):
        """Run command with timeout monitoring"""
        self.output = [[],[]] #[output, error]
        self.process = None

        if self_exit:
            self.executeSelfExitingCommand(command,env,cwd)
        else:
            self.stop_event = threading.Event()
            
            # Start execution thread
            exec_thread = threading.Thread(target=self.executeCommand, args=(command,env,cwd,))
            timeout_thread = threading.Thread(target=self.kill_after_timeout)
            
            exec_thread.start()
            timeout_thread.start()

            # Wait for execution to complete
            exec_thread.join()
            
            # Stop timeout thread if execution finished first
            self.stop_event.set()
            
            # Don't wait too long for timeout thread
            timeout_thread.join(timeout=1)

        return self.output


# Alternative implementation using threading for concurrent stdout/stderr reading
class ImprovedPythonExecutor:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.output = [[],[]]

        self.stop_event = threading.Event()
        self.process = None

    def read_stream(self, stream, stream_name):
        """Read from a stream (stdout or stderr) in a separate thread"""
        try:
            for line in iter(stream.readline, ''):
                if self.stop_event.is_set():
                    break
                if line:
                    # if stream_name == 'stderr':
                    #     print(f"ERROR: {line.strip()}")
                    # else:
                    #     print(line.strip())
                    if stream_name == "stdout":
                        self.output[0].append(line)
                    else:
                        self.output[1].append(line)

                    # self.output.append((stream_name, line))
        except Exception as err:
            print(f"Error reading {stream_name}: {err}")
        finally:
            stream.close()

    def timeout_handler(self):
        """Handle timeout"""
        time.sleep(self.timeout)
        if not self.stop_event.is_set():
            print("Terminating due to timeout")
            self.stop_event.set()

            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()

    def runCommand(self, command,cwd):
        """Run command with improved concurrent output handling"""
        self.output = [[],[]]
        self.stop_event = threading.Event()

        try:
            # Start process
            self.process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            # Start reader threads
            stdout_thread = threading.Thread(
                target=self.read_stream, 
                args=(self.process.stdout, 'stdout'),
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=self.read_stream, 
                args=(self.process.stderr, 'stderr'),
                daemon=True
            )
            timeout_thread = threading.Thread(target=self.timeout_handler,daemon=True)

            stdout_thread.start()
            stderr_thread.start()
            timeout_thread.start()

            # Wait for process to complete
            self.process.wait()
            
            # Signal threads to stop
            self.stop_event.set()

            # Wait for threads to finish
            stdout_thread.join(timeout=2)
            stderr_thread.join(timeout=2)
            timeout_thread.join(timeout=1)

            print("Command completed")

        except Exception as err:
            # print(f"Error: {err}")
            self.stop_event.set()

        return self.output


# # Test both implementations
# if __name__ == "__main__":
#     print("=== Testing Original Fixed Version ===")
#     executor1 = PythonExecutor(timeout=5)
#     result1_output, result1_error = executor1.runCommand(["pip", "install","django-boto"],True)
#     print(f"Captured {len(result1_output)} lines")
    
#     print("\n","#"*10,"\n")
#     print("\n".join(result1_output))

#     result2, result2_error = executor1.runCommand(["python", "manage.py","runserver"])
#     print("\n Result 2 \n")
#     print("".join(result2_error))
    
#     # print("\n=== Testing Improved Version ===")
#     # executor2 = ImprovedPythonExecutor(timeout=5)
#     # result2 = executor2.runCommand(["python", "manage.py","runserver"])
#     # print(f"Captured {len(result2)} lines")
    
#     # print("\n=== Testing with a command that has both stdout and stderr ===")
#     # executor3 = ImprovedPythonExecutor(timeout=5)
#     # result3 = executor3.runCommand(["python3", "-c", "import sys; print('stdout message'); print('stderr message', file=sys.stderr)"])
#     # print(f"Captured {len(result3)} lines")
#     # for stream, line in result3:
#     #     print(f"{stream}: {line.strip()}")