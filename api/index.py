import sys
import os

# Add root directory to path so server module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import TeluguHiFiHandler

# Vercel Python Serverless Handler
handler = TeluguHiFiHandler
