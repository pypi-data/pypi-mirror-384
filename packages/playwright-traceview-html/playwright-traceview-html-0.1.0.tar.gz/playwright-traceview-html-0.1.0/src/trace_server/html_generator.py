
import os
import webbrowser
import http.server
import socketserver
import subprocess
import threading
from urllib.parse import urlparse, parse_qs

PORT = 8008
RESULTS_DIRECTORY = "test-results"
REPORT_FILENAME = "html_report.html"


def create_html_and_start_server(folder_path: str, output_filename: str):
    """
    Scans a folder, creates an HTML report, and starts a local server
    that can be shut down from the report itself.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: Directory not found at '{folder_path}'")
        return

    try:
        files = [f for f in os.listdir(folder_path) if f.startswith("trace_") and f.endswith(".zip")]
        files.sort()

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>Test Automation Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px; background-color: #f4f7f9; }}
        .container {{ max-width: 900px; margin: 0 auto; background-color: #ffffff; padding: 20px 40px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
        h1 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; }}
        a {{ text-decoration: none; color: #007bff; font-weight: 500; }}
        .status-passed {{ color: #28a745; font-weight: bold; }}
        .status-failed {{ color: #dc3545; font-weight: bold; }}
        .footer {{ margin-top: 30px; text-align: center; }}
        .stop-button {{ padding: 10px 20px; font-size: 14px; font-weight: 600; color: #fff; background-color: #dc3545; border: none; border-radius: 5px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Automation Report</h1>
        <table>
            <thead><tr><th>Test Case Name</th><th>Result</th><th>Trace View</th></tr></thead>
            <tbody>
"""
        if not files:
            html_content += '<tr><td colspan="3">No test results found.</td></tr>'
        else:
            for filename in files:
                test_name = filename.split('test_')[-1].split('.zip')[0]
                status = test_name.split('_')[-1]
                link = f'<a href="http://localhost:{PORT}/run_trace?file={filename}" target="_blank">Open Trace</a>'
                html_content += f'<tr><td>{test_name.split('[')[0]}</td><td class="status-{status.lower()}">{status.capitalize()}</td><td>{link}</td></tr>'

        html_content += """
            </tbody>
        </table>
        <div class="footer">
            <button class="stop-button" onclick="stopServer()">Stop Report Server</button>
        </div>
    </div>
    <script>
        function stopServer() {
            fetch('/shutdown');
            document.body.innerHTML = '<h1>Server has been stopped. You can close this window.</h1>';
        }
    </script>
</body>
</html>"""

        output_path = os.path.join(folder_path, output_filename)
        with open(output_path, "w") as f:
            f.write(html_content)
        print(f"✅ HTML report created at: {output_path}")

    except Exception as e:
        print(f"An error occurred during report generation: {e}")
        return

    class CommandServer(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=folder_path, **kwargs)

        def do_GET(self):
            parsed_path = urlparse(self.path)
            if parsed_path.path == '/run_trace':
                # ... (this part is unchanged)
                query = parse_qs(parsed_path.query)
                filename = query.get('file', [None])[0]
                if filename:
                    file_path = os.path.join(folder_path, filename)
                    if os.path.exists(file_path):
                        command = ["playwright", "show-trace", file_path]
                        subprocess.Popen(command)
                        self.send_response(200)
                        self.send_header("Content-type", "text/html")
                        self.end_headers()
                        self.wfile.write(b"<html><body>Trace command sent! You can close this tab.</body></html>")
                    else:
                        self.send_error(404, "Trace file not found.")
                else:
                    self.send_error(400, "Missing 'file' parameter.")

            elif parsed_path.path == '/shutdown':
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"Server is shutting down.")

                def shutdown():
                    httpd.shutdown()
                    httpd.server_close()

                threading.Thread(target=shutdown).start()

            else:
                super().do_GET()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CommandServer) as httpd:
        report_url = f"http://localhost:{PORT}/{output_filename}"
        print(f"\n--- Starting interactive report server ---")
        print(f"✅ Server is running. Open your report here:\n   {report_url}")
        print("\nWhen you are finished, click the 'Stop Report Server' button in the report.")

        webbrowser.open(report_url)
        httpd.serve_forever()
        print("\nServer has been shut down.")


def main():
    target_folder = os.path.join(os.getcwd(), RESULTS_DIRECTORY)
    if not os.path.exists(target_folder):
        raise FileNotFoundError(f"Results directory '{target_folder}' not found.")
    create_html_and_start_server(target_folder, REPORT_FILENAME)

