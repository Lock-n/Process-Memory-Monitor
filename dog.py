import sys, imp;

# Check if psutil is installed
try:
    f, pathname, desc = imp.find_module("psutil", sys.path[1:])
except ImportError:
    print("Install psutil with \"pip install --user psutil\"")
    sys.exit(0)

import psutil, time, threading, ctypes  # An included library with Python install.

class inputThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print("Enter \"stop\" to stop execution:")
        while True:
            kbinput = input()

            if kbinput.lower() == "stop":
                break


def print_time(threadName, delay, counter):
   while counter:
      if exitFlag:
         threadName.exit()
      time.sleep(delay)
      print ("%s: %s" % (threadName, time.ctime(time.time())))
      counter -= 1


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

names = []
try:
    with open("list.txt", "r") as handle:
        names.append(handle.readline())
        handle.close()
except FileNotFoundError as fnfe:
    print("WARNING: No processes will be closed on detection")

TARGET_NAME = "veyon-server.exe"
SLEEP_TIME_SEC = 0.5

target = find_process(TARGET_NAME)

killable_processes = find_processes(names)

base_memory = None
if (target is not None):
    t_input = inputThread()
    t_input.start()

    while (t_input.isAlive()):
        minfo = target.memory_info()
        
        memory_usage = minfo.rss
        memory_usage_kilobytes = memory_usage / 1024
        memory_usage_megabytes = memory_usage_kilobytes / 1024
        print("Memory usage: " + str(memory_usage_kilobytes) + " KB")

        if (not base_memory):
            base_memory = memory_usage_kilobytes

        if (memory_usage_kilobytes > base_memory + 1000):
            for killable_process in killable_processes:
                killable_process.kill()
                killable_processes.remove(killable_process)
            
            Mbox("Hm...", "Maybe...", 0)

        try:
            time.sleep(SLEEP_TIME_SEC)
        except KeyboardInterrupt:
            break