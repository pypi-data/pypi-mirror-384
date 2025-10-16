#!/usr/bin/env python3
"""
Create GitHub release for SAP Datasphere MCP Server
"""

import subprocess
import sys

def create_github_release():
    """Create a GitHub release using gh CLI"""
    
    release_notes = """# SAP Datasphere MCP Server v0.1.0

🎉 **First Release** - A professional Model Context Protocol server for SAP Datasphere integration!

## ✨ Features

- 🔐 **OAuth 2.0 Authentication** - Secure client credentials flow
- 🏢 **Space Management** - List and explore Datasphere spaces  
- 📊 **Catalog Access** - Browse data models, tables, and views
- 🔗 **Connection Management** - Manage data source connections
- 🧠 **AI-Friendly** - Structured responses optimized for AI consumption
- 🛡️ **Enterprise Ready** - Built for production SAP environments

## 🚀 Installation

```bash
pip install sap-datasphere-mcp
```

## 🛠️ MCP Tools Available

| Tool | Description |
|------|-------------|
| `test_connection` | Test OAuth connectivity |
| `discover_endpoints` | Find available API endpoints |
| `list_spaces` | List all Datasphere spaces |
| `get_space_info` | Get detailed space information |
| `list_catalog` | Browse data catalog |
| `get_table_info` | Get table schema and metadata |
| `list_connections` | List data source connections |

## 📖 Documentation

- [Setup Guide](SETUP.md) - Complete setup instructions
- [README](README.md) - Overview and quick start
- [Examples](examples/) - Usage examples

## 🔗 Links

- **PyPI Package**: https://pypi.org/project/sap-datasphere-mcp/
- **Documentation**: [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/MarioDeFelipe/sap-datasphere-mcp/issues)

## 🙏 Acknowledgments

Built with the Model Context Protocol framework and designed for seamless AI integration with SAP Datasphere.

---

**Full Changelog**: https://github.com/MarioDeFelipe/sap-datasphere-mcp/commits/v0.1.0"""

    try:
        # Check if gh CLI is available
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ GitHub CLI (gh) not found. Please install it first:")
            print("   https://cli.github.com/")
            return False
        
        print("✅ GitHub CLI found")
        
        # Create the release
        print("🚀 Creating GitHub release v0.1.0...")
        
        cmd = [
            'gh', 'release', 'create', 'v0.1.0',
            '--title', 'SAP Datasphere MCP Server v0.1.0',
            '--notes', release_notes,
            '--latest'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ GitHub release created successfully!")
            print(f"🔗 Release URL: https://github.com/MarioDeFelipe/sap-datasphere-mcp/releases/tag/v0.1.0")
            return True
        else:
            print(f"❌ Failed to create release: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    
    print("🎯 Creating GitHub Release for SAP Datasphere MCP Server")
    print("=" * 60)
    
    success = create_github_release()
    
    if success:
        print("\n🎉 Release creation completed!")
        print("\n📋 Next steps:")
        print("• Add repository topics on GitHub")
        print("• Update repository description")
        print("• Share on social media")
        print("• Submit to MCP registry")
    else:
        print("\n💡 Manual release creation:")
        print("1. Go to: https://github.com/MarioDeFelipe/sap-datasphere-mcp/releases/new")
        print("2. Tag: v0.1.0")
        print("3. Title: SAP Datasphere MCP Server v0.1.0")
        print("4. Copy release notes from this script")

if __name__ == "__main__":
    main()