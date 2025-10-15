FROM jupyter/minimal-notebook:latest

# Install the collaboration server extension (pulls ypy/jupyter_ydoc deps)
RUN pip install --no-cache-dir \
    "jupyter-collaboration>=4.1.1" \
    "agent-data-toolkit[postgresql]"