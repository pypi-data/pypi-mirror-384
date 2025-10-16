# Playwright-TraceView-HTML

A lightweight Python tool that scans your Playwright test results, generates a clean HTML dashboard, and starts a local interactive server to view traces — with a one-click stop button.

## 🚀 Features
- Auto-discovers all `trace_*.zip` Playwright traces
- Generates an HTML summary report
- Lets you open each trace in Playwright Viewer (`playwright show-trace`)
- Runs a lightweight local server with stop button
- Works on Windows, macOS, and Linux


---

## 💻 Installation

```bash
pip install playwright-traceview-html
```
---



: Usage :
---------

Run this command from your Playwright project root (after test run):

playwright-traceview-html

It will look for your `test-results/` folder then generate `html_report.html` opens the dashboard in your browser automatically



You’ll see something like:

✅ HTML report created at: `test-results/html_report.html`

✅ Server running on `http://localhost:8008/html_report.html`


Output:

<img width="1740" height="1014" alt="image" src="https://github.com/user-attachments/assets/b9e6a1cf-46ed-4d50-8b16-d0340070d473" />
<img width="1740" height="1014" alt="image" src="https://github.com/user-attachments/assets/f0d9a389-0f21-4e45-82cd-808643dbbe4d" />


---

🪪 License

MIT License © 2025 JAYA KRISHNA

---

