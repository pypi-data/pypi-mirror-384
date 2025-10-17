"""
Android App Build Module
Handles the building of Android App Bundles (.aab files)
"""
import subprocess
import os
import shutil
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any
from airobo.modules.capacitorMacro import prepare_capacitor_app, sync_platform


def _find_jdk21_path():
    """Try to find a JDK 21 installation path on this machine."""
    # 1) Respect existing JAVA_HOME if it's a 21
    java_home = os.environ.get("JAVA_HOME")
    if java_home and ("21" in java_home or Path(java_home, "release").exists()):
        try:
            rel = Path(java_home, "release")
            if rel.exists():
                txt = rel.read_text(errors="ignore")
                if "JDK 21" in txt or 'JAVA_VERSION="21' in txt:
                    return java_home
        except Exception:
            pass

    # 2) Common Windows locations
    common_windows = [
        r"C:\\Program Files\\Java",
        r"C:\\Program Files\\Microsoft",
        r"C:\\Program Files\\Eclipse Adoptium",
    ]
    for base in common_windows:
        if os.path.isdir(base):
            try:
                for entry in os.listdir(base):
                    if "21" in entry.lower() and entry.lower().startswith(("jdk", "temurin", "microsoft")):
                        cand = os.path.join(base, entry)
                        if os.path.isdir(cand):
                            return cand
            except Exception:
                pass

    # 3) Fallback None
    return None


def _gradle_env_with_jdk21():
    """Build an environment dict ensuring Gradle uses JDK 21 if found."""
    env = os.environ.copy()
    jdk21 = _find_jdk21_path()
    if jdk21:
        jdk_bin = os.path.join(jdk21, "bin")
        # Prepend JDK bin for safety
        env["PATH"] = f"{jdk_bin};{env.get('PATH','')}"
        env["JAVA_HOME"] = jdk21
    return env, jdk21


def force_clean_gradle(android_dir):
    """Force clean Gradle build directories"""
    print("🧹 Force cleaning Gradle build...")
    
    gradlew_cmd = "gradlew.bat" if platform.system() == "Windows" else "./gradlew"
    env, jdk21 = _gradle_env_with_jdk21()
    # Export Android SDK env vars if we can detect it
    sdk = _detect_android_sdk_path()
    if sdk:
        env["ANDROID_SDK_ROOT"] = sdk
        env.setdefault("ANDROID_HOME", sdk)
    
    try:
        # Prefer setting org.gradle.java.home if we found JDK 21
        cmd = [gradlew_cmd]
        if jdk21:
            cmd.append(f"-Dorg.gradle.java.home={jdk21}")
        cmd.append("clean")
        subprocess.run(cmd, 
                      cwd=android_dir, 
                      check=True, 
                      shell=True,
                      env=env,
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        print("✅ Gradle clean completed")
    except subprocess.CalledProcessError:
        print("⚠️ Gradle clean failed, attempting force clean...")
        
        # Force clean by manually deleting build directories
        import time
        
        build_dirs = [
            os.path.join(android_dir, "app", "build"),
            os.path.join(android_dir, "build"),
            os.path.join(android_dir, ".gradle")
        ]
        
        for build_dir in build_dirs:
            if os.path.exists(build_dir):
                try:
                    # Wait a moment and try to delete
                    time.sleep(1)
                    shutil.rmtree(build_dir, ignore_errors=True)
                    print(f"🗑️ Removed {os.path.basename(build_dir)} directory")
                except Exception as e:
                    print(f"⚠️ Could not remove {os.path.basename(build_dir)}: {str(e)[:50]}...")
        
        print("✅ Force clean completed")


def build_android_bundle(app_path):
    """
    Build Android App Bundle (.aab) from the app source
    
    Args:
        app_path (str): Path to the app source code
        
    Returns:
        Optional[str]: Path to the generated AAB file, or None if build failed
    """
    print("🔨 Building Android App Bundle...")
    
    # Step 1: Prepare Capacitor app
    print("📱 Preparing Capacitor app...")
    if not prepare_capacitor_app(app_path):
        print("❌ Capacitor preparation failed")
        return None
    
    # Step 2: Sync to Android platform
    print("🔄 Syncing to Android...")
    if not sync_platform(app_path, "android"):
        print("❌ Android sync failed")
        return None
    
    android_dir = os.path.join(app_path, "android")
    
    # Create output directory (under app cache root, not under android/)
    output_dir = create_build_output_dir(app_path)
    
    # Force clean first
    force_clean_gradle(android_dir)
    
    # Configure Android SDK
    _ensure_android_sdk_config(android_dir)
    
    # Update version based on git commits (using app root)
    update_android_version(app_path)
    vinfo = get_current_version_info(app_path) or {}
    version_label = vinfo.get("version_name") or str(vinfo.get("version_code") or "unknown")
    # Sanitize version label for filenames
    version_label = str(version_label).replace("/", "-").replace(" ", "-")
    
    # Get the .aab file path before building
    expected_aab_path = os.path.join(android_dir, "app", "build", "outputs", "bundle", "release", "app-release.aab")
    
    # Build release bundle using gradlew
    print("🏗️  Building release bundle...")
    
    # Run Gradle bundle command
    gradlew_cmd = "gradlew.bat" if platform.system() == "Windows" else "./gradlew"
    env, jdk21 = _gradle_env_with_jdk21()
    # Export Android SDK env vars if we can detect it
    sdk = _detect_android_sdk_path()
    if sdk:
        env["ANDROID_SDK_ROOT"] = sdk
        env.setdefault("ANDROID_HOME", sdk)
    cmd = [gradlew_cmd]
    if jdk21:
        print(f"🔧 Using JDK 21 at: {jdk21}")
        cmd.append(f"-Dorg.gradle.java.home={jdk21}")
    # Add helpful flags; keep no-daemon and stacktrace for clearer errors
    cmd += [
        "--no-daemon",
        "--stacktrace",
        "bundleRelease",
    ]
    result = subprocess.run(cmd, 
                          cwd=android_dir,
                          shell=True, 
                          capture_output=True, 
                          text=True,
                          env=env)
    
    if result.returncode != 0:
        print(f"❌ Gradle build failed:")
        print(result.stderr)
        return None
    
    # Check if AAB was created
    if not os.path.exists(expected_aab_path):
        print(f"❌ AAB file not found at expected location: {expected_aab_path}")
        return None
    
    # Copy AAB to output directory with version
    aab_filename = f"app-release-{version_label}.aab"
    final_aab_path = os.path.join(output_dir, aab_filename)
    shutil.copy2(expected_aab_path, final_aab_path)
    
    print(f"✅ Android App Bundle built successfully!")
    print(f"📱 Version: {version_label}")
    print(f"📦 Output: {final_aab_path}")
    
    return final_aab_path

def update_android_version(app_path):
    """Update Android version codes before building using git commit count"""
    import os
    import re
    import subprocess
    from datetime import datetime
    
    print("Updating Android version...")
    
    try:
        # Path to build.gradle file
        gradle_file = os.path.join(app_path, "android", "app", "build.gradle")
        
        if not os.path.exists(gradle_file):
            print("❌ build.gradle not found")
            return False
        
        # Get git commit count as version code
        original_dir = os.getcwd()
        os.chdir(app_path)
        
        try:
            git_result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            new_version_code = int(git_result.stdout.strip())
        except subprocess.CalledProcessError:
            print("❌ Failed to get git commit count, using timestamp fallback")
            new_version_code = int(datetime.now().timestamp())
        finally:
            os.chdir(original_dir)
        
        # Get git tag or branch for version name
        os.chdir(app_path)
        try:
            # Try to get latest git tag
            tag_result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"], 
                capture_output=True, 
                text=True
            )
            if tag_result.returncode == 0:
                version_name = tag_result.stdout.strip()
            else:
                # Fallback to branch name + commit count
                branch_result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                    capture_output=True, 
                    text=True,
                    check=True
                )
                branch_name = branch_result.stdout.strip()
                # Sanitize branch name for safe versionName (no slashes/spaces)
                import re as _re
                safe_branch = _re.sub(r"[^A-Za-z0-9._-]+", "-", branch_name)
                version_name = f"{safe_branch}-{new_version_code}"
        except subprocess.CalledProcessError:
            # Final fallback
            version_name = f"build-{new_version_code}"
        finally:
            os.chdir(original_dir)
        
        # Read current build.gradle
        with open(gradle_file, 'r') as f:
            content = f.read()
        
        # Update versionCode
        content = re.sub(
            r'versionCode\s+\d+',
            f'versionCode {new_version_code}',
            content
        )
        
        # Update versionName
        content = re.sub(
            r'versionName\s+["\'][^"\']*["\']',
            f'versionName "{version_name}"',
            content
        )
        
        # Write back to file
        with open(gradle_file, 'w') as f:
            f.write(content)
        
        print(f"Updated versionCode to: {new_version_code}")
        print(f"Updated versionName to: {version_name}")
        return True
        
    except Exception as e:
        print(f"❌ Version update failed: {e}")
        return False

def get_current_version_info(app_path):
    """Get current version info from build.gradle"""
    import os
    import re
    
    gradle_file = os.path.join(app_path, "android", "app", "build.gradle")
    
    if not os.path.exists(gradle_file):
        return None
    
    try:
        with open(gradle_file, 'r') as f:
            content = f.read()
        
        version_code_match = re.search(r'versionCode\s+(\d+)', content)
        version_name_match = re.search(r'versionName\s+["\']([^"\']*)["\']', content)
        
        return {
            "version_code": int(version_code_match.group(1)) if version_code_match else None,
            "version_name": version_name_match.group(1) if version_name_match else None
        }
    except:
        return None

def create_build_output_dir(app_path):
    """Create a build output directory in the app cache"""
    import os
    
    # Create builds directory in the same cache location as the app
    app_name = os.path.basename(app_path)
    cache_dir = os.path.dirname(app_path)  # This is the app-cache directory
    build_dir = os.path.join(cache_dir, f"{app_name}-builds", "android")
    
    # Create directory if it doesn't exist
    os.makedirs(build_dir, exist_ok=True)
    
    print(f"Build output directory: {build_dir}")
    return build_dir

def _detect_android_sdk_path() -> Optional[str]:
    """Detect Android SDK path from env or common locations, return with forward slashes."""
    # Prefer explicit environment
    for key in ("ANDROID_SDK_ROOT", "ANDROID_HOME"):
        val = os.environ.get(key)
        if val and os.path.isdir(val):
            return val.replace("\\", "/")

    # Common Windows locations
    candidates = [
        os.path.expanduser("~/AppData/Local/Android/Sdk"),
        f"C:/Users/{os.getlogin()}/AppData/Local/Android/Sdk",
        "C:/Android/Sdk",
        "C:/Program Files/Android/Sdk",
        "C:/Program Files (x86)/Android/Sdk",
    ]
    for p in candidates:
        if os.path.isdir(p):
            return p.replace("\\", "/")
    return None


def _ensure_android_sdk_config(android_path):
    """
    Ensure Android SDK is properly configured by creating local.properties file
    with a normalized (forward slash) sdk.dir.
    """
    local_properties_path = os.path.join(android_path, "local.properties")
    sdk = _detect_android_sdk_path()
    if sdk:
        # Always write forward slashes; Gradle accepts this on Windows
        with open(local_properties_path, 'w', encoding='utf-8') as f:
            f.write(f"sdk.dir={sdk}\n")
        print(f"✅ Android SDK configured: {sdk}")
    else:
        print("⚠️ Android SDK not found. Please install Android Studio or set ANDROID_SDK_ROOT")
        print("   Download from: https://developer.android.com/studio")



