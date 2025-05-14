<!-- README.md -->

<p align="center">
  <img src="assets/logo.png" alt="WhatsChecker Logo" height="150"/>
</p>

<h1 align="center">WhatsChecker</h1>

<p align="center">
  🕵️‍♂️ A powerful multi-threaded CLI tool to <strong>check WhatsApp number validity</strong> via WhatsApp Web.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.0.1-blue?style=flat-square" alt="Version Badge" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License Badge" />
  <img src="https://img.shields.io/badge/python-3.9%2B-yellow?style=flat-square" alt="Python Badge" />
  <img src="https://img.shields.io/badge/status-beta-orange?style=flat-square" alt="Status Badge" />
</p>

---

## 🌟 Features

- ✅ **Detect Active/Inactive WhatsApp Numbers**
- 🧠 **Intelligent Login Handling** (QR scan and session reuse)
- 🔀 **Concurrent Multi-Account Checking**
- 🛡️ **Proxy Support** (optional, per account)
- 🗃️ **Persistent Profiles** – saves WhatsApp login sessions
- 🕶️ **Headless Mode** – optional
- 🕓 **Customizable Delays** – mimic human-like behavior
- 📂 **Custom Config Support** (`whatschecker.config.json`)
- 📈 **Built with Selenium + Undetected ChromeDriver**
- 💥 **Auto dependency installs on first run**
- 📇 **Extracts valid WhatsApp numbers from saved contacts on the device**


---

## 🚀 Usage

### 1. 📦 Installation

```bash
git clone https://github.com/bitbytelab/WhatsChecker.git
cd WhatsChecker
chmod +x whatschecker.py
```

### 2. 🧪 First-time Setup (Scan QR)

```bash
./whatschecker.py --add-account
```

Scan the QR code to save your WhatsApp session. You can add multiple accounts this way.

---

### 3. 📤 Checking Numbers

Prepare an input file (e.g., `numbers.txt`) with **one number per line**:

```
+12025550123
+447911123456
+8801711123456
```

Run the checker:

```bash
./whatschecker.py --input numbers.txt --valid active.txt --invalid inactive.txt
```

You can also run in headless mode:

```bash
./whatschecker.py --input numbers.txt --valid active.txt --invalid inactive.txt --headless
```

---

### 4. 📇 Contacts Extraction

To extract valid WhatsApp numbers from your saved contacts:

```bash
python -m whatschecker --input contacts
```

This will:

1. Launch WhatsApp Web and log you in.
2. Open the "New Chat" sidebar to access all device contacts.
3. Incrementally scroll through the list and extract each visible contact.
4. Save valid WhatsApp numbers along with name, about, and avatar info to a CSV.

The generated CSV will be saved as:

```
valid_whatsapp_contacts_YYYY_mm_dd_HH_MM.csv
```

📁 Example output preview:

| name         | about                        | user_avatar                                     |
|--------------|------------------------------|-------------------------------------------------|
| 019xxxxxxxxx | Always learning               | https://media.whatsapp.net/...                  |
| 018xxxxxxxxx | Big brother watching you 😊   | default                                         |

📝 **Note:** Contact names must be saved as numbers (i.e., "017xxxxxxx") to work properly with this feature.



### 5. 🧩 Optional Arguments

| Flag            | Description                                      |
|-----------------|--------------------------------------------------|
| `--input`       | Input file with numbers                          |
| `--valid`       | Output file for active numbers                   |
| `--invalid`     | Output file for inactive numbers                 |
| `--delay`       | Base delay in seconds between number checks      |
| `--proxies`     | List of proxies (e.g., `http://ip:port`)         |
| `--headless`    | Run Chrome in headless mode                      |
| `--add-account` | Launch new profile and scan QR to add account    |

---

### 6. ⚙️ Config File Support

You can also define your settings in a `whatschecker.config.json` file:

```json
{
  "input": "numbers.txt",
  "valid": "active.txt",
  "invalid": "inactive.txt",
  "delay": 8,
  "proxies": ["http://127.0.0.1:8000", null]
}
```

Then just run:

```bash
./whatschecker.py
```

---

## 🔐 Session Management

Saved WhatsApp sessions are stored in:

```bash
./Profiles/account1
./Profiles/account2
...
```

Remove a folder to reset that session.

---

## 🧰 Dependencies

- Python `3.9+`
- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)
- [selenium](https://pypi.org/project/selenium)

📦 Auto-installs on first run if not found!

---

## ❓ FAQ

**Q: Will my WhatsApp account get banned?**  
A: This script mimics human behavior using real browser sessions and delays. Use proxies and multiple accounts to reduce risk. No API violations.

**Q: Is this open source?**  
A: Yes! MIT licensed. Use it responsibly and contribute back.

---

## 👨‍💻 Author

Made with ❤️ by [BitByteLab](https://github.com/bitbytelab)  
📧 Contact: [bbytelab@gmail.com](mailto:bbytelab@gmail.com)

---

## 📄 License

MIT License – see [LICENSE](LICENSE) file for details.

---

## ⭐️ Star this project

If you find this useful, please consider starring the repo!  
👉 [github.com/bitbytelab/WhatsChecker](https://github.com/bitbytelab/WhatsChecker)
