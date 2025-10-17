"""
Security middleware patterns for MCP servers.

Implements CORS, rate limiting, request validation, and security headers.
"""

from typing import Dict


def get_python_security_middleware() -> str:
    """Generate Python security middleware (FastAPI)."""
    return '''
# Security middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# Trusted host middleware
if os.environ.get("ALLOWED_HOSTS"):
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=os.environ.get("ALLOWED_HOSTS").split(",")
    )

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
'''


def get_nodejs_security_middleware() -> str:
    """Generate Node.js security middleware (Express)."""
    return '''
// Security middleware
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');

// Security headers
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
  },
}));

// CORS
const allowedOrigins = (process.env.ALLOWED_ORIGINS || '*').split(',');
app.use(cors({
  origin: allowedOrigins,
  credentials: true,
  methods: ['GET', 'POST', 'OPTIONS'],
  maxAge: 3600,
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100, // 100 requests per minute
  message: { error: { code: -32006, message: 'Too many requests' } },
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/mcp', limiter);
'''


def get_go_security_middleware() -> str:
    """Generate Go security middleware."""
    return '''
// Security middleware
import (
\t"strings"
\t"sync"
\t"time"
)

// Rate limiter
type RateLimiter struct {
\tmu       sync.Mutex
\trequests map[string][]time.Time
\tlimit    int
\twindow   time.Duration
}

func NewRateLimiter(limit int, window time.Duration) *RateLimiter {
\treturn &RateLimiter{
\t\trequests: make(map[string][]time.Time),
\t\tlimit:    limit,
\t\twindow:   window,
\t}
}

func (rl *RateLimiter) Allow(clientIP string) bool {
\trl.mu.Lock()
\tdefer rl.mu.Unlock()

\tnow := time.Now()
\tcutoff := now.Add(-rl.window)

\t// Clean old requests
\tvar recent []time.Time
\tfor _, reqTime := range rl.requests[clientIP] {
\t\tif reqTime.After(cutoff) {
\t\t\trecent = append(recent, reqTime)
\t\t}
\t}
\trl.requests[clientIP] = recent

\tif len(recent) >= rl.limit {
\t\treturn false
\t}

\trl.requests[clientIP] = append(rl.requests[clientIP], now)
\treturn true
}

var rateLimiter = NewRateLimiter(100, time.Minute)

// CORS middleware
func corsMiddleware(next http.HandlerFunc) http.HandlerFunc {
\tallowedOrigins := strings.Split(os.Getenv("ALLOWED_ORIGINS"), ",")
\tif len(allowedOrigins) == 0 || allowedOrigins[0] == "" {
\t\tallowedOrigins = []string{"*"}
\t}

\treturn func(w http.ResponseWriter, r *http.Request) {
\t\tw.Header().Set("Access-Control-Allow-Origin", allowedOrigins[0])
\t\tw.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
\t\tw.Header().Set("Access-Control-Allow-Headers", "*")
\t\tw.Header().Set("Access-Control-Max-Age", "3600")

\t\tif r.Method == "OPTIONS" {
\t\t\tw.WriteHeader(http.StatusOK)
\t\t\treturn
\t\t}

\t\tnext(w, r)
\t}
}

// Security headers middleware
func securityHeadersMiddleware(next http.HandlerFunc) http.HandlerFunc {
\treturn func(w http.ResponseWriter, r *http.Request) {
\t\tw.Header().Set("X-Content-Type-Options", "nosniff")
\t\tw.Header().Set("X-Frame-Options", "DENY")
\t\tw.Header().Set("X-XSS-Protection", "1; mode=block")
\t\tw.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

\t\tnext(w, r)
\t}
}

// Rate limit middleware
func rateLimitMiddleware(next http.HandlerFunc) http.HandlerFunc {
\treturn func(w http.ResponseWriter, r *http.Request) {
\t\tclientIP := r.RemoteAddr
\t\tif !rateLimiter.Allow(clientIP) {
\t\t\tw.WriteHeader(http.StatusTooManyRequests)
\t\t\tjson.NewEncoder(w).Encode(map[string]interface{}{
\t\t\t\t"jsonrpc": "2.0",
\t\t\t\t"error": map[string]interface{}{
\t\t\t\t\t"code":    -32006,
\t\t\t\t\t"message": "Too many requests",
\t\t\t\t},
\t\t\t})
\t\t\treturn
\t\t}

\t\tnext(w, r)
\t}
}
'''


def get_csharp_security_middleware() -> str:
    """Generate C# security middleware."""
    return '''
// Security middleware
using Microsoft.AspNetCore.RateLimiting;
using System.Threading.RateLimiting;

var builder = WebApplication.CreateBuilder(args);

// Rate limiting
builder.Services.AddRateLimiter(options =>
{
    options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(context =>
        RateLimitPartition.GetFixedWindowLimiter(
            partitionKey: context.Connection.RemoteIpAddress?.ToString() ?? "unknown",
            factory: _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit = 100,
                Window = TimeSpan.FromMinutes(1),
                QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
                QueueLimit = 0
            }));

    options.OnRejected = async (context, cancellationToken) =>
    {
        context.HttpContext.Response.StatusCode = 429;
        await context.HttpContext.Response.WriteAsJsonAsync(new
        {
            jsonrpc = "2.0",
            error = new
            {
                code = -32006,
                message = "Too many requests"
            }
        }, cancellationToken);
    };
});

// CORS
var allowedOrigins = Environment.GetEnvironmentVariable("ALLOWED_ORIGINS")?.Split(',')
    ?? new[] { "*" };

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins(allowedOrigins)
              .AllowAnyMethod()
              .AllowAnyHeader()
              .AllowCredentials()
              .SetPreflightMaxAge(TimeSpan.FromHours(1));
    });
});

var app = builder.Build();

// Use CORS
app.UseCors();

// Use rate limiting
app.UseRateLimiter();

// Security headers middleware
app.Use(async (context, next) =>
{
    context.Response.Headers.Add("X-Content-Type-Options", "nosniff");
    context.Response.Headers.Add("X-Frame-Options", "DENY");
    context.Response.Headers.Add("X-XSS-Protection", "1; mode=block");
    context.Response.Headers.Add("Strict-Transport-Security", "max-age=31536000; includeSubDomains");
    await next();
});
'''


def get_rust_security_middleware() -> str:
    """Generate Rust security middleware."""
    return '''
// Security middleware
use warp::http::header::{HeaderMap, HeaderValue};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

// Rate limiter
struct RateLimiter {
    requests: Arc<Mutex<HashMap<String, Vec<Instant>>>>,
    limit: usize,
    window: Duration,
}

impl RateLimiter {
    fn new(limit: usize, window: Duration) -> Self {
        RateLimiter {
            requests: Arc::new(Mutex::new(HashMap::new())),
            limit,
            window,
        }
    }

    fn allow(&self, client_ip: &str) -> bool {
        let mut requests = self.requests.lock().unwrap();
        let now = Instant::now();
        let cutoff = now - self.window;

        let recent: Vec<Instant> = requests
            .get(client_ip)
            .map(|times| {
                times.iter()
                    .filter(|&&t| t > cutoff)
                    .copied()
                    .collect()
            })
            .unwrap_or_default();

        if recent.len() >= self.limit {
            return false;
        }

        let mut updated = recent;
        updated.push(now);
        requests.insert(client_ip.to_string(), updated);

        true
    }
}

lazy_static::lazy_static! {
    static ref RATE_LIMITER: RateLimiter = RateLimiter::new(100, Duration::from_secs(60));
}

// CORS filter
fn with_cors() -> warp::cors::Cors {
    // Check if specific origins are set, otherwise allow any
    match env::var("ALLOWED_ORIGINS") {
        Ok(origins) if !origins.is_empty() && origins != "*" => {
            // Parse comma-separated origins
            let origin_list: Vec<&str> = origins.split(',').map(|s| s.trim()).collect();
            let mut cors = warp::cors();
            for origin in origin_list {
                cors = cors.allow_origin(origin);
            }
            cors.allow_methods(vec!["GET", "POST", "OPTIONS"])
                .allow_headers(vec!["Content-Type", "Authorization"])
                .max_age(3600)
                .build()
        }
        _ => {
            // Allow any origin (for development)
            warp::cors()
                .allow_any_origin()
                .allow_methods(vec!["GET", "POST", "OPTIONS"])
                .allow_headers(vec!["Content-Type", "Authorization"])
                .max_age(3600)
                .build()
        }
    }
}

// Security headers filter
fn with_security_headers() -> impl Filter<Extract = (HeaderMap,), Error = std::convert::Infallible> + Clone {
    warp::any().map(|| {
        let mut headers = HeaderMap::new();
        headers.insert("X-Content-Type-Options", HeaderValue::from_static("nosniff"));
        headers.insert("X-Frame-Options", HeaderValue::from_static("DENY"));
        headers.insert("X-XSS-Protection", HeaderValue::from_static("1; mode=block"));
        headers.insert("Strict-Transport-Security",
            HeaderValue::from_static("max-age=31536000; includeSubDomains"));
        headers
    })
}
'''


def get_security_requirements(language: str) -> Dict[str, str]:
    """Get package requirements for security features."""
    requirements = {
        "python": {
            "packages": ["slowapi", "python-multipart"],
            "already_has": ["fastapi[all]"]  # Includes CORS
        },
        "nodejs": {
            "packages": ["helmet", "cors", "express-rate-limit"],
            "already_has": ["express"]
        },
        "go": {
            "packages": [],  # Built-in
            "already_has": ["net/http"]
        },
        "csharp": {
            "packages": [],  # Built-in ASP.NET Core
            "already_has": ["Microsoft.AspNetCore.RateLimiting"]
        },
        "rust": {
            "packages": ["lazy_static = \"1.4\""],
            "already_has": ["warp"]
        }
    }

    return requirements.get(language, {})
