# airobo/modules/capacitorBuild.py
"""
Shared Capacitor Build Module
"""
import subprocess
import os


def prepare_capacitor_app(app_path):
    print("Preparing Capacitor app...")
    
    try:
        original_dir = os.getcwd()
        os.chdir(app_path)
        
        print("Installing dependencies...")
        # Run npm install silently
        subprocess.run(["npm", "install"], check=True, shell=True, 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("Building web assets...")
        # Run npm build silently  
        subprocess.run(["npm", "run", "build"], check=True, shell=True,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("Capacitor app prepared")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Capacitor preparation failed: {e}")
        return False
    finally:
        os.chdir(original_dir)

def sync_platform(app_path, platform):
    print(f"Syncing to {platform}...")
    
    try:
        original_dir = os.getcwd()
        os.chdir(app_path)
        
        subprocess.run(["npx", "cap", "sync", platform], check=True, shell=True,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print(f"{platform} sync completed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {platform} sync failed: {e}")
        return False
    finally:
        os.chdir(original_dir)