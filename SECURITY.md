# Security policy

Never commit API tokens. Use environment variables or a secret manager. Regenerate a leaked token immediately. Avoid logging full HTTP requests or exception tracebacks that may include API URLs with bot tokens. In production, validate webhook authenticity, limit request body sizes, use HTTPS, and deduplicate update IDs. Do not assume requests from an unknown platform are authenticated. Report vulnerabilities privately to the repository maintainer once a contact method is configured.
