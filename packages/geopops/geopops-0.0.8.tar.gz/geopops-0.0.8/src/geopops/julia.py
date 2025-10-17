import os
import subprocess
import json
from pathlib import Path
from shutil import which

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_config(config_path=None):
    """Load config file to get user-specified path."""
    cfg_path = config_path if config_path is not None else os.path.join(BASE_DIR, "config.json")
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"config.json file not found at {cfg_path}. Please create this file with the required configuration.")
    with open(cfg_path, "r") as f:
        return json.load(f)

class RunJulia:
    """Orchestrates Julia script execution using the existing functions in this module.
    """
    
    def __init__(self, base_dir=None, config_path=None):
        """Create a Julia runner.
        
        Args:
            base_dir: Optional base dir to use for relative paths. If None, uses path from config.json.
            config_path: Optional path to config file. Defaults to package config.json.
        """
        # Julia scripts are always in the package directory
        self.julia_scripts_dir = os.path.join(BASE_DIR, "julia")
        
        # Output directory from config or provided base_dir
        if base_dir is not None:
            self.output_dir = base_dir
        else:
            # Load config to get user-specified path for output
            config = load_config(config_path)
            self.output_dir = config.get("path", BASE_DIR)
            
        # Determine the correct Julia command
        self.julia_cmd = self._get_julia_cmd("1.9.0")
            
        # Set up Julia environment with required packages
        self.setup_julia_environment()
        self.run_all()
    
    def _get_julia_cmd(self, version="1.9.0", explicit_path=None):
        """Get the correct Julia command with version selection."""
        if explicit_path:
            return [explicit_path]
        
        # First try juliaup version selector
        if which("julia"):
            try:
                result = subprocess.run(["julia", f"+{version}"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    # juliaup supports +version selector
                    return ["julia", f"+{version}"]
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass
        
        # Try just "julia" and check version
        if which("julia"):
            try:
                result = subprocess.run(["julia", "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and "julia version 1.9" in result.stdout:
                    return ["julia"]
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass
        
        # If we get here, Julia 1.9 is not available
        raise RuntimeError(
            f"Julia 1.9.0 not found. Please install Julia 1.9.0 or juliaup with version 1.9.\n"
            f"Current julia version: {subprocess.run(['julia', '--version'], capture_output=True, text=True).stdout if which('julia') else 'Julia not found on PATH'}"
        )
    
    def setup_julia_environment(self):
        """Set up Julia environment with required packages."""
        # Use the existing Julia 1.9 environment
        self.julia_env_path = "/Users/Alisa/.julia/environments/v1.9"
        
        # Check if the environment exists
        if not os.path.exists(self.julia_env_path):
            raise RuntimeError(f"Julia environment not found at {self.julia_env_path}")
        
        print(f"Using Julia environment: {self.julia_env_path}")
        
        # Optional: Verify required packages are installed
        required_packages = [
            "CSV", "DataFrames", "Graphs", "InlineStrings", "JSON"
        ]
        
        try:
            # Check if packages are available
            jl_check = 'using Pkg; Pkg.activate(raw"' + self.julia_env_path + '"); ' + \
                      '; '.join([f'using {pkg}' for pkg in required_packages])
            subprocess.run([*self.julia_cmd, "--startup-file=no", "-e", jl_check], 
                         check=True, text=True, capture_output=True)
            print("All required packages are available!")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Some packages may not be installed in the environment: {e}")
            print("You may need to manually install missing packages.")
    
    def CO(self):
        """Run the CO.jl Julia script."""
        subprocess.run([
            *self.julia_cmd,
            f"--project={self.julia_env_path}",
            os.path.join(self.julia_scripts_dir, "CO.jl")
        ], check=True, text=True, cwd=self.output_dir)
        
    def SynthPop(self):
        """Run the synthpop.jl Julia script."""
        print("Running synthpop.jl...")
        try:
            result = subprocess.run([
                *self.julia_cmd,
                f"--project={self.julia_env_path}",
                os.path.join(self.julia_scripts_dir, "synthpop.jl")
            ], check=True, text=True, cwd=self.output_dir, capture_output=True)
            print("synthpop.jl completed successfully")
            return result
        except subprocess.CalledProcessError as e:
            print(f"synthpop.jl failed with exit code {e.returncode}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            raise
        
    def Export(self):
        """Run the export_synthpop.jl and the export_network.jl Julia scripts."""
        subprocess.run([
            *self.julia_cmd,
            f"--project={self.julia_env_path}",
            os.path.join(self.julia_scripts_dir, "export_synthpop.jl")
        ], check=True, text=True, cwd=self.output_dir)
        subprocess.run([
            *self.julia_cmd,
            f"--project={self.julia_env_path}",
            os.path.join(self.julia_scripts_dir, "export_network.jl")
        ], check=True, text=True, cwd=self.output_dir)
    
    def run_all(self):
        """Run all Julia scripts in sequence."""
        self.CO()
        self.SynthPop()
        self.Export()

def main():
    runner = RunJulia()
    # runner.run_all()

if __name__ == "__main__":
    main()

