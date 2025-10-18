"""
Cross-Language Library Mapping System

This module provides intelligent library/dependency translation across all 5 supported languages.
It maps common patterns like HTTP clients, JSON handling, async primitives, collections, etc.

Design Principles:
1. Functional equivalence - Map to libraries with similar capabilities
2. Idiomatic usage - Use language-specific best practices
3. Standard libraries first - Prefer built-in over external deps
4. Fallback support - Handle unmapped libraries gracefully

Usage:
    from language.library_mapping import LibraryMapper

    mapper = LibraryMapper()

    # Translate a Python import to JavaScript
    js_import = mapper.translate_import("requests", "python", "javascript")
    # Returns: {"module": "axios", "package": "axios", "import_type": "npm"}

    # Get equivalent function call
    js_call = mapper.translate_call("requests.get", "python", "javascript")
    # Returns: "axios.get"
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class ImportType(Enum):
    """Type of import/dependency."""
    BUILTIN = "builtin"  # Standard library
    NPM = "npm"  # npm package
    PIP = "pip"  # PyPI package
    CRATE = "crate"  # Cargo crate
    NUGET = "nuget"  # NuGet package
    GO_MODULE = "go_module"  # Go module


@dataclass
class LibraryMapping:
    """
    Represents a library mapping across languages.

    Attributes:
        python: Python library name (e.g., "requests")
        javascript: JavaScript/Node.js library (e.g., "axios")
        go: Go package (e.g., "net/http")
        rust: Rust crate (e.g., "reqwest")
        csharp: C# namespace/package (e.g., "System.Net.Http")
        category: Library category (e.g., "http_client")
        description: Brief description
    """
    python: Optional[str] = None
    javascript: Optional[str] = None
    go: Optional[str] = None
    rust: Optional[str] = None
    csharp: Optional[str] = None
    category: str = "general"
    description: str = ""

    # Import types for each language
    python_type: ImportType = ImportType.PIP
    javascript_type: ImportType = ImportType.NPM
    go_type: ImportType = ImportType.GO_MODULE
    rust_type: ImportType = ImportType.CRATE
    csharp_type: ImportType = ImportType.NUGET


# ============================================================================
# Core Library Mappings
# ============================================================================

# HTTP Client Libraries
HTTP_CLIENTS = [
    LibraryMapping(
        python="requests",
        javascript="axios",
        go="net/http",
        rust="reqwest",
        csharp="System.Net.Http",
        category="http_client",
        description="HTTP client for making requests",
        python_type=ImportType.PIP,
        javascript_type=ImportType.NPM,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.BUILTIN,
    ),
    LibraryMapping(
        python="urllib.request",
        javascript="node-fetch",
        go="net/http",
        rust="reqwest",
        csharp="System.Net.Http",
        category="http_client",
        description="Standard HTTP client",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.NPM,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.BUILTIN,
    ),
    LibraryMapping(
        python="httpx",
        javascript="axios",
        go="net/http",
        rust="reqwest",
        csharp="System.Net.Http",
        category="http_client",
        description="Modern async HTTP client",
        python_type=ImportType.PIP,
        javascript_type=ImportType.NPM,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.BUILTIN,
    ),
]

# JSON Libraries
JSON_LIBRARIES = [
    LibraryMapping(
        python="json",
        javascript="JSON",
        go="encoding/json",
        rust="serde_json",
        csharp="System.Text.Json",
        category="json",
        description="JSON encoding/decoding",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.BUILTIN,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.BUILTIN,
    ),
]

# Async/Concurrency Libraries
ASYNC_LIBRARIES = [
    LibraryMapping(
        python="asyncio",
        javascript="async/await",
        go="goroutines",
        rust="tokio",
        csharp="System.Threading.Tasks",
        category="async",
        description="Asynchronous programming primitives",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.BUILTIN,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.BUILTIN,
    ),
    LibraryMapping(
        python="threading",
        javascript="worker_threads",
        go="sync",
        rust="std::thread",
        csharp="System.Threading",
        category="threading",
        description="Thread-based concurrency",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.BUILTIN,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.BUILTIN,
        csharp_type=ImportType.BUILTIN,
    ),
]

# Collection/Data Structure Libraries
COLLECTION_LIBRARIES = [
    LibraryMapping(
        python="collections",
        javascript="built-in",
        go="container",
        rust="std::collections",
        csharp="System.Collections.Generic",
        category="collections",
        description="Advanced data structures",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.BUILTIN,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.BUILTIN,
        csharp_type=ImportType.BUILTIN,
    ),
]

# File I/O Libraries
FILE_IO_LIBRARIES = [
    LibraryMapping(
        python="pathlib",
        javascript="fs/promises",
        go="os",
        rust="std::fs",
        csharp="System.IO",
        category="file_io",
        description="File system operations",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.BUILTIN,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.BUILTIN,
        csharp_type=ImportType.BUILTIN,
    ),
    LibraryMapping(
        python="os.path",
        javascript="path",
        go="path/filepath",
        rust="std::path",
        csharp="System.IO.Path",
        category="file_io",
        description="Path manipulation",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.BUILTIN,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.BUILTIN,
        csharp_type=ImportType.BUILTIN,
    ),
]

# Date/Time Libraries
DATETIME_LIBRARIES = [
    LibraryMapping(
        python="datetime",
        javascript="Date",
        go="time",
        rust="chrono",
        csharp="System.DateTime",
        category="datetime",
        description="Date and time handling",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.BUILTIN,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.BUILTIN,
    ),
]

# Regular Expression Libraries
REGEX_LIBRARIES = [
    LibraryMapping(
        python="re",
        javascript="RegExp",
        go="regexp",
        rust="regex",
        csharp="System.Text.RegularExpressions",
        category="regex",
        description="Regular expressions",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.BUILTIN,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.BUILTIN,
    ),
]

# Database Libraries
DATABASE_LIBRARIES = [
    LibraryMapping(
        python="sqlite3",
        javascript="better-sqlite3",
        go="database/sql",
        rust="rusqlite",
        csharp="System.Data.SQLite",
        category="database",
        description="SQLite database",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.NPM,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.NUGET,
    ),
    LibraryMapping(
        python="psycopg2",
        javascript="pg",
        go="github.com/lib/pq",
        rust="tokio-postgres",
        csharp="Npgsql",
        category="database",
        description="PostgreSQL client",
        python_type=ImportType.PIP,
        javascript_type=ImportType.NPM,
        go_type=ImportType.GO_MODULE,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.NUGET,
    ),
    LibraryMapping(
        python="pymongo",
        javascript="mongodb",
        go="go.mongodb.org/mongo-driver",
        rust="mongodb",
        csharp="MongoDB.Driver",
        category="database",
        description="MongoDB client",
        python_type=ImportType.PIP,
        javascript_type=ImportType.NPM,
        go_type=ImportType.GO_MODULE,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.NUGET,
    ),
]

# Logging Libraries
LOGGING_LIBRARIES = [
    LibraryMapping(
        python="logging",
        javascript="winston",
        go="log",
        rust="log",
        csharp="Microsoft.Extensions.Logging",
        category="logging",
        description="Logging framework",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.NPM,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.NUGET,
    ),
]

# Testing Libraries
TESTING_LIBRARIES = [
    LibraryMapping(
        python="unittest",
        javascript="jest",
        go="testing",
        rust="std::test",
        csharp="Microsoft.VisualStudio.TestTools.UnitTesting",
        category="testing",
        description="Unit testing framework",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.NPM,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.BUILTIN,
        csharp_type=ImportType.NUGET,
    ),
    LibraryMapping(
        python="pytest",
        javascript="jest",
        go="testing",
        rust="std::test",
        csharp="xUnit",
        category="testing",
        description="Modern testing framework",
        python_type=ImportType.PIP,
        javascript_type=ImportType.NPM,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.BUILTIN,
        csharp_type=ImportType.NUGET,
    ),
]

# Math/Science Libraries
MATH_LIBRARIES = [
    LibraryMapping(
        python="math",
        javascript="Math",
        go="math",
        rust="std::f64",
        csharp="System.Math",
        category="math",
        description="Mathematical functions",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.BUILTIN,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.BUILTIN,
        csharp_type=ImportType.BUILTIN,
    ),
    LibraryMapping(
        python="random",
        javascript="Math.random",
        go="math/rand",
        rust="rand",
        csharp="System.Random",
        category="random",
        description="Random number generation",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.BUILTIN,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.BUILTIN,
    ),
]

# Environment/Config Libraries
ENV_LIBRARIES = [
    LibraryMapping(
        python="os",
        javascript="process",
        go="os",
        rust="std::env",
        csharp="System.Environment",
        category="environment",
        description="Environment variables and system info",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.BUILTIN,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.BUILTIN,
        csharp_type=ImportType.BUILTIN,
    ),
    LibraryMapping(
        python="dotenv",
        javascript="dotenv",
        go="github.com/joho/godotenv",
        rust="dotenv",
        csharp="DotNetEnv",
        category="config",
        description=".env file loading",
        python_type=ImportType.PIP,
        javascript_type=ImportType.NPM,
        go_type=ImportType.GO_MODULE,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.NUGET,
    ),
]

# Serialization Libraries
SERIALIZATION_LIBRARIES = [
    LibraryMapping(
        python="pickle",
        javascript="serialize-javascript",
        go="encoding/gob",
        rust="bincode",
        csharp="System.Runtime.Serialization",
        category="serialization",
        description="Object serialization",
        python_type=ImportType.BUILTIN,
        javascript_type=ImportType.NPM,
        go_type=ImportType.BUILTIN,
        rust_type=ImportType.CRATE,
        csharp_type=ImportType.BUILTIN,
    ),
]

# Combine all mappings
ALL_MAPPINGS = (
    HTTP_CLIENTS +
    JSON_LIBRARIES +
    ASYNC_LIBRARIES +
    COLLECTION_LIBRARIES +
    FILE_IO_LIBRARIES +
    DATETIME_LIBRARIES +
    REGEX_LIBRARIES +
    DATABASE_LIBRARIES +
    LOGGING_LIBRARIES +
    TESTING_LIBRARIES +
    MATH_LIBRARIES +
    ENV_LIBRARIES +
    SERIALIZATION_LIBRARIES
)


# ============================================================================
# Function Call Mappings
# ============================================================================

FUNCTION_MAPPINGS = {
    # HTTP requests
    "requests.get": {
        "python": "requests.get",
        "javascript": "axios.get",
        "go": "http.Get",
        "rust": "reqwest::get",
        "csharp": "httpClient.GetAsync",
    },
    "requests.post": {
        "python": "requests.post",
        "javascript": "axios.post",
        "go": "http.Post",
        "rust": "reqwest::Client::new().post",
        "csharp": "httpClient.PostAsync",
    },

    # JSON operations
    "json.dumps": {
        "python": "json.dumps",
        "javascript": "JSON.stringify",
        "go": "json.Marshal",
        "rust": "serde_json::to_string",
        "csharp": "JsonSerializer.Serialize",
    },
    "json.loads": {
        "python": "json.loads",
        "javascript": "JSON.parse",
        "go": "json.Unmarshal",
        "rust": "serde_json::from_str",
        "csharp": "JsonSerializer.Deserialize",
    },

    # File operations
    "open": {
        "python": "open",
        "javascript": "fs.readFileSync",
        "go": "os.Open",
        "rust": "std::fs::File::open",
        "csharp": "File.Open",
    },

    # Logging
    "logging.info": {
        "python": "logging.info",
        "javascript": "console.log",
        "go": "log.Println",
        "rust": "log::info",
        "csharp": "logger.LogInformation",
    },
    "logging.error": {
        "python": "logging.error",
        "javascript": "console.error",
        "go": "log.Println",
        "rust": "log::error",
        "csharp": "logger.LogError",
    },

    # Math operations
    "math.sqrt": {
        "python": "math.sqrt",
        "javascript": "Math.sqrt",
        "go": "math.Sqrt",
        "rust": "f64::sqrt",
        "csharp": "Math.Sqrt",
    },
    "math.floor": {
        "python": "math.floor",
        "javascript": "Math.floor",
        "go": "math.Floor",
        "rust": "f64::floor",
        "csharp": "Math.Floor",
    },
    "math.sin": {
        "python": "math.sin",
        "javascript": "Math.sin",
        "go": "math.Sin",
        "rust": "f64::sin",
        "csharp": "Math.Sin",
    },
    "math.cos": {
        "python": "math.cos",
        "javascript": "Math.cos",
        "go": "math.Cos",
        "rust": "f64::cos",
        "csharp": "Math.Cos",
    },
    "math.atan2": {
        "python": "math.atan2",
        "javascript": "Math.atan2",
        "go": "math.Atan2",
        "rust": "f64::atan2",
        "csharp": "Math.Atan2",
    },

    # Random operations
    "random.random": {
        "python": "random.random",
        "javascript": "Math.random",
        "go": "rand.Float64",
        "rust": "rand::random::<f64>",
        "csharp": "Random.NextDouble",
    },
    "random.choice": {
        "python": "random.choice",
        "javascript": "(arr) => arr[Math.floor(Math.random() * arr.length)]",
        "go": "Choice",  # Will use helper function
        "rust": "(arr) => arr[rand::thread_rng().gen_range(0..arr.len())]",
        "csharp": "(arr) => arr[Random.Next(arr.Length)]",
    },

    # Time/Sleep operations
    "time.sleep": {
        "python": "time.sleep",
        "javascript": "(ms) => new Promise(resolve => setTimeout(resolve, ms * 1000))",
        "go": "time.Sleep",
        "rust": "std::thread::sleep",
        "csharp": "Thread.Sleep",
    },

    # OS operations
    "os.system": {
        "python": "os.system",
        "javascript": "require('child_process').execSync",
        "go": "exec.Command(...).Run",
        "rust": "std::process::Command::new(...).status",
        "csharp": "Process.Start",
    },

    # Built-in functions
    "len": {
        "python": "len",
        "javascript": ".length",
        "go": "len",
        "rust": ".len()",
        "csharp": ".Length",
    },
    "range": {
        "python": "range",
        "javascript": "Array.from({length: n}, (_, i) => i)",
        "go": "make([]int, n)",
        "rust": "(0..n)",
        "csharp": "Enumerable.Range(0, n)",
    },
    "enumerate": {
        "python": "enumerate",
        "javascript": "arr.map((item, index) => [index, item])",
        "go": "/* for i, item := range arr */",
        "rust": "arr.iter().enumerate()",
        "csharp": "arr.Select((item, index) => new { index, item })",
    },
    "set": {
        "python": "set",
        "javascript": "new Set",
        "go": "make(map[T]bool)",  # Go idiom for sets
        "rust": "HashSet::new",
        "csharp": "new HashSet",
    },
    "tuple": {
        "python": "tuple",
        "javascript": "Array",  # JS doesn't have tuples
        "go": "struct",  # Go uses structs for tuples
        "rust": "tuple",  # Rust has native tuples
        "csharp": "ValueTuple",  # C# has value tuples
    },
    "zip": {
        "python": "zip",
        "javascript": "arr1.map((item, i) => [item, arr2[i]])",
        "go": "/* manual zip with for loop */",
        "rust": "arr1.iter().zip(arr2.iter())",
        "csharp": "arr1.Zip(arr2)",
    },
    "map": {
        "python": "map",
        "javascript": "Array.prototype.map",
        "go": "/* manual map with for loop */",
        "rust": "Iterator::map",
        "csharp": "Enumerable.Select",
    },
    "filter": {
        "python": "filter",
        "javascript": "Array.prototype.filter",
        "go": "/* manual filter with for loop */",
        "rust": "Iterator::filter",
        "csharp": "Enumerable.Where",
    },
    "sorted": {
        "python": "sorted",
        "javascript": "Array.prototype.sort",
        "go": "sort.Slice",
        "rust": "Iterator::collect + Vec::sort",
        "csharp": "Enumerable.OrderBy",
    },
    "reversed": {
        "python": "reversed",
        "javascript": "Array.prototype.reverse",
        "go": "/* manual reverse */",
        "rust": "Iterator::rev",
        "csharp": "Enumerable.Reverse",
    },
    "sum": {
        "python": "sum",
        "javascript": "arr.reduce((a, b) => a + b, 0)",
        "go": "/* manual sum with for loop */",
        "rust": "Iterator::sum",
        "csharp": "Enumerable.Sum",
    },
    "any": {
        "python": "any",
        "javascript": "Array.prototype.some",
        "go": "/* manual check with for loop */",
        "rust": "Iterator::any",
        "csharp": "Enumerable.Any",
    },
    "all": {
        "python": "all",
        "javascript": "Array.prototype.every",
        "go": "/* manual check with for loop */",
        "rust": "Iterator::all",
        "csharp": "Enumerable.All",
    },
    "print": {
        "python": "print",
        "javascript": "console.log",
        "go": "fmt.Println",
        "rust": "println!",
        "csharp": "Console.WriteLine",
    },
}

# ============================================================================
# Import/Module Mappings
# ============================================================================

IMPORT_MAPPINGS = {
    # Python module → target language import/require
    "math": {
        "python": "import math",
        "javascript": None,  # Built-in Math object, no import needed
        "go": "math",
        "rust": "std::f64::consts",
        "csharp": "System.Math",  # Built-in, no using needed
    },
    "random": {
        "python": "import random",
        "javascript": None,  # Use Math.random(), no import
        "go": "math/rand",
        "rust": "rand",  # External crate
        "csharp": "System.Random",  # Built-in
    },
    "os": {
        "python": "import os",
        "javascript": "const os = require('os')",  # Node.js
        "go": "os",
        "rust": "std::env",
        "csharp": "System.Environment",
    },
    "sys": {
        "python": "import sys",
        "javascript": None,  # Use process object, no import
        "go": "os",  # Go uses os package for sys-like functionality
        "rust": "std::env",
        "csharp": "System.Environment",
    },
    "time": {
        "python": "import time",
        "javascript": None,  # Built-in setTimeout/setInterval
        "go": "time",
        "rust": "std::time",
        "csharp": "System.Threading",
    },
    "datetime": {
        "python": "import datetime",
        "javascript": None,  # Built-in Date object
        "go": "time",
        "rust": "chrono",  # External crate
        "csharp": "System.DateTime",
    },
    "json": {
        "python": "import json",
        "javascript": None,  # Built-in JSON object
        "go": "encoding/json",
        "rust": "serde_json",  # External crate
        "csharp": "System.Text.Json",
    },
    "re": {
        "python": "import re",
        "javascript": None,  # Built-in RegExp
        "go": "regexp",
        "rust": "regex",  # External crate
        "csharp": "System.Text.RegularExpressions",
    },
    "subprocess": {
        "python": "import subprocess",
        "javascript": "const { execSync } = require('child_process')",
        "go": "os/exec",
        "rust": "std::process",
        "csharp": "System.Diagnostics.Process",
    },
    "threading": {
        "python": "import threading",
        "javascript": None,  # Use async/await or Worker threads
        "go": "sync",
        "rust": "std::thread",
        "csharp": "System.Threading",
    },
    "asyncio": {
        "python": "import asyncio",
        "javascript": None,  # Native async/await
        "go": None,  # Use goroutines
        "rust": "tokio",  # External crate
        "csharp": "System.Threading.Tasks",
    },
    "collections": {
        "python": "import collections",
        "javascript": None,  # Use Map, Set, etc.
        "go": None,  # Use built-in maps and slices
        "rust": "std::collections",
        "csharp": "System.Collections.Generic",
    },
    "typing": {
        "python": "from typing import ...",
        "javascript": None,  # Use TypeScript types
        "go": None,  # Go has built-in types
        "rust": None,  # Rust has built-in types
        "csharp": None,  # C# has built-in types
    },
    "__future__": {
        "python": "from __future__ import ...",
        "javascript": None,  # Python-specific language evolution feature
        "go": None,  # No equivalent
        "rust": None,  # No equivalent
        "csharp": None,  # No equivalent
    },
    "dataclasses": {
        "python": "from dataclasses import ...",
        "javascript": None,  # Use plain objects/classes
        "go": None,  # Use structs directly
        "rust": None,  # Use structs with derive macros
        "csharp": None,  # Use classes/records
    },
}

# ============================================================================
# String Method Mappings
# ============================================================================

STRING_METHOD_MAPPINGS = {
    # Python string method → target language equivalent
    "upper": {
        "python": "upper",
        "javascript": "toUpperCase",
        "go": "strings.ToUpper",  # Need to pass string as arg
        "rust": "to_uppercase",
        "csharp": "ToUpper",
    },
    "lower": {
        "python": "lower",
        "javascript": "toLowerCase",
        "go": "strings.ToLower",
        "rust": "to_lowercase",
        "csharp": "ToLower",
    },
    "strip": {
        "python": "strip",
        "javascript": "trim",
        "go": "strings.TrimSpace",
        "rust": "trim",
        "csharp": "Trim",
    },
    "split": {
        "python": "split",
        "javascript": "split",
        "go": "strings.Split",  # Reversed args: strings.Split(str, sep)
        "rust": "split",
        "csharp": "Split",
    },
    "replace": {
        "python": "replace",
        "javascript": "replace",
        "go": "strings.Replace",  # strings.Replace(s, old, new, -1)
        "rust": "replace",
        "csharp": "Replace",
    },
    "startswith": {
        "python": "startswith",
        "javascript": "startsWith",
        "go": "strings.HasPrefix",
        "rust": "starts_with",
        "csharp": "StartsWith",
    },
    "endswith": {
        "python": "endswith",
        "javascript": "endsWith",
        "go": "strings.HasSuffix",
        "rust": "ends_with",
        "csharp": "EndsWith",
    },
}

# ============================================================================
# Exception Type Mappings
# ============================================================================

EXCEPTION_MAPPINGS = {
    # Python exception → target language exception
    "Exception": {
        "python": "Exception",
        "javascript": "Error",
        "go": "error",
        "rust": "Box<dyn std::error::Error>",
        "csharp": "Exception",
    },
    "ValueError": {
        "python": "ValueError",
        "javascript": "TypeError",
        "go": "error",
        "rust": "ValueError",  # Custom or use anyhow
        "csharp": "ArgumentException",
    },
    "TypeError": {
        "python": "TypeError",
        "javascript": "TypeError",
        "go": "error",
        "rust": "TypeError",
        "csharp": "InvalidCastException",
    },
    "KeyError": {
        "python": "KeyError",
        "javascript": "Error",
        "go": "error",
        "rust": "KeyError",
        "csharp": "KeyNotFoundException",
    },
    "IndexError": {
        "python": "IndexError",
        "javascript": "RangeError",
        "go": "error",
        "rust": "IndexError",
        "csharp": "IndexOutOfRangeException",
    },
    "AttributeError": {
        "python": "AttributeError",
        "javascript": "Error",
        "go": "error",
        "rust": "AttributeError",
        "csharp": "MissingMemberException",
    },
    "FileNotFoundError": {
        "python": "FileNotFoundError",
        "javascript": "Error",  # or custom FileNotFoundError class
        "go": "error",
        "rust": "std::io::ErrorKind::NotFound",
        "csharp": "FileNotFoundException",
    },
    "IOError": {
        "python": "IOError",
        "javascript": "Error",
        "go": "error",
        "rust": "std::io::Error",
        "csharp": "IOException",
    },
    "ZeroDivisionError": {
        "python": "ZeroDivisionError",
        "javascript": "Error",  # JS allows Infinity
        "go": "error",
        "rust": "DivideByZeroError",
        "csharp": "DivideByZeroException",
    },
    "RuntimeError": {
        "python": "RuntimeError",
        "javascript": "Error",
        "go": "error",
        "rust": "RuntimeError",
        "csharp": "Exception",
    },
    "KeyboardInterrupt": {
        "python": "KeyboardInterrupt",
        "javascript": "Error",  # or handle as process signal
        "go": "error",  # or handle as os.Signal
        "rust": "std::io::Error",  # or handle as signal
        "csharp": "OperationCanceledException",
    },
    "ImportError": {
        "python": "ImportError",
        "javascript": "Error",  # Module not found
        "go": "error",
        "rust": "ImportError",
        "csharp": "FileNotFoundException",
    },
    "NotImplementedError": {
        "python": "NotImplementedError",
        "javascript": "Error",
        "go": "error",
        "rust": "std::io::Error",  # or custom
        "csharp": "NotImplementedException",
    },
}


# ============================================================================
# LibraryMapper Class
# ============================================================================

class LibraryMapper:
    """
    Intelligent library mapping and translation system.

    This class provides methods to:
    1. Translate library imports across languages
    2. Map function calls to equivalent APIs
    3. Detect library usage patterns
    4. Generate appropriate import statements
    """

    def __init__(self):
        """Initialize the library mapper with all mappings."""
        self.mappings = ALL_MAPPINGS
        self.function_mappings = FUNCTION_MAPPINGS

        # Create lookup indices for fast access
        self._build_indices()

    def _build_indices(self) -> None:
        """Build lookup indices for fast library lookup."""
        self.python_index: Dict[str, LibraryMapping] = {}
        self.javascript_index: Dict[str, LibraryMapping] = {}
        self.go_index: Dict[str, LibraryMapping] = {}
        self.rust_index: Dict[str, LibraryMapping] = {}
        self.csharp_index: Dict[str, LibraryMapping] = {}

        for mapping in self.mappings:
            if mapping.python:
                self.python_index[mapping.python] = mapping
            if mapping.javascript:
                self.javascript_index[mapping.javascript] = mapping
            if mapping.go:
                self.go_index[mapping.go] = mapping
            if mapping.rust:
                self.rust_index[mapping.rust] = mapping
            if mapping.csharp:
                self.csharp_index[mapping.csharp] = mapping

    def translate_import(
        self,
        library: str,
        from_lang: str,
        to_lang: str
    ) -> Optional[Dict[str, str]]:
        """
        Translate a library import from one language to another.

        Args:
            library: Library name in source language
            from_lang: Source language (python, javascript, go, rust, csharp)
            to_lang: Target language

        Returns:
            Dict with:
                - module: Module/library name in target language
                - import_type: Type of import (builtin, npm, pip, etc.)
                - category: Library category
            Returns None if no mapping found

        Example:
            >>> mapper = LibraryMapper()
            >>> mapper.translate_import("requests", "python", "javascript")
            {'module': 'axios', 'import_type': 'npm', 'category': 'http_client'}
        """
        # Get mapping from source language
        from_index = getattr(self, f"{from_lang}_index", {})
        mapping = from_index.get(library)

        if not mapping:
            return None

        # Get target library name
        to_library = getattr(mapping, to_lang, None)
        to_import_type = getattr(mapping, f"{to_lang}_type", ImportType.BUILTIN)

        if not to_library:
            return None

        return {
            "module": to_library,
            "import_type": to_import_type.value,
            "category": mapping.category,
            "description": mapping.description,
        }

    def translate_call(
        self,
        call: str,
        from_lang: str,
        to_lang: str
    ) -> Optional[str]:
        """
        Translate a function call from one language to another.

        Args:
            call: Function call (e.g., "requests.get")
            from_lang: Source language
            to_lang: Target language

        Returns:
            Translated function call, or None if no mapping

        Example:
            >>> mapper.translate_call("requests.get", "python", "javascript")
            'axios.get'
        """
        if call not in self.function_mappings:
            return None

        return self.function_mappings[call].get(to_lang)

    def get_required_imports(
        self,
        library: str,
        lang: str
    ) -> List[str]:
        """
        Get all required imports for a library in a specific language.

        Some libraries require multiple imports or setup.

        Args:
            library: Library name
            lang: Target language

        Returns:
            List of import statements
        """
        # Get the mapping
        index = getattr(self, f"{lang}_index", {})
        mapping = index.get(library)

        if not mapping:
            return []

        # Generate import statement based on language
        if lang == "python":
            return [f"import {library}"]
        elif lang == "javascript":
            if mapping.javascript_type == ImportType.BUILTIN:
                return []  # Built-in, no import needed
            return [f"const {library.split('/')[-1]} = require('{library}');"]
        elif lang == "go":
            return [f'import "{library}"']
        elif lang == "rust":
            if mapping.rust_type == ImportType.BUILTIN:
                return []  # Built-in
            return [f"use {library};"]
        elif lang == "csharp":
            return [f"using {library};"]

        return []

    def get_category_libraries(self, category: str) -> List[LibraryMapping]:
        """
        Get all library mappings in a specific category.

        Args:
            category: Category name (e.g., "http_client", "json")

        Returns:
            List of LibraryMapping objects
        """
        return [m for m in self.mappings if m.category == category]

    def find_mapping_by_category(
        self,
        category: str,
        lang: str
    ) -> Optional[LibraryMapping]:
        """
        Find the primary library mapping for a category in a language.

        Args:
            category: Category name
            lang: Language

        Returns:
            First matching LibraryMapping or None
        """
        category_libs = self.get_category_libraries(category)
        if not category_libs:
            return None

        # Return first mapping (usually the most common one)
        return category_libs[0]

    def get_all_categories(self) -> Set[str]:
        """Get set of all library categories."""
        return {m.category for m in self.mappings}

    def supports_library(self, library: str, lang: str) -> bool:
        """Check if a library is supported in the mapping system."""
        index = getattr(self, f"{lang}_index", {})
        return library in index
