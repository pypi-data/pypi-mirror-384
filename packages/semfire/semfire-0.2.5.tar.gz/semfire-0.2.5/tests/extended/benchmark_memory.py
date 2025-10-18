import psutil
import time
import os

def monitor_memory(pid, duration=10):
    process = psutil.Process(pid)
    mem_usage = []
    for _ in range(duration):
        mem = process.memory_info().rss / (1024 * 1024)  # MB
        mem_usage.append(mem)
        print(f"Memory usage: {mem:.2f} MB")
        time.sleep(1)
    return mem_usage

if __name__ == "__main__":
    pid = int(input("Enter PID to monitor: "))
    monitor_memory(pid)
