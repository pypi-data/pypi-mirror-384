# 🚀 C2i Athena MCP Setup Prompts

Copy and paste these prompts to GitHub Copilot Chat to automatically set up the C2i Athena MCP server on your system.

---

## 📱 **For Mac Users**

```
I need to set up the C2i Athena MCP server for VS Code. Please help me:

1. Install uvx package manager if not already installed: pip install uv
2. Test that the package works: uvx --upgrade c2i-athena-mcp --help
3. Add this EXACT configuration to my VS Code MCP configuration file (NOT settings.json):
   - Find the MCP configuration file in VS Code (usually in your user settings)
   - Add this server configuration:

{
  "mcpServers": {
    "c2i-athena": {
      "command": "uvx",
      "args": [
        "--upgrade", 
        "c2i-athena-mcp"
      ],
      "env": {
        "AWS_REGION": "us-east-1",
        "AWS_PROFILE": "C2iAlefResearchAccess-340686126008"
      }
    }
  }
}

4. Restart VS Code completely
5. Test that the server is working by asking: "List available Athena databases"

IMPORTANT: 
- Use "uvx --upgrade" (this is the working syntax)
- Test the command manually first: uvx --upgrade c2i-athena-mcp --help
- This configuration goes in the MCP file, NOT settings.json

This is for macOS. The MCP server provides AWS Athena database operations and MRD calculations for C2i Genomics research.
```

---

## 🪟 **For Windows Users**

```
I need to set up the C2i Athena MCP server for VS Code on Windows. Please help me:

1. Install uvx package manager if not already installed: pip install uv
2. Test that the package works: uvx --upgrade c2i-athena-mcp --help
3. Add this EXACT configuration to my VS Code MCP configuration file (NOT settings.json):
   - Find the MCP configuration file in VS Code (usually in your user settings)
   - Add this server configuration:

{
  "mcpServers": {
    "c2i-athena": {
      "command": "uvx",
      "args": [
        "--upgrade", 
        "c2i-athena-mcp"
      ],
      "env": {
        "AWS_REGION": "us-east-1",
        "AWS_PROFILE": "C2iAlefResearchAccess-340686126008",
      }
    }
  }
}

4. Restart VS Code completely
5. Test that the server is working by asking: "List available Athena databases"

IMPORTANT: 
- Use "uvx --upgrade" (this is the working syntax)
- Test the command manually first: uvx --upgrade c2i-athena-mcp --help
- This configuration goes in the MCP file, NOT settings.json

This is for Windows. The MCP server provides AWS Athena database operations and MRD calculations for C2i Genomics research.
```

---

## 🐧 **For Linux Users**

```
I need to set up the C2i Athena MCP server for VS Code on Linux. Please help me:

1. Install uvx package manager if not already installed: pip install uv
2. Test that the package works: uvx --upgrade c2i-athena-mcp --help
3. Add this EXACT configuration to my VS Code MCP configuration file (NOT settings.json):
   - Find the MCP configuration file in VS Code (usually in your user settings)
   - Add this server configuration:

{
  "mcpServers": {
    "c2i-athena": {
      "command": "uvx",
      "args": [
        "--upgrade", 
        "c2i-athena-mcp"
      ],
      "env": {
        "AWS_REGION": "us-east-1",
        "AWS_PROFILE": "C2iAlefResearchAccess-340686126008"
      }
    }
  }
}

4. Restart VS Code completely
5. Test that the server is working by asking: "List available Athena databases"

IMPORTANT: 
- Use "uvx --upgrade" (this is the working syntax)
- Test the command manually first: uvx --upgrade c2i-athena-mcp --help
- This configuration goes in the MCP file, NOT settings.json

This is for Linux. The MCP server provides AWS Athena database operations and MRD calculations for C2i Genomics research.
```

---

## 🔧 **Troubleshooting Prompt**

```
My C2i Athena MCP server is not working correctly in VS Code. Please help me troubleshoot:

1. Check if uvx is installed and working
2. Verify c2i-athena-mcp package is installed correctly
3. Validate my VS Code MCP configuration for the c2i-athena server
4. Check for any connection errors or import issues
5. Test the MCP server connection and functionality

The server should provide AWS Athena database operations and MRD calculations. Show me the configuration that should be in my VS Code settings and help me fix any issues.
```

---

## 📋 **Expected Results**

After running the setup prompt, users should have:

✅ **uvx installed** and accessible from command line
✅ **VS Code MCP configuration** updated with correct server config (not in settings.json)
✅ **Auto-upgrading setup** - uvx will fetch latest version each time
✅ **MCP connection** active and responding
✅ **Ready to use** - Can ask questions like:
   - "Show me all available Athena databases"
   - "Calculate MRD score for sample SAMPLE123"
   - "Query the latest 10 samples from the research database"

---

## 🎯 **For Team Distribution**

**Share this with your team:**

> 🧬 **C2i Athena MCP Setup**
> 
> Copy and paste the prompt for your OS (Mac/Windows/Linux) into GitHub Copilot Chat to automatically set up our Athena MCP server. 
> 
> **Setup prompts:** [Link to this file]
> 
> Once set up, you can query our Athena databases and calculate MRD scores directly through VS Code Chat!

---

## 🔄 **Auto-Update Feature**

The configuration uses `uvx run --upgrade c2i-athena-mcp` instead of installing the package locally. This means:

- **Always latest version**: uvx fetches the newest version from PyPI each time
- **No manual updates**: Users never need to run update commands
- **No local installation**: Package isn't stored locally, reducing conflicts
- **Zero maintenance**: Set it up once, always get the latest features

This is why we use `uvx run` with `--upgrade`, not `uvx install`!