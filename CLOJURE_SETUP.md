# Clojure Setup for Strategify

This guide covers installing Clojure on Windows for the Strategify "Strategy Synthesizer" layer.

## Prerequisites

### 1. Install Java (JDK 21)

```powershell
winget install -e --id Oracle.JDK.21
```

Or download manually from: https://www.oracle.com/java/technologies/downloads/

Verify:
```powershell
java -version
```

### 2. Install Leiningen (Build Tool)

```powershell
winget install -e --id Technomancy.Leiningen
```

Or manually:
1. Download from: https://github.com/technomancy/leiningen/releases
2. Extract to `C:\leiningen`
3. Add to PATH: `C:\leiningen\bin`

Verify:
```powershell
lein version
```

### 3. VS Code Extension: Calva

Install **Calva** extension in VS Code:
- Open VS Code
- `Ctrl+Shift+X`
- Search "Calva"
- Install

## Project Structure

```
strategify-clj/
├── project.clj          # Leiningen config
├── src/
│   └── strategify/
│       └── core.clj    # Game theory logic
└── README.md
```

## Quick Start

### Terminal

```powershell
cd D:\GitHub\projects\Strategify\strategify-clj

# REPL
lein repl

# Run
lein run

# Test
lein test
```

### VS Code (Calva)

1. Open project in VS Code
2. `Ctrl+Alt+C` then `Ctrl+Alt+J` to start REPL
3. Evaluate code with `Ctrl+Enter`

## Python Integration

```python
from strategify.logic.clj import ClojureBridge

bridge = ClojureBridge()
result = bridge.execute_strategy("hawk", {"version": 0, "players": {}})
```

## Strategy Functions

```clojure
;; In core.clj
-:hawk (fn [state player]
       (if (dominates? state player (opponent player))
         :attack
         :retreat))

;; Available: hawk, dove, tit-for-tat, grudger, adaptive
```

## Timeline Branching

```clojure
;; Branch multiple futures
(s/branch-timelines state [:attack :display :retreat])

;; Compare outcomes
(s/compare-timelines timelines player score-fn)
```

## Troubleshooting

### Leiningen not found

Add to PATH:
```powershell
$env:PATH += ";C:\leiningen\bin"
```

### Port already in use

Kill existing REPL:
```powershell
Get-Process -Name java | Stop-Process
```

### Memory issues

Edit `project.clj`:
```clojure
:jvm-opts ["-Xmx2g"]
```