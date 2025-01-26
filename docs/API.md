
# Nexus Security Scanner API Reference

## Core API

### Scanner

```python
from nexus import Scanner

scanner = Scanner(config_path="config.yml")
result = scanner.scan_target("example.com")



API.md
Methods
scan_target(target: str) -> ScanResult
scan_multiple(targets: List[str]) -> List[ScanResult]
configure(config: Dict) -> None
get_status() -> ScannerStatus
Reporter
from nexus import Reporter

reporter = Reporter(format="json")
reporter.generate(scan_result)



Methods
generate(result: ScanResult) -> str
export(path: Path) -> None
get_formats() -> List[str]
Advanced Features
Custom Rules
from nexus import Rule

rule = Rule(
    name="custom_check",
    severity="HIGH",
    callback=lambda target: check_vulnerability(target)
)
scanner.add_rule(rule)



Filters
from nexus import Filter

filter = Filter(
    field="severity",
    operator="equals",
    value="HIGH"
)
results.apply_filter(filter)



WebSocket API
Events
ws = new WebSocket("ws://localhost:8080/nexus")

ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    console.log(data.status)
}



Available Events
scan.started
scan.progress
scan.completed
scan.error
Commands
ws.send(JSON.stringify({
    command: "start_scan",
    target: "example.com"
}))



REST API
Endpoints
Scan Operations
POST /api/v1/scan
Content-Type: application/json

{
    "target": "example.com",
    "options": {
        "depth": 2,
        "timeout": 30
    }
}



Results
GET /api/v1/results/{scan_id}
Authorization: Bearer {token}



Configuration
PUT /api/v1/config
Content-Type: application/json

{
    "max_depth": 3,
    "threads": 10
}



Authentication
POST /api/v1/auth
Content-Type: application/json

{
    "api_key": "your-api-key"
}



Response:

{
    "token": "jwt-token",
    "expires_in": 3600
}



Error Handling
Error Codes
4000: Invalid Request
4001: Authentication Failed
4002: Rate Limit Exceeded
5000: Internal Error
Error Response
{
    "error": {
        "code": 4000,
        "message": "Invalid target format",
        "details": {
            "field": "target",
            "reason": "Must be valid domain"
        }
    }
}



Rate Limiting
Default: 100 requests per minute
Premium: 1000 requests per minute
Headers:
X-RateLimit-Limit
X-RateLimit-Remaining
X-RateLimit-Reset
SDK Examples
Python
from nexus import NexusClient

client = NexusClient(api_key="your-api-key")
scan = client.create_scan("example.com")
results = scan.wait_for_completion()



JavaScript
const Nexus = require('nexus-client');

const client = new Nexus({
    apiKey: 'your-api-key'
});

client.scan('example.com')
    .then(results => console.log(results));



Best Practices
Always handle rate limits
Use webhook callbacks for long scans
Implement proper error handling
Cache results when possible
Use compression for large datasets
Support
Documentation: https://docs.nexus-scanner.io
Issues: https://github.com/nexus/issues
Support: support@nexus-scanner.io

Would you like to create another documentation file for Nexus?

