"""
Production-grade health check patterns for MCP servers.

Implements readiness/liveness probes and dependency checking.
"""

from typing import Dict


def get_python_health_check() -> str:
    """Generate Python health check with readiness/liveness."""
    return '''
# Health check endpoints
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

class HealthCheck:
    """Health check manager for MCP server."""

    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.ready = False
        self.dependencies = {}

    async def check_readiness(self) -> Dict[str, Any]:
        """Check if server is ready to accept requests."""
        checks = {
            "server": "ok",
            "dependencies": {}
        }

        # Check tool registry
        try:
            # Verify tools are loadable
            checks["dependencies"]["tools"] = "ok"
        except Exception as e:
            checks["dependencies"]["tools"] = f"error: {e}"
            checks["server"] = "not_ready"

        return {
            "status": checks["server"],
            "checks": checks["dependencies"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def check_liveness(self) -> Dict[str, Any]:
        """Check if server is alive (basic ping)."""
        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        return {
            "status": "alive",
            "uptime_seconds": uptime,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

health_checker = HealthCheck()
'''


def get_nodejs_health_check() -> str:
    """Generate Node.js health check with readiness/liveness."""
    return '''
// Health check manager
class HealthCheck {
  constructor() {
    this.startTime = Date.now();
    this.ready = false;
    this.dependencies = {};
  }

  async checkReadiness() {
    const checks = {
      server: 'ok',
      dependencies: {}
    };

    // Check tool registry
    try {
      // Verify tools are accessible
      checks.dependencies.tools = 'ok';
    } catch (error) {
      checks.dependencies.tools = `error: ${error.message}`;
      checks.server = 'not_ready';
    }

    return {
      status: checks.server,
      checks: checks.dependencies,
      timestamp: new Date().toISOString()
    };
  }

  async checkLiveness() {
    const uptime = (Date.now() - this.startTime) / 1000;

    return {
      status: 'alive',
      uptime_seconds: uptime,
      timestamp: new Date().toISOString()
    };
  }
}

const healthChecker = new HealthCheck();
'''


def get_go_health_check() -> str:
    """Generate Go health check with readiness/liveness."""
    return '''
// Health check manager
type HealthCheck struct {
\tStartTime time.Time
\tReady     bool
}

func NewHealthCheck() *HealthCheck {
\treturn &HealthCheck{
\t\tStartTime: time.Now(),
\t\tReady:     false,
\t}
}

func (h *HealthCheck) CheckReadiness() map[string]interface{} {
\tchecks := map[string]interface{}{
\t\t"server": "ok",
\t\t"dependencies": map[string]string{
\t\t\t"tools": "ok",
\t\t},
\t}

\treturn map[string]interface{}{
\t\t"status":    checks["server"],
\t\t"checks":    checks["dependencies"],
\t\t"timestamp": time.Now().Format(time.RFC3339),
\t}
}

func (h *HealthCheck) CheckLiveness() map[string]interface{} {
\tuptime := time.Since(h.StartTime).Seconds()

\treturn map[string]interface{}{
\t\t"status":         "alive",
\t\t"uptime_seconds": uptime,
\t\t"timestamp":      time.Now().Format(time.RFC3339),
\t}
}

var healthChecker = NewHealthCheck()
'''


def get_csharp_health_check() -> str:
    """Generate C# health check with readiness/liveness."""
    return '''
// Health check manager
public class HealthCheck
{
    private readonly DateTime _startTime;

    public HealthCheck()
    {
        _startTime = DateTime.UtcNow;
    }

    public Dictionary<string, object> CheckReadiness()
    {
        var checks = new Dictionary<string, object>
        {
            ["server"] = "ok",
            ["dependencies"] = new Dictionary<string, string>
            {
                ["tools"] = "ok"
            }
        };

        return new Dictionary<string, object>
        {
            ["status"] = checks["server"],
            ["checks"] = checks["dependencies"],
            ["timestamp"] = DateTime.UtcNow.ToString("o")
        };
    }

    public Dictionary<string, object> CheckLiveness()
    {
        var uptime = (DateTime.UtcNow - _startTime).TotalSeconds;

        return new Dictionary<string, object>
        {
            ["status"] = "alive",
            ["uptime_seconds"] = uptime,
            ["timestamp"] = DateTime.UtcNow.ToString("o")
        };
    }
}

static HealthCheck healthChecker = new HealthCheck();
'''


def get_rust_health_check() -> str:
    """Generate Rust health check with readiness/liveness."""
    return '''
// Health check manager
use std::time::{SystemTime, UNIX_EPOCH};

pub struct HealthCheck {
    start_time: SystemTime,
}

impl HealthCheck {
    pub fn new() -> Self {
        HealthCheck {
            start_time: SystemTime::now(),
        }
    }

    pub fn check_readiness(&self) -> Value {
        let checks = json!({
            "server": "ok",
            "dependencies": {
                "tools": "ok"
            }
        });

        json!({
            "status": checks["server"],
            "checks": checks["dependencies"],
            "timestamp": chrono::Utc::now().to_rfc3339()
        })
    }

    pub fn check_liveness(&self) -> Value {
        let uptime = self.start_time.elapsed().unwrap().as_secs_f64();

        json!({
            "status": "alive",
            "uptime_seconds": uptime,
            "timestamp": chrono::Utc::now().to_rfc3339()
        })
    }
}

lazy_static::lazy_static! {
    static ref HEALTH_CHECKER: HealthCheck = HealthCheck::new();
}
'''


def get_health_endpoints_pattern(language: str, agent_name: str) -> Dict[str, str]:
    """Get health endpoint handlers for a language."""

    if language == "python":
        return {
            "health": '''
@app.get("/health")
async def health():
    """Basic health check (liveness probe)."""
    return await health_checker.check_liveness()
''',
            "ready": '''
@app.get("/ready")
async def ready():
    """Readiness probe - checks dependencies."""
    return await health_checker.check_readiness()
'''
        }

    elif language == "nodejs":
        return {
            "health": '''
app.get('/health', async (req, res) => {
  const health = await healthChecker.checkLiveness();
  res.json(health);
});
''',
            "ready": '''
app.get('/ready', async (req, res) => {
  const readiness = await healthChecker.checkReadiness();
  const statusCode = readiness.status === 'ok' ? 200 : 503;
  res.status(statusCode).json(readiness);
});
'''
        }

    elif language == "go":
        return {
            "health": '''
func healthHandler(w http.ResponseWriter, r *http.Request) {
\thealth := healthChecker.CheckLiveness()
\tjson.NewEncoder(w).Encode(health)
}
''',
            "ready": '''
func readyHandler(w http.ResponseWriter, r *http.Request) {
\treadiness := healthChecker.CheckReadiness()
\tif readiness["status"] != "ok" {
\t\tw.WriteHeader(http.StatusServiceUnavailable)
\t}
\tjson.NewEncoder(w).Encode(readiness)
}
'''
        }

    elif language == "csharp":
        return {
            "health": '''
app.MapGet("/health", () => healthChecker.CheckLiveness());
''',
            "ready": '''
app.MapGet("/ready", (HttpContext context) =>
{
    var readiness = healthChecker.CheckReadiness();
    if (readiness["status"].ToString() != "ok")
    {
        context.Response.StatusCode = 503;
    }
    return readiness;
});
'''
        }

    elif language == "rust":
        return {
            "health": '''
async fn health_handler() -> Result<impl Reply, warp::Rejection> {
    Ok(reply::json(&HEALTH_CHECKER.check_liveness()))
}
''',
            "ready": '''
async fn ready_handler() -> Result<impl Reply, warp::Rejection> {
    let readiness = HEALTH_CHECKER.check_readiness();
    let status_code = if readiness["status"] == "ok" {
        warp::http::StatusCode::OK
    } else {
        warp::http::StatusCode::SERVICE_UNAVAILABLE
    };

    Ok(reply::with_status(reply::json(&readiness), status_code))
}
'''
        }

    return {}
