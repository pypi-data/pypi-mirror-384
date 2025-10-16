# Security policy

**Do not** create public issues for security vulnerabilities, instead contact us at security@glassalpha.com

## Our security commitment

GlassAlpha is designed for regulated industries requiring high trust and transparency. Security is fundamental to our mission of providing audit-ready ML compliance tools.

## Reporting security vulnerabilities

If you discover a security vulnerability in GlassAlpha, please help us protect our users by reporting it responsibly:

### How to report

- **Email**: security@glassalpha.com
- **Response Time**: We aim to acknowledge reports within 48 hours
- **Process**: We will investigate all reports and provide updates on our progress

### What to include

- Description of the vulnerability and its potential impact
- Steps to reproduce the issue
- Your assessment of severity
- Any suggested fixes or mitigations

### What NOT to do

- **Do not** create public GitHub issues for security vulnerabilities
- **Do not** publicly disclose the vulnerability before we've had a chance to address it

## Supported versions

| Version | Supported                                  |
| ------- | ------------------------------------------ |
| 0.1.x   | :white_check_mark: (Pre-alpha development) |

## Security design principles

GlassAlpha follows these security principles:

- **On-Premise First**: No external network calls or cloud dependencies by design
- **Privacy by Default**: No telemetry collection (opt-in only via `GLASSALPHA_TELEMETRY=on`)
- **Data Protection**: Never logs raw PII; all identifiers are hashed
- **Reproducible Security**: All operations are deterministic and auditable

## Security features

- **Local Processing**: All model analysis happens on your infrastructure
- **No Data Transmission**: Your data never leaves your environment
- **Audit Trail**: Complete lineage tracking with cryptographic hashes
- **Deterministic Output**: Identical results for compliance verification

## Reporting security vulnerabilities

Please report security vulnerabilities to us at security@glassalpha.com

## Questions?

Contact us: security@glassalpha.com
