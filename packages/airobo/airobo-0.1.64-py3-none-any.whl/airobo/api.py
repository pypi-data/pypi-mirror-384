"""
API callbacks!
"""

# Declarations / modules
from airobo.modules.android.publishAndroid import publish_android
from airobo.modules.ios.publishIOS import publish_ios
from airobo.modules.getLatestAppSource import get_app_for_publishing

# ======================================================================================

"""
Simulate publishing something.
"""
def publish(plat=None):
    if plat != "ios" and plat != "android" and plat != None:
        return "Supply a valid platform type!"
    
    # First, get the latest app source (only once)
    print("=======================================")
    print("""
  ___  ___________ ___________  _____ 
 / _ \|_   _| ___ \  _  | ___ \|  _  |
/ /_\ \ | | | |_/ / | | | |_/ /| | | |
|  _  | | | |    /| | | | ___ \| | | |
| | | |_| |_| |\ \\ \_/ / |_/ /\ \_/ /
\_| |_/\___/\_| \_|\___/\____/  \___/ 

[PUBLISHING]..                                      
""")
    source_result = get_app_for_publishing()
    
    if not source_result["success"]:
        print(f"❌ Failed to get app source: {source_result['message']}")
        return {"success": False, "message": "Failed to get app source"}
    
    app_path = source_result["local_path"]
    
    # Now publish to the specified platform(s)
    if plat == "ios":
        publish_ios(app_path)
    elif plat == "android":
        publish_android(app_path)
    else:                       #default : publish all.
        publish_ios(app_path)
        publish_android(app_path)

#----------------------------------------

"""
Get version from package metadata
"""
def version():
    try:
        import importlib.metadata
        # Get version from installed package metadata
        print(importlib.metadata.version('airobo'))
    except Exception:
        # Fallback if package not installed or other error
        print("0.1.10")