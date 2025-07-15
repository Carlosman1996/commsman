# 🚀 **v0.3.3 — Core UX, Results, and Infrastructure Polish**

## 🔧 Functional & UI Improvements

* [ ] Fix export button
* [ ] Execute button state: Loading → Running → Stopping → Ready
* [ ] Disable edit in response tables
* [ ] Ellipsis + tooltip on long texts
* [ ] Results table layout: display full return text cleanly
* [ ] Show request execution session as header
* [ ] Save last opened tab per request

## 📊 Results & History

* [ ] Rework result history: per request & per collection
* [ ] Limit number of stored results (configurable)
* [ ] Add "Clear Results" button
* [ ] Filter/sort results by status (OK, KO, error)
* [ ] Show results inside collections

## 🏠 Home & Parallel Execution

* [ ] HOME page showing all running instances
* [ ] Notification bar with links to running executions
* [ ] Allow multiple parallel executions

## 📦 Logging & Performance

* [ ] Logging system: structured logs, per-session log files
* [ ] Improve SQLite performance:

  * Avoid full UI reload on update
  * Background thread/process for update ops
* [ ] UI responsiveness on low-performance devices
* [ ] Decimal values for polling interval and delay

## 🔧 Misc Technical Cleanup

* [ ] Add "description" tab to all requests/collections
* [ ] Raise exception if request has children (check in `__post_init__`)
* [ ] Handle orphaned `client` and `run_options` when requests are deleted
* [ ] Splitter must be a component with stretch factor: expand second element
* [ ] Add connection name for reuse
* [ ] Allow reuse of previous connections
* [ ] Improve usability: move general results tab, vertical splitter
* [ ] Disable "execute" button until backend confirms start
* [ ] BaseResult and BaseDetail are calling the same API multiple times – refactor

---

# 📡 **v0.4.0 — MQTT + Alerts & Validation Engine**

## 📶 MQTT Protocol Support

* [ ] Connect to broker (TCP)
* [ ] Publish / Subscribe (with topic wildcards)
* [ ] Retain, QoS (0/1/2)
* [ ] Display message history (timestamp, topic, payload)
* [ ] Scheduled publishing or looping messages
* [ ] Retain client settings in collections

## ⚠️ Alerts & Rule Validation

* [ ] Define validation rules:

  * Value thresholds
  * Bitmask match
  * Regex/pattern
* [ ] Highlight invalid responses (colors/icons)
* [ ] Session alert panel
* [ ] Export alerts

## 🛡️ Security & Storage

* [ ] Encrypt SQLite (optional)
* [ ] Add foreign key constraints and cascade deletes
* [ ] Add pre-request delay (e.g., sleep X ms before run)

---

# 📁 **v0.5.0 — Import/Export, Workspace, and Integration Testing**

## 📥 Import / Export

* [ ] Import collections/requests from Excel or CSV
* [ ] Export to Excel, CSV, or JSON (requests, history)
* [ ] Export alerts and validation results
* [ ] Export/import whole workspace (\*.cmws / \*.json)

## 🧪 Integration Testing / CI

* [ ] Define test sets (workspace or standalone test files)
* [ ] CLI to run test set (with pass/fail result)
* [ ] Auto-run test set on app start or from pipeline
* [ ] Conditions or expected values per request

## 💾 Data Management

* [ ] Add table view for collections
* [ ] Option to batch delete or remove results
* [ ] Add description tab to all views
* [ ] Support raw register parsing for `write multiple registers`
* [ ] Control number of saved results globally

---

# 🔌 **v0.6.0 — Plugin Architecture & Licensing (If userbase grows)**

## 🧩 Plugin System

* [ ] Load plugins from external folder or via entry\_points
* [ ] Allow plugins to define:

  * New protocols (CAN, SPI, Serial Raw, etc.)
  * Validators
  * Exporters
  * UI tabs or tools
* [ ] Simple plugin config system

## 🔑 Licensing (Optional)

* [ ] Add license activation (offline or token-based)
* [ ] Load-only-if-valid mechanism for plugins

## 🔧 Plugin Ideas (Not yet implemented)

* Test Automation (CLI/looped/test conditions)
* Advanced Alert Actions (webhooks, sequences)
* Modbus Server Mode
* Project Encryption Plugin

---

# 🌐 **Parallel Tasks — Web & Distribution**

## 🌍 Landing Page / Documentation Site

* [ ] Simple homepage (GitHub Pages, VitePress, or raw HTML)
* [ ] Showcase:

  * Features
  * Screenshots
  * Download buttons
  * Security info (e.g., unsigned .exe note)
  * Roadmap
  * Support email

## 🪪 Code Signing

* [ ] Buy or generate signing certificate (e.g., Certum, DigiCert)
* [ ] Sign `.exe` and `.msi` during release
* [ ] CI process with signing step (optional)
* [ ] Update README with info about Defender warnings and why
