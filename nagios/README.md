# Phoenix Nagios Core Observability & Custom Plugins

Comprehensive monitoring infrastructure declared for Project **Phoenix**, providing host and service health probes, custom Python and Bash plugins, and automated proof-of-recovery verification.

---

## 1. Directory Structure

```text
nagios/
├── install_nagios.sh        # Automated compilation and installation script
├── validate_config.py       # Configuration integrity validator
├── etc/
│   ├── nagios.cfg           # Main Nagios Core daemon configuration
│   └── objects/
│       ├── commands.cfg     # Command definitions (standard + custom plugins)
│       ├── hosts.cfg        # Host definitions: app-server, puppet-master, nagios-server
│       ├── services.cfg     # 12 Service definitions across hosts
│       ├── templates.cfg    # Generic host and service templates
│       ├── timeperiods.cfg  # Standard 24x7 time period definition
│       └── contacts.cfg     # Administrative notification contacts
├── plugins/
│   ├── check_portal_health.py # Custom Python plugin for /health & latency
│   ├── check_web_errors.sh    # Custom Bash plugin for Nginx 5xx log scanning
│   └── check_web_errors.py    # Python implementation of log error parser
└── tests/
    └── test_nagios_plugins.py # Automated unit test suite simulating 0, 1, 2, 3 states
```

---

## 2. Custom Plugins Specification

### Plugin 1: `check_portal_health.py`
Queries the application's `/health` probe, tests database connectivity, measures latency, and outputs Nagios performance data:
```bash
python3 plugins/check_portal_health.py -H 192.168.56.30 -p 80 -u /health -w 500 -c 1500
```
- **Exit 0 (OK)**: HTTP 200, `status=healthy`, `db=ok`, latency < 500ms.
- **Exit 1 (WARNING)**: HTTP 200, latency $\ge$ 500ms and < 1500ms.
- **Exit 2 (CRITICAL)**: Service unreachable, HTTP 5xx, `db=failed`, or latency $\ge$ 1500ms.
- **Exit 3 (UNKNOWN)**: Argument error or unhandled network exception.

### Plugin 2: `check_web_errors.sh`
Scans the web server access log for HTTP 5xx server errors within a sliding time window:
```bash
bash plugins/check_web_errors.sh -f /var/log/nginx/access.log -w 5 -c 20 -m 5
```
- **Exit 0 (OK)**: 5xx count < 5.
- **Exit 1 (WARNING)**: 5xx count between 5 and 19.
- **Exit 2 (CRITICAL)**: 5xx count $\ge$ 20.
- **Exit 3 (UNKNOWN)**: Log file does not exist.

---

## 3. Local Unit Testing

Run the complete plugin unit test suite:
```bash
python -m pytest -v nagios/tests/test_nagios_plugins.py
```
*(Executes 9 automated test cases verifying healthy, slow, down, connection refused, and unknown states).*

---

## 4. Configuration Validation

Validate all object definitions before deploying to the Nagios VM:
```bash
python nagios/validate_config.py
```

On the Nagios Server VM:
```bash
sudo /usr/local/nagios/bin/nagios -v /usr/local/nagios/etc/nagios.cfg
```

---

## 5. Live Demonstration Runbook

Refer to [`docs/NAGIOS_DEMO.md`](file:///c:/Users/venum/.gemini/antigravity-ide/scratch/Phoenix/docs/NAGIOS_DEMO.md) for the step-by-step alert lifecycle demonstration guide with screenshot points.
