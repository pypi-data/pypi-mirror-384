# Bundling MCP Servers Guide

This guide explains how to bundle your Simply-MCP server into a standalone executable using the `simply-mcp bundle` command.

## Overview

The bundle command uses PyInstaller to package your Python MCP server and all its dependencies into a single executable file that can be distributed without requiring Python or any dependencies to be installed on the target system.

## Prerequisites

### Install PyInstaller

First, install PyInstaller:

```bash
# Install PyInstaller separately
pip install pyinstaller

# Or install Simply-MCP with bundling extras
pip install simply-mcp[bundling]
```

### Verify Your Server

Make sure your server runs correctly before bundling:

```bash
simply-mcp run your_server.py
```

## Basic Usage

### Simple Bundle

Bundle your server with default settings:

```bash
simply-mcp bundle your_server.py
```

This will:
- Validate your server file
- Detect dependencies
- Generate a PyInstaller spec file
- Build a single-file executable
- Output to `./dist/` directory

### Custom Name

Specify a custom name for the executable:

```bash
simply-mcp bundle your_server.py --name my-awesome-server
```

### Custom Output Directory

Specify where to save the bundled executable:

```bash
simply-mcp bundle your_server.py --output ./build
```

## Bundle Options

### Single File vs Directory

**Single File (Default)**
```bash
simply-mcp bundle your_server.py --onefile
```
Creates a single executable file that extracts dependencies to a temporary directory at runtime.

**Directory Bundle**
```bash
simply-mcp bundle your_server.py --no-onefile
```
Creates a directory with the executable and all dependencies. Faster startup but more files to distribute.

### Console Window

**With Console (Default for servers)**
```bash
simply-mcp bundle your_server.py --no-windowed
```
Shows a console window when the executable runs. Recommended for servers to see logs.

**Without Console**
```bash
simply-mcp bundle your_server.py --windowed
```
Hides the console window. Generally not recommended for servers.

### Custom Icon

Add a custom icon to your executable:

```bash
simply-mcp bundle your_server.py --icon path/to/icon.ico
```

Note: Icon format requirements vary by platform:
- Windows: `.ico` file
- macOS: `.icns` file
- Linux: `.png` file

### Clean Build Artifacts

Remove temporary build files after bundling:

```bash
simply-mcp bundle your_server.py --clean
```

## Complete Examples

### Example 1: Basic Weather Server

```bash
# Bundle a simple weather server
simply-mcp bundle weather_server.py
```

Output:
```
./dist/weather_server          # On Linux/macOS
./dist/weather_server.exe      # On Windows
```

### Example 2: Production Server with Custom Settings

```bash
simply-mcp bundle production_server.py \
  --name company-mcp-server \
  --output ./releases \
  --icon assets/logo.ico \
  --clean
```

Output:
```
./releases/company-mcp-server          # On Linux/macOS
./releases/company-mcp-server.exe      # On Windows
```

### Example 3: Directory Bundle for Faster Startup

```bash
simply-mcp bundle large_server.py \
  --no-onefile \
  --output ./dist
```

Output:
```
./dist/large_server/              # Directory containing all files
./dist/large_server/large_server  # Main executable
```

## Platform-Specific Notes

### Windows

- Executables have `.exe` extension
- Windows Defender may flag the executable (false positive)
- Use `.ico` format for icons
- Consider code signing for production distribution

**Code Signing (Windows)**
```bash
# After bundling, sign the executable
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist/your_server.exe
```

### macOS

- Executables are unsigned by default
- Users may see "unidentified developer" warning
- Use `.icns` format for icons
- Consider code signing and notarization for production

**Code Signing (macOS)**
```bash
# After bundling, sign the executable
codesign --sign "Developer ID Application: Your Name" dist/your_server

# For distribution, also notarize
xcrun notarytool submit dist/your_server.zip --keychain-profile "notary-profile"
```

### Linux

- Executables work on systems with compatible glibc
- May need to bundle for different distributions
- Use `.png` format for icons
- Consider building on older distributions for broader compatibility

**Building for Multiple Distributions**
```bash
# Build on oldest supported distribution
# Example: Ubuntu 20.04 for broader compatibility
docker run -v $(pwd):/work ubuntu:20.04 bash -c "
  apt-get update && apt-get install -y python3 python3-pip &&
  pip3 install simply-mcp pyinstaller &&
  cd /work && simply-mcp bundle your_server.py
"
```

## Distribution

### Single File Distribution

1. Bundle as single file:
   ```bash
   simply-mcp bundle your_server.py --onefile --clean
   ```

2. Distribute the single executable file:
   ```
   dist/your_server        # Or your_server.exe on Windows
   ```

3. Users can run it directly:
   ```bash
   ./your_server           # On Linux/macOS
   your_server.exe         # On Windows
   ```

### Directory Distribution

1. Bundle as directory:
   ```bash
   simply-mcp bundle your_server.py --no-onefile --clean
   ```

2. Zip the entire directory:
   ```bash
   cd dist
   zip -r your_server.zip your_server/
   ```

3. Users extract and run:
   ```bash
   unzip your_server.zip
   cd your_server
   ./your_server
   ```

## Troubleshooting

### Import Errors

If your bundled server has import errors:

1. Check that all dependencies are listed in your requirements
2. Add missing modules to hidden imports by modifying the spec file
3. Some dynamic imports may need to be explicit

### Large Executable Size

To reduce size:

1. Use `--no-onefile` for directory bundle
2. Remove unused dependencies
3. Use PyInstaller's `--exclude-module` for unneeded packages
4. Consider using UPX compression (automatically attempted)

### Runtime Errors

Common issues:

1. **Missing Data Files**: Add data files to the spec file
   ```python
   datas=[('config.toml', '.'), ('templates/', 'templates')],
   ```

2. **Environment Variables**: Set them before running
   ```bash
   export API_KEY=your_key
   ./your_server
   ```

3. **Working Directory**: The executable uses a temporary directory
   ```python
   # In your code, get the correct path
   import sys
   import os

   if getattr(sys, 'frozen', False):
       # Running as bundled executable
       bundle_dir = sys._MEIPASS
   else:
       # Running as script
       bundle_dir = os.path.dirname(__file__)
   ```

### Platform Compatibility

**Cross-platform bundling is NOT supported.** You must bundle on the target platform:

- Bundle on Windows → Windows executable
- Bundle on macOS → macOS executable
- Bundle on Linux → Linux executable

For multi-platform distribution, set up CI/CD to build on each platform:

```yaml
# Example: GitHub Actions
name: Build Executables

on: [push]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install simply-mcp[bundling]
      - run: simply-mcp bundle server.py --clean
      - uses: actions/upload-artifact@v2
        with:
          name: server-${{ matrix.os }}
          path: dist/
```

## Advanced Customization

### Modifying the Spec File

The bundle command generates a `.spec` file. You can modify it for advanced options:

1. Bundle with default settings:
   ```bash
   simply-mcp bundle your_server.py --output ./dist
   ```

2. Find the generated spec file:
   ```bash
   ls dist/your_server.spec
   ```

3. Edit the spec file to add customizations:
   ```python
   # Add data files
   datas=[
       ('config/*.toml', 'config'),
       ('templates/', 'templates'),
   ],

   # Add binary dependencies
   binaries=[
       ('/path/to/libfoo.so', '.'),
   ],

   # Exclude modules
   excludes=['tkinter', 'matplotlib'],
   ```

4. Rebuild using the spec file:
   ```bash
   pyinstaller dist/your_server.spec
   ```

### Adding Hidden Imports

If your server uses dynamic imports:

```python
# In the spec file, add to hiddenimports
hiddenimports=[
    'simply_mcp',
    'your_dynamic_module',
    'another_module',
],
```

## Best Practices

1. **Test Before Bundling**: Always test your server works correctly before bundling
2. **Version Control**: Keep spec files in version control for reproducible builds
3. **Clean Builds**: Use `--clean` to ensure fresh builds
4. **Size Optimization**: Only include necessary dependencies
5. **Documentation**: Include a README with distribution
6. **Testing**: Test the bundled executable on target platforms
7. **Updates**: Have a strategy for distributing updates
8. **Logging**: Ensure logs are written to accessible locations

## Example Server for Bundling

Here's a complete example server ready for bundling:

```python
# calculator_server.py
from simply_mcp.api.builder import SimplyMCP

server = SimplyMCP(
    name="Calculator Server",
    version="1.0.0",
    description="A simple calculator MCP server"
)

@server.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

@server.tool()
def subtract(a: float, b: float) -> float:
    """Subtract two numbers."""
    return a - b

@server.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

@server.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run_stdio())
```

Bundle it:
```bash
simply-mcp bundle calculator_server.py --name calculator --clean
```

Distribute:
```bash
./dist/calculator
```

## Getting Help

If you encounter issues:

1. Check the PyInstaller logs in `build/` directory
2. Run with `--clean` to clear cached builds
3. Verify your server works without bundling
4. Check Simply-MCP documentation
5. Report issues on GitHub

## Resources

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Simply-MCP Documentation](https://github.com/Clockwork-Innovations/simply-mcp-py)
- [MCP Specification](https://modelcontextprotocol.io/)
