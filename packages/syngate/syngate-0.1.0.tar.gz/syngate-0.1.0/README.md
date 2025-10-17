---

# 🧩 SynGate: File-Based Queue, Scheduler, Batch Processor, and Mutex Locker for Python (Windows, macOS, Linux)

**SynGate** is a lightweight, cross-platform solution for managing access between multiple local Python processes or console scripts.  
It serves as a **queue manager, task scheduler, and mutex locker**, all using the local file system as its only backend.  
No threads, no networking, and no external services required.

Built on top of [`withopen`](https://pypi.org/project/withopen/) for reliable and atomic file-based control.

---

## ✅ Features

SynGate provides mechanisms to:

* 🚦 Queue tasks in order using session IDs
* ⏲️ Delay or skip processes based on time freshness (pulse)
* 🔐 Lock or block execution with `"Active"` tags
* ✅ Signal readiness with `"Done"` tags
* 🔒 Serve as a file-based **mutex lock** across terminals or scripts

Compatible with **Windows**, **macOS**, and **Linux**.

---

## 🔰 Basic Example: Run a Task When It Is Safe

```python
from syngate import enter, done

if enter("my_task", pulse=15):
    run_expensive_job()
    done("my_task")
```

### What this does:

* `enter()` checks if it is safe to run based on timing and queue state
* If safe, your task runs
* `done()` marks it as completed so others can proceed

---

## ⚙️ Parameters and Behavior

### 🧠 `pulse`: Freshness Timeout

The `pulse` defines how long an `"Active"` tag is considered fresh.
If a tag is older than the `pulse`, it is considered **stale**, allowing a new task to proceed.

```python
enter("data_export", pulse=20)
```

In this example, no other task can enter this gate for 20 seconds unless `done()` is called earlier.

---

### 🔄 `wait=True` (default): Wait Your Turn

The process waits until it is allowed to proceed.

```python
# Only one terminal trims logs; others wait
if enter("log_trim", pulse=10, wait=True):
    trim_logs()
    done("log_trim")
```

---

### 🕊 `wait=False`: Skip If Blocked

The process skips execution if the gate is held.
This is useful when you want one console to handle the task, but skip silently if another process is already doing it.

```python
# Multiple tabs open; only one should handle cleanup
if enter("log_trim", pulse=10, wait=False):
    trim_logs()
    done("log_trim")
else:
    print("Skipped. Another tab is already trimming.")
```

---

### 👁️ `display=True`: Show Status in Console

The `display` parameter controls whether status messages are printed to the console.

```python
if enter("my_task", pulse=12, display=True):
    do_something()
    done("my_task")
```

You will see messages like:

```
🧩 SYNGATE | LOADING 🟣 [12:01:03]
🧩 SYNGATE | QUEUING 🟡 [12:01:04]
🧩 SYNGATE | DEQUEUE 🟢 [12:01:07]
```

To run silently, set `display=False`:

```python
if enter("silent_task", pulse=10, display=False):
    run_silently()
    done("silent_task")
```

---

## ✅ Using `done()`: Signal Early Completion

By default, `pulse` controls how long others must wait.
If your task finishes early, call `done()` to release the gate immediately.

```python
if enter("fast_task", pulse=15):
    do_quick_thing()
    done("fast_task")  # Allow the next task to proceed without waiting 15 seconds
```

---

## 🔐 Using `active()`: Extend "I'm Busy" Signal

If your process is still working but has not re-entered the gate, use `active()` to manually signal that it is still in progress.

```python
# Prevent others from starting while work is still ongoing
active("data_load", pulse=12)
```

This delays others from entering until the `pulse` expires, acting like a soft lock.

---

## 🧠 Use Cases

* 🧪 Queueing batch tasks across Python scripts
* 🔒 Mutex locking using only the file system
* 🧼 Preventing overlapping jobs such as log trimming or backups
* 🕰️ Controlling time-spaced executions, with optional waiting or skipping

---

## 🛠 Console Output Indicators

| Icon | Meaning                                  |
| ---- | ---------------------------------------- |
| 🔴   | HOLDING. Waiting for a valid time window |
| 🟡   | QUEUING. Preparing to enter              |
| 🟢   | DEQUEUE. Successfully entered the gate   |
| ⚫    | FLYOVER. Skipped due to wait=False       |
| 🟣   | LOADING. Pre-checking conditions         |

These icons appear when `display=True` is enabled.

---

## 💡 Developer Note

> I created this tool to manage multiple bots and scripts that needed to run in order or avoid conflicts, such as editing a shared log.
> The `done()` function sped things up when I did not want to wait, and `active()` allowed me to hold the gate when work was still ongoing.
> It is simple, fast, and avoids unnecessary complexity by using just the file system.

---

## 📜 License

All Rights Reserved — Permission Required

Copyright (c) 2025 [henry]

This software is provided for viewing and educational purposes only.

Any form of reuse, reproduction, modification, distribution, or inclusion in other
projects or products (whether commercial or non-commercial) is strictly prohibited
without the prior **explicit written permission** of the author.

This includes, but is not limited to:
- Copying the source code into another project
- Reposting the code online or in packages
- Creating modified versions or forks
- Using the code in commercial tools, scripts, or libraries

To request permission, contact: [osas2henry@gmail.com]

By viewing or downloading this code, you agree to these terms.

---


