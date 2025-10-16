"""Port management and leasing system for mem8."""

import socket
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import yaml
import psutil


class PortManager:
    """Manages port leases across projects to prevent conflicts."""

    # Port ranges for different service types
    PORT_RANGES = {
        'frontend': (20000, 29999),      # Web frontends (Next.js, React, etc)
        'backend': (8000, 8999),         # Backend APIs
        'database': (5432, 5532),        # Database services
        'cache': (6379, 6479),           # Redis, memcached
        'websocket': (9000, 9099),       # WebSocket servers
        'dev_tools': (9100, 9199),       # Hot reload, debuggers, etc
        'custom': (30000, 39999),        # User-defined services
    }

    def __init__(self):
        """Initialize port manager with global registry."""
        mem8_home = Path.home() / ".mem8"
        mem8_home.mkdir(parents=True, exist_ok=True)
        self.registry_file = mem8_home / "port_leases.yaml"
        self.leases = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load global port registry."""
        if not self.registry_file.exists():
            return {
                'leases': {},
                'last_updated': datetime.now().isoformat()
            }

        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {'leases': {}, 'last_updated': datetime.now().isoformat()}
        except (yaml.YAMLError, IOError):
            return {'leases': {}, 'last_updated': datetime.now().isoformat()}

    def _save_registry(self) -> None:
        """Save global port registry."""
        self.leases['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.leases, f, default_flow_style=False, sort_keys=False)
        except (yaml.YAMLError, IOError) as e:
            print(f"Warning: Could not save port registry: {e}")

    def get_project_id(self) -> str:
        """Get unique identifier for current project."""
        cwd = Path.cwd()
        # Use absolute path as project ID
        return str(cwd.resolve())

    def is_port_available(self, port: int) -> bool:
        """Check if a port is available on the system."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                result = s.connect_ex(('localhost', port))
                return result != 0  # 0 means port is in use
        except socket.error:
            return False

    def find_available_ports(self, start: int, count: int, service_type: Optional[str] = None) -> List[int]:
        """Find available ports starting from a base port.

        Args:
            start: Starting port number
            count: Number of ports needed
            service_type: Optional service type for range validation

        Returns:
            List of available port numbers
        """
        available = []
        current = start
        max_port = 65535

        # If service type specified, constrain to that range
        if service_type and service_type in self.PORT_RANGES:
            min_range, max_range = self.PORT_RANGES[service_type]
            current = max(start, min_range)
            max_port = max_range

        # Find available ports
        while len(available) < count and current <= max_port:
            if self.is_port_available(current) and not self._is_port_leased_elsewhere(current):
                available.append(current)
            current += 1

        return available

    def _is_port_leased_elsewhere(self, port: int) -> bool:
        """Check if port is leased to another project."""
        project_id = self.get_project_id()
        for proj, lease in self.leases.get('leases', {}).items():
            if proj != project_id:
                start = lease.get('start_port')
                count = lease.get('port_count')
                if start and count:
                    end = start + count - 1
                    if start <= port <= end:
                        return True
        return False

    def lease_ports(self, start: Optional[int] = None, count: int = 5) -> Dict[str, Any]:
        """Lease ports for the current project.

        Args:
            start: Starting port number (None for auto-assign)
            count: Number of ports to lease

        Returns:
            Dictionary with lease information
        """
        project_id = self.get_project_id()
        project_name = Path.cwd().name

        # Auto-assign starting port if not provided
        if start is None:
            start = self._find_best_starting_port(count)

        # Find available ports
        available = self.find_available_ports(start, count)

        if len(available) < count:
            raise ValueError(f"Could not find {count} available ports starting from {start}")

        # Create lease - only store essential fields (end_port and port_range are calculated)
        lease = {
            'project_name': project_name,
            'project_path': project_id,
            'start_port': available[0],
            'port_count': len(available),
            'leased_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        # Update registry
        self.leases['leases'][project_id] = lease
        self._save_registry()

        # Return enriched lease with calculated fields
        return self._enrich_lease(lease)

    def _find_best_starting_port(self, count: int) -> int:
        """Find best starting port by looking for gaps in leases."""
        # Start with frontend range by default
        return 20000

    def _enrich_lease(self, lease: Dict[str, Any]) -> Dict[str, Any]:
        """Add calculated fields to a lease."""
        if not lease:
            return lease
        enriched = lease.copy()
        start = lease['start_port']
        count = lease['port_count']
        enriched['end_port'] = start + count - 1
        enriched['port_range'] = f"{start}-{enriched['end_port']}"
        return enriched

    def get_lease(self) -> Optional[Dict[str, Any]]:
        """Get current project's port lease with calculated fields."""
        project_id = self.get_project_id()
        lease = self.leases.get('leases', {}).get(project_id)
        return self._enrich_lease(lease) if lease else None

    def release_lease(self) -> bool:
        """Release current project's port lease."""
        project_id = self.get_project_id()
        if project_id in self.leases.get('leases', {}):
            del self.leases['leases'][project_id]
            self._save_registry()
            return True
        return False

    def list_all_leases(self) -> Dict[str, Any]:
        """List all port leases across all projects with calculated fields."""
        leases = self.leases.get('leases', {})
        return {proj: self._enrich_lease(lease) for proj, lease in leases.items()}

    def check_conflicts(self) -> List[Dict[str, Any]]:
        """Check for port conflicts across all leases."""
        conflicts = []
        all_ports = {}

        for project_id, lease in self.leases.get('leases', {}).items():
            start = lease.get('start_port')
            count = lease.get('port_count')
            if start and count:
                for port in range(start, start + count):
                    if port in all_ports:
                        conflicts.append({
                            'port': port,
                            'project1': all_ports[port],
                            'project2': project_id
                        })
                    else:
                        all_ports[port] = project_id

        return conflicts

    def is_port_in_project_range(self, port: int) -> bool:
        """Check if port is within current project's leased range."""
        lease = self.get_lease()
        if not lease:
            return False
        start = lease.get('start_port')
        end = lease.get('end_port')
        return start and end and start <= port <= end

    def kill_port(self, port: int, force: bool = False) -> Tuple[bool, str]:
        """Kill process using a specific port (cross-platform with psutil).

        Args:
            port: Port number to kill
            force: If False, only kill if port is in project's range

        Returns:
            Tuple of (success, message)
        """
        # Safety check - only kill ports in project's range unless forced
        if not force and not self.is_port_in_project_range(port):
            lease = self.get_lease()
            if lease:
                return False, f"Port {port} is outside project's range ({lease['port_range']}). Use --force to override."
            else:
                return False, "No port lease for this project. Use --force to kill anyway."

        # Find and kill process using psutil
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    try:
                        process = psutil.Process(conn.pid)
                        process_name = process.name()
                        process.terminate()
                        # Wait a bit for graceful termination
                        try:
                            process.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            # Force kill if still running
                            process.kill()
                        return True, f"Killed {process_name} (PID {conn.pid}) on port {port}"
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        return False, f"Could not kill process: {e}"

            return False, f"No process found listening on port {port}"
        except (psutil.AccessDenied, PermissionError):
            return False, "Permission denied. Try running with administrator/sudo privileges."
        except Exception as e:
            return False, f"Error: {e}"


def generate_ports_markdown(lease: Dict[str, Any]) -> str:
    """Generate ports.md content from lease information.

    Note: Expects enriched lease with calculated end_port and port_range.
    """
    start_port = lease['start_port']
    port_count = lease['port_count']
    lease['end_port']  # Calculated field
    port_range = lease['port_range']  # Calculated field

    content = f"""---
# Auto-generated by mem8 ports
# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Project: {lease['project_name']}
# Port Range: {port_range}

project_name: {lease['project_name']}
project_path: '{lease['project_path']}'
start_port: {start_port}
port_count: {port_count}
leased_at: '{lease['leased_at']}'
---

# Port Range: {port_range}

This project has leased ports **{port_range}** from the global mem8 port registry.

## Usage Instructions for AI Agents

**ALWAYS use ports within this range ({port_range}) for all services in this project.**

### Port Assignment Strategy

You have **{lease['port_count']} ports** available. Assign them as needed:

- Port {start_port}: Main frontend (Next.js, React, Vue, etc)
- Port {start_port + 1}: Backend API
- Port {start_port + 2}: Database
- Port {start_port + 3}: Cache/Redis
- Port {start_port + 4}: Additional services

### Examples

**Next.js Frontend:**
```bash
# Force specific port (prevents auto-increment to 3001)
PORT={start_port} npm run dev
# OR
next dev -p {start_port}
```

**Backend API:**
```bash
# FastAPI
uvicorn main:app --port {start_port + 1} --reload

# Flask
flask run --port {start_port + 1}

# Express
PORT={start_port + 1} npm start
```

**Docker Compose:**
```yaml
services:
  frontend:
    ports:
      - "{start_port}:3000"
  backend:
    ports:
      - "{start_port + 1}:8000"
  database:
    ports:
      - "{start_port + 2}:5432"
```

## Killing Processes on Ports

### Safe Kill (Only Ports in Project Range)
```bash
mem8 ports --kill {start_port}
```

This will only kill processes on ports {port_range} (your project's range).

### Force Kill (Any Port - Use with Caution)
```bash
mem8 ports --kill <port> --force
```

### Alternative Methods
```bash
# Cross-platform with npx
npx kill-port {start_port}

# Windows
netstat -ano | findstr :{start_port}
taskkill /PID <pid> /F

# Unix/Linux/Mac
lsof -ti :{start_port} | xargs kill -9
```

## Important Notes

1. **Next.js Auto-Increment:** Next.js will use 3001, 3002 if 3000 is taken. Always force the port with `PORT=` or `-p` flag.

2. **Docker Port Mapping:** Map container ports to your assigned range:
   ```yaml
   ports:
     - "{start_port}:3000"  # External:Internal
   ```

3. **Environment Variables:** Set `PORT` env var before starting services:
   ```bash
   export PORT={start_port}  # Unix
   set PORT={start_port}      # Windows cmd
   $env:PORT={start_port}     # Windows PowerShell
   ```

## Global Registry

View all projects and their port assignments:
```bash
mem8 ports --list-all
```

Check for conflicts across projects:
```bash
mem8 ports --check-conflicts
```

Release ports when project is complete:
```bash
mem8 ports --release
```

Registry location: `~/.mem8/port_leases.yaml`

## Project Notes

Add project-specific port configuration notes here. This section is preserved when regenerating.
"""

    return content


def save_ports_file(lease: Dict[str, Any], workspace_dir: Optional[Path] = None) -> Path:
    """Save ports.md file for current project."""
    if workspace_dir is None:
        workspace_dir = Path.cwd()

    mem8_dir = workspace_dir / '.mem8'
    mem8_dir.mkdir(exist_ok=True)

    output_file = mem8_dir / 'ports.md'
    content = generate_ports_markdown(lease)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return output_file
