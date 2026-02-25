# Atlassian MCP + Claude Integration Guide

------------------------------------------------------------------------

# System Architecture

``` mermaid
flowchart LR
Claude[Claude Code]
MCP[MCP Bridge]
Atlassian[Atlassian MCP]
Jira[Jira Cloud]

Claude --> MCP
MCP --> Atlassian
Atlassian --> Jira
```

------------------------------------------------------------------------

# Installing the Bridge

``` bash
npm install -g mcp-remote
```

------------------------------------------------------------------------

# Register Atlassian MCP

``` bash
claude mcp add --transport stdio atlassian -- mcp-remote https://mcp.atlassian.com/v1/mcp
```

------------------------------------------------------------------------

# Verify

``` bash
claude mcp list
```

------------------------------------------------------------------------

# Authentication Flow

``` mermaid
sequenceDiagram
Developer->>Claude: Request Jira action
Claude->>Browser: OAuth login
Browser->>Atlassian: Authenticate
Atlassian-->>Claude: Token
Claude->>MCP: Access Jira
```

------------------------------------------------------------------------

# Example Automation

Prompt:

Create Jira stories from SRS.md

Workflow:

``` mermaid
flowchart LR
SRS[SRS Document]
Claude[Claude Analysis]
Jira[Jira Stories]

SRS --> Claude
Claude --> Jira
```
