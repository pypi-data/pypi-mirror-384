# 🧠 Unifisa Core

**Unifisa Core** is a Python utility library that centralizes reusable modules for automation, email handling, logging, Selenium WebDriver setup, and SQL Server integration.  
Originally created by Unifisa collaborators, this project is open source and welcomes contributions from the community.

---

## 🚀 Installation

Install directly from **PyPI**:

```bash
pip install unifisa-core
```
Or, for a specific version:

```bash
pip install unifisa-core==0.1.0
```
## 📦 Modules Overview

| Module                   | Description                                                                 |
| :----------------------- | :-------------------------------------------------------------------------- |
| `unifisa_core.email`     | Send and manage emails easily via SMTP.                                     |
| `unifisa_core.log`       | Centralized logging configuration using **Loguru**.                         |
| `unifisa_core.selenium`  | Manage Chrome WebDriver and helper functions for Selenium automation.       |
| `unifisa_core.sqlserver` | Simplified connection and query execution with SQL Server using **pyodbc**. |

## 🧩 Usage Examples

### 📧 Email Manager
```python
from unifisa_core.email.email_manager import EmailManager

email = EmailManager(
    smtp_server="smtp.gmail.com",
    port=587,
    sender="example@gmail.com",
    password="your_password"
)

email.send_email(
    to="recipient@example.com",
    subject="Automation Report",
    body="Your automation finished successfully!"
)
```

### 🧾 Logger Configuration
```python
from unifisa_core.log.logger_config import setup_logger

logger = setup_logger("automation.log")
logger.info("Process started successfully.")
```

### 🌐 Selenium Helper
```python
from unifisa_core.selenium.chrome_driver_settings import ChromeDriverSettings
from unifisa_core.selenium.selenium_helper import SeleniumHelper

driver = ChromeDriverSettings().get_driver()
helper = SeleniumHelper(driver)

helper.open_url("https://www.google.com")
```


### 🗄️ SQL Server Integration
```python
from unifisa_core.sqlserver.sql_server_pyodbc import SQLServerConnection

db = SQLServerConnection(
    server="SERVER_NAME",
    database="DB_NAME",
    username="user",
    password="password"
)

data = db.query("SELECT TOP 10 * FROM employees")
print(data)
```

### 📁 Project Structure
```bash
unifisa-core/
├── src/
│   └── unifisa_core/
│       ├── email/
│       │   └── email_manager.py
│       ├── log/
│       │   └── logger_config.py
│       ├── selenium/
│       │   ├── chrome_driver_settings.py
│       │   └── selenium_helper.py
│       └── sqlserver/
│           └── sql_server_pyodbc.py
├── LICENSE
└── README.md
```

## 🧑‍💻 Authors

### vinicinhus (Vincius)
🔗 [GitHub Profile](https://github.com/vinicinhus)

### Jpzinn654 (Juan Pablo)
📧 juan654.pablo@gmail.com

🔗 [GitHub Profile](https://github.com/Jpzinn654)

## ⚖️ License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
