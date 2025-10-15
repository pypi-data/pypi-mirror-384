import sys
import platform
import pkg_resources
import os
import datetime
import html
import socket
import multiprocessing

def pyinfo():
    coretextweb = os.getenv("CORETEXTWEB")
    coretextweb_value = html.escape(coretextweb) if coretextweb else "Змінна CORETEXTWEB не встановлена."

    # Отримуємо локальну IP і хост
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        hostname = "Невідомо"
        local_ip = "Невідомо"

    # Встановлені бібліотеки
    libs = sorted([f"{d.project_name} {d.version}" for d in pkg_resources.working_set])

    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Python Info</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

            body {{
                font-family: 'JetBrains Mono', monospace;
                background: radial-gradient(circle at top, #0c0c0c, #040404);
                color: #d8d8d8;
                padding: 20px;
                margin: 0;
                line-height: 1.6;
            }}
            header {{
                position: sticky;
                top: 0;
                background: rgba(0, 0, 0, 0.9);
                backdrop-filter: blur(8px);
                padding: 15px 0;
                margin-bottom: 20px;
                border-bottom: 2px solid #0f0;
                text-align: center;
                font-size: 26px;
                color: #0f0;
                letter-spacing: 1px;
                box-shadow: 0 0 10px #0f0;
                text-shadow: 0 0 6px #0f0;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-top: 10px;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 0 25px rgba(0, 255, 100, 0.1);
                animation: fadeIn 1s ease-in-out;
            }}
            th {{
                background: linear-gradient(90deg, #0f0, #0b5);
                color: #000;
                text-align: left;
                padding: 10px;
                font-weight: 700;
            }}
            td {{
                border-top: 1px solid #222;
                padding: 8px 12px;
                transition: background 0.25s;
            }}
            tr:hover td {{
                background: rgba(0, 255, 100, 0.07);
            }}
            ul {{
                list-style-type: none;
                padding: 0;
                columns: 2;
                column-gap: 40px;
                animation: fadeInUp 1.2s ease-in-out;
            }}
            li {{
                background: #0a0a0a;
                border: 1px solid #222;
                margin: 5px 0;
                padding: 6px 10px;
                border-radius: 6px;
                transition: all 0.3s ease;
            }}
            li:hover {{
                background: #111;
                border-color: #0b5;
                transform: scale(1.02);
            }}
            h2 {{
                color: #0b5;
                border-left: 5px solid #0f0;
                padding-left: 10px;
                margin-top: 40px;
            }}
            a {{
                color: #0f0;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(-10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes fadeInUp {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            footer {{
                margin-top: 40px;
                text-align: center;
                font-size: 13px;
                color: #777;
                border-top: 1px solid #222;
                padding-top: 10px;
            }}
        </style>
    </head>
    <body>
        <header>Python Info Dashboard</header>

        <table>
            <tr><th>Property</th><th>Value</th></tr>
            <tr><td>Python version</td><td>{platform.python_version()}</td></tr>
            <tr><td>Implementation</td><td>{platform.python_implementation()}</td></tr>
            <tr><td>Build</td><td>{platform.python_build()}</td></tr>
            <tr><td>Compiler</td><td>{platform.python_compiler()}</td></tr>
            <tr><td>Platform</td><td>{platform.platform()}</td></tr>
            <tr><td>Architecture</td><td>{platform.architecture()[0]}</td></tr>
            <tr><td>System</td><td>{platform.system()} {platform.release()}</td></tr>
            <tr><td>Machine</td><td>{platform.machine()}</td></tr>
            <tr><td>Processor</td><td>{platform.processor()}</td></tr>
            <tr><td>CPU Cores</td><td>{multiprocessing.cpu_count()}</td></tr>
            <tr><td>Hostname</td><td>{hostname}</td></tr>
            <tr><td>Local IP</td><td>{local_ip}</td></tr>
            <tr><td>Working Directory</td><td>{os.getcwd()}</td></tr>
            <tr><td>Current Time</td><td>{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td></tr>
            <tr><td>CORETEXTWEB</td><td>{coretextweb_value}</td></tr>
        </table>

        <h2>Installed Packages</h2>
        <ul>
            {''.join(f'<li>{lib}</li>' for lib in libs)}
        </ul>

        <footer>Generated automatically by CoreTextWeb Python Engine</footer>
    </body>
    </html>
    """
    return html_content
