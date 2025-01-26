# Nexus Security Scanner

A modern, extensible, and robust security scanning tool for web applications and infrastructure. Nexus Security Scanner is designed to deliver deep insights and actionable data for improving security posture.

---

## Features

### ✨ **Advanced Scanning Capabilities**
- Multi-threaded and adaptive scanning engine.
- Support for custom rules and modular scanners.
- Real-time vulnerability detection and reporting.
- Advanced crawling with filtering options.

### 🔧 **Rich and Flexible Reporting**
- Interactive CLI-based reports.
- JSON, HTML, and tree-structured outputs.
- Export to custom formats and templates.
- Detailed performance and trend analysis.

### ⚙️ **Integration-Friendly**
- REST API and WebSocket support for automation.
- CI/CD plugins for seamless DevSecOps workflows.
- Webhooks for real-time notifications.

### 🌐 **Scanners and Tools**
- **Port Scanner**: Detect open ports and services.
- **SSL Checker**: Verify SSL/TLS configurations.
- **WAF Detector**: Identify Web Application Firewalls.
- **Technology Detector**: Discover backend technologies.
- **CDN Detector**: Analyze content delivery networks.

---

## Project Structure

```text
├── src/
│   ├── core/
│   │   ├── scanner.py          # Main scanning engine
│   │   ├── crawler.py          # URL crawler
│   │   └── analyzer.py         # Data analysis module
│   │
│   ├── scanners/
│   │   ├── port_scanner.py     # Port scanning logic
│   │   ├── ssl_checker.py      # SSL/TLS validation
│   │   ├── waf_detector.py     # WAF detection
│   │   └── tech_detector.py    # Backend technology detection
│   │
│   ├── ui/
│   │   ├── progress.py         # Progress bars for CLI
│   │   ├── graphs.py           # ASCII graph visualizations
│   │   └── menu.py             # Interactive menu system
│   │
│   ├── reporters/
│   │   ├── cli_reporter.py     # CLI-based reporting
│   │   ├── json_reporter.py    # JSON format output
│   │   └── log_handler.py      # Logging utilities
│   │
│   ├── utils/
│   │   ├── config.py           # Configuration manager
│   │   ├── threading.py        # Thread management helpers
│   │   └── helpers.py          # General utility functions
│
├── tests/
├── config/
├── docs/
├── main.py                     # Application entry point
└── requirements.txt            # Dependency list
```

---

## Installation

Install the Nexus Security Scanner via pip:

```bash
pip install nexus-scanner
```

---

## Usage

### Quick Start

Run a basic scan on a target:

```python
from src.core.scanner import Scanner

scanner = Scanner()
results = scanner.scan("example.com")
```

### Configuration

Edit `config/default_config.yaml` to customize your scanning options:

```yaml
scan:
  depth: 3
  threads: 10
  timeout: 20
```

You can also specify authentication details:

```yaml
auth:
  api_key: YOUR_API_KEY
  token: YOUR_TOKEN
```

---

## Key Features and Examples

### 1. **Custom Rules**
Define and apply custom security rules:

```python
from src.core.analyzer import Rule

def check_headers(response):
    return "X-Frame-Options" not in response.headers

rule = Rule(
    name="missing_headers",
    severity="HIGH",
    check=check_headers
)
```

### 2. **Integrations**
- **GitHub Actions**

```yaml
steps:
  - uses: nexus-scanner/action@v1
    with:
      target: ${{ env.DEPLOY_URL }}
```

- **Jenkins Pipeline**

```groovy
stage('Security Scan') {
    steps {
        nexusScan target: 'production.com'
    }
}
```

### 3. **Performance Tips**
- Enable async scanning for large targets.
- Use result caching for recurring scans.
- Optimize rule execution order to reduce scan time.

---

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Commit and push your changes.
4. Submit a pull request.

We welcome contributions from the security and developer community!

---

## Support


- **Community**: [Join Discord](https://t.me/nexusscann)
- **Issues**: [GitHub Issues](https://github.com/hexday/nexus-scanner)

---

## License

MIT License – See `LICENSE` file for details.

---

## Acknowledgments

- Thanks to the security research community and open-source contributors.
- Special recognition to our beta testers and enterprise partners.

---
## Note: This file has not been fully tested yet
This file may encounter issues during certain scans or under specific conditions. If you notice any problems or bugs, please report them using one of the following methods:

Submit a Pull Request if you have a solution to fix the issue.

- **Send an email to**: [my Email](mahdi.ghourchi.me@gmail.com).

Any feedback or suggestions for improving this file are highly appreciated. Thank you for your cooperation!
