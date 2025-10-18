# hcom — Claude Hook Comms

[![PyPI - Version](https://img.shields.io/pypi/v/hcom)](https://pypi.org/project/hcom/)
 [![PyPI - License](https://img.shields.io/pypi/l/hcom)](https://opensource.org/license/MIT) [![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org) [![DeepWiki](https://img.shields.io/badge/DeepWiki-aannoo%2Fclaude--hook--comms-blue.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAyCAYAAAAnWDnqAAAAAXNSR0IArs4c6QAAA05JREFUaEPtmUtyEzEQhtWTQyQLHNak2AB7ZnyXZMEjXMGeK/AIi+QuHrMnbChYY7MIh8g01fJoopFb0uhhEqqcbWTp06/uv1saEDv4O3n3dV60RfP947Mm9/SQc0ICFQgzfc4CYZoTPAswgSJCCUJUnAAoRHOAUOcATwbmVLWdGoH//PB8mnKqScAhsD0kYP3j/Yt5LPQe2KvcXmGvRHcDnpxfL2zOYJ1mFwrryWTz0advv1Ut4CJgf5uhDuDj5eUcAUoahrdY/56ebRWeraTjMt/00Sh3UDtjgHtQNHwcRGOC98BJEAEymycmYcWwOprTgcB6VZ5JK5TAJ+fXGLBm3FDAmn6oPPjR4rKCAoJCal2eAiQp2x0vxTPB3ALO2CRkwmDy5WohzBDwSEFKRwPbknEggCPB/imwrycgxX2NzoMCHhPkDwqYMr9tRcP5qNrMZHkVnOjRMWwLCcr8ohBVb1OMjxLwGCvjTikrsBOiA6fNyCrm8V1rP93iVPpwaE+gO0SsWmPiXB+jikdf6SizrT5qKasx5j8ABbHpFTx+vFXp9EnYQmLx02h1QTTrl6eDqxLnGjporxl3NL3agEvXdT0WmEost648sQOYAeJS9Q7bfUVoMGnjo4AZdUMQku50McDcMWcBPvr0SzbTAFDfvJqwLzgxwATnCgnp4wDl6Aa+Ax283gghmj+vj7feE2KBBRMW3FzOpLOADl0Isb5587h/U4gGvkt5v60Z1VLG8BhYjbzRwyQZemwAd6cCR5/XFWLYZRIMpX39AR0tjaGGiGzLVyhse5C9RKC6ai42ppWPKiBagOvaYk8lO7DajerabOZP46Lby5wKjw1HCRx7p9sVMOWGzb/vA1hwiWc6jm3MvQDTogQkiqIhJV0nBQBTU+3okKCFDy9WwferkHjtxib7t3xIUQtHxnIwtx4mpg26/HfwVNVDb4oI9RHmx5WGelRVlrtiw43zboCLaxv46AZeB3IlTkwouebTr1y2NjSpHz68WNFjHvupy3q8TFn3Hos2IAk4Ju5dCo8B3wP7VPr/FGaKiG+T+v+TQqIrOqMTL1VdWV1DdmcbO8KXBz6esmYWYKPwDL5b5FA1a0hwapHiom0r/cKaoqr+27/XcrS5UwSMbQAAAABJRU5ErkJggg==)](https://deepwiki.com/aannoo/claude-hook-comms)

Launch multiple Claude Code terminals (or headless) that communicate together in real time via hooks.

![Demo](https://raw.githubusercontent.com/aannoo/claude-hook-comms/main/screencapture.gif)

## Start

#### Run without installing
```bash
uvx hcom 2
```

#### Install
```bash
pip install hcom   # or: uv tool install hcom
```

#### Use
```bash
claude 'run hcom start'
```


## What it does

`hcom` adds hooks then launches terminals with Claude Code that remain active, waiting to respond to messages. Normal `claude` remains unaffected by hcom, but can opt-in/out with `hcom start`/`hcom stop`. Safely remove hcom hooks with `hcom reset`. Works on Mac, Linux, Windows, Android.


## Commands

| Command | Description
|---------|-------------|
| `hcom <n>` | Launch `n` instances |
| `hcom watch` | Live dashboard and messaging |
| `hcom stop [alias\|all]` | Disable participation |
| `hcom start [alias]` | Enable participation |
| `hcom reset [logs\|hooks\|config]` | Safe Cleanup |



## Examples

#### Interactive subagents
```bash
# Claude Code subagents from .claude/agents
HCOM_AGENT=planner,code-writer,reviewer hcom 1
```

#### Persistent headless instances
```bash
hcom 1 claude -p    # default 30min timeout
hcom watch          # See what it's doing
hcom stop           # Let it die earlier than timeout
```

#### @-mention: groups and direct
```bash
HCOM_TAG=cooltag hcom 2
hcom send '@cooltag hi, you both are cool'
hcom send '@john you are cooler'
```

#### Toggle inside Claude Code
```bash
claude              # Normal Claude Code
'run hcom start'    # Opt-in to receive messages
'run hcom stop'     # Opt-out, continue as normal claude code
```


<details>
<summary><strong>All commands</strong></summary>

### `[ENV_VARS] hcom <COUNT> [claude <ARGS>]`


```bash
Usage: [ENV_VARS] hcom <COUNT> [claude <ARGS>...]
       hcom watch [--logs|--status|--wait [SEC]]
       hcom send "message"
       hcom stop [alias|all] [--force]
       hcom start [alias]
       hcom reset [logs|hooks|config]

Launch Examples:
  hcom 3             Open 3 terminals with claude connected to hcom
  hcom 3 claude -p                            + Background/headless
  HCOM_TAG=api hcom 3 claude -p               + @-mention group tag
  claude 'run hcom start'    claude code with prompt will also work

Commands:
  watch              Interactive messaging/status dashboard
    --logs           Print all messages
    --status         Print instance status JSON
    --wait [SEC]     Wait and notify for new message

  send "msg"         Send message to all instances
  send "@alias msg"  Send to specific instance/group

  stop               Stop current instance (from inside Claude)
  stop <alias>       Stop specific instance
  stop all           Stop all instances
    --force          Emergency stop (denies Bash tool)

  start              Start current instance (from inside Claude)
  start <alias>      Start specific instance

  reset              Stop all + archive logs + remove hooks + clear config
  reset logs         Clear + archive conversation log
  reset hooks        Safely remove hcom hooks from claude settings.json
  reset config       Clear + backup config.env

Environment Variables:
  HCOM_TAG=name      Group tag (creates name-* instances)
  HCOM_AGENT=type    Agent type (comma-separated for multiple)
  HCOM_TERMINAL=mode Terminal: new|here|print|"custom {script}"
  HCOM_PROMPT=text   "Say hi in hcom chat" (default)
  HCOM_HINTS=text    Text appended to all messages received by instance
  HCOM_TIMEOUT=secs  Time until disconnected from hcom chat (default 1800s / 30mins)

  ANTHROPIC_MODEL=opus # Passed through to Claude Code

  Persist Env Vars in `~/.hcom/config.env`

```
</details>

<details>
<summary><strong> Terminal Options</strong></summary>

### Default Terminals

- **macOS**: Terminal.app
- **Linux**: gnome-terminal, konsole, or xterm
- **Windows (native) & WSL**: Windows Terminal / Git Bash
- **Android**: Termux

### Terminal Mode

- `HCOM_TERMINAL=new` - New terminal windows (default)
- `HCOM_TERMINAL=here` - Current terminal window
- `HCOM_TERMINAL="open -a iTerm {script}"` - Custom terminal (**iTerm2**)


### Custom Terminal

Your custom command just needs to:
1. Accept `{script}` as a placeholder that will be replaced with a script path
2. Execute that script with bash

### Custom Terminal Examples

##### [ttab](https://github.com/mklement0/ttab) (new tab instead of new window in Terminal.app)
```bash
HCOM_TERMINAL="ttab {script}"
```

##### [wttab](https://github.com/lalilaloe/wttab) (new tab in Windows Terminal)
```bash
HCOM_TERMINAL="wttab {script}"
```

##### More
```bash
# Wave Terminal Mac/Linux/Windows. From within Wave Terminal:
HCOM_TERMINAL="wsh run -- bash {script}"

# Alacritty macOS:
HCOM_TERMINAL="open -n -a Alacritty.app --args -e bash {script}"

# Alacritty Linux:
HCOM_TERMINAL="alacritty -e bash {script}"

# Kitty macOS:
HCOM_TERMINAL="open -n -a kitty.app --args {script}"

# Kitty Linux
HCOM_TERMINAL="kitty {script}"

# tmux with split panes and 3 claude instances in hcom chat
HCOM_TERMINAL="tmux split-window -h {script}" hcom 3

# WezTerm Linux/Windows
HCOM_TERMINAL="wezterm start -- bash {script}"

# Tabs from within WezTerm
HCOM_TERMINAL="wezterm cli spawn -- bash {script}"

# WezTerm macOS:
HCOM_TERMINAL="open -n -a WezTerm.app --args start -- bash {script}"

# Tabs from within WezTerm macOS
HCOM_TERMINAL="/Applications/WezTerm.app/Contents/MacOS/wezterm cli spawn -- bash {script}"
```

#### Android (Termux)

```bash
#1. Install:
    Termux from F-Droid (not Google Play)
#2. Setup:
   pkg install python nodejs
   npm install -g @anthropic-ai/claude-cli
   pip install hcom
#3. Enable:
   echo "allow-external-apps=true" >> ~/.termux/termux.properties
   termux-reload-settings
#4. Enable: 
    "Display over other apps" permission for visible terminals
#5. Run: 
    `hcom 2`
```

---

</details>

## Requirements

- Python 3.10+
- Claude Code

## License

MIT

