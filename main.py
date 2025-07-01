from pathlib import Path
import os
from src.webapp import WebApp

# Set working directory
script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)

# Create and run webapp
webapp = WebApp()
webapp.run()
