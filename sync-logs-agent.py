#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import signal
import urllib2
import multiprocessing

class LogsAgent:
    def __init__(self, log_file, api_url, timeout=None):
        self.log_file = log_file
        self.api_url = api_url
        self.timeout = timeout
        self.stop_event = multiprocessing.Event()

    def validate_file(self):
        """Check if log file exists and is accessible"""
        if not os.path.isfile(self.log_file):
            sys.stderr.write("[ERROR] Log file not found: {0}\n".format(self.log_file))
            return False
        return True

    def validate_api(self):
        """Test API connection"""
        try:
            data = json.dumps({'test': 'connection'})
            request = urllib2.Request(
                self.api_url, data, {"Content-Type": "application/json"}
            )
            request.get_method = lambda: "POST"
            response = urllib2.urlopen(request, timeout=2)
            return response.getcode() == 200
        except Exception as e:
            sys.stderr.write("[ERROR] Could not connect to API: {0}\n".format(str(e)))
            return False

    def read_logs(self):
        """Tail log file and send entries to API"""
        try:
            with open(self.log_file, "r") as f:
                f.seek(0, os.SEEK_END)
                while not self.stop_event.is_set():
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    self.send_log(line.strip())
        except IOError as e:
            sys.stderr.write("[ERROR] Could not read log file: {0}\n".format(str(e)))
            self.stop_event.set()

    def send_log(self, log_data):
        """Send log entry to API (silently)"""
        try:
            data = json.dumps({
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'message': log_data,
                'source': self.log_file
            })
            request = urllib2.Request(self.api_url, data, {"Content-Type": "application/json"})
            request.get_method = lambda: "POST"
            urllib2.urlopen(request, timeout=2)
        except Exception:
            # Fail silently
            pass

    def run(self):
        """Main agent execution method"""
        # Ignore interrupt signals in child process
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        
        if not self.validate_file() or not self.validate_api():
            sys.exit(1)
        
        if self.timeout:
            # Run for specified time if timeout is set
            start_time = time.time()
            while time.time() - start_time < self.timeout and not self.stop_event.is_set():
                self.read_logs()
        else:
            # Run forever in background
            self.read_logs()

def start_agent(log_file, api_url, timeout=None):
    """Start a new agent process"""
    agent = LogsAgent(log_file, api_url, timeout)
    process = multiprocessing.Process(target=agent.run)
    process.daemon = False  # Important for independent running
    process.start()
    return (process, agent)

def main():
    """Main application entry point"""
    # Ignore Ctrl+C in main process while configuring agents
    original_sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
    
    print("=== Log Sync Agent ===")
    
    try:
        while True:
            print("\nConfigure new agent (leave empty to finish setup)")
            log_file = raw_input("Log file path: ").strip()
            if not log_file:
                break
                
            api_url = raw_input("API URL: ").strip()
            timeout = raw_input("Test duration in seconds (optional): ").strip()
            timeout = int(timeout) if timeout.isdigit() else None
            
            # Validate before starting
            test_agent = LogsAgent(log_file, api_url)
            if not test_agent.validate_file():
                continue
            if not test_agent.validate_api():
                continue
            
            process, agent = start_agent(log_file, api_url, timeout)
            print("Agent started (PID: {0}) for {1}".format(process.pid, log_file))
            
            if timeout:
                time.sleep(timeout)
                agent.stop_event.set()
                process.terminate()
                print("Test completed for {0}".format(log_file))
        
        # Restore original signal handler
        signal.signal(signal.SIGINT, original_sigint)
        
        print("\nAgents are running in background.")
        print("To stop agents, use: kill <PID>")
        
        # Exit immediately without waiting
        sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nExiting configuration. Agents will continue running.")
        print("To stop agents, use: kill <PID>")
        sys.exit(0)

if __name__ == "__main__":
    main()