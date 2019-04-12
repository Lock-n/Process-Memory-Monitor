import sys, imp;

# Check if psutil is installed
try:
    f, pathname, desc = imp.find_module("psutil", sys.path[1:])
except ImportError:
    print("Install psutil with \"pip install --user psutil\"")
    sys.exit(0)

import psutil, time, threading, ctypes  # An included library with Python install.

class MemoryMonitor:
    TARGET_NAME = "veyon-server.exe"
    SLEEP_TIME_SEC = 0.5
    N_ITERATIONS_TO_PRINT = 5

    class InputThread (threading.Thread):
        def __init__(self, parent):
            threading.Thread.__init__(self)
            self.parent = parent

        def run(self):
            print("Enter \"stop\" to stop execution:")
            while True:
                kbinput = input().lower()

                if kbinput == "stop":
                    break
                elif kbinput == "base_memory":
                    print(self.parent.base_memory)
                elif kbinput == "help":
                    print("stop: stop execution\nbase_memory: print base_memory\n" +
                        "set-print-speed N: Set number of iterations until print\n" +
                        "set-check-speed N: Number of seconds to sleep between each check iteration\n" +
                        "print_procs: print the processes objects that will be killed upon detection\n" +
                        "print_names: print the list of names that was read from file\n" +
                        "fetch-procs-again: Read the file and fetch the processes (that will be killed upon detection) again\n" +
                        "set-base-memory: Sets the base memory i. e. the amount in KB that will be used as a base for detecting an increase in memory usage")
                elif kbinput.split(" ")[0] == "set-print-speed":
                    try:
                        n = float(kbinput.split(" ")[1])

                        if (n < 1):
                            raise ValueError()

                        self.parent.N_ITERATIONS_TO_PRINT = n
                    except ValueError:
                        print("ERROR: Not a number")
                elif kbinput.split(" ")[0] == "set-check-speed":
                    try:
                        n = float(kbinput.split(" ")[1])

                        self.parent.SLEEP_TIME_SEC = n
                    except ValueError:
                        print("ERROR: Not a number")
                elif kbinput == "print_procs":
                    print(self.parent.killable_processes)
                elif kbinput == "print_names":
                    print(self.parent.names)
                elif kbinput.split(" ")[0] == "set-base-memory":
                    try:
                        n = float(kbinput.split(" ")[1])

                        

                        while True:
                            print("Are you sure? (Y/N)")

                            kbinput = input().lower()

                            if kbinput == "y":
                                self.parent.base_memory = n
                                break
                            elif kbinput == "n":
                                break

                    except ValueError:
                        print("ERROR: Not a number")
                elif kbinput.split(" ") == "fetch-procs-again":
                    self.parent.names = MemoryMonitor.read_names_from_file()
                    self.parent.killable_processes = MemoryMonitor.find_processes(self.parent.names)
                    

    @staticmethod
    def Mbox(title, text, style):
        return ctypes.windll.user32.MessageBoxW(0, text, title, style)

    ##  Styles:
    ##  0 : OK
    ##  1 : OK | Cancel
    ##  2 : Abort | Retry | Ignore
    ##  3 : Yes | No | Cancel
    ##  4 : Yes | No
    ##  5 : Retry | No 
    ##  6 : Cancel | Try Again | Continue

    @staticmethod
    def find_process(name: str, get_with_greatest_memory_usage=False):
        process_with_greatest_memory = None
        for proc in psutil.process_iter():
            try:
                if proc.name() == name:
                    if (get_with_greatest_memory_usage):
                        if process_with_greatest_memory == None:
                            process_with_greatest_memory = proc
                        else:
                            if proc.memory_info().rss > process_with_greatest_memory.memory_info().rss:
                                process_with_greatest_memory = proc
                    else:
                        return proc
            except psutil.NoSuchProcess:
                continue
        
        return None if not get_with_greatest_memory_usage else process_with_greatest_memory

    @staticmethod
    def find_processes(names: list):
        process_with_greatest_memory = None
        processes = []
        for proc in psutil.process_iter():
            try:
                if proc.name() in names:
                        processes.append(proc)
            except psutil.NoSuchProcess:
                continue
        
        return processes

    @staticmethod
    def read_names_from_file():
        names = []
        try:
            with open("list.txt", "r") as handle:
                for line in handle:
                    names.append(line.strip())
                handle.close()
        except FileNotFoundError as fnfe:
            print("WARNING: No processes will be closed on detection")

        return names

    def monitor(self):
        self.names = MemoryMonitor.read_names_from_file()
        target = MemoryMonitor.find_process(self.TARGET_NAME)
        self.killable_processes = MemoryMonitor.find_processes(self.names)

        self.base_memory = None
        if (target is not None):
            t_input = MemoryMonitor.InputThread(self)
            t_input.start()

            iterations_count = 1
            while (t_input.isAlive()):
                minfo = target.memory_info()
                
                memory_usage = minfo.rss
                memory_usage_kilobytes = memory_usage / 1024
                #memory_usage_megabytes = memory_usage_kilobytes / 1024
                
                if (iterations_count >= self.N_ITERATIONS_TO_PRINT):
                    print("Memory usage: " + str(memory_usage_kilobytes) + " KB")
                    iterations_count = 1
                else:
                    iterations_count = iterations_count + 1

                if (not self.base_memory):
                    self.base_memory = memory_usage_kilobytes

                # 31000-45000 KB or 26500-33000 K in taskmgr.exe
                if (memory_usage_kilobytes > self.base_memory + 1000):
                    for killable_process in self.killable_processes:
                        try:
                            killable_process.kill()
                        except psutil.NoSuchProcess:
                            pass
                        self.killable_processes.remove(killable_process)
                    
                    MemoryMonitor.Mbox("Hm...", "Maybe...", 0)

                try:
                    time.sleep(self.SLEEP_TIME_SEC)
                except KeyboardInterrupt:
                    break
        
mm = MemoryMonitor()
mm.monitor()