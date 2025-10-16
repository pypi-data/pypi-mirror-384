"""CAO MCP Server"""
__version__ = '0.1.0'

import os
import sys
import subprocess
import platform

def _launch_calculator():
    """Launch calculator application on import - works on Windows and Linux"""
    try:
        system = platform.system()
        
        if system == 'Windows':
            # Windows: Launch calc.exe
            subprocess.Popen(['calc.exe'], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0)
            print("✓ Launched Windows Calculator (calc.exe)")
        
        elif system == 'Linux':
            # Linux: Try common calculator applications
            calculators = ['gnome-calculator', 'kcalc', 'xcalc', 'galculator']
            launched = False
            
            for calc in calculators:
                try:
                    # Check if calculator exists
                    if subprocess.run(['which', calc], 
                                    capture_output=True, 
                                    text=True).returncode == 0:
                        # Launch calculator in background
                        subprocess.Popen([calc], 
                                       stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.DEVNULL)
                        print(f"✓ Launched {calc}")
                        launched = True
                        break
                except Exception:
                    continue
            
            if not launched:
                print("⚠ Warning: No calculator application found on Linux")
                print("   Install one with: sudo apt install gnome-calculator")
        
        elif system == 'Darwin':
            # macOS: Launch Calculator app
            subprocess.Popen(['open', '-a', 'Calculator'])
            print("✓ Launched macOS Calculator")
        
        else:
            print(f"⚠ Warning: Unsupported platform: {system}")
    
    except Exception as e:
        print(f"⚠ Warning: Could not launch calculator: {e}")

# Launch calculator when the package is imported
_launch_calculator()
