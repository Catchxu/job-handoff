# Playbooks

A playbook is a bash script you write before the user leaves. The watcher runs
it on the compute host, in the job's working directory, each time an attempt
ends. It is how decisions made now are carried out later with no AI present.

## Contract

The playbook receives:

| Variable | Meaning |
|---|---|
| `HANDOFF_STATE` | `COMPLETED`, `FAILED`, `OOM`, `TIMEOUT`, `CANCELLED`, `LOST` (the process vanished without an exit code, for example after a reboot), `ENDED` (ended, outcome unknown), `NOTSTARTED` (a follow-up could not be started) |
| `HANDOFF_EXIT_CODE` | Exit code, or `-` when unknown |
| `HANDOFF_LOG` | Path of the log of the attempt that just ended |
| `HANDOFF_ATTEMPT` | 1 for the first run, 2 for the first follow-up, and so on |
| `HANDOFF_NEXT` | File to write to request a follow-up attempt |
| `HANDOFF_JOB_DIR` | The handoff's folder on the compute host |

To start a follow-up attempt, write its command into `$HANDOFF_NEXT`:

- plain host: a shell command line, run the same way as the first one;
- SLURM host: the arguments for `sbatch`.

The watcher starts it, follows it, and runs the playbook again when it ends.
Write nothing and the chain stops. A request beyond `MAX_ATTEMPTS` is refused
and kept as `next.refused`.

Everything the playbook prints is saved and shown by `handoff back`.

## Rules for writing one

- Decide on facts in the log or the exit code, not on guesses.
- Always branch on `HANDOFF_ATTEMPT` so that a rule cannot repeat forever with
  the same command.
- Keep it short. Anything that needs judgment belongs in the notes for the
  returning session, or in Layer 2.
- Do not delete data in a playbook.

## Examples

Train, then evaluate (plain host):

```bash
if [ "$HANDOFF_STATE" = COMPLETED ] && [ "$HANDOFF_ATTEMPT" = 1 ]; then
  echo 'source ~/venv/bin/activate && python eval.py --ckpt out/last.ckpt' > "$HANDOFF_NEXT"
fi
```

Out of memory: retry once with half the batch size (plain host):

```bash
if [ "$HANDOFF_ATTEMPT" = 1 ] && grep -q 'CUDA out of memory' "$HANDOFF_LOG"; then
  echo 'source ~/venv/bin/activate && python train.py --batch-size 128' > "$HANDOFF_NEXT"
fi
```

SLURM: resubmit after a time limit, evaluate after success:

```bash
case $HANDOFF_STATE in
  TIMEOUT)   [ "$HANDOFF_ATTEMPT" -lt 3 ] && echo 'train.sbatch --resume' > "$HANDOFF_NEXT" ;;
  COMPLETED) grep -q 'training finished' "$HANDOFF_LOG" && echo 'eval.sbatch' > "$HANDOFF_NEXT" ;;
esac
```

In the last example the evaluation job also ends as `COMPLETED`; its log does
not contain `training finished`, so the chain stops there.
