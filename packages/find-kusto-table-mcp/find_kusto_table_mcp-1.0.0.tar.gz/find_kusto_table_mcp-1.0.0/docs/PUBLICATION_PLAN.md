# Publication Plan: VS Code One-Click Installation

## Overview
This document outlines the plan for publishing the Kusto MCP Server (`find-kusto-table-mcp`) to enable one-click installation in VS Code, similar to the existing TypeScript MCP server (`enhanced-ado-mcp`).

## Reference Implementation Analysis

### TypeScript Server (enhanced-ado-mcp)
**Distribution Method:**
- Published to NPM registry
- Installed via `npx` (Node Package eXecuter)
- URL Format: `vscode.dev/redirect/mcp/install?name=enhanced-ado-msp&config={base64}&inputs={base64}`

**Key Components:**
1. **Package.json**: Defines package metadata, dependencies, entry point
2. **NPM Publication**: `npm publish` to registry
3. **One-Click Install URL**: VS Code redirect with encoded configuration
4. **Config Object** (Base64-encoded JSON):
   ```json
   {
     "mcpServers": {
       "enhanced-ado-mcp": {
         "command": "npx",
         "args": ["-y", "enhanced-ado-mcp"],
         "env": {}
       }
     }
   }
   ```
5. **Inputs Object** (Base64-encoded JSON): Prompts for user credentials/tokens

## Python MCP Server Publication Strategy

### Option 1: PyPI + pipx (Recommended)
**Advantages:**
- Standard Python packaging ecosystem
- `pipx` provides isolated virtual environments (similar to `npx`)
- Widely adopted for Python CLIs
- Easy to maintain and update

**Implementation Steps:**
1. **Package Structure**:
   ```
   find-kusto-table-mcp/
   ├── pyproject.toml  (or setup.py)
   ├── README.md
   ├── LICENSE
   ├── src/
   │   └── kusto_mcp/
   │       ├── __init__.py
   │       ├── __main__.py  (entry point)
   │       └── ...
   ```

2. **pyproject.toml Configuration**:
   ```toml
   [build-system]
   requires = ["setuptools>=45", "wheel"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "find-kusto-table-mcp"
   version = "1.0.0"
   description = "Enhanced MCP server for Kusto table discovery"
   authors = [{name = "Your Name", email = "your.email@example.com"}]
   license = {text = "MIT"}
   readme = "README.md"
   requires-python = ">=3.10"
   dependencies = [
       "fastmcp>=2.12.0",
       "azure-kusto-data>=4.0.0",
       "azure-identity>=1.14.0",
       "pandas>=2.0.0",
       "matplotlib>=3.7.0"
   ]

   [project.scripts]
   find-kusto-table-mcp = "kusto_mcp.__main__:main"

   [project.urls]
   Homepage = "https://github.com/yourusername/find-kusto-table-mcp"
   Repository = "https://github.com/yourusername/find-kusto-table-mcp"
   ```

3. **Entry Point (__main__.py)**:
   ```python
   def main():
       """Main entry point for the MCP server"""
       import sys
       from kusto_server import run_server
       run_server()

   if __name__ == "__main__":
       main()
   ```

4. **Build and Publish**:
   ```powershell
   # Build the package
   python -m build

   # Test locally
   pipx install --editable .

   # Publish to PyPI
   python -m twine upload dist/*
   ```

5. **One-Click Install Configuration**:
   ```json
   {
     "mcpServers": {
       "find-kusto-table-mcp": {
         "command": "pipx",
         "args": ["run", "find-kusto-table-mcp"],
         "env": {}
       }
     }
   }
   ```

6. **Installation URL**:
   ```
   https://vscode.dev/redirect/mcp/install?name=find-kusto-table-mcp&config={base64_config}&inputs={base64_inputs}
   ```

### Option 2: PyPI + uvx (Alternative)
**Advantages:**
- Modern, faster alternative to pipx
- Built on `uv` (ultra-fast Python package installer)
- Growing adoption in Python community

**Implementation:**
- Same package structure as Option 1
- Replace `pipx` with `uvx` in config:
  ```json
  {
    "command": "uvx",
    "args": ["find-kusto-table-mcp"]
  }
  ```

### Option 3: Docker Container (Enterprise)
**Advantages:**
- Complete isolation
- Consistent environment across platforms
- Easy dependency management

**Disadvantages:**
- Requires Docker installation
- Higher overhead
- More complex for end users

**Implementation:**
```json
{
  "command": "docker",
  "args": ["run", "-i", "--rm", "your-registry/find-kusto-table-mcp:latest"]
}
```

## Recommended Implementation Plan

### Phase 1: Package Preparation (Week 1)
1. **Restructure for Distribution**:
   - Move `kusto_server.py` to `src/kusto_mcp/__main__.py`
   - Create `pyproject.toml` with proper metadata
   - Ensure all dependencies are pinned with minimum versions
   - Add LICENSE file (recommend MIT)

2. **Testing**:
   - Test local installation: `pip install -e .`
   - Test pipx installation: `pipx install .`
   - Verify entry point works: `find-kusto-table-mcp --help`

3. **Documentation Updates**:
   - Update README.md with installation instructions
   - Add PyPI badges
   - Document configuration options

### Phase 2: PyPI Publication (Week 2)
1. **Create PyPI Account**:
   - Register at https://pypi.org
   - Set up 2FA
   - Generate API token

2. **Build Package**:
   ```powershell
   python -m pip install --upgrade build twine
   python -m build
   ```

3. **Test on TestPyPI**:
   ```powershell
   python -m twine upload --repository testpypi dist/*
   pipx install --index-url https://test.pypi.org/simple/ find-kusto-table-mcp
   ```

4. **Publish to PyPI**:
   ```powershell
   python -m twine upload dist/*
   ```

### Phase 3: VS Code Integration (Week 3)
1. **Create Configuration Template**:
   ```json
   {
     "mcpServers": {
       "find-kusto-table-mcp": {
         "command": "pipx",
         "args": ["run", "find-kusto-table-mcp"],
         "env": {
           "KUSTO_CLUSTER": "${input:kustoCluster}",
           "KUSTO_DATABASE": "${input:kustoDatabase}"
         }
       }
     }
   }
   ```

2. **Create Inputs Template**:
   ```json
   {
     "kustoCluster": {
       "type": "promptString",
       "description": "Enter your Kusto cluster URL",
       "password": false
     },
     "kustoDatabase": {
       "type": "promptString",
       "description": "Enter your Kusto database name",
       "password": false
     }
   }
   ```

3. **Generate Installation URL**:
   - Base64 encode config and inputs
   - Create markdown buttons in README.md:
     ```markdown
     [![Install in VS Code](https://img.shields.io/badge/VS%20Code-Install-blue?logo=visualstudiocode)](https://vscode.dev/redirect/mcp/install?name=find-kusto-table-mcp&config=BASE64_CONFIG&inputs=BASE64_INPUTS)
     
     [![Install in VS Code Insiders](https://img.shields.io/badge/VS%20Code%20Insiders-Install-green?logo=visualstudiocode)](https://insiders.vscode.dev/redirect/mcp/install?name=find-kusto-table-mcp&config=BASE64_CONFIG&inputs=BASE64_INPUTS)
     ```

4. **Test Installation Flow**:
   - Click install button
   - Verify VS Code prompts for inputs
   - Confirm MCP server starts correctly
   - Test Claude Desktop integration

### Phase 4: Documentation & Launch (Week 4)
1. **Create Documentation**:
   - Installation guide
   - Configuration guide
   - Troubleshooting section
   - Video walkthrough (optional)

2. **Announcement**:
   - Update GitHub repository README
   - Create GitHub Release with notes
   - Announce on relevant forums/communities

3. **Monitoring**:
   - Set up PyPI download statistics
   - Monitor GitHub issues
   - Collect user feedback

## Configuration Details

### Base Config Object
```json
{
  "mcpServers": {
    "find-kusto-table-mcp": {
      "command": "pipx",
      "args": ["run", "find-kusto-table-mcp"],
      "env": {
        "EXPORT_DIR": "${workspaceFolder}/exports",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Inputs Object
```json
{
  "kustoCluster": {
    "type": "promptString",
    "description": "Kusto cluster URL (e.g., https://cluster.kusto.windows.net)",
    "password": false
  },
  "kustoDatabase": {
    "type": "promptString",
    "description": "Default Kusto database name",
    "password": false
  }
}
```

## Security Considerations

1. **Credentials Management**:
   - Use Azure CLI authentication (default)
   - Support managed identity for Azure VMs
   - Never store credentials in config

2. **Connection Strings**:
   - Store in `cache/connection_strings.json` (git-ignored)
   - Prompt user on first run
   - Validate cluster URLs

3. **Dependencies**:
   - Pin all dependency versions
   - Regular security audits
   - Monitor for vulnerabilities

## Maintenance Plan

### Version Strategy
- **Semantic Versioning**: MAJOR.MINOR.PATCH
  - MAJOR: Breaking changes
  - MINOR: New features, backward compatible
  - PATCH: Bug fixes

### Release Process
1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create Git tag: `v1.0.0`
4. Build and publish to PyPI
5. Create GitHub Release with notes

### Support Channels
- GitHub Issues for bug reports
- GitHub Discussions for questions
- Documentation site for guides

## Success Metrics

1. **Installation Success Rate**: >95% of users successfully install
2. **Active Users**: Track PyPI downloads
3. **GitHub Stars**: Measure community interest
4. **Issue Response Time**: <48 hours
5. **User Satisfaction**: Positive feedback ratio

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|---------|------------|
| PyPI account compromise | High | Enable 2FA, use API tokens |
| Breaking dependency update | Medium | Pin versions, test thoroughly |
| Poor user experience | Medium | Comprehensive docs, video guides |
| Limited pipx adoption | Low | Provide alternative (pip, uvx) |
| VS Code API changes | Low | Monitor VS Code releases |

## Timeline Summary

- **Week 1**: Package preparation and local testing
- **Week 2**: PyPI publication and validation
- **Week 3**: VS Code integration and testing
- **Week 4**: Documentation and launch

**Total**: 4 weeks to production-ready one-click installation

## Next Steps

1. **Immediate** (This Week):
   - Create `pyproject.toml`
   - Restructure code for packaging
   - Set up PyPI account

2. **Short Term** (Next 2 Weeks):
   - Publish to TestPyPI
   - Create installation URLs
   - Test end-to-end flow

3. **Medium Term** (Next Month):
   - Official PyPI publication
   - Launch announcement
   - Gather initial feedback

## Conclusion

Publishing the Kusto MCP Server with one-click VS Code installation is achievable using standard Python packaging tools (PyPI + pipx). The TypeScript server provides an excellent reference implementation, and the Python ecosystem offers equivalent tools (`pipx` ~= `npx`). Following this plan will deliver a professional, user-friendly installation experience comparable to the existing TypeScript server.
