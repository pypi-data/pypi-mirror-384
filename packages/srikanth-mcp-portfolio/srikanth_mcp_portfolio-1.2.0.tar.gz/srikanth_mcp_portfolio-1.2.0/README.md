# Portfolio MCP Server

A dual-stack Model Context Protocol (MCP) server for Srikanth Karthikeyan's portfolio data, available in both Node.js and Python implementations with containerized deployment options.

## Features

The server provides the following tools:

### 🔍 `search_portfolio`
Search through portfolio data by keywords, category, or content.

**Parameters:**
- `query` (required): Search query to find relevant information
- `category` (optional): Filter by specific category
- `limit` (optional): Maximum results to return (default: 10)

### 📂 `get_portfolio_categories`
Get all available categories in the portfolio data.

### 🎯 `get_portfolio_item`
Get a specific portfolio item by ID.

**Parameters:**
- `id` (required): The ID of the portfolio item

### 📞 `get_contact_info`
Get all contact information.

### 💻 `get_tech_stack`
Get detailed information about technical skills and tools.

**Parameters:**
- `type` (optional): Filter by specific tech type

## 🚀 Installation & Deployment

### Package Registries

#### Node.js Packages (Both Registries)
```bash
# From npmjs.com (public)
npm install srikanth-mcp-portfolio-server

# From GitHub Packages 
npm install @srikanth-karthi/srikanth-mcp-portfolio-server
```

#### Python Package
```bash
# From PyPI (public)
pip install srikanth-mcp-portfolio
```

### Docker Deployment (Multiple Registries)

#### From Docker Hub (Public)
```bash
# Node.js version
docker run -it srikanthkarthi/mcp-portfolio-server:nodejs-latest

# Python version  
docker run -it srikanthkarthi/mcp-portfolio-server:python-latest

# Multi-runtime version
docker run -it srikanthkarthi/mcp-portfolio-server:multi-latest
```

#### From GitHub Container Registry
```bash
# Node.js version
docker run -it ghcr.io/srikanth-karthi/mcp-portfolio-server:nodejs-latest

# Python version
docker run -it ghcr.io/srikanth-karthi/mcp-portfolio-server:python-latest

# Multi-runtime version
docker run -it ghcr.io/srikanth-karthi/mcp-portfolio-server:multi-latest
```

#### Using Docker Compose (Local Development)
```bash
# Choose one:
docker compose up mcp-portfolio-nodejs    # Node.js only
docker compose up mcp-portfolio-python    # Python only
docker compose up mcp-portfolio-multi     # Both runtimes
```

### Development Setup

#### Node.js Development
```bash
npm install
npm run dev
```

#### Python Development
```bash
pip install -e .
python -m mcp_portfolio_server.server
```

## 🔧 Claude Desktop Integration

### Using Docker Hub (Public)
```json
{
  "mcpServers": {
    "portfolio": {
      "command": "docker", 
      "args": [
        "run", "-i", "--rm",
        "srikanthkarthi/mcp-portfolio-server:latest"
      ]
    }
  }
}
```

### Using GitHub Container Registry  
```json
{
  "mcpServers": {
    "portfolio": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", 
        "ghcr.io/srikanthkarthi/mcp-portfolio-server:latest"
      ]
    }
  }
}
```

### Using npm Package (Public Registry)
```json
{
  "mcpServers": {
    "portfolio": {
      "command": "npx",
      "args": ["srikanth-mcp-portfolio-server"]
    }
  }
}
```

### Using npm Package from GitHub Packages
```json
{
  "mcpServers": {
    "portfolio": {
      "command": "npx",
      "args": ["@srikanth-karthi/srikanth-mcp-portfolio-server"]
    }
  }
}
```

### Using Python Package
```json
{
  "mcpServers": {
    "portfolio": {
      "command": "python",
      "args": ["-m", "mcp_portfolio_server.server"]
    }
  }
}
```

### Development Mode
```json
{
  "mcpServers": {
    "portfolio": {
      "command": "node",
      "args": ["/path/to/mcp-portfolio/src/index.js"],
      "cwd": "/path/to/mcp-portfolio"
    }
  }
}
```

## 📦 Automated Building & Publishing

### GitHub Actions Workflows

The repository includes automated CI/CD workflows:

- **Triggers**: Git tags (`v*`) or manual workflow dispatch
- **Builds**: Multi-architecture Docker images (AMD64/ARM64)
- **Publishes**: 
  - Node.js package to GitHub Packages
  - Python package to PyPI  
  - Docker images to GitHub Container Registry

### Manual Building

#### Docker Build Commands
```bash
# Build Node.js image
docker build --target nodejs -t mcp-portfolio:nodejs .

# Build Python image  
docker build --target python -t mcp-portfolio:python .

# Build multi-runtime image
docker build --target multi -t mcp-portfolio:multi .
```

### Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `NODE_ENV` | Node.js environment | `production` |
| `PYTHONUNBUFFERED` | Python output buffering | `1` |
| `DATA_PATH` | Portfolio data file path | `/app/sample-data.json` |

Switch between Node.js and Python in multi-runtime container:
```yaml
# In docker-compose.yml, uncomment to use Python:
command: ["python3", "-m", "mcp_portfolio_server.server"]
```

## Data Categories

The server provides access to the following portfolio categories:

- **Profile Summary**: Overview and introduction
- **Current Position**: Job title, company, duration
- **Current Work**: Responsibilities and projects
- **Experience**: Work history and achievements
- **Education**: Academic background
- **Tech Stack**: Programming languages, frameworks, tools
- **Certifications**: Professional certifications
- **Volunteerism**: Community service and activities
- **Contact**: Social media and professional links
- **Languages**: Language proficiency

## Example Queries

- Search for cloud experience: `search_portfolio("cloud", "Experience")`
- Get all tech stack info: `get_tech_stack()`
- Find contact information: `get_contact_info()`
- Search for certifications: `search_portfolio("aws certification")`

## License

MIT
