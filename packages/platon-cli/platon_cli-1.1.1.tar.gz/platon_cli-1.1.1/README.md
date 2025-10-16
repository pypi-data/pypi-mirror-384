# Platon CLI

a command-line tool for managing Vault secrets and Kubernetes resources for Sikt repos.

includes...

- vault secret management
- kubernetes resource operations
- auto-detection of repository configuration
- interactive tui menu
- shell completion for bash and zsh

## Installation

Install Vault CLI:

```bash
# macOS
brew tap hashicorp/tap
brew install hashicorp/tap/vault

# Linux (Ubuntu/Debian)
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install vault

# Windows
choco install vault

# for other platforms, see: https://developer.hashicorp.com/vault/install
```

### Install Platon CLI

```bash
# Using uv (recommended)
uv pip install platon-cli

# Using pip
pip install platon-cli
```

### Vault Login

login to vault using oidc:

```bash
vault login -method=oidc mount=microsoft
```

## Quick Start

navigate to a local repo and run:

```bash
platon

platon --help

platon status
```

For detailed usage, configuration, and examples, see [docs.md](docs.md).

