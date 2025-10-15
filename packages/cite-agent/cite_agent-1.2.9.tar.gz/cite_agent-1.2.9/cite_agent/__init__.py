"""
Nocturnal Archive - Beta Agent

A Groq-powered research and finance co-pilot with deterministic tooling and
prior stacks preserved only in Git history, kept out of the runtime footprint.
"""

from .enhanced_ai_agent import EnhancedNocturnalAgent, ChatRequest, ChatResponse

__version__ = "0.9.0b1"
__author__ = "Nocturnal Archive Team"
__email__ = "contact@nocturnal.dev"

__all__ = [
    "EnhancedNocturnalAgent",
    "ChatRequest", 
    "ChatResponse"
]

# Package metadata
PACKAGE_NAME = "nocturnal-archive"
PACKAGE_VERSION = __version__
PACKAGE_DESCRIPTION = "Beta CLI agent for finance + research workflows"
PACKAGE_URL = "https://github.com/Spectating101/nocturnal-archive"

def get_version():
    """Get the package version"""
    return __version__

def quick_start():
    """Print quick start instructions"""
    print("""
🚀 Nocturnal Archive Quick Start
================================

1. Install the package and CLI:
   pip install nocturnal-archive

2. Configure your Groq key:
   nocturnal --setup

3. Ask a question:
   nocturnal "Compare Apple and Microsoft net income this quarter"

4. Prefer embedding in code? Minimal example:
   ```python
   import asyncio
   from nocturnal_archive import EnhancedNocturnalAgent, ChatRequest

   async def main():
       agent = EnhancedNocturnalAgent()
       await agent.initialize()

       response = await agent.process_request(ChatRequest(question="List repo workspace files"))
       print(response.response)

       await agent.close()

   asyncio.run(main())
   ```

Full installation instructions live in docs/INSTALL.md.
""")

if __name__ == "__main__":
    quick_start()
