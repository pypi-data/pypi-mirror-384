# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Do not report security vulnerabilities through public GitHub issues.**

Email: **security@velatir.com**

Include:
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fixes (if any)

We will respond within 48 hours.

## Security Best Practices

### API Keys
- Never commit API keys to version control
- Use environment variables
- Rotate keys regularly
- Use different keys for dev/prod

### Data Security
- Review data sent to Velatir API
- Avoid sending sensitive data in metadata
- Implement proper access controls

### Network Security
- HTTPS is used by default
- SSL certificates are validated

## Data Transmission

This package sends to Velatir API:
- Function names and arguments
- Agent responses
- Conversation context (configurable)
- Custom metadata

All transmitted over HTTPS.

## Contact

- Security: security@velatir.com
- General: hello@velatir.com
- Website: https://www.velatir.com/security
