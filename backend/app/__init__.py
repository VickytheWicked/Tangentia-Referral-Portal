import sys

# In Azure App Service Linux, the Application Insights platform sidecar injects /agents/python
# into sys.path, shadowing virtualenv packages with outdated modules (e.g. typing_extensions lacking sentinel).
# Remove any /agents paths from sys.path to guarantee the virtualenv packages take priority.
sys.path = [p for p in sys.path if not ("/agents/python" in p or p.startswith("/agents"))]
if "typing_extensions" in sys.modules:
    del sys.modules["typing_extensions"]
