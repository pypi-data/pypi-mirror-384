"""
GitHub Repository Clone/Pull Module
Handles getting the latest source code from a GitHub repository
"""

import os
import subprocess
import shutil
from pathlib import Path


def get_app_cache_dir():
    """
    Get the user's app cache directory for storing app source code
    
    Returns:
        Path: Path to the cache directory (creates it if it doesn't exist)
    """
    # Get user's home directory
    home = Path.home()
    
    # Create platform-appropriate cache directory
    if os.name == 'nt':  # Windows
        cache_dir = home / 'AppData' / 'Local' / 'airobo' / 'app-cache'
    else:  # macOS/Linux
        cache_dir = home / '.cache' / 'airobo' / 'app-cache'
    
    # Create directory if it doesn't exist
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    return cache_dir


def get_app_cache_info():
    """
    Get information about the app cache directory
    
    Returns:
        dict: Information about cache directory and its contents
    """
    cache_dir = get_app_cache_dir()
    
    info = {
        "cache_directory": str(cache_dir),
        "exists": cache_dir.exists(),
        "projects": []
    }
    
    if cache_dir.exists():
        # List all project directories in cache
        for item in cache_dir.iterdir():
            if item.is_dir():
                is_git_repo = (item / '.git').exists()
                info["projects"].append({
                    "name": item.name,
                    "path": str(item),
                    "is_git_repo": is_git_repo
                })
    
    return info


def get_repo_url_from_env():
    """
    Read the repository URL from .env file
    
    Returns:
        tuple: (repo_url, branch) or (None, None) if not found
    """
    try:
        # Look for .env file in current directory and parent directories
        current_dir = Path.cwd()
        env_file = None
        
        # Search up the directory tree for .env file
        for parent in [current_dir] + list(current_dir.parents):
            potential_env = parent / '.env'
            if potential_env.exists():
                env_file = potential_env
                break
        
        if not env_file:
            return None, None
            
        # Read .env file and extract gitURL
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('gitURL='):
                    original_url = line.split('=', 1)[1].strip()
                    
                    # Extract branch if it contains /tree/
                    branch = "main"  # default branch
                    repo_url = original_url
                    
                    if '/tree/' in original_url:
                        parts = original_url.split('/tree/')
                        repo_url = parts[0]
                        if len(parts) > 1:
                            branch = parts[1]
                    
                    # Ensure it ends with .git for proper cloning
                    if not repo_url.endswith('.git'):
                        repo_url += '.git'
                    
                    return repo_url, branch
                    
        return None, None
        
    except Exception as e:
        print(f"⚠️ Error reading .env file: {e}")
        return None, None


def get_repo_url_only_from_env():
    """
    Backward compatibility function - returns just the repo URL
    
    Returns:
        str: Repository URL from .env file, or None if not found
    """
    repo_url, _ = get_repo_url_from_env()
    return repo_url


def clone_or_pull_repo(repo_url, local_path, branch="main"):
    """
    Clone a repository if it doesn't exist, or pull latest changes if it does
    
    Args:
        repo_url (str): GitHub repository URL (https://github.com/user/repo.git)
        local_path (str): Local directory path where repo should be cloned/updated
        branch (str): Branch to checkout (default: "main")
    
    Returns:
        dict: Result with success status and message
    """
    try:
        local_path = Path(local_path)
        
        if local_path.exists() and (local_path / '.git').exists():
            # Repository already exists, pull latest changes
            print(f"\t> PULLING...")
            return pull_latest_changes(local_path, branch)
        else:
            # Repository doesn't exist, clone it
            print(f"\t\t📥 Cloning repository from {repo_url}...")
            return clone_repository(repo_url, local_path, branch)
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


def clone_repository(repo_url, local_path, branch="main"):
    """Clone a repository from GitHub"""
    try:
        # Ensure parent directory exists
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clone the repository
        cmd = ["git", "clone", "-b", branch, repo_url, str(local_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        print(f"\t- Successfully cloned repository to {local_path}")
        return {
            "success": True,
            "message": f"Repository cloned successfully to {local_path}",
            "action": "cloned"
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "message": f"Git clone failed: {e.stderr}"
        }


def pull_latest_changes(local_path, branch="main"):
    """Pull latest changes from remote repository"""
    try:
        # Change to repository directory
        original_cwd = os.getcwd()
        os.chdir(local_path)
        
        # Fetch latest changes
        subprocess.run(["git", "fetch", "origin"], capture_output=True, text=True, check=True)
        
        # Checkout the specified branch
        subprocess.run(["git", "checkout", branch], capture_output=True, text=True, check=True)
        
        # Pull latest changes
        result = subprocess.run(["git", "pull", "origin", branch], capture_output=True, text=True, check=True)
        
        # Get commit info
        commit_info = subprocess.run(["git", "log", "-1", "--oneline"], capture_output=True, text=True, check=True)
        
        # Return to original directory
        os.chdir(original_cwd)
        
        print(f"\t\t- Successfully pulled latest changes!")
        
        return {
            "success": True,
            "message": f"Repository updated successfully. Latest commit: {commit_info.stdout.strip()}",
            "action": "pulled"
        }
        
    except subprocess.CalledProcessError as e:
        os.chdir(original_cwd)  # Ensure we return to original directory
        return {
            "success": False,
            "message": f"Git pull failed: {e.stderr}"
        }


def get_app_source(repo_url, project_name=None, branch="main", base_path=None):
    """
    Main function to get the latest app source code into user's cache directory
    
    Args:
        repo_url (str): GitHub repository URL
        project_name (str): Local project directory name (auto-detected if None)
        branch (str): Branch to use (default: "main")
        base_path (str): Base directory for projects (default: user's cache directory)
    
    Returns:
        dict: Result with success status, message, and local path
    """
    try:
        # Use cache directory if no base_path provided
        if base_path is None:
            base_path = get_app_cache_dir()
        
        # Auto-detect project name from URL if not provided
        if not project_name:
            project_name = repo_url.split('/')[-1].replace('.git', '')
        
        # Construct local path in cache directory
        local_path = Path(base_path) / project_name
        
        print(f"\t-----")
        print(f"\t\t- Repository:\t{repo_url}")
        print(f"\t\t-    ...Branch:\t\t~{branch}")
        print(f"\n\t\t--> Cache path: {local_path}\n\t-----")
        print()
        
        # Clone or pull the repository
        result = clone_or_pull_repo(repo_url, local_path, branch)
        
        if result["success"]:
            result["local_path"] = str(local_path)
            result["project_name"] = project_name
            result["cache_path"] = str(local_path)  # Specific path for cached content
            
            # Print success message with formatting
            print(f"\t- - - - -\n\tAPP SOURCE READY AT: {local_path}\n\t- - - - -")
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get app source: {str(e)}"
        }


def clean_project_directory(local_path):
    """
    Clean/remove a project directory
    
    Args:
        local_path (str): Path to the project directory to remove
    
    Returns:
        dict: Result with success status and message
    """
    try:
        local_path = Path(local_path)
        
        if local_path.exists():
            # Handle Windows readonly files in .git directories
            def handle_remove_readonly(func, path, exc):
                """Error handler for removing readonly files on Windows"""
                if os.name == 'nt':
                    os.chmod(path, 0o777)
                    func(path)
                else:
                    raise exc[1]
            
            shutil.rmtree(local_path, onerror=handle_remove_readonly)
            print(f"🧹 Cleaned project directory: {local_path}")
            return {
                "success": True,
                "message": f"Project directory cleaned: {local_path}"
            }
        else:
            return {
                "success": True,
                "message": f"Project directory doesn't exist: {local_path}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to clean directory: {str(e)}"
        }


# Example usage functions
def get_capacitor_app(repo_url, project_name=None):
    """Helper function specifically for Capacitor app repositories"""
    return get_app_source(repo_url, project_name, branch="main")


def get_app_for_publishing(repo_url=None, project_name=None, clean_first=False, branch=None):
    """
    Get app source specifically for publishing workflow into user's cache directory
    
    Args:
        repo_url (str): GitHub repository URL (will read from .env if not provided)
        project_name (str): Local project name
        clean_first (bool): Whether to clean the directory first
        branch (str): Branch to use (will read from .env if not provided)
    
    Returns:
        dict: Result with success status and local path
    """
    # Get repo URL and branch from .env if not provided
    if not repo_url or not branch:
        env_repo_url, env_branch = get_repo_url_from_env()
        if not repo_url:
            repo_url = env_repo_url
        if not branch:
            branch = env_branch or "main"
            
        if not repo_url:
            return {
                "success": False,
                "message": "No repository URL provided and none found in .env file. Add gitURL to .env"
            }
    
    # Auto-detect project name if not provided
    if not project_name:
        project_name = repo_url.split('/')[-1].replace('.git', '')
    
    if clean_first:
        cache_dir = get_app_cache_dir()
        project_path = cache_dir / project_name
        clean_result = clean_project_directory(str(project_path))
        if not clean_result["success"]:
            return clean_result
    
    return get_app_source(repo_url, project_name, branch)