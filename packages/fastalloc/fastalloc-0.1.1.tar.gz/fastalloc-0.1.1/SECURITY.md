# Security Policy

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in fastalloc, please report it by emailing:

**eshanized@proton.me**

Please include:

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Status Updates**: Every week until resolution
- **Fix Timeline**: Critical issues within 2 weeks, others within 4 weeks

### Disclosure Policy

- Please do not publicly disclose the vulnerability until we have released a fix
- We will credit you in the security advisory (unless you prefer to remain anonymous)
- We follow coordinated disclosure practices

## Security Best Practices

When using fastalloc:

1. **Keep Updated**: Always use the latest version
2. **Review Dependencies**: Regularly audit your dependency tree
3. **Validate Input**: Sanitize object factories and reset methods
4. **Resource Limits**: Set appropriate capacity limits for pools
5. **Monitor**: Use statistics collection to detect anomalies

## Known Security Considerations

- **Memory Exhaustion**: Large pools can consume significant memory
- **Thread Safety**: Ensure proper pool type selection for concurrent usage
- **Object State**: Reset methods must properly clean sensitive data
- **Pickle Safety**: Be cautious when pickling pools with sensitive objects

## Contact

For security-related questions: eshanized@proton.me
