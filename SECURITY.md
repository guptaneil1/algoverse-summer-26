# Security

Do not commit API keys, Hugging Face tokens, tracking credentials, private dataset URLs, or personal data. Use environment variables or GitHub Secrets. Do not expose self-hosted GPU runners to untrusted pull requests.

Report a suspected credential or private-data exposure privately to the repository administrator. Rotate the affected secret immediately; removing it from the latest commit is not sufficient because Git history may retain it.
