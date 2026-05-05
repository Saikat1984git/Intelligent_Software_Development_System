---
name: windows-powershell-skill
description: Use this skill for using Windows PowerShell. It provides explicit instructions on essential PowerShell commands for everyday file management, navigation, and data manipulation (the equivalents of common Linux commands).
license: MIT
---

# Agent Skill: Windows PowerShell Execution

## Skill Overview
You are equipped to execute Windows PowerShell commands. This skill allows you to navigate the file system, manage files, and search text using PowerShell equivalents of common Linux/Unix shell commands.

## Strict Execution Rules
When generating PowerShell commands, you **must** adhere to the following constraints for headless execution:
* **No Interactive Commands:** NEVER use cmdlets that prompt for user input (e.g., `Read-Host`).
* **Force Quiet Execution:** Always use `-Force` and `-Confirm:$false` when modifying or deleting files.
* **Structured Output:** Pipe data-gathering commands to JSON using `| ConvertTo-Json -Compress -Depth 5` to ensure parsable results.

---

## The "Linux-to-PowerShell" Cheat Sheet
PowerShell natively includes aliases for most common Linux commands, meaning you can often just use the Linux command name. Here is the translation guide:

| Linux Command | PowerShell Cmdlet | Built-in Alias | Purpose | Example |
| :--- | :--- | :--- | :--- | :--- |
| `pwd` | `Get-Location` | `pwd`, `gl` | Print working directory. | `pwd` |
| `cd` | `Set-Location` | `cd`, `sl` | Change directory. | `cd C:\Logs` |
| `ls` / `ll` | `Get-ChildItem` | `ls`, `dir` | List directory contents. Supports globbing natively (`*`, `?`). | `ls *.txt` |
| `cat` | `Get-Content` | `cat`, `gc` | Read a file's contents. | `cat config.json` |
| `grep` | `Select-String` | `sls` | Search text using regular expressions. | `ls | sls "Error"` |
| `rm` | `Remove-Item` | `rm`, `del` | Remove files or directories. | `rm old_file.txt -Force` |
| `cp` | `Copy-Item` | `cp`, `copy` | Copy files or directories. | `cp app.js backup.js` |
| `mv` | `Move-Item` | `mv`, `move` | Move or rename files. | `mv file.txt ./archive/` |
| `mkdir`/`touch`| `New-Item` | `md`, `ni` | Create a new directory or file. | `ni newfile.txt` |
| `ps` | `Get-Process` | `ps` | List running processes. | `ps node` |
| `kill` | `Stop-Process` | `kill` | Terminate a process. | `kill -Name node -Force` |
| `curl`/`wget` | `Invoke-WebRequest`| `curl`, `wget` | Fetch data from a URL. | `curl http://localhost:8080` |
| `clear` | `Clear-Host` | `clear`, `cls`| Clear the terminal screen. | `clear` |