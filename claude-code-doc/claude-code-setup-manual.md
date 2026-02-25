# Claude Code Setup Manual

## Overview

This manual explains how to install and configure Claude Code in a
professional development environment.

------------------------------------------------------------------------

# Architecture

``` mermaid
flowchart LR
User[Developer]
VSCode[VSCode Terminal]
Claude[Claude Code CLI]

User --> VSCode
VSCode --> Claude
```

------------------------------------------------------------------------

# Requirements

-   Windows / macOS / Linux
-   Node.js 18+
-   npm
-   VSCode recommended

Check installation:

``` bash
node -v
npm -v
```

------------------------------------------------------------------------

# Install Claude Code

``` bash
npm install -g @anthropic-ai/claude-code
```

Verify:

``` bash
claude --version
```

------------------------------------------------------------------------

# Basic Usage

``` bash
claude
```

Example prompt:

    Analyze this repository and generate documentation.

------------------------------------------------------------------------

# Updating

``` bash
npm update -g @anthropic-ai/claude-code
```

------------------------------------------------------------------------

# Troubleshooting

``` bash
where claude
npm prefix -g
```

------------------------------------------------------------------------

# Recommended Folder Structure

    project/
     docs/
     src/
     README.md
