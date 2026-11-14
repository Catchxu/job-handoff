# job-handoff

**English** | [简体中文](README.zh-CN.md)

An agent skill for Claude Code and Codex. Tell your agent "I have to go", close
the laptop, and your remote compute job keeps moving. Say "I'm back" and the
agent picks up where it left off.

It is for people who drive a lab server or an HPC cluster from a laptop: the
job runs over there, the agent runs over here, and the laptop has to leave.

## The problem

Closing the laptop loses three things:

| Lost | What it costs |
|---|---|
| **The job**, if the agent started it through its own connection | The run dies with the session. |
| **The agent's memory of what it was waiting for** | On return you explain again which job, where the log is, what counts as done, what comes next. |
| **The hours between the job ending and you returning** | The run finishes at 2 a.m. and the GPU idles until morning. Or the job waits five hours in a queue, crashes in two minutes on a typo, and you find out the next day. |

Cloud agent sessions do not help here: they cannot reach a private server
behind a bastion or a campus cluster.

## Two layers

job-handoff works at two layers. Layer 1 is the default. Layer 2 is opt-in.

| | Layer 1: Handoff | Layer 2: Wake |
|---|---|---|
| **What runs while you are away** | A small watcher script. No AI. | The watcher, plus an AI agent that is started when the job chain ends and exits when it is done. |
| **What you get** | The job survives. A handoff record (notes, state, logs) lets any session resume. A **playbook** written before you leave carries out fixed rules: "on success run the evaluation", "on out-of-memory rerun with half the batch size". Results can be prefetched and a notification sent. On return, one command reports everything and collects the results; if the job is still running, the agent takes over again. | Judgment while you are away. In `report` mode the agent reads the notes, the outcome and the log and writes a report. In `act` mode it can also inspect the compute host and request a follow-up run. |
| **What it needs** | SSH access to the compute host. Nothing is installed there by hand. | Layer 1, plus Claude Code or Codex installed and logged in on the machine where the watcher runs, in a region the provider serves. |
| **Risk** | A wrong playbook rule wastes compute. | An unattended agent with shell access. See the warnings. |

Layer 1 covers what you can foresee. Layer 2 covers what you cannot.

## How it works

```
your machine                 watch host                         compute host
(agent + handoff)            (compute host itself, or a relay)  (SSH server / SLURM)

handoff launch  ───────────────────────────────────────────────▶ job starts detached
handoff leave   ──▶ watcher starts ──── checks state ──────────▶ job ends
                     │  runs the playbook ─────────────────────▶ follow-up run (optional)
   laptop closed     │  Layer 2: wakes the agent, saves its report
                     │  prefetches results, sends a notification
handoff back    ──▶ report + results; a watcher still waiting is stopped
```

The watcher runs on the compute host by default. A separate **relay** (any
small always-on Linux machine) is needed only when the compute host forbids
long-running processes, or when Layer 2 is wanted and the compute host cannot
run the agent. For Layer 1 a relay can be located anywhere.

## Install

```bash
git clone https://github.com/Catchxu/job-handoff.git
```

```bash
./job-handoff/install.sh
```

`install.sh` links the skill into `~/.claude/skills` (Claude Code) and
`~/.agents/skills` (Codex), and links the `handoff` command into `~/.local/bin`.

Requirements: `bash`, `ssh` and `rsync` on your machine; `bash`, `nohup` and
`setsid` on the remote hosts (standard on Linux).

## Use

Talk to your agent. The skill tells it what to do.

| You say | The agent does |
|---|---|
| "Set up job-handoff for my server `lab`" | Asks a few questions (hosts, relay, notification, Layer 2), writes the configuration, runs `handoff doctor`. |
| "Start the training on `lab`" | Starts it with `handoff launch`, so it survives the session. |
| "I have to go" | Writes the handoff notes, proposes a playbook for your approval, runs `handoff leave`, and tells you what will and will not happen while you are away. |
| "I'm back" | Runs `handoff back`, reads the report, collects the results, and continues the work. |

The same from a shell:

```bash
handoff init
handoff host add lab                       # detects SLURM by itself
handoff doctor

handoff launch --host lab --name bert-ft --dir ~/proj --cmd 'python train.py'
# ... write the notes file printed by: handoff notes <id>
handoff leave <id> --playbook playbook.sh --fetch out/metrics.json --into ./results
handoff back
```

Details: [configuration](skills/job-handoff/references/configuration.md),
[playbooks](skills/job-handoff/references/playbook.md).

## Warnings

> [!WARNING]
> **Layer 1**
> - A playbook runs commands on the compute host with nobody watching. A wrong
>   rule burns GPU hours or allocation. The attempt cap (`MAX_ATTEMPTS`,
>   default 3) is the only brake.
> - The watcher is a long-running process. Some clusters forbid those on login
>   nodes. Check your site's policy or use a relay.
> - A relay holds an SSH key that reaches your compute host. Create a dedicated
>   key on the relay, never copy your personal private key there, and follow
>   the access rules of your lab or cluster. Whoever controls the relay
>   controls that account.
> - Results prefetched to a relay are stored on it. Do not prefetch data that
>   must not leave the compute site.
> - Messages sent to public notification services can be read by anyone who
>   knows the topic.
> - Nothing thinks in Layer 1. A failure the playbook did not foresee waits
>   until you return.

> [!CAUTION]
> **Layer 2**
> - In `act` mode an AI agent runs shell commands on your compute host with
>   nobody watching. It can do anything your SSH account can do, including
>   deleting data and using up your allocation. Start with `report` mode.
> - The agent reads job logs. Text in a log can steer an agent (prompt
>   injection). Do not use `act` mode on jobs that process untrusted input.
> - The agent's login token is stored on the watch host. Anyone with access to
>   that host can use your Claude or Codex account.
> - Each wake uses your subscription or API credit without you seeing it.
> - The agent sees only the handoff notes, the log tail and the playbook
>   output, not your conversation.
> - Running an AI agent on a shared cluster login node may violate site policy.

## Status

Version 0.1.0.

| Part | Tested |
|---|---|
| Plain SSH host: launch, leave, playbook follow-ups, return, fetch | On real servers, one of them behind a bastion |
| SLURM: launch, playbook follow-up, cancel, adopt, return, fetch | On a real cluster (SLURM 25.11) |
| Layer 2 `report` mode | With real Claude Code and real Codex |
| Relay | In a simulation only |
| Layer 2 `act` mode | In a simulation only, not yet with a real agent |
| macOS as the local machine | Not tested |

## Limits

- Jobs on your own machine stop with it; no handoff is possible.
- A job that was not started detached cannot be rescued. Start jobs with `handoff launch`.
- SLURM job arrays and other schedulers (PBS, LSF) are not supported.

## License

MIT
