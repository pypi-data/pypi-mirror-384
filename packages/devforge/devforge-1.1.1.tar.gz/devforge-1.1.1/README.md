🧱 DevForge

DevForge is a lightweight command-line tool that helps developers quickly scaffold custom project hierarchies — ideal for bootstrapping new apps, APIs, or full-stack projects with your own structure.

You define the structure, and DevForge handles the rest.
Templates and advanced automation features will be added in future releases.

🚀 Features

⚙️ Custom hierarchy generation – create your own directory & file structure interactively or via configuration.

📂 Recursive project creation – supports multi-level directories.

🧾 Automatic README + main file setup – starts your project with key files in place.

🪶 Lightweight and dependency-free – pure Python, no external packages required.

🧠 Future-ready – template-based scaffolding and AI integration are planned for later versions.

📦 Installation
pip install devforge

⚡ Quick Start

Run the CLI to create a new project:

devforge create myproject


Use the --debug flag to see detailed logs:

devforge create myproject --debug


Your new project will be created under the current directory with a clean, organized structure.

🧰 Example Output
[INFO] ✅ Project created at: D:\MoneyProjects\TestArea\myproject


Project structure example:

myproject/
├── backend/
│   ├── main.py
│   ├── routes/
│   └── models/
├── frontend/
│   ├── src/
│   └── App.jsx
└── README.md

🧩 Coming Soon

📦 Built-in templates (FastAPI, Flask, React, etc.)

🧠 AI-assisted project setup

🧱 Config-driven hierarchy definitions

🐳 Dockerized scaffolding

💡 Why DevForge?

Because setting up a new project shouldn’t take longer than coding it.
DevForge helps you focus on building, not boilerplate.

🪪 License

MIT License © 2025 Hythm