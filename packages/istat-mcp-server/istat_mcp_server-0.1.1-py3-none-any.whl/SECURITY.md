# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of ISTAT MCP Server seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please DO NOT:

- Open a public GitHub issue for security vulnerabilities
- DiVsclose the vulnerability publicly before it has been addressed

### Please DO:

1. **Report via GitHub Security Advisory**: Use [GitHub's private vulnerability reporting](https://github.com/Halpph/istat-mcp-server/security/advisories/new) feature
2. **Or email**: Send details to the maintainer (see GitHub profile for contact)

### What to Include:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect:

- **Acknowledgment**: We will acknowledge your report within 48 hours
- **Updates**: We will send you regular updates about our progress
- **Disclosure**: Once a fix is available, we will coordinate disclosure timing with you
- **Credit**: We will credit you in the release notes (unless you prefer to remain anonymous)

## Security Best Practices

### For Users:

1. **Keep dependencies updated**: Regularly update the MCP server and its dependencies
   ```bash
   uv sync
   ```

2. **Review storage paths**: Ensure `MCP_STORAGE_DIR` points to a safe location with appropriate permissions

3. **Monitor logs**: Check for unusual activity or errors in your MCP server logs

4. **Use latest version**: Always use the latest stable version of the server

### For Contributors:

1. **Never commit secrets**: Don't commit API keys, tokens, or credentials
2. **Review dependencies**: Check for known vulnerabilities in dependencies
3. **Validate input**: Always validate and sanitize user inputs
4. **Follow secure coding practices**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## Known Security Considerations

### Path Traversal Protection

The server includes built-in path traversal protection for file operations. All file downloads are restricted to the configured storage directory.

### Network Requests

The server makes HTTP requests to ISTAT's SDMX API. These are read-only operations and do not transmit sensitive data.

### Local Storage

Downloaded datasets are stored locally. Ensure your storage directory has appropriate file system permissions.

## Security Updates

Security updates will be released as patch versions (e.g., 0.1.1, 0.1.2) and announced in:
- [GitHub Security Advisories](https://github.com/Halpph/istat-mcp-server/security/advisories)
- [Release Notes](https://github.com/Halpph/istat-mcp-server/releases)
- The project README

## Questions?

If you have questions about security that don't involve reporting a vulnerability, please open a regular GitHub issue with the "security" label.
