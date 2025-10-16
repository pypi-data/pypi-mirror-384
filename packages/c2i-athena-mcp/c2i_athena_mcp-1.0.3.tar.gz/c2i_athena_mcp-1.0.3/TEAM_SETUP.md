# C2i Athena MCP - Team Setup Guide

This guide shows how to deploy the C2i Athena MCP server for your team using modern MCP distribution patterns.

## 🎯 Distribution Options

### Option 1: VS Code with GitHub Copilot (Recommended for Enterprise)

**For Organization Admins:**

1. **Set up the MCP Registry** in your GitHub Copilot organization settings:
   ```
   Registry URL: https://raw.githubusercontent.com/c2i-genomics/c2i-athena-mcp/main/registry.json
   ```

2. **Users automatically see the server** in VS Code once MCP is enabled - no manual installation needed!

**For Individual Users:**

If your org admin hasn't set this up yet, add to `~/.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "c2i-athena": {
      "command": "uvx",
      "args": ["c2i-athena-mcp"],
      "env": {
        "AWS_REGION": "us-east-1",
        "AWS_PROFILE": "C2iAlefResearchAccess-340686126008"
      }
    }
  }
}
```

### Option 2: Claude Desktop (One-click Install)

**Install the Desktop Extension:**

1. Download the extension file: [extension.json](./extension.json)
2. In Claude Desktop: Settings → Extensions → Install from file
3. Configure your AWS profile when prompted
4. Done! The Athena tools are now available.

### Option 3: Remote Server (No Local Install)

**Deploy on your existing EC2:**

```bash
# Install on the server
pip install c2i-athena-mcp

# Run as a service
c2i-athena-mcp --host 0.0.0.0 --port 3000
```

**Users connect via HTTP:**

```json
{
  "mcpServers": {
    "c2i-athena-remote": {
      "command": "curl",
      "args": ["-X", "POST", "http://your-server:3000/mcp"],
      "env": {
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

## 🔧 Prerequisites

### For All Users:

1. **AWS CLI configured** with C2i Genomics access
2. **Python 3.11+** (for uvx/pip installations)
3. **uv or uvx installed** (recommended):
   ```bash
   # Install uv (includes uvx)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### AWS Permissions Required:

Users need an AWS profile with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "athena:ListDataCatalogs",
        "athena:ListDatabases",
        "athena:ListTableMetadata", 
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:StartQueryExecution",
        "athena:ListQueryExecutions"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject", 
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::airflow-research-main-1-us-east-1/*",
        "arn:aws:s3:::airflow-research-main-1-us-east-1"
      ]
    }
  ]
}
```

## 🚀 Quick Test

Once installed, users can test with:

```
# In VS Code or Claude Desktop
"List all available Athena databases"
→ Should show: default, research_db, clinical_data, etc.

"Calculate MRD score for sample SAMPLE123" 
→ Should return MRD calculation results

"Show me the schema for the samples table"
→ Should display table structure
```

## 📦 Deployment Workflow

### For Maintainers:

1. **Update version** in `pyproject.toml`
2. **Create git tag**: `git tag v1.0.1 && git push --tags`  
3. **GitHub Actions automatically**:
   - Builds the package
   - Publishes to PyPI
   - Updates the registry
   - Creates GitHub release

4. **Users get updates automatically** (if using org registry) or via:
   ```bash
   uvx --upgrade c2i-athena-mcp
   ```

### Security Best Practices:

- ✅ **No hardcoded AWS credentials** - uses IAM roles/profiles
- ✅ **Least privilege access** - minimal required permissions
- ✅ **Audit logs** - all queries logged in CloudTrail
- ✅ **Scoped S3 access** - only designated result buckets
- ✅ **Version pinning** - explicit version control for stability

## 🔍 Troubleshooting

### Common Issues:

**"AWS credentials not found"**
```bash
# Check AWS configuration
aws configure list-profiles
aws sts get-caller-identity --profile C2iAlefResearchAccess-340686126008
```

**"Permission denied for Athena"**
- Verify your AWS profile has the required permissions above
- Contact your AWS admin to add Athena access

**"MCP server not found"**
```bash
# Verify installation
uvx --version
uvx list | grep c2i-athena-mcp

# Reinstall if needed
uvx install c2i-athena-mcp
```

**"VS Code MCP not working"**
- Ensure VS Code is updated (MCP support requires recent versions)
- Check MCP is enabled in VS Code settings
- Verify configuration in `~/.vscode/mcp.json`

## 📞 Support

- **Internal Issues**: Contact R&D Platform team
- **GitHub Issues**: [c2i-genomics/c2i-athena-mcp/issues](https://github.com/c2i-genomics/c2i-athena-mcp/issues)
- **AWS Access**: Contact IT/DevOps for profile setup

## 🔄 Migration from Old Setup

If you were using the old EC2-based setup:

1. **Remove old VS Code config** (SSM/SSH entries)
2. **Install new package**: `uvx install c2i-athena-mcp`
3. **Add new config** (see Option 1 above)
4. **Test functionality** with the Quick Test section

The new setup is more reliable and doesn't require VPN or SSH access!