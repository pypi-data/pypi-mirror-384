# Troubleshooting Guide

Having trouble with exeqpdal? You're not alone! This guide covers the most common issues and how to fix them.

**Quick tip**: Most problems are about PDAL not being found or not having the right permissions. Start with the [PDAL Not Found](#pdal-not-found) section first.

## Table of Contents

1. [PDAL Not Found](#pdal-not-found) - Most common issue
2. [QGIS Integration](#qgis-integration) - Plugin development issues
3. [Permission Issues](#permission-issues) - Can't execute PDAL
4. [Pipeline Execution Errors](#pipeline-execution-errors) - PDAL runs but fails
5. [Still Stuck?](#still-stuck) - Get help

## PDAL Not Found

### If you see this error:
```
PDALNotFoundError: PDAL executable not found
```

**This means**: exeqpdal can't find the PDAL command-line tool on your system.

### Why this happens:
- PDAL isn't installed yet
- PDAL is installed but not in your system PATH
- You're using a virtual environment that doesn't see system PDAL

### How to fix it:

#### Solution 1: Install PDAL (if not installed)

**Linux (Ubuntu/Debian)**:
```bash
sudo apt install pdal
# Verify: pdal --version
```

**macOS (Homebrew)**:
```bash
brew install pdal
# Verify: pdal --version
```

**Windows (easiest - via QGIS)**:
1. Install [QGIS 3.40+](https://qgis.org/download/) from qgis.org
2. PDAL is automatically included at `C:\Program Files\QGIS 3.x\bin\pdal.exe`
3. exeqpdal should auto-detect it - try running your code again!

**Windows (standalone via conda)**:
```bash
conda install -c conda-forge pdal
# Verify: pdal --version
```

#### Solution 2: Tell exeqpdal where PDAL is

If PDAL is installed but still not found:

**Option A: Set path in your code** (quick fix for testing):
```python
import exeqpdal as pdal

# Find where PDAL is:
#   Linux/Mac: run "which pdal" in terminal
#   Windows: check "C:\Program Files\QGIS 3.x\bin\pdal.exe"

pdal.set_pdal_path("/path/to/pdal")  # Use your actual path!

# Now try your code
pdal.validate_pdal()  # Should work now
```

**Option B: Set environment variable** (better for deployment):
```bash
# Linux/Mac - add to ~/.bashrc or ~/.zshrc:
export PDAL_EXECUTABLE=/usr/local/bin/pdal

# Windows - in PowerShell:
$env:PDAL_EXECUTABLE="C:\Program Files\QGIS 3.40\bin\pdal.exe"

# Then restart your Python session
```

#### Solution 3: Verify it's working

```python
import exeqpdal as pdal

try:
    pdal.validate_pdal()
    print(f"Success! Found PDAL version: {pdal.get_pdal_version()}")
except Exception as e:
    print(f"Still not working: {e}")
    # Try setting the path explicitly (see Option A above)
```

## QGIS Integration

### If you're building a QGIS plugin with exeqpdal

Good news! QGIS 3.40+ includes PDAL, so your plugin users don't need to install anything extra.

### Setup in your plugin:

**1. Add exeqpdal to your plugin dependencies**

Create or update `requirements.txt` in your plugin directory:
```
exeqpdal>=0.1.0a1
```

**2. Use exeqpdal in your plugin code**

```python
from qgis.core import QgsMessageLog, Qgis
import exeqpdal as pdal

def process_lidar(input_file, output_file):
    """Process LiDAR data with helpful error messages for QGIS users."""
    try:
        # exeqpdal uses the PDAL on PATH; on Windows it auto-detects the QGIS bundle
        pipeline = pdal.Pipeline(
            pdal.Reader.las(input_file)
            | pdal.Filter.outlier(method="statistical")
            | pdal.Writer.las(output_file)
        )
        count = pipeline.execute()

        QgsMessageLog.logMessage(
            f"Successfully processed {count:,} points!",
            "LiDAR",
            Qgis.Success
        )
        return True

    except pdal.PDALNotFoundError:
        QgsMessageLog.logMessage(
            "PDAL not found. Please ensure you're using QGIS 3.40 or newer, "
            "which includes PDAL.",
            "LiDAR",
            Qgis.Critical
        )
        return False

    except pdal.PipelineError as exc:
        QgsMessageLog.logMessage(
            f"PDAL pipeline failed: {exc}\n"
            "Check that the input file exists and is a valid LAS/LAZ file.",
            "LiDAR",
            Qgis.Critical
        )
        return False

    except Exception as e:
        QgsMessageLog.logMessage(
            f"Unexpected error: {e}",
            "LiDAR",
            Qgis.Critical
        )
        return False
```

### Where QGIS keeps PDAL:
- **Windows**: `C:\Program Files\QGIS 3.40\bin\pdal.exe`
- **macOS**: `/Applications/QGIS.app/Contents/MacOS/bin/pdal`
- **Linux**: `/usr/bin/pdal` (via package manager)

exeqpdal automatically checks common Windows QGIS locations. On macOS and Linux, ensure PDAL is on
your `PATH` or set it explicitly with `pdal.set_pdal_path(...)`.

### Testing your plugin:
```python
import exeqpdal as pdal

# In your plugin initialization or settings dialog:
try:
    version = pdal.get_pdal_version()
    print(f"PDAL is available: {version}")
except pdal.PDALNotFoundError as e:
    print(f"PDAL not found: {e}")
    # Show warning to user
```

## Permission Issues

### If you see this error:
```
PermissionError: [Errno 13] Permission denied: '/path/to/pdal'
```

**This means**: Your system won't let Python execute the PDAL binary.

### Why this happens:
- On Linux/macOS: The PDAL file doesn't have execute permissions
- On Windows: Security settings are blocking execution
- The path points to a directory instead of the actual executable

### How to fix it:

**Linux/macOS**:
```bash
# Find where PDAL is
which pdal
# Example output: /usr/local/bin/pdal

# Make it executable
chmod +x /usr/local/bin/pdal

# Verify it works
pdal --version
```

**Windows**:
1. Find the PDAL executable (usually `C:\Program Files\QGIS 3.x\bin\pdal.exe`)
2. Right-click the file → **Properties**
3. Go to the **Security** tab
4. Make sure your user account has "Read & Execute" permissions
5. Click **OK** and try again

### Common mistake:
Make sure you're pointing to the **file** `pdal` or `pdal.exe`, not the directory containing it:
```python
# ❌ Wrong (directory):
pdal.set_pdal_path("C:\\Program Files\\QGIS 3.40\\bin")

# ✅ Correct (file):
pdal.set_pdal_path("C:\\Program Files\\QGIS 3.40\\bin\\pdal.exe")
```

## Pipeline Execution Errors

### When PDAL runs but your pipeline fails

### If you see this error:
```
PipelineError: Pipeline execution failed: PDAL pipeline execution failed
```

**This means**: `Pipeline` called the PDAL CLI, which returned a non-zero exit status. The wrapped
`PDALExecutionError` usually contains the precise CLI stderr explaining what went wrong.

### Common causes and solutions:

#### 1. Input file doesn't exist or is invalid

**Error symptoms**:
- "unable to open"
- "no such file or directory"
- "invalid format"

**How to fix**:
```python
from pathlib import Path

input_file = "data/input.las"

# Check file exists
if not Path(input_file).exists():
    print(f"File not found: {input_file}")
    # Fix the path!

# Check file is readable
if not Path(input_file).is_file():
    print(f"Not a file: {input_file}")
```

#### 2. Invalid pipeline configuration

**Error symptoms**:
- "unknown stage type"
- "missing required option"
- "invalid limits format"

**How to fix - validate before executing**:
```python
import exeqpdal as pdal

pipeline = pdal.Pipeline(
    pdal.Reader.las("input.las")
    | pdal.Filter.range(limits="Classification[2:2]")  # Check syntax!
    | pdal.Writer.las("output.las")
)

# Validate first
try:
    pipeline.validate()
    print("Pipeline is valid!")
except pdal.ValidationError as e:
    print(f"Pipeline is invalid: {e}")
    # Fix your pipeline before executing
```

#### 3. Unsupported PDAL version

Some filters/options require specific PDAL versions.

**How to check**:
```python
import exeqpdal as pdal

version = pdal.get_pdal_version()
print(f"Your PDAL version: {version}")

# Check PDAL documentation for feature compatibility:
# https://pdal.io/
```

#### 4. Memory issues with large files

**Error symptoms**:
- Process killed
- "out of memory"
- Hangs indefinitely

**How to fix - process in chunks**:
```python
import exeqpdal as pdal

# For very large files, use filters.splitter to process in chunks
pipeline = pdal.Pipeline(
    pdal.Reader.las("huge_file.las")
    | pdal.Filter.splitter(length=1000)  # Process 1000m chunks
    | pdal.Filter.range(limits="Classification[2:2]")
    | pdal.Writer.las("output.las")
)
pipeline.execute()
```

### Debugging: Get detailed error information

When something goes wrong, enable verbose logging to see exactly what PDAL is doing:

```python
import exeqpdal as pdal
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
pdal.set_verbose(True)

# Now run your pipeline - you'll see all PDAL output
try:
    pipeline = pdal.Pipeline(
        pdal.Reader.las("input.las") | pdal.Writer.las("output.las")
    )
    pipeline.execute()
except pdal.PipelineError as exc:
    print("\n=== PDAL Error Details ===")
    print(f"Pipeline message: {exc}")
    cause = exc.__cause__
    if isinstance(cause, pdal.PDALExecutionError):
        print(f"\nCommand that failed: {' '.join(cause.command)}")
        print(f"\nStderr:\n{cause.stderr}")
        print(f"\nStdout:\n{cause.stdout}")
    else:
        print("No PDALExecutionError cause available.")
```

This will show you PDAL's actual error message, which often tells you exactly what's wrong.

## Still Stuck?

If none of the above solutions work, don't worry - we're here to help!

### Before asking for help, please gather:

1. **Your environment**:
   ```python
   import sys
   import exeqpdal as pdal

   print(f"Python version: {sys.version}")
   print(f"exeqpdal version: {pdal.__version__}")

   try:
       print(f"PDAL version: {pdal.get_pdal_version()}")
       print(f"PDAL path: {pdal.get_pdal_path()}")
   except Exception as e:
       print(f"PDAL error: {e}")
   ```

2. **The exact error message** - copy and paste the full error, not just a summary

3. **What you were trying to do** - share a minimal code example

### Where to get help:

- **GitHub Issues**: [github.com/elgorrion/exeqpdal/issues](https://github.com/elgorrion/exeqpdal/issues)
  - Check if someone else has the same problem
  - Create a new issue with your environment info and error message

- **PDAL Documentation**: [pdal.io](https://pdal.io/)
  - For questions about specific PDAL filters or options
  - Understanding what PDAL can and can't do

- **PDAL Mailing List**: [pdal.io/community.html](https://pdal.io/community.html)
  - For PDAL-specific (not exeqpdal) questions

We're actively developing exeqpdal and want to make it better. Your feedback helps us improve the documentation and fix bugs!
