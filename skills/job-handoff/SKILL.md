---
name: job-handoff
description: Hand a long-running remote compute job (plain SSH server or SLURM cluster) to a watcher before the user closes their laptop, and pick it up when they return. Use when the user is about to leave while a remote training or analysis job is running or queued ("I have to go", "hand it off", "keep it going while I'm away", 我要走了, 交接一下, 帮我盯着, 交给服务器), when they come back ("I'm back", "what happened", 回来了, 结果怎么样), and whenever you are about to start a job on a remote host that should outlive this session. Also covers first-time setup and the optional unattended agent. Not for jobs that run on the user's own machine.
---

# job-handoff

When the user's laptop closes, three things are lost: jobs started through the
session's own connection, the session's knowledge of what it was waiting for,
and the hours between the job ending and the user returning. This skill keeps
all three, with one command-line tool, `handoff`.

`handoff` is `scripts/handoff` in this skill's folder (`install.sh` links it
onto the PATH). It copies itself to the remote hosts it uses; nothing else is
installed there.

Three machines are involved:

- **your machine**: where you and the user work.
- **compute host**: where the job runs. An SSH alias from the user's SSH config.
- **watch host**: where the watcher runs while the user is away. By default the
  compute host itself; optionally a **relay**, a small always-on server.

## The two layers

Always tell the user which layer a handoff uses.

| | Layer 1: Handoff | Layer 2: Wake |
|---|---|---|
| What runs while the user is away | A small watcher script. No AI. | The watcher, plus an AI agent started when the job chain ends. |
| What it does | Keeps the job alive, follows it, runs the playbook written before leaving (fixed rules such as "on success run eval", "on out-of-memory rerun with a smaller batch"), prefetches results, notifies. | Reads the notes, the outcome and the log, then writes a report (`report` mode) or also inspects the compute host and requests a follow-up run (`act` mode). |
| Needs | SSH access to the compute host. | Layer 1, plus Claude Code or Codex installed and logged in on the watch host, in a region the provider serves. |
| Default | On. | Off. Enabled only after the user has read the warnings and said yes. |

## Rules

1. Start every remote job that should outlive the session with `handoff launch`.
   A job started through a foreground `ssh` or your own background task dies
   with the laptop and cannot be handed off afterwards.
2. Before the first handoff with a playbook, a relay, or Layer 2, show the user
   the matching warnings from the Warnings section, in their language, and get
   an explicit yes. Do not paraphrase them into something milder.
3. Show the user the playbook you wrote and get a go-ahead before `handoff leave`.
   It will run unattended.
4. Write the handoff notes before leaving. They are the only memory that
   survives: the session that returns may have lost its context, and a woken
   agent knows nothing else.

## First use: configuration

Run `handoff host list`. If the compute host is not listed, do the setup. Ask
the user only what you cannot find out yourself:

1. **Compute hosts**: which SSH aliases, and for each, plain server or SLURM
   (`handoff host add` detects SLURM by itself).
2. **Relay**: needed only when the watcher cannot live on the compute host (the
   site forbids long-running processes on the login node) or when Layer 2 is
   wanted and the compute host cannot run the agent. Otherwise no relay.
3. **Phone notifications**: none, ntfy (built in), or another push service.
   They are one-way status messages: a queued job starts, a follow-up run
   starts, the compute host is unreachable, the handoff ends with its result.
   For ntfy, generate the topic yourself (`echo "jh-$(openssl rand -hex 10)"`),
   set `NTFY_TOPIC`, give the topic to the user to subscribe to in the app, and
   run `handoff notify-test <alias>` once they have.
4. **Layer 2**: off, `report`, or `act`, and with which agent. Show the Layer 2
   warnings before the user answers.

Then:

```bash
handoff init                                  # writes ~/.job-handoff/config
handoff host add <alias> [--relay <alias>]    # one per compute host
handoff doctor                                # every line must say ok
```

Edit `~/.job-handoff/config` for notifications and the wake command. Prefer the
built-in ntfy setting; write `NOTIFY_CMD` and `WAKE_CMD` only in the forms given
in the reference, which keep tokens, log lines and the brief out of process
lists that every user of a shared host can read. All keys,
the relay setup, hosts that need a custom transfer command, clusters with
two-factor login, and ready-made wake commands for Claude Code and Codex are in
`references/configuration.md`. Read it before writing the config.

## Launching a job

```bash
# plain server: the command runs detached, its exit code is recorded
handoff launch --host lab --name bert-ft --dir ~/proj --cmd 'source ~/venv/bin/activate && python train.py --bs 256'

# SLURM: the arguments go to sbatch
handoff launch --host hpc --name bert-ft --dir ~/proj -- train.sbatch
```

The command runs in a non-interactive shell: include environment activation in
it. `launch` prints the handoff ID used by every other command.

A job that is already running can be followed if it was started detached
(`nohup`, `tmux`, `sbatch`): `handoff adopt --host lab --name x --pid 12345 --log ~/proj/train.log`
or `--job <slurm id>`. If it was not started detached, say so plainly: it will
die with the connection, and the choice is to restart it with `handoff launch`
or to keep the laptop open.

While the user is present, follow a job with `handoff status <id>` or run
`handoff wait <id>` as a background task.

## When the user leaves

1. Write the notes to the path printed by `handoff notes <id>`:

   ```markdown
   # Goal
   What this run is for and what the user wants to learn from it.
   # Running
   Command, host, directory, expected duration, where outputs go.
   # How to judge the outcome
   Metrics and thresholds; what success and failure look like in the log.
   # Next steps
   What to do on success. What to do on each failure you can foresee.
   # Do not touch
   Data, checkpoints and directories that must stay as they are.
   ```

2. If the user wants something to happen automatically, write a playbook
   (`references/playbook.md`) and show it to them.
3. Hand off:

   ```bash
   handoff leave <id> [--playbook playbook.sh] [--fetch results/metrics.json --into ./results] [--wake]
   ```

   `--fetch` paths are relative to the job directory. `--wake` turns Layer 2 on
   for this handoff.
4. Tell the user, in one short message: which layer is active, what will happen
   on success and on failure, what will not happen (in Layer 1 nothing thinks:
   an unforeseen failure waits for them), whether their phone will get status
   messages, and that they can close the laptop.

## When the user returns

Run `handoff back` (all handoffs) or `handoff back <id>`. It prints the
attempts, the playbook output, the wake report and the last log lines, and then:

- **finished**: results are copied into the `--into` folder. Read the report
  and the notes, then continue the work the notes describe.
- **stopped now, the job has not ended**: the watcher is stopped and you are in
  charge again. Keep following the job with `handoff wait <id>`. If the user
  leaves again, run `handoff leave` again.
- **post-processing is still running**: the playbook or the woken agent is
  still at work. Run `handoff back` again shortly.
- **DIED unexpectedly**: read the watcher log it prints, tell the user, and
  check the job with `handoff status <id>`.

Treat a wake report as a colleague's note, not as fact: check its claims
against the log before building on them.

## Warnings

Show the user the ones that apply, before the first use of each feature.

**Layer 1**

- A playbook runs commands on the compute host with nobody watching. A wrong
  rule burns GPU hours or allocation. The attempt cap (`MAX_ATTEMPTS`, default
  3) is the only brake; keep it low.
- The watcher is a long-running process. Some clusters forbid those on login
  nodes; check the site policy or use a relay.
- A relay holds an SSH key that reaches the compute host. Create a dedicated
  key on the relay, never copy a personal private key there, and follow the
  access rules of the lab or cluster. Whoever controls the relay controls that
  account.
- Results prefetched to a relay are stored on it. Do not prefetch data that
  must not leave the compute site.
- Notifications carry the job name, the host alias, log lines and the start of
  the agent's report. On a public service such as ntfy.sh, anyone who knows the
  topic can read them. Use a long random topic.
- Nothing thinks in Layer 1. A failure the playbook did not foresee waits until
  the user returns.

**Layer 2**

- In `act` mode an AI agent runs shell commands on the compute host with
  nobody watching. It can do anything the SSH account can do, including
  deleting data and using up allocation. Start with `report` mode.
- The agent reads job logs. Text in a log can steer an agent (prompt
  injection). Do not use `act` mode on jobs that process untrusted input.
- The agent's login token is stored on the watch host. Anyone with access to
  that host can use the user's Claude or Codex account.
- Each wake uses the user's subscription or API credit, unseen.
- The agent sees only the handoff notes, the log tail and the playbook output,
  not the conversation. Thin notes give poor decisions.
- Running an AI agent on a shared cluster login node may violate site policy.

## Limits

- Jobs on the user's own machine stop with it; no handoff is possible.
- SLURM job arrays and other schedulers (PBS, LSF) are not supported.
- One job chain per handoff; several jobs need several handoffs.
