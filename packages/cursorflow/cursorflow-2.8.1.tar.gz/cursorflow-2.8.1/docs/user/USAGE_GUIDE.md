# Universal CursorFlow - Usage Guide

## 🌌 **Built for the Universe**

This testing framework adapts to **any web architecture** - use the same commands and concepts whether you're testing legacy Perl systems, modern React apps, or anything in between.

## 🎯 **v2.7.0: AI-Optimized Output**

**Test results now organized for AI consumption** - no more 3.7M token JSON files:

```bash
# Test generates structured output automatically
cursorflow test --base-url http://localhost:3000 --path /app

# Results organized in: .cursorflow/artifacts/sessions/session_XXX/
# ├── summary.json       # Quick metrics (2-5KB)
# ├── errors.json        # Console errors (10-50KB)  
# ├── network.json       # Network data (50-200KB)
# ├── console.json       # Console messages (20-100KB)
# ├── server_logs.json   # Server logs (SSH/local/Docker)
# ├── dom_analysis.json  # DOM structure (500KB-2MB)
# ├── performance.json   # Performance metrics (10-30KB)
# ├── timeline.json      # Event timeline (20-50KB)
# ├── screenshots.json   # Screenshot metadata
# ├── data_digest.md     # AI summary (10-20KB)
# └── screenshots/       # Visual artifacts

# Query data instantly
cursorflow query session_XXX --errors
cursorflow query session_XXX --network --failed
cursorflow query --list  # Show recent sessions

# Compare test runs
cursorflow query session_A --compare-with session_B
```

**Why this matters:** Each file fits in AI context windows. Read `data_digest.md` for instant overview, query specific data as needed. 90% faster diagnosis.

## 🔍 **Query Interface (v2.7.0+)**

Fast data extraction from test results - supports ALL CursorFlow data types:

### Core Data Queries

```bash
# List recent sessions
cursorflow query --list

# Query browser console errors
cursorflow query session_123 --errors
cursorflow query session_123 --errors --severity critical

# Query server logs (SSH/local/Docker/systemd)
cursorflow query session_123 --server-logs
cursorflow query session_123 --server-logs --level error,warning
cursorflow query session_123 --server-logs --source ssh
cursorflow query session_123 --server-logs --pattern "database"
cursorflow query session_123 --server-logs --contains "timeout"

# Query network requests
cursorflow query session_123 --network
cursorflow query session_123 --network --failed
cursorflow query session_123 --network --status 4xx,5xx
cursorflow query session_123 --network --status 404,500

# Query console messages
cursorflow query session_123 --console
cursorflow query session_123 --console --type error,warning

# Query performance metrics
cursorflow query session_123 --performance

# Query summary
cursorflow query session_123 --summary
```

### Advanced Data Queries

```bash
# Query DOM analysis
cursorflow query session_123 --dom
cursorflow query session_123 --dom --selector "button"
cursorflow query session_123 --dom --visible  # Visible elements only
cursorflow query session_123 --dom --interactive  # Interactive elements only
cursorflow query session_123 --dom --role button  # By ARIA role
cursorflow query session_123 --dom --with-attr data-testid  # With specific attribute

# Query screenshots
cursorflow query session_123 --screenshots
cursorflow query session_123 --screenshots --with-errors
cursorflow query session_123 --screenshot 2  # Specific screenshot by index

# Query timeline events
cursorflow query session_123 --timeline
cursorflow query session_123 --timeline --around 1234567890 --window 10

# Query responsive testing results (if --responsive was used)
cursorflow query session_123 --responsive
cursorflow query session_123 --responsive --viewport mobile

# Query mockup comparison results (if compare-mockup was used)
cursorflow query session_123 --mockup
cursorflow query session_123 --mockup --similarity-under 90

# Query CSS iterations (if css_iteration_session was used)
cursorflow query session_123 --css-iterations
cursorflow query session_123 --css-iterations --iteration 3
```

### Enhanced Filtering (Phase 1)

```bash
# Filter errors by source file/pattern
cursorflow query session_123 --errors --from-file "app.js"
cursorflow query session_123 --errors --from-pattern "*.component.ts"

# Filter errors by message content
cursorflow query session_123 --errors --contains "undefined"
cursorflow query session_123 --errors --matches "TypeError.*undefined"

# Filter network by URL patterns
cursorflow query session_123 --network --url-contains "/api/"
cursorflow query session_123 --network --url-matches ".*\\.js$"

# Filter network by timing (user-defined thresholds)
cursorflow query session_123 --network --over 500ms  # Slow requests
cursorflow query session_123 --network --method POST,PUT  # By method

# Filter by timestamp ranges
cursorflow query session_123 --errors --after 1234567890
cursorflow query session_123 --errors --between 1234567890,1234567900
```

### Cross-Referencing (Phase 2)

```bash
# Errors with related data (time-based correlation)
cursorflow query session_123 --errors --with-network  # ±5s network requests
cursorflow query session_123 --errors --with-console  # ±5s console messages
cursorflow query session_123 --errors --with-server-logs  # ±5s server logs

# Network with related data
cursorflow query session_123 --network --failed --with-errors  # Errors near failures
```

### Contextual Queries (Phase 3)

```bash
# Get full context for specific error
cursorflow query session_123 --context-for-error 2 --window 10
# Returns: Error + all network/console/server logs within ±10s

# Group all data by URL pattern
cursorflow query session_123 --group-by-url "/api/users"
# Returns: All requests, errors, logs related to that URL

# Group all data by DOM selector
cursorflow query session_123 --group-by-selector "#button"
# Returns: All clicks, errors, DOM state for that element
```

### Enhanced Comparison (Phase 4)

```bash
# Message-level error comparison
cursorflow query session_A --compare-with session_B --errors
# Shows: New errors, fixed errors, frequency changes

# URL-level network comparison
cursorflow query session_A --compare-with session_B --network
# Shows: New URLs, removed URLs, status changes, timing changes
```

### Export Formats

```bash
# JSON (default)
cursorflow query session_123 --errors

# Markdown
cursorflow query session_123 --errors --export markdown

# CSV (for spreadsheet analysis)
cursorflow query session_123 --network --export csv
```

### Session Comparison

```bash
# Compare two test runs
cursorflow query session_A --compare-with session_B
cursorflow query session_A --compare-with session_B --errors
cursorflow query session_A --compare-with session_B --network
```

**Use this instead of:** Manual JSON parsing, grep commands, reading massive files

---

## 📖 **Query Cookbook - Real-World Scenarios**

### Scenario 1: Finding the Root Cause of an Error

```bash
# You have an error, need to understand what caused it

# Step 1: Get the error details
cursorflow query session_XXX --errors
# Returns: Error message, source file, line number

# Step 2: Get full context (what happened around it)
cursorflow query session_XXX --context-for-error 0 --window 10
# Returns: Network requests, console logs, server logs ±10s

# Step 3: Check if network failure caused it
cursorflow query session_XXX --errors --with-network
# Returns: Errors with related network requests

# Step 4: Export for documentation
cursorflow query session_XXX --context-for-error 0 --export markdown > error_report.md
```

### Scenario 2: Debugging Slow Performance

```bash
# User reports "page is slow"

# Step 1: Find slow network requests
cursorflow query session_XXX --network --over 1000ms

# Step 2: Group by API endpoint
cursorflow query session_XXX --group-by-url "/api/data"
# Returns: All requests to that endpoint + related errors

# Step 3: Check server side
cursorflow query session_XXX --server-logs --pattern "slow query"

# Step 4: Compare with fast version
cursorflow query session_slow --compare-with session_fast --network
# Returns: timing_changes showing which requests got slower
```

### Scenario 3: Regression Detection

```bash
# Feature worked yesterday, broken today

# Step 1: Compare sessions
cursorflow query session_today --compare-with session_yesterday --errors
# Returns: new_errors, fixed_errors, frequency_changes

# Step 2: Check network changes
cursorflow query session_today --compare-with session_yesterday --network
# Returns: new_urls, removed_urls, status_changes

# Step 3: Find specific regression
cursorflow query session_today --errors --from-file "feature.js"
```

### Scenario 4: API Debugging

```bash
# API endpoint returning errors

# Step 1: Find all requests to endpoint
cursorflow query session_XXX --network --url-contains "/api/users"

# Step 2: Find failed ones
cursorflow query session_XXX --network --url-contains "/api/users" --status 4xx,5xx

# Step 3: Get errors that happened at same time
cursorflow query session_XXX --network --failed --with-errors

# Step 4: Check server logs
cursorflow query session_XXX --server-logs --pattern "api/users"
```

### Scenario 5: Complete Frontend + Backend Correlation

```bash
# Complex issue needs full picture

# Step 1: Get error with all related data
cursorflow query session_XXX --context-for-error 0 --window 10
# Returns: error, network, console, server logs, timeline

# Step 2: Export as markdown report
cursorflow query session_XXX --context-for-error 0 --export markdown > investigation.md

# Step 3: Share with team or use for documentation
# investigation.md has complete formatted context
```

---

## 📊 **Server Log Configuration**

CursorFlow can monitor server logs from multiple sources during testing:

### SSH Remote Logs

**Configuration:**
```json
{
  "environments": {
    "staging": {
      "base_url": "https://staging.example.com",
      "logs": "ssh",
      "ssh_config": {
        "hostname": "staging-server",
        "username": "deploy",
        "key_file": "~/.ssh/staging_key"
      },
      "log_paths": {
        "app_error": "/var/log/app/error.log",
        "apache_error": "/var/log/httpd/error_log"
      }
    }
  }
}
```

**CLI Usage:**
```bash
cursorflow test --base-url https://staging.example.com \
  --logs ssh \
  --config cursor-test-config.json
```

### Local Logs

**Configuration:**
```json
{
  "environments": {
    "local": {
      "base_url": "http://localhost:3000",
      "logs": "local",
      "log_paths": {
        "app": "logs/app.log",
        "error": "logs/error.log"
      }
    }
  }
}
```

**CLI Usage:**
```bash
cursorflow test --base-url http://localhost:3000 --logs local
```

### Docker Container Logs

**Configuration:**
```json
{
  "logs": "docker",
  "container_name": "app-container",
  "log_paths": ["/var/log/app.log"]
}
```

### Systemd Service Logs

**Configuration:**
```json
{
  "logs": "systemd",
  "service_name": "myapp.service"
}
```

### Querying Server Logs

```bash
# All server logs
cursorflow query session_123 --server-logs

# Filter by severity
cursorflow query session_123 --server-logs --level error
cursorflow query session_123 --server-logs --level error,warning

# Filter by source
cursorflow query session_123 --server-logs --source ssh
cursorflow query session_123 --server-logs --source local

# Filter by file path
cursorflow query session_123 --server-logs --file "/var/log/app/error.log"

# Filter by content
cursorflow query session_123 --server-logs --pattern "database"
cursorflow query session_123 --server-logs --contains "timeout"
cursorflow query session_123 --server-logs --matches "error.*connection"

# Filter by timestamp
cursorflow query session_123 --server-logs --after 1234567890
cursorflow query session_123 --server-logs --between 1234567890,1234567900

# Combined filters
cursorflow query session_123 --server-logs \
  --level error \
  --pattern "database" \
  --after 1234567890
```

---

## 📋 **Action Format Reference**

### **Valid Action Formats**

CursorFlow supports multiple action formats for flexibility:

**Simple format (action type as key):**
```json
{"navigate": "/dashboard"}
{"click": ".button"}
{"wait": 2}
{"screenshot": "page-loaded"}
```

**Configuration format (action with options):**
```json
{"click": {"selector": ".button"}}
{"fill": {"selector": "#username", "value": "test@example.com"}}
{"wait_for": {"selector": ".loaded", "timeout": 5000}}
```

**Explicit type format (for programmatic generation):**
```json
{"type": "click", "selector": ".button"}
{"type": "fill", "selector": "#email", "value": "user@test.com"}
```

### **Supported Action Types**

**CursorFlow-specific:**
- `navigate` - Navigate to URL or path
- `screenshot` - Capture screenshot with comprehensive data
- `authenticate` - Use authentication handler

**Any Playwright Page method works:**
- `click`, `dblclick`, `hover`, `tap`
- `fill`, `type`, `press`
- `check`, `uncheck`, `select_option`
- `focus`, `blur`
- `drag_and_drop`
- `wait_for_selector`, `wait_for_load_state`, `wait_for_timeout`
- `goto`, `reload`, `go_back`, `go_forward`
- `evaluate`, `route`, `expose_function`
- And 80+ more Playwright methods

**Full API:** https://playwright.dev/python/docs/api/class-page

**Pass-Through Architecture:** CursorFlow provides smart defaults but doesn't limit you. Any Playwright Page method works, and you can configure ANY browser/context option. This makes CursorFlow forward-compatible with future Playwright releases.

**Configuration Pass-Through:**
```json
{
  "browser_config": {
    "browser_launch_options": {
      "devtools": true,
      "channel": "chrome",
      "proxy": {"server": "http://proxy:3128"}
    }
  },
  "context_options": {
    "color_scheme": "dark",
    "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
    "timezone_id": "America/New_York"
  }
}
```

See Playwright docs for all options:
- Browser: https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch
- Context: https://playwright.dev/python/docs/api/class-browser#browser-new-context

### **Complete Workflow Example**

```json
[
  {"navigate": "/login"},
  {"wait_for": "#login-form"},
  {"fill": {"selector": "#username", "value": "admin"}},
  {"fill": {"selector": "#password", "value": "pass123"}},
  {"click": "#submit-button"},
  {"wait_for": ".dashboard"},
  {"screenshot": "logged-in"},
  {"validate": {"selector": ".error", "exists": false}}
]
```

## 🚀 **CLI Commands**

### **Testing Commands**

**Basic test:**
```bash
cursorflow test --base-url http://localhost:3000 --path /page
```

**Inline actions:**
```bash
cursorflow test --base-url http://localhost:3000 \
  --path /login \
  --wait-for "#login-form" \
  --fill "#username=admin" \
  --fill "#password=secret" \
  --click "#submit" \
  --screenshot "logged-in" \
  --show-console \
  --open-trace
```

**Wait strategies:**
```bash
--wait-for ".selector"              # Wait for element
--wait-timeout 60                   # Timeout in seconds
--wait-for-network-idle             # Wait for no network activity
```

**Output options:**
```bash
--show-console                      # Show errors and warnings
--show-all-console                  # Show all console messages
--open-trace                        # Auto-open Playwright trace
--quiet                             # JSON output only
```

### **Authentication & Session Management**

CursorFlow provides universal authentication support for testing protected pages and features. Session persistence allows you to login once and reuse authentication state across multiple tests.

#### **Why Authentication Matters**

Most real applications have:
- User dashboards and protected pages
- Role-based access control
- Personalized content
- Shopping carts and user data
- Admin panels and settings

Without authentication support, you can only test public pages. CursorFlow's authentication enables comprehensive testing of the entire application.

---

#### **Authentication Methods**

CursorFlow supports three universal authentication strategies that work with any web framework.

##### **Method 1: Form Authentication (Most Common)**

For traditional username/password login forms.

**Configuration (`.cursorflow/config.json`):**
```json
{
  "base_url": "http://localhost:3000",
  "auth": {
    "method": "form",
    "username": "test@example.com",
    "password": "testpass123",
    "username_selector": "#email",
    "password_selector": "#password",
    "submit_selector": "button[type='submit']",
    "session_storage": ".cursorflow/sessions/",
    "success_indicators": ["dashboard", "profile", "logout"],
    "auth_check_selectors": [".user-menu", "#user-profile"]
  }
}
```

**Field Reference:**
- `method`: `"form"` - Indicates form-based authentication
- `username`: Your test user's username/email
- `password`: Your test user's password
- `username_selector`: CSS selector for username input field
- `password_selector`: CSS selector for password input field
- `submit_selector`: CSS selector for login button
- `session_storage`: Directory to store session files (default: `.cursorflow/sessions/`)
- `success_indicators`: Keywords that indicate successful auth (optional)
- `auth_check_selectors`: Elements that only appear when authenticated (optional)

**CLI Usage:**
```bash
# Login once and save session
cursorflow test --base-url http://localhost:3000 \
  --path /login \
  --save-session "authenticated"

# Reuse saved session (no re-login needed)
cursorflow test --base-url http://localhost:3000 \
  --path /dashboard \
  --use-session "authenticated"
```

##### **Method 2: Cookie Authentication**

For applications that use cookie-based auth (JWT in cookies, session cookies, etc.).

**Configuration:**
```json
{
  "base_url": "https://staging.example.com",
  "auth": {
    "method": "cookies",
    "cookies": [
      {
        "name": "session_token",
        "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "domain": "staging.example.com",
        "path": "/",
        "httpOnly": true,
        "secure": true
      },
      {
        "name": "user_id",
        "value": "12345",
        "domain": "staging.example.com",
        "path": "/"
      }
    ],
    "session_storage": ".cursorflow/sessions/"
  }
}
```

**Cookie Format:**
- `name`: Cookie name
- `value`: Cookie value
- `domain`: Cookie domain (must match your base_url)
- `path`: Cookie path (default: "/")
- `httpOnly`: True for HTTP-only cookies
- `secure`: True for HTTPS-only cookies
- `sameSite`: "Strict", "Lax", or "None" (optional)

**Use Case:** 
- Testing with long-lived JWT tokens
- Using cookies from browser DevTools
- Bypassing complex OAuth flows

##### **Method 3: Header Authentication**

For API token or Bearer token authentication.

**Configuration:**
```json
{
  "base_url": "https://api.example.com",
  "auth": {
    "method": "headers",
    "headers": {
      "Authorization": "Bearer sk_test_51HqZ2RKr4...",
      "X-API-Key": "your-api-key-here",
      "X-User-ID": "12345"
    },
    "session_storage": ".cursorflow/sessions/"
  }
}
```

**Use Case:**
- API testing with Bearer tokens
- Custom authentication headers
- Service-to-service authentication

---

#### **Session Management**

Session persistence allows you to authenticate once and reuse the session across multiple tests, saving time and reducing server load.

##### **Saving Sessions**

```bash
# Save session with custom name
cursorflow test --base-url http://localhost:3000 \
  --path /login \
  --save-session "admin-user"

# Session saved to: .cursorflow/sessions/admin-user_session.json
```

**What gets saved:**
- All cookies (session cookies, JWT tokens, etc.)
- localStorage state
- sessionStorage state
- Timestamp and authentication method

##### **Reusing Sessions**

```bash
# Use saved session
cursorflow test --base-url http://localhost:3000 \
  --path /protected-page \
  --use-session "admin-user"

# If session is invalid, CursorFlow automatically:
# 1. Detects the session is expired
# 2. Deletes invalid session file
# 3. Performs fresh authentication
```

##### **Managing Sessions**

```bash
# List all saved sessions
cursorflow sessions list

# Delete a specific session
cursorflow sessions delete "admin-user"

# Clear all sessions
cursorflow sessions clear
```

---

#### **SSO/OAuth Session Capture (STREAMLINED)**

For SSO authentication (Google, Microsoft, Azure AD, Okta), CursorFlow provides a streamlined one-command workflow to capture and use sessions immediately.

##### **Quick Start: Capture & Use Session**

```bash
# RECOMMENDED: Capture SSO session and save directly
cursorflow capture-auth \
  --base-url http://localhost:3001 \
  --path /dashboard \
  --save-as-session "sso"

# Session is immediately ready to use (no manual steps!)
cursorflow test --use-session "sso" --path /dashboard
```

##### **Capture & Test in One Command**

```bash
# Capture session and verify it works immediately
cursorflow capture-auth \
  --base-url http://localhost:3001 \
  --path /dashboard \
  --save-as-session "sso" \
  --test-immediately

# Output shows:
# ✅ Authentication state captured and saved as session!
# 🧪 Testing captured session...
# ✅ Session test PASSED!
# 🎉 localStorage was successfully restored
```

##### **How It Works**

1. **Browser Opens**: CursorFlow opens a browser (use `--browser chrome` for better visibility)
2. **Manual Login**: You complete SSO login in the browser
3. **Navigate**: Go to a protected page (e.g., /dashboard)
4. **Press Enter**: CursorFlow captures everything:
   - All cookies (100+ Microsoft SSO cookies if using Azure AD)
   - localStorage (JWT tokens, user data)
   - sessionStorage
   - Current URL and base URL
5. **Session Saved**: Automatically saved to `.cursorflow/sessions/sso_session.json`
6. **Ready to Use**: Session works immediately with `--use-session`

##### **Troubleshooting Sessions**

If session restoration fails or localStorage seems empty:

```bash
# Use debug mode to see detailed restoration steps
cursorflow test \
  --use-session "sso" \
  --path /dashboard \
  --debug-session \
  --verbose

# Debug output shows:
# 🔍 [Session Debug] Loaded session: sso
#    • Cookies: 102
#    • localStorage items: 3
#    • sessionStorage items: 0
# ✅ [Session Debug] Added 102 cookies
# 🔍 [Session Debug] Navigating to domain: http://localhost:3001
# 🔍 [Session Debug] Injecting localStorage...
# ✅ [Session Debug] localStorage injected: 3 keys
#    • auth_token: eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJ1Y2...
#    • ucip_user: {"id":1,"email":"user@example.com"...
#    • theme: system
```

**Common Issues & Solutions:**

| Issue | Cause | Solution |
|-------|-------|----------|
| "localStorage is empty" | Session restored before navigating to domain | **FIXED** in latest version - now navigates first |
| "Session no longer valid" | JWT token expired (typical: 24h) | Re-capture auth: `cursorflow capture-auth --save-as-session "sso"` |
| "Cookies not working" | Wrong domain in session file | Check session file has correct `base_url` field |
| "Page redirects to login" | localStorage not injected | Use `--debug-session` to verify injection |

##### **Session File Structure**

```json
{
  "captured_at": "2025-10-14 10:25:50",
  "base_url": "http://localhost:3001",
  "url": "http://localhost:3001/dashboard",
  "method": "cookies",
  "cookies": [
    {
      "name": "session_token",
      "value": "...",
      "domain": ".example.com",
      "httpOnly": true,
      "secure": true
    }
  ],
  "localStorage": {
    "auth_token": "eyJhbGci...",
    "user_data": "{\"id\":1,...}",
    "theme": "dark"
  },
  "sessionStorage": {}
}
```

---

#### **Session Validation**

CursorFlow validates authentication using multiple strategies:

**1. Error Indicators** (checks for):
- `.error`, `.alert-danger`, `.login-error`
- Text containing: "error", "invalid", "failed", "incorrect"

**2. Success Indicators** (from config):
- Keywords in page content: "dashboard", "profile", "logout"
- Configured in `success_indicators` array

**3. URL Changes**:
- URL no longer contains: `/login`, `/signin`, `/auth`

**4. Auth-Specific Elements** (from config):
- Elements that only appear when authenticated
- Configured in `auth_check_selectors` array

**Example validation configuration:**
```json
{
  "auth": {
    "method": "form",
    "username": "test@example.com",
    "password": "testpass",
    "success_indicators": ["Welcome back", "My Account", "Sign Out"],
    "auth_check_selectors": [".user-avatar", "#user-menu", ".logout-button"]
  }
}
```

---

#### **Complete Authentication Workflows**

##### **Workflow 1: Testing User Dashboard**

```bash
# 1. Configure auth in .cursorflow/config.json (one-time setup)
cat > .cursorflow/config.json << 'EOF'
{
  "base_url": "http://localhost:3000",
  "auth": {
    "method": "form",
    "username": "test@example.com",
    "password": "testpass",
    "username_selector": "#email",
    "password_selector": "#password",
    "submit_selector": "button[type='submit']"
  }
}
EOF

# 2. Login and save session
cursorflow test --base-url http://localhost:3000 \
  --path /login \
  --save-session "user"

# 3. Test protected pages (using saved session)
cursorflow test --base-url http://localhost:3000 \
  --path /dashboard \
  --use-session "user" \
  --screenshot "dashboard"

cursorflow test --base-url http://localhost:3000 \
  --path /settings \
  --use-session "user" \
  --screenshot "settings"
```

##### **Workflow 2: Testing Different User Roles**

```json
{
  "environments": {
    "admin": {
      "base_url": "http://localhost:3000",
      "auth": {
        "method": "form",
        "username": "admin@example.com",
        "password": "adminpass",
        "username_selector": "#email",
        "password_selector": "#password",
        "submit_selector": "#login-button"
      }
    },
    "user": {
      "base_url": "http://localhost:3000",
      "auth": {
        "method": "form",
        "username": "user@example.com",
        "password": "userpass",
        "username_selector": "#email",
        "password_selector": "#password",
        "submit_selector": "#login-button"
      }
    }
  }
}
```

```bash
# Test admin panel
cursorflow test --base-url http://localhost:3000 \
  --path /admin \
  --save-session "admin" \
  --config config.json --env admin

# Test user dashboard  
cursorflow test --base-url http://localhost:3000 \
  --path /dashboard \
  --save-session "user" \
  --config config.json --env user
```

##### **Workflow 3: Cookie-Based API Testing**

```json
{
  "base_url": "https://api.example.com",
  "auth": {
    "method": "cookies",
    "cookies": [
      {
        "name": "jwt_token",
        "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0...",
        "domain": "api.example.com",
        "path": "/",
        "httpOnly": true,
        "secure": true,
        "sameSite": "Strict"
      }
    ]
  }
}
```

```bash
# Test authenticated API endpoint
cursorflow test --base-url https://api.example.com \
  --path /v1/user/profile \
  --screenshot "api-response"
```

##### **Workflow 4: Header-Based Authentication**

```json
{
  "base_url": "https://api.example.com",
  "auth": {
    "method": "headers",
    "headers": {
      "Authorization": "Bearer your-api-token-here",
      "X-API-Key": "your-api-key",
      "X-Client-ID": "cursorflow-test"
    }
  }
}
```

```bash
# Test API with bearer token
cursorflow test --base-url https://api.example.com \
  --path /v1/protected-resource \
  --screenshot "protected-data"
```

---

#### **Python API Authentication**

**Form Authentication:**
```python
from cursorflow import CursorFlow

flow = CursorFlow(
    base_url="http://localhost:3000",
    auth_config={
        "method": "form",
        "username": "test@example.com",
        "password": "testpass",
        "username_selector": "#email",
        "password_selector": "#password",
        "submit_selector": "#login-button",
        "success_indicators": ["Dashboard", "Welcome"],
        "auth_check_selectors": [".user-menu"]
    }
)

# CursorFlow handles login automatically
results = await flow.execute_and_collect([
    {"navigate": "/dashboard"},
    {"screenshot": "authenticated-dashboard"}
])
```

**Session Reuse:**
```python
# Save session
flow = CursorFlow(
    base_url="http://localhost:3000",
    auth_config={...}
)

results = await flow.execute_and_collect(
    actions=[{"navigate": "/login"}],
    session_options={"save_session": True, "session_name": "test-user"}
)

# Reuse session (much faster!)
results = await flow.execute_and_collect(
    actions=[{"navigate": "/dashboard"}],
    session_options={"reuse_session": True, "session_name": "test-user"}
)
```

**Cookie Authentication:**
```python
flow = CursorFlow(
    base_url="https://staging.example.com",
    auth_config={
        "method": "cookies",
        "cookies": [
            {
                "name": "session_id",
                "value": "abc123xyz",
                "domain": "staging.example.com",
                "path": "/",
                "httpOnly": True,
                "secure": True
            }
        ]
    }
)
```

**Header Authentication:**
```python
flow = CursorFlow(
    base_url="https://api.example.com",
    auth_config={
        "method": "headers",
        "headers": {
            "Authorization": "Bearer your-token",
            "X-API-Key": "your-key"
        }
    }
)
```

---

#### **Troubleshooting Authentication**

##### **Common Issues**

**Problem: "Authentication failed"**

**Solution:**
1. Verify selectors are correct:
```bash
# Test without auth to inspect login form
cursorflow inspect --base-url http://localhost:3000 \
  --path /login \
  --selector "input[type='email']"
```

2. Check credentials are valid
3. Verify success indicators:
```json
{
  "auth": {
    "success_indicators": ["dashboard", "profile"],  // Keywords after login
    "auth_check_selectors": [".user-avatar"]  // Elements only when logged in
  }
}
```

**Problem: "Session not persisting"**

**Solution:**
1. Verify session directory exists and is writable:
```bash
ls -la .cursorflow/sessions/
```

2. Check session file was created:
```bash
cat .cursorflow/sessions/authenticated_session.json
```

3. Ensure cookies are being saved:
```json
{
  "timestamp": 1234567890,
  "method": "form",
  "cookies": [...],  // Should have cookies here
  "localStorage": {...},
  "sessionStorage": {...}
}
```

**Problem: "Session expires immediately"**

**Solution:**
- Check if application has aggressive session timeout
- Use `fresh_session: True` to force new login:
```bash
cursorflow test --use-session "user" --fresh-session
```

##### **Debugging Authentication**

**Enable verbose logging:**
```bash
# See detailed auth flow
cursorflow test --base-url http://localhost:3000 \
  --path /login \
  --save-session "test" \
  --verbose
```

**Check what CursorFlow is doing:**
```
🔐 Performing fresh authentication...
Filled username: #email
Filled password: #password
Clicked submit: button[type='submit']
✅ Form authentication successful
💾 Session saved: test
```

**Inspect saved session:**
```bash
cat .cursorflow/sessions/test_session.json | python3 -m json.tool
```

**Problem: "Browser not appearing" (capture-auth)**

**Solution:**

The browser IS launching but may be hidden by macOS window management:

1. **Use system Chrome** (more visible):
```bash
cursorflow capture-auth --base-url http://localhost:3000 \
  --browser chrome \
  --path /dashboard
```

2. **Check all desktop spaces**: 
   - Press F3 or swipe up with 3 fingers (Mission Control)
   - Look for Chromium/Chrome window

3. **Check your Dock**:
   - Look for Chromium icon that appeared
   - Click to bring window forward

4. **Verify browser launched**:
   - Look for "✅ Browser opened!" in terminal output
   - If you see this, browser is running somewhere

---

#### **Advanced Authentication Scenarios**

##### **Multi-Step Authentication (2FA, OAuth)**

For complex auth flows, use explicit actions instead of auto-auth:

```bash
cursorflow test --base-url http://localhost:3000 --actions '[
  {"navigate": "/login"},
  {"fill": {"selector": "#email", "value": "test@example.com"}},
  {"fill": {"selector": "#password", "value": "testpass"}},
  {"click": "#login-button"},
  {"wait_for": "#otp-input"},
  {"fill": {"selector": "#otp-input", "value": "123456"}},
  {"click": "#verify-button"},
  {"wait_for": ".dashboard"},
  {"screenshot": "authenticated"}
]' --save-session "2fa-user"
```

##### **Testing Multiple User Roles**

```bash
# Admin session
cursorflow test --base-url http://localhost:3000 \
  --config admin-config.json \
  --path /admin \
  --save-session "admin"

# Regular user session
cursorflow test --base-url http://localhost:3000 \
  --config user-config.json \
  --path /dashboard \
  --save-session "regular-user"

# Test admin-only features
cursorflow test --use-session "admin" \
  --path /admin/users \
  --screenshot "admin-users"

# Test user features
cursorflow test --use-session "regular-user" \
  --path /profile \
  --screenshot "user-profile"
```

##### **Getting Cookies from Browser**

**From Chrome DevTools:**
1. Login to your app in Chrome
2. Open DevTools (F12) → Application → Cookies
3. Copy cookie values
4. Add to config:

```json
{
  "auth": {
    "method": "cookies",
    "cookies": [
      {
        "name": "session_id",  // From DevTools
        "value": "copied-value-here",  // From DevTools
        "domain": "yourapp.com",
        "path": "/"
      }
    ]
  }
}
```

**From Network Tab:**
1. Login in browser
2. DevTools → Network → Find login request
3. Look at Response Headers for `Set-Cookie`
4. Copy cookie details to config

##### **SSO Authentication (OAuth, SAML, Google/Microsoft Login)**

SSO authentication is complex because it involves external identity providers and multi-step flows. CursorFlow handles this by capturing the final authenticated state.

**The SSO Challenge:**
- Involves external domains (accounts.google.com, login.microsoftonline.com, etc.)
- Complex token exchanges and redirects
- CSRF tokens and state parameters
- May use multiple cookies across domains

**Solution: Capture After Manual Login**

CursorFlow provides a helper to capture your authenticated state after manually logging in:

**Step 1: Login manually in Chrome**
```bash
# Open your app and complete the SSO login manually
# This handles all the OAuth redirects, token exchanges, etc.
```

**Step 2: Capture authentication state**
```bash
# Capture all cookies and storage from your logged-in session
cursorflow capture-auth --base-url http://localhost:3000 \
  --path /dashboard \
  --output sso-auth.json

# Use system Chrome for better visibility (recommended for macOS)
cursorflow capture-auth --base-url http://localhost:3000 \
  --path /dashboard \
  --browser chrome \
  --output sso-auth.json

# This opens a browser, lets you login, then captures:
# - All cookies (including third-party cookies if needed)
# - localStorage state
# - sessionStorage state
# - Any tokens or auth data
```

**Command Options:**
- `--base-url`: Your application URL
- `--path`: Page to navigate to after login (default: `/`)
- `--output`: File to save auth state (default: `auth-capture.json`)
- `--browser`: Browser to use - `chromium`, `chrome`, or `firefox` (default: `chromium`)
- `--wait`: Maximum seconds to wait for login (default: `60`)

**Browser Visibility:**
- Use `--browser chrome` on macOS for better window visibility
- Browser opens maximized in headed mode
- If you don't see it, check other desktop spaces or behind windows

**Step 3: Use captured auth in config**
```json
{
  "base_url": "http://localhost:3000",
  "auth": {
    "method": "cookies",
    "cookies": [
      // Automatically populated from capture-auth
      {
        "name": "auth_token",
        "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "domain": "yourapp.com",
        "path": "/",
        "httpOnly": true,
        "secure": true
      },
      {
        "name": "refresh_token",
        "value": "abc123...",
        "domain": "yourapp.com",
        "path": "/",
        "httpOnly": true,
        "secure": true
      }
    ]
  }
}
```

**Alternative: Manual Cookie Extraction**

If `capture-auth` is not available, extract cookies manually:

**For Google SSO:**
```bash
# 1. Login via Google in Chrome
# 2. DevTools (F12) → Application → Cookies
# 3. Look for cookies from BOTH domains:
#    - yourapp.com (your application cookies)
#    - accounts.google.com (Google auth cookies, if needed)
# 4. Copy all authentication-related cookies:
```

**For Microsoft/Azure AD SSO:**
```bash
# Same process, look for:
# - yourapp.com cookies
# - login.microsoftonline.com cookies (if needed)
# - Any cookies with names like: auth_token, id_token, access_token
```

**For Okta/Auth0:**
```bash
# Look for cookies like:
# - okta-oauth-redirect-params
# - okta-oauth-state
# - sid (session ID)
# - dt (device token)
```

**Complete cookie capture example:**
```json
{
  "auth": {
    "method": "cookies",
    "cookies": [
      {
        "name": "appSession",
        "value": "long-base64-encoded-value...",
        "domain": "yourapp.com",
        "path": "/",
        "httpOnly": true,
        "secure": true,
        "sameSite": "Lax"
      },
      {
        "name": "identity.token",
        "value": "another-long-token...",
        "domain": "yourapp.com",
        "path": "/",
        "httpOnly": false,
        "secure": true,
        "sameSite": "None"
      }
    ]
  }
}
```

**SSO Best Practices:**

1. **Capture all cookies**: SSO often uses multiple cookies
2. **Check localStorage**: Some SSO solutions store tokens in localStorage
3. **Watch for expiration**: SSO tokens typically expire (1 hour - 24 hours)
4. **Test token validity**: 
```bash
cursorflow test --use-session "sso-user" --path /dashboard
# If fails, capture fresh session
```

5. **Multi-domain considerations**: Some SSO requires cookies on multiple domains
```json
{
  "auth": {
    "method": "cookies",
    "cookies": [
      {"name": "app_session", "domain": "yourapp.com", "value": "..."},
      {"name": "sso_token", "domain": "sso.yourapp.com", "value": "..."}
    ]
  }
}
```

**Refreshing SSO Tokens:**

SSO tokens expire. When they do:
```bash
# 1. Clear old session
cursorflow sessions delete "sso-user"

# 2. Manually login again in Chrome

# 3. Capture new auth state
cursorflow capture-auth --base-url http://localhost:3000 \
  --path /dashboard \
  --output sso-auth-refreshed.json

# 4. Update config with new tokens
```

**Programmatic SSO (Advanced):**

For automated SSO without manual login, you need service account credentials from your identity provider. This is complex and varies by provider - consult your SSO provider's documentation for headless authentication flows.

##### **Environment-Specific Auth**

Different credentials for local/staging/production:

```json
{
  "environments": {
    "local": {
      "base_url": "http://localhost:3000",
      "auth": {
        "method": "form",
        "username": "dev@example.com",
        "password": "devpass"
      }
    },
    "staging": {
      "base_url": "https://staging.example.com",
      "auth": {
        "method": "form",
        "username": "staging@example.com",
        "password": "stagingpass"
      }
    },
    "production": {
      "base_url": "https://example.com",
      "auth": {
        "method": "cookies",
        "cookies": [{"name": "prod_token", "value": "..."}]
      }
    }
  }
}
```

```bash
# Test on staging with staging credentials
cursorflow test --config config.json \
  --env staging \
  --path /dashboard
```

---

#### **Session Management Commands**

```bash
# List all saved sessions
cursorflow sessions list
# Output:
# admin-user (saved: 2025-10-10 14:23:45)
# regular-user (saved: 2025-10-10 14:25:12)

# Delete specific session
cursorflow sessions delete "admin-user"

# Clear all sessions
cursorflow sessions clear

# View session info
cursorflow sessions info "admin-user"
# Output:
# Session: admin-user
# Timestamp: 2025-10-10 14:23:45
# Method: form
# Cookies: 3
# Local Storage: 5 items
# Session Storage: 2 items
```

---

#### **Security Considerations**

**Storing Credentials:**
- Never commit `.cursorflow/config.json` with credentials to version control
- Add to `.gitignore`:
```bash
echo ".cursorflow/config.json" >> .gitignore
echo ".cursorflow/sessions/" >> .gitignore
```

- Use environment variables for sensitive data:
```json
{
  "auth": {
    "method": "form",
    "username": "${TEST_USER}",
    "password": "${TEST_PASSWORD}"
  }
}
```

**Session Storage:**
- Session files contain cookies and tokens - keep secure
- Stored in `.cursorflow/sessions/` (gitignored by default)
- Delete sessions when done: `cursorflow sessions clear`

**Best Practices:**
- Use test accounts, not production accounts
- Rotate test credentials regularly
- Use short-lived tokens when possible
- Clear sessions after testing

---

#### **Without Authentication**

Testing public pages doesn't require auth_config:

```bash
# No auth needed for public pages
cursorflow test --base-url https://example.com \
  --path /about \
  --screenshot "about-page"

# Session flags are ignored without auth_config
cursorflow test --base-url https://example.com \
  --path /contact \
  --save-session "ignored"  # Has no effect
```

### **Quick Commands**

**Rerun last test:**
```bash
cursorflow rerun
cursorflow rerun --click ".other-element"
```

**Inspect elements (comprehensive data):**
```bash
# Inspect with full element analysis
cursorflow inspect --base-url http://localhost:3000 --selector "#messages-panel"

# Inspect with custom path
cursorflow inspect -u http://localhost:3000 -p /dashboard -s ".card"

# Show all computed CSS properties
cursorflow inspect -u http://localhost:3000 -s ".button" --verbose
```

**Measure element dimensions (surgical precision):**
```bash
# Quick dimension check
cursorflow measure --base-url http://localhost:3000 --selector "#panel"

# Multiple elements at once
cursorflow measure -u http://localhost:3000 -s "#panel1" -s "#panel2"

# Show all CSS properties
cursorflow measure -u http://localhost:3000 -s ".card" --verbose
```

**Count elements:**
```bash
cursorflow count --base-url http://localhost:3000 --selector ".message-item"
```

**View timeline:**
```bash
cursorflow timeline --session session_12345
```

### **Element Analysis Commands**

CursorFlow provides powerful element inspection tools for CSS debugging and layout analysis.

#### **`inspect` - Comprehensive Element Analysis**

The `inspect` command captures full page data and displays detailed element information:

**What you get:**
- **Computed CSS** - All browser-computed styles (display, position, flex, dimensions, etc.)
- **Dimensions** - Rendered width, height, and position
- **Selectors** - Unique CSS selector for targeting
- **Accessibility** - Role, interactive state, ARIA attributes
- **Visual Context** - Visibility, z-index, viewport position
- **Screenshot** - Visual reference saved to artifacts

**Example output:**
```
═══ Element 1/1 ═══
Tag:       div
ID:        #messages-panel
Classes:   .console-panel.message-list-panel

📐 Dimensions:
   Position:  x=320, y=73
   Size:      532w × 927h

🎨 Key CSS Properties:
   display:   flex
   flex:      1 1 0%
   flex-basis: 260px
   width:     532px

♿ Accessibility:
   Role:         None
   Interactive:  ❌

👁️  Visual Context:
   Visibility:   ✅ Visible

📸 Screenshot saved: .cursorflow/artifacts/screenshots/inspection.png
```

**Use cases:**
- Debug CSS layout issues
- Verify flex/grid calculations
- Check computed vs authored styles
- Find optimal selectors for automation
- Analyze element visibility and positioning

#### **`measure` - Surgical Dimension Checking**

The `measure` command provides quick dimension and CSS checks without verbose output:

**What you get:**
- **Rendered dimensions** - Actual width × height on screen
- **Position** - x, y coordinates
- **Key CSS** - display, width, flex properties
- **Multiple elements** - Measure several at once
- **All CSS (--verbose)** - Complete computed styles (76+ properties)

**Example output:**
```
h1
  📐 Rendered:  600w × 38h
  📍 Position:  x=420, y=133
  🎨 Display:   block
  📦 CSS Width: 600px
  🔧 Flex:      0 1 auto
  💡 Use --verbose to see all 76 CSS properties
```

**Use cases:**
- Verify CSS changes took effect
- Check flex layout calculations
- Compare dimensions across breakpoints
- Quick dimension reference during development
- Validate responsive behavior

#### **Comparison: inspect vs measure**

| Feature | `inspect` | `measure` |
|---------|-----------|-----------|
| **Purpose** | Comprehensive analysis | Quick dimension check |
| **Output** | Detailed, multi-section | Concise, focused |
| **Screenshot** | Always included | Captured but not shown |
| **Use when** | Debugging complex CSS | Verifying dimensions |
| **Speed** | ~3 seconds | ~2 seconds |
| **Multiple elements** | One at a time | Multiple with `-s` flags |

**Workflow example:**
```bash
# 1. Use measure for quick check
cursorflow measure -u http://localhost:3000 -s "#panel"
# Output: 260w × 900h

# 2. If dimensions seem wrong, use inspect for full analysis
cursorflow inspect -u http://localhost:3000 -s "#panel" --verbose
# Output: Full CSS, accessibility, visual context, screenshot

# 3. Make CSS changes based on insights

# 4. Verify with measure again
cursorflow measure -u http://localhost:3000 -s "#panel"
# Output: 532w × 900h ✅ Fixed!
```

### **Visual Comparison Commands**

CursorFlow provides visual comparison tools for iterating toward design specifications through pure measurement.

#### **`compare-mockup` - Visual Design Comparison**

Compare a design mockup against your work-in-progress implementation:

**What you get (pure data)**:
- **Screenshots** - Both mockup and implementation captured
- **Visual diff images** - Pixel-by-pixel difference highlighting
- **Similarity percentage** - Quantified visual match (0-100%)
- **Element position data** - X, Y coordinates for both versions
- **Size measurements** - Width, height comparisons
- **CSS property data** - Computed styles for matching elements

**Philosophy**: CursorFlow observes both realities (mockup + implementation) and provides measurements. Cursor analyzes the data and decides what changes to make.

**Basic usage**:
```bash
cursorflow compare-mockup https://mockup.example.com/dashboard \
  --base-url http://localhost:3000 \
  --output comparison-results.json
```

**With custom actions**:
```bash
cursorflow compare-mockup https://mockup.example.com/dashboard \
  --base-url http://localhost:3000 \
  --mockup-actions '[{"navigate": "/dashboard"}]' \
  --implementation-actions '[{"navigate": "/dashboard"}, {"wait_for": "#main-content"}]'
```

**With multiple viewports**:
```bash
cursorflow compare-mockup https://mockup.example.com \
  --base-url http://localhost:3000 \
  --viewports '[
    {"width": 1440, "height": 900, "name": "desktop"},
    {"width": 768, "height": 1024, "name": "tablet"}
  ]'
```

**Output structure**:
```json
{
  "comparison_id": "mockup_comparison_123456",
  "mockup_url": "https://mockup.example.com",
  "implementation_url": "http://localhost:3000",
  "summary": {
    "average_similarity": 87.73,
    "viewports_tested": 2,
    "similarity_by_viewport": [
      {"viewport": "desktop", "similarity": 89.5},
      {"viewport": "tablet", "similarity": 85.96}
    ]
  },
  "results": [
    {
      "viewport": {"width": 1440, "height": 900, "name": "desktop"},
      "mockup_screenshot": "path/to/mockup.png",
      "implementation_screenshot": "path/to/impl.png",
      "visual_diff": {
        "similarity_score": 89.5,
        "different_pixels": 45000,
        "total_pixels": 1296000,
        "diff_image": "path/to/diff.png",
        "highlighted_diff": "path/to/highlighted.png"
      },
      "layout_analysis": {
        "mockup_elements": 45,
        "implementation_elements": 52,
        "differences": [...]
      }
    }
  ]
}
```

**Use cases**:
- Compare implementation to Figma exports
- Verify design system component accuracy
- Measure progress toward design specifications
- Document visual differences for stakeholders

#### **`iterate-mockup` - CSS Iteration with Measurement**

Test multiple CSS changes and observe which gets closer to the mockup:

**Basic usage**:
```bash
cursorflow iterate-mockup https://mockup.example.com/dashboard \
  --base-url http://localhost:3000 \
  --css-improvements '[
    {"name": "spacing-fix", "css": ".header { padding: 2rem; }"},
    {"name": "color-adjust", "css": ".btn { background: #007bff; }"}
  ]'
```

**What it does**:
1. Captures baseline similarity
2. Temporarily injects each CSS change
3. Observes the REAL rendered result
4. Captures similarity for each variation
5. Provides measurements for Cursor to analyze

**Output**: Similarity data for each CSS variation (Cursor decides which to apply)

### **Artifact Management**

CursorFlow generates screenshots, traces, and session data. Clean up regularly:

**Clean old artifacts (>7 days):**
```bash
cursorflow cleanup --artifacts --old-only --yes
```

**Clean everything:**
```bash
cursorflow cleanup --all --yes
```

**Preview first:**
```bash
cursorflow cleanup --all --dry-run
```

**Best practices:**
- Run `cleanup --artifacts --old-only --yes` weekly
- Always use `--yes` for autonomous/CI operation
- Use `--dry-run` to preview before deleting
- Clean sessions periodically: `cleanup --sessions --yes`

**Typical growth:** 50-100MB/day light usage, 500MB-1GB/day heavy usage

### **Visual Comparison Commands**

CursorFlow provides mockup comparison for visual iteration - comparing your implementation to design specifications through pure data collection.

#### **compare-mockup - Visual Measurement**

Compare two URLs and get quantified similarity data:

```bash
# Basic comparison
cursorflow compare-mockup "https://mockup.example.com" \
  --base-url http://localhost:3000

# With custom actions
cursorflow compare-mockup "https://mockup.example.com" \
  --base-url http://localhost:3000 \
  --implementation-actions '[{"navigate": "/dashboard"}]'

# Multiple viewports
cursorflow compare-mockup "https://mockup.example.com" \
  --base-url http://localhost:3000 \
  --viewports '[{"width": 1440, "height": 900, "name": "desktop"}, {"width": 375, "height": 667, "name": "mobile"}]'
```

**Output Data Structure**:
```json
{
  "comparison_id": "mockup_comparison_123456",
  "mockup_url": "https://mockup.example.com",
  "implementation_url": "http://localhost:3000",
  "results": [
    {
      "viewport": {"width": 1440, "height": 900, "name": "desktop"},
      "mockup_screenshot": "path/to/mockup.png",
      "implementation_screenshot": "path/to/impl.png",
      "visual_diff": {
        "diff_image": "path/to/diff.png",
        "highlighted_diff": "path/to/highlighted.png",
        "similarity_score": 87.3,
        "different_pixels": 45230,
        "total_pixels": 1296000
      }
    }
  ],
  "summary": {
    "average_similarity": 87.3,
    "viewports_tested": 1,
    "similarity_by_viewport": [...]
  }
}
```

**Philosophy**: Pure data collection - provides measurements, Cursor interprets them.

#### **iterate-mockup - CSS Experimentation**

Test multiple CSS variations and observe real outcomes:

```bash
# Create CSS improvements JSON
cat > improvements.json << 'EOF'
[
  {
    "name": "fix-spacing",
    "css": ".container { padding: 2rem; gap: 1.5rem; }"
  },
  {
    "name": "adjust-colors",
    "css": ".btn-primary { background: #007bff; }"
  }
]
EOF

# Run iteration
cursorflow iterate-mockup "https://mockup.example.com" \
  --base-url http://localhost:3000 \
  --css-improvements improvements.json
```

**What it does**:
1. Captures baseline comparison
2. Temporarily injects each CSS variation
3. Captures screenshot of REAL outcome
4. Measures similarity for each variation
5. Provides quantified data for each experiment

**Output**: Similarity percentages for each CSS variation, Cursor decides which to apply.

**Use case**: Rapid CSS experimentation with quantified feedback.

## ⚡ **Quick Usage Examples**

### **OpenSAS/Mod_Perl (Our Current Project)**
```bash
# Test message console with staging server logs
cursor-test test message-console \
  --framework mod_perl \
  --base-url https://staging.resumeblossom.com \
  --logs ssh \
  --params orderid=6590532419829

# Auto-detect and test
cd /path/to/opensas
cursor-test auto-test --environment staging
```

### **React Application** 
```bash
# Test React dashboard with local logs
cursor-test test user-dashboard \
  --framework react \
  --base-url http://localhost:3000 \
  --logs local \
  --params userId=123

# Test Next.js app
cursor-test test admin-panel \
  --framework react \
  --base-url http://localhost:3000 \
  --workflows auth,data_load,interaction
```

### **PHP/Laravel System**
```bash
# Test with Docker container logs
cursor-test test admin-users \
  --framework php \
  --base-url https://app.example.com \
  --logs docker \
  --params token=abc123
```

### **Django Application**
```bash
# Test with systemd logs
cursor-test test blog-editor \
  --framework django \
  --base-url http://localhost:8000 \
  --logs systemd \
  --params postId=456
```

## 🔧 **Installation & Setup**

### **1. Install the Framework**
```bash
# Install universal testing agent
pip install cursorflow
playwright install chromium

# Or install from source
git clone /path/to/cursorflow
cd cursorflow
pip install -e .
```

### **2. Initialize Any Project**
```bash
# Auto-detect framework and create config
cursor-test init . --framework auto-detect

# Or specify framework manually
cursor-test init . --framework mod_perl
cursor-test init . --framework react
cursor-test init . --framework php
```

### **3. Configure for Your Environment**
Edit the generated `cursor-test-config.json`:

```json
{
  "framework": "mod_perl",
  "environments": {
    "local": {
      "base_url": "http://localhost:8080",
      "logs": "local",
      "log_paths": {"app": "logs/app.log"}
    },
    "staging": {
      "base_url": "https://staging.example.com", 
      "logs": "ssh",
      "ssh_config": {
        "hostname": "staging-server",
        "username": "deploy",
        "key_filename": "~/.ssh/staging_key"
      },
      "log_paths": {
        "apache_error": "/var/log/httpd/error_log"
      }
    }
  }
}
```

## 📋 **Common Test Patterns**

### **Smoke Testing (Any Framework)**
```bash
# Test basic functionality
cursor-test test component-name --workflows smoke_test

# Test all components
cursor-test auto-test
```

### **Debugging Specific Issues**
```bash
# Test with verbose logging
cursor-test test component-name --verbose --workflows load,ajax,interaction

# Focus on specific functionality
cursor-test test message-console --workflows modal_test --params orderid=123
```

### **Performance Testing**
```bash
# Monitor performance during test
cursor-test test dashboard --workflows load,data_refresh --capture-performance

# Continuous monitoring
cursor-test monitor critical-component --interval 300
```

## 🎯 **Framework-Specific Features**

### **Mod_Perl/OpenSAS Features**
- **AJAX Authentication**: Automatically handles pid/hash/timestamp
- **Component Loading**: Waits for OpenSAS component initialization
- **Perl Error Detection**: Recognizes compilation errors, missing functions
- **Database Error Correlation**: Matches DBD::mysql errors with actions

### **React Features**
- **Component Mounting**: Waits for React component lifecycle
- **State Management**: Monitors Redux/Context state changes
- **API Integration**: Tracks fetch requests and responses
- **Hydration Detection**: Identifies SSR hydration issues

### **PHP Features**
- **Laravel Routing**: Handles Laravel route patterns
- **Eloquent Errors**: Detects ORM and database issues
- **Blade Templates**: Monitors template rendering errors
- **Session Management**: Tracks authentication state

## 📊 **Understanding Test Results**

### **Success Indicators**
- `✅ PASSED` - All workflows completed without critical issues
- Low error count in correlations
- No failed network requests
- Performance metrics within acceptable ranges

### **Failure Indicators**
- `❌ FAILED` - Critical issues found or workflows failed
- High correlation confidence between browser actions and server errors
- Console errors or failed network requests
- Performance degradation

### **Report Sections**
1. **Test Summary** - Overview of test execution
2. **Critical Issues** - Problems requiring immediate attention
3. **Recommendations** - Suggested fixes and improvements
4. **Workflow Results** - Step-by-step execution details
5. **Performance Metrics** - Timing and resource usage
6. **Debug Information** - Raw data for deep debugging

## 🛠️ **Advanced Usage**

### **Custom Test Definitions**
Create `test_definitions/component-name.yaml`:

```yaml
my_component:
  framework: react  # or mod_perl, php, django
  
  workflows:
    custom_workflow:
      - navigate: {params: {id: "123"}}
      - wait_for: "[data-testid='loaded']"
      - click: {selector: "#action-button"}
      - validate: {selector: ".success", exists: true}
      
  assertions:
    - selector: "#main-content"
      not_empty: true
    - api_response: "/api/data"
      status: 200
```

### **Programmatic Usage**
```python
from cursor_testing_agent import TestAgent

# Any framework with same API
agent = TestAgent('react', 'http://localhost:3000', logs='local')
results = await agent.test('user-dashboard', {'userId': '123'})

# Chain multiple tests
components = ['login', 'dashboard', 'profile']
for component in components:
    result = await agent.test(component)
    if not result['success']:
        print(f"❌ {component} failed")
        break
```

### **Integration with CI/CD**
```yaml
# .github/workflows/ui-tests.yml
- name: Run UI Tests
  run: |
    cursor-test auto-test --environment staging
    cursor-test test critical-component --workflows full
```

## 🔍 **Troubleshooting**

### **Common Issues**
- **SSH Connection Failed**: Check SSH config and key permissions
- **Log Files Not Found**: Verify log paths exist and are readable
- **Browser Launch Failed**: Reinstall Playwright browsers
- **Framework Not Detected**: Manually specify framework with `--framework`

### **Debug Commands**
```bash
# Test SSH connection
ssh deploy@staging-server "echo test"

# Verify log files
ssh deploy@staging-server "tail -5 /var/log/httpd/error_log"

# Test browser automation
python -c "from cursor_testing_agent import TestAgent; print('✅ Import successful')"
```

## 🎯 **Best Practices**

### **For Any Framework**
1. **Start with smoke tests** to catch basic issues
2. **Use environment-specific configs** for different deployment stages
3. **Monitor logs during active development** to catch issues early
4. **Create custom workflows** for your specific user journeys

### **For Team Usage**
1. **Share config files** across team members
2. **Standardize test definitions** for consistency
3. **Use in CI/CD pipelines** for automated quality gates
4. **Generate reports** for debugging sessions

## 🚀 **Scaling Across Projects**

### **Single Developer, Multiple Projects**
```bash
# Same tool, different projects
cd /path/to/react-project && cursor-test auto-test
cd /path/to/opensas-project && cursor-test auto-test  
cd /path/to/laravel-project && cursor-test auto-test
```

### **Team with Mixed Tech Stack**
```bash
# Everyone uses same commands regardless of tech stack
cursor-test test login-component     # Works for React
cursor-test test message-console     # Works for Mod_Perl  
cursor-test test admin-panel         # Works for PHP
```

**The power**: Learn once, test everywhere! 🌌

## 💡 **Success Stories**

**Scenario 1**: Debug OpenSAS AJAX issues
- **Before**: Manual clicking + SSH terminal + guesswork
- **After**: `cursor-test test message-console` → automatic correlation + fix recommendations

**Scenario 2**: Test React component across environments  
- **Before**: Manual testing on local, staging, production
- **After**: `cursor-test test component --environment staging` → consistent testing everywhere

**Scenario 3**: Onboard new team member
- **Before**: Complex setup docs for each framework
- **After**: `cursor-test init .` → auto-configured testing for any project

**The vision**: Universal testing that scales across frameworks, environments, and teams! 🚀✨
