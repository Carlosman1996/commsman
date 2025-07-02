# CommsMan

**CommsMan** (Communication Manager) is a powerful, extensible tool for testing, monitoring, and managing industrial communication protocols. It is designed to help engineers and testers interact with embedded systems, PLCs, and other field devices via common industrial protocols.

Currently, CommsMan supports **Modbus TCP** and **Modbus RTU** protocols, with a focus on usability, structured data organization, and continuous monitoring.

---

## 🚀 Current Capabilities

### ✅ Protocols

* **Modbus TCP**
* **Modbus RTU**

### ✅ Core Features

* **Collections-Based Architecture**
  Organize your communication flows into nested *Collections* and *Requests*.

* **Request Execution**
  Send and receive Modbus messages with customizable parameters (function code, address, quantity, etc.).

* **Continuous Monitoring**
  Poll devices continuously and view real-time updates and historical results for both *Collections* and *Requests*.

* **Request History**
  Every request and collection stores a timestamped history of results (RTU and TCP).

* **Inheritance of Clients**
  Requests can inherit the Modbus client (TCP or RTU) from their parent collection.

---

## 📥 Download

Prebuilt executables for **Windows**, **Linux**, and **macOS** are available in every [GitHub Release](https://github.com/Carlosman1996/commsman/releases).  
You can download the latest version of Commsman for your platform without needing to install Python or any dependencies.

> ⚠️ **Important Note for Windows Users:**  
> When downloading the `.exe` version of CommsMan, **Windows Defender or your antivirus may falsely detect it as a virus or unknown app**.  
> This is a **false positive** — the code is **100% open source and trustworthy**.  
> However, since CommsMan is an independent project and does **not have funding for a code-signing certificate**, Windows marks it as "unrecognized."  
> You can safely run the application after allowing it through your antivirus.

The source code is fully available and verifiable in this repository.

---

## 📦 Installation & Setup

### 1. Create and Activate Virtual Environment

```bash
python3 -m pip install virtualenv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. Run the Application

```bash
python start.py
```

---

## 📌 Roadmap & Future Plans

### 🔐 Database & Security

* Secure SQLite storage with access restrictions
* Encrypted history logs
* Control over what data can be exported or viewed

### ⚠️ Monitoring & Validation

* Alarm and event system for threshold violations
* Define validation rules per request or collection
* Highlight invalid or unexpected responses

### 📁 Data Import / Export

* Import full projects (Collections, Requests, Modbus maps) from CSV
* Export request results and logs for offline analysis

### 🔧 Protocol Expansion

* Add support for:

  * MQTT (client and broker integration)
  * CAN Bus
  * SPI & I2C
  * Serial Raw (generic binary protocols)

### 📜 Request Scripting & Automation

* Chain requests into execution sequences
* Loop and conditional logic blocks for advanced automation
* Scheduled execution

### 🖥️ Modbus Server Mode

* Run CommsMan as a Modbus TCP/RTU server
* Simulate responses based on predefined registers or logic

### 🧪 Integration Testing

* Run scripted sequences from CLI or CI pipelines
* Return pass/fail status based on custom rules
* Auto-execute test sets for regression validation

### 🌐 Interface Enhancements

* Improved visual feedback and error highlighting
* Exportable request/collection diagrams
* Plugin support for new protocols or processors

---

## 🧠 Philosophy

CommsMan is designed with the mindset of being **protocol-agnostic**, **extensible**, and **integrated into real engineering workflows**. Whether you're debugging a single device or validating a full industrial system, CommsMan aims to be your go-to companion for communication diagnostics and automation.
