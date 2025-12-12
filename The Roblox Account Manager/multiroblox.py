import sys
import time
import win32api
import win32event
import winerror

def main():

    try:
        mutex = win32event.CreateMutex(None, 1, "ROBLOX_singletonEvent")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
           
            sys.exit(0)
    except Exception:
        sys.exit(0)
    
   
    try:
        while True:
            time.sleep(3600)  
    except KeyboardInterrupt:
        pass  
    finally:
       
        try:
            win32api.CloseHandle(mutex)
        except Exception:
            pass

if __name__ == "__main__":
    
    try:
        import win32api
        import win32event
    except ImportError:
        sys.exit(1)  
    
    main()