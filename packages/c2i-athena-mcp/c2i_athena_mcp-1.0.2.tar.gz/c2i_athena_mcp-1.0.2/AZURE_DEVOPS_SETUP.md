# Azure DevOps Setup Guide for C2i Athena MCP

## 🚀 Step-by-Step Publishing Setup

### Step 1: Build and Test Package Locally

```bash
cd /home/ec2-user/c2i_alg_mcp_clean
./build_and_test.sh
```

This will:
- ✅ Install build dependencies
- ✅ Build the Python package
- ✅ Validate package integrity
- ✅ Test basic imports

### Step 2: Set Up PyPI Account

1. **Create PyPI Account**: https://pypi.org/account/register/
2. **Verify email** and enable 2FA
3. **Generate API Token**:
   - Go to: https://pypi.org/manage/account/token/
   - Create token with scope: "Entire account"
   - Copy the token (starts with `pypi-`)

### Step 3: Manual PyPI Upload (First Time)

```bash
# Configure PyPI credentials
echo '[pypi]' > ~/.pypirc
echo 'username = __token__' >> ~/.pypirc
echo 'password = pypi-YOUR_TOKEN_HERE' >> ~/.pypirc

# Upload to PyPI
cd src/c2i_athena_mcp
twine upload dist/*
```

### Step 4: Set Up Azure DevOps Pipeline

1. **Create Azure DevOps Project** (if not exists)
2. **Connect to your Git repository**
3. **Set Up Service Connections**:

   **PyPI Service Connection:**
   - Go to: Project Settings → Service connections
   - New service connection → Python package upload (PyPI)
   - Name: `PyPI-Connection`
   - Server URL: `https://upload.pypi.org/legacy/`
   - Username: `__token__`
   - Password: Your PyPI token

   **GitHub Service Connection** (if using GitHub):
   - New service connection → GitHub
   - Name: `GitHub-Connection`
   - Authorize with GitHub

4. **Create Pipeline**:
   - Go to Pipelines → New pipeline
   - Choose your repository
   - Select "Existing Azure Pipelines YAML file"
   - Path: `/azure-pipelines.yml`

### Step 5: Set Up Environments

1. **Create Environment**:
   - Go to Pipelines → Environments
   - New environment: `pypi-production`
   - Add approval checks if needed for production releases

### Step 6: Push to Repository and Create Release

```bash
# Add all files
git add .
git commit -m "Initial MCP package setup with Azure DevOps pipeline"

# Push to your repository (Azure DevOps or GitHub)
git push origin main

# Create first release tag
git tag v1.0.0
git push origin v1.0.0
```

## 📋 What Happens When You Tag a Release

1. **Azure Pipeline Triggers** on tag push
2. **Builds Package** and runs quality checks
3. **Publishes to PyPI** automatically
4. **Updates Registry** with new version
5. **Creates GitHub Release** (if configured)

## 🔧 Azure DevOps Pipeline Features

The `azure-pipelines.yml` includes:

- ✅ **Multi-stage pipeline** (Build → Publish → Update Registry)
- ✅ **Only publishes on tags** (prevents accidental releases)
- ✅ **Quality gates** (package validation)
- ✅ **Artifact management** (stores built packages)
- ✅ **Environment protection** (approval workflows)
- ✅ **Automatic registry updates**

## 🎯 Team Distribution URLs

Once published, share these with your team:

### For GitHub Copilot Admins:
```
MCP Registry URL: https://raw.githubusercontent.com/c2i-genomics/c2i-athena-mcp/main/registry.json
```

### For Individual Users:
```bash
# Install command
uvx install c2i-athena-mcp

# VS Code configuration
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

## 🔄 Future Updates Workflow

1. **Make code changes**
2. **Update version** in `src/c2i_athena_mcp/__init__.py`
3. **Commit and tag**: `git tag v1.0.1 && git push origin v1.0.1`
4. **Pipeline auto-publishes** new version
5. **Users get updates** via `uvx --upgrade c2i-athena-mcp`

## 🛠️ Troubleshooting

**Pipeline fails on PyPI upload:**
- Check PyPI token is valid
- Verify service connection configuration
- Ensure version number is incremented

**Package import errors:**
- Run local build test: `./build_and_test.sh`
- Check all dependencies in `pyproject.toml`
- Verify relative imports work correctly

**Registry not updating:**
- Check GitHub service connection
- Verify repository permissions
- Check if GitHub releases are being created

## 📞 Support

- **Azure DevOps Issues**: Check pipeline logs and service connections
- **PyPI Issues**: Verify tokens and package metadata
- **GitHub Issues**: Check repository permissions and service connections

---

**Your automated publishing pipeline is ready! 🎉**

Tag a release and watch the magic happen!