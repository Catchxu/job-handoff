# Configuration

Everything lives in `~/.job-handoff/` on the user's machine:

```
~/.job-handoff/
  config               global settings (below)
  hosts/<alias>.conf   one profile per compute host, written by `handoff host add`
  jobs/<id>/           one record per handoff: job.conf, notes.md, watch.conf, phase
```

On a compute host or relay, `~/.job-handoff/` holds the copied script
(`bin/handoff`) and one folder per handoff with logs, exit codes, the playbook,
the watcher log and reports. Delete a handoff's folder when it is no longer needed.

## Global settings: `~/.job-handoff/config`

Created by `handoff init`. It is a bash file.

| Key | Default | Meaning |
|---|---|---|
| `POLL_SECONDS` | `60` | How often the watcher checks the job. |
| `MAX_ATTEMPTS` | `3` | Runs per handoff: the first one plus follow-ups from the playbook or the agent. |
| `LOG_TAIL` | `200` | Log lines kept for the report and the wake brief. |
| `NOTIFY_CMD` | empty | Command run on the watch host when a handoff ends. `$1` is a one-line message. |
| `WAKE_MODE` | `report` | Layer 2 mode: `report` or `act`. |
| `WAKE_CMD` | empty | Layer 2 command, run on the watch host. Empty means Layer 2 cannot be used. |

Settings are copied to the watch host at `handoff leave`; a change applies to
the next handoff.

### Notification commands

```bash
# ntfy (use a long random topic; anyone who knows it can read the messages)
NOTIFY_CMD='curl -fsS -d "$1" https://ntfy.sh/your-long-random-topic'

# Bark (iOS)
NOTIFY_CMD='curl -fsS https://api.day.app/push -H "Content-Type: application/json" -d "{\"device_key\":\"YOUR_KEY\",\"body\":\"$1\"}"'

# Feishu / Lark bot webhook
NOTIFY_CMD='curl -fsS -H "Content-Type: application/json" -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$1\"}}" https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN'
```

The watch host must be able to reach the service.

## Host profiles: `handoff host add`

```bash
handoff host add <alias> [--scheduler none|slurm] [--relay <alias>]
                 [--relay-compute <alias>] [--fetch-cmd CMD] [--relay-fetch-cmd CMD]
```

| Option | Meaning |
|---|---|
| `<alias>` | The compute host, as named in the user's SSH config. Login must work without a prompt. |
| `--scheduler` | `none` for a plain server, `slurm` for a cluster. Detected when omitted (`sbatch` present means `slurm`). |
| `--relay` | SSH alias of the relay, as seen from the user's machine. Omit to run the watcher on the compute host. |
| `--relay-compute` | The compute host's alias in the relay's own SSH config. Defaults to the same alias. |
| `--fetch-cmd` | Command that copies results from the compute host to the user's machine. Default `rsync -az {host}:{remote} {local}/`. Placeholders: `{host}`, `{remote}`, `{local}`. |
| `--relay-fetch-cmd` | The same, run on the relay to prefetch results. `none` skips the prefetch: results then come straight from the compute host at `handoff back`. |

Run `handoff host add` again to change a profile. `handoff doctor` checks every
profile; fix each `FAIL` before the first handoff.

### Hosts where rsync does not work

Some bastions allow neither rsync nor scp. Give the profile the site's own
transfer command, for example `--fetch-cmd 'mytransfer get {remote} {local}'`.
With a relay, either install the same tool on the relay (`--relay-fetch-cmd`)
or pass `--relay-fetch-cmd none` to skip the prefetch.

### Clusters with two-factor login

`handoff` cannot answer prompts. Let SSH reuse one authenticated connection:

```
Host hpc
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 12h
```

Log in once by hand; later calls reuse that connection until it expires. The
watcher runs on the login node and needs no SSH of its own. A relay cannot pass
a two-factor prompt, so such a cluster works with a relay only if it also
accepts key-only logins.

## Setting up a relay

A relay is any always-on Linux machine with `ssh`, `rsync`, `nohup` and
`setsid`. No root is needed, and for Layer 1 it can be anywhere.

1. On the relay, create a dedicated key: `ssh-keygen -t ed25519 -f ~/.ssh/handoff_ed25519`.
   Never copy a personal private key to the relay.
2. Authorize the new public key on the compute host, through whatever process
   the lab or cluster requires.
3. On the relay, add a `Host` entry for the compute host to `~/.ssh/config`
   using that key, and log in once by hand to accept the host key.
4. On the user's machine: `handoff host add <alias> --relay <relay alias>`,
   then `handoff doctor <alias>`. The line `<relay> -> <alias>: login without
   a prompt` must say ok.

With a relay, results named by `--fetch` are copied to the relay as soon as the
handoff ends and to the user's machine at `handoff back`. Check the relay's
free disk space against the size of the results.

## Layer 2: the wake command

`WAKE_CMD` runs on the watch host, in the handoff's folder, when the job chain
ends. The brief is the file `$HANDOFF_BRIEF`; whatever the command prints is
saved as the wake report.

Requirements on the watch host:

- Claude Code or Codex installed, and the host located where the provider
  offers service.
- Logged in. Claude Code: run `claude setup-token` on a machine with a browser
  and export the token on the watch host, or log in once interactively there.
  Codex: `codex login --device-auth`.
- The watcher runs in a non-interactive shell that does not read `~/.bashrc`.
  The native Claude Code installer puts `claude` in `~/.local/bin`, which is
  not on that shell's `PATH`: start the command with
  `export PATH=$HOME/.local/bin:$PATH;`. Tokens and other variables can go in
  a file on the watch host (`chmod 600`) that the command sources first:
  `WAKE_CMD='. ~/.job-handoff/agent.env; claude -p ...'`.

`report` mode, the agent has no tools:

```bash
WAKE_MODE=report
# Claude Code
WAKE_CMD='claude -p "$(cat "$HANDOFF_BRIEF")" --tools ""'
# Codex
WAKE_CMD='codex exec --sandbox read-only --skip-git-repo-check "$(cat "$HANDOFF_BRIEF")"'
```

`act` mode, the agent may run commands. Read the Layer 2 warnings in `SKILL.md`
with the user first.

```bash
WAKE_MODE=act
# Claude Code on a relay: shell access limited to ssh into the compute host
WAKE_CMD='claude -p "$(cat "$HANDOFF_BRIEF")" --allowedTools "Bash(ssh lab *)" "Read" "Write"'
# Claude Code on the compute host itself: unrestricted shell
WAKE_CMD='claude -p "$(cat "$HANDOFF_BRIEF")" --allowedTools "Bash" "Read" "Write"'
# Codex: ssh needs network access, which only the unsandboxed mode gives
WAKE_CMD='codex exec --sandbox danger-full-access --skip-git-repo-check "$(cat "$HANDOFF_BRIEF")"'
```

Replace `lab` with the compute host's alias on the relay. In `act` mode the
agent requests a follow-up run by writing its command into `./next_cmd`; the
watcher starts and follows it, within `MAX_ATTEMPTS`.

`handoff doctor` does not run the wake command. Test it once by hand, in the
same non-interactive shell the watcher uses:
`ssh <watch host> 'export PATH=$HOME/.local/bin:$PATH; claude -p "say ok" --tools ""'`.
