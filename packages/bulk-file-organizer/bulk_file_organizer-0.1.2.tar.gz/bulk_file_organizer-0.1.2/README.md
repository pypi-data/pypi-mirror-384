# 🗂️ Bulk File Organizer

**Bulk File Organizer** is a Python command-line tool that automatically sorts files in a directory based on their file extensions. It organizes your digital chaos into clean, structured folders — with colorful terminal feedback powered by **Rich** ✨

---

## 🚀 Features

- 📦 Automatically categorizes files into folders (Images, Documents, Archives, etc.)
- 💡 Smart handling for unknown extensions (goes into `Others`)
- 🧩 Configurable via `pyproject.toml`
- 🌈 Beautiful CLI output using [Rich](https://github.com/Textualize/rich)
- 🧪 Dry-run mode to preview changes before organizing
- 📊 Summary table after organization
- 🪄 Recursive scanning of subdirectories

---

## ⚙️ Installation

```bash
pip install bulk-file-organizer
```

Or install from source:

```bash
git clone https://github.com/Shravan250/bulk-file-organizer.git
cd bulk-file-organizer
pip install .
```

---

## 🖥️ Usage

```bash
bulk-organizer /path/to/your/folder
```

### Options

| Flag          | Description                                |
| ------------- | ------------------------------------------ |
| `--dry-run`   | Simulate organization without moving files |
| `--summary`   | Show summary table at the end              |
| `--recursive` | Recursively organize subdirectories        |
| `--version`   | Show current version                       |

Example:

```bash
bulk-organizer ~/Downloads --dry-run --summary
```

---

## 🧠 Example Output

```text
──────────────────────────── Bulk Organizer v0.1.0 ─────────────────────────────
Target Directory: ~/Downloads

Dry Run Mode Enabled — no files will be moved.

✨ Organizing files... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:02

📊 Organization Summary

┏━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Folder    ┃ File Count ┃ Example Files                ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Images    │ 12         │ photo.png, logo.jpg, …       │
│ Documents │ 8          │ resume.pdf, notes.txt, …     │
│ Archives  │ 2          │ backup.zip, logs.tar.gz      │
└───────────┴────────────┴──────────────────────────────┘
──────────────────────────── Operation Complete ─────────────────────────────
```

---

## 🧩 Project Structure

```
bulk-file-organizer/
│
├── bulk_organizer/
│   ├── __init__.py
│   ├── cli.py
│   ├── scanner.py
│   ├── mapper.py
│   ├── organizer.py
│
├── tests/
│
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

---

## 🧑‍💻 Contributing

We love clean code and clever minds. Check out [CONTRIBUTING.md](CONTRIBUTING.md) to learn how you can contribute to this project.

---

## 🪪 License

This project is licensed under the **MIT License**.

---

## ⭐ Show Some Love

If this tool helped you bring order to your chaos —
please consider giving it a ⭐ on [GitHub](https://github.com/Shravan250/bulk-file-organizer)!
Every star helps this project grow and makes the world a little more organized 🌍✨
