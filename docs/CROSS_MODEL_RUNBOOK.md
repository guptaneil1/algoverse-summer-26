# Cross-model runbook

Run the four additional model families on Azure, from a machine that has nothing but a
browser, and publish the artifacts back to this repository.

Assumes: a GitHub account with access to this repo, an Azure subscription with credit,
and no local setup at all. Everything else is below.

**Read [§0](#0-what-you-are-running) before spending anything.** The order of the runs is
chosen so that a cheap run fails first if something is wrong.

---

## 0. What you are running

The pilot of 2026-08-20 covered one model, GPT-2 124M: five arms
(`no_rescue`, `random`, `schedule_only`, `selection_only`, `joint`) across five seeds
(101, 202, 303, 404, 505) at horizon 10, so 25 chains. This runbook adds four more
families under the same conditions.

| Order | Model | Params | Family | Why it is in this position |
|---|---|---|---|---|
| 1 | `HuggingFaceTB/SmolLM2-135M` | 135M | Llama-style | Cheapest. The shakedown: if the cross-model path is broken, it breaks here for a few dollars |
| 2 | `EleutherAI/pythia-160m` | 160M | GPT-NeoX | Scale ladder, rung 1 |
| 3 | `EleutherAI/pythia-410m` | 410M | GPT-NeoX | Rung 2. Two rungs make a trend |
| 4 | `Qwen/Qwen2.5-0.5B` | 494M | Qwen2.5 | Fourth family, different tokenizer |
| 5 | `EleutherAI/pythia-1b` | 1B | GPT-NeoX | Rung 3. Most expensive; run last, and only if the effect replicates |

**Keep the Pythia rungs on the same VM size.** They are the scale comparison, so if 160M
runs on a T4 and 1B on an A100, hardware varies along the axis you are measuring. Mixed
hardware across *families* is fine; mixed hardware *within the ladder* is not.

### What must not change

`configs/experiment/cross_model_budget.json` is frozen. Do not edit it to make a run fit.
Held identical across every model: the five arms, the five seeds, horizon 10, the same 400
WikiText-103 articles, block size 512, loss on the last 256 tokens, batch size 8, one
epoch, bfloat16, top-k 50 at temperature 1.0, and the 2% effect threshold.

Only four things differ per model: the model identifier, the manifest and corpus paths,
the three budget numbers, and the run identity. `scripts/make_model_pilot.py` produces
exactly that diff and nothing else.

### The budget rule

Each model gets the same *fraction* of its own optimizer tokens, not the same absolute
number, because tokenizers differ in efficiency:

```
T_model = 16,678,912 × (base_train tokens under this tokenizer ÷ under GPT-2's)
B       = round(0.04495798 × T_model)
```

`f = 0.04495798` is what the GPT-2 run actually realised, which is why that run counts as
the first row without a rerun. You never type a budget in by hand.

---

## 1. Azure setup

### 1.1 Check what your credit is

**Portal → Subscriptions → your subscription → Overview.** Note the balance and the
**expiry date**. A free-account credit expires ~30 days after activation; a sponsorship
usually runs a year. This decides how hard you push, nothing else.

Also check **`spendingLimit`**. If it is `Off`, charges continue after the credit is
exhausted and bill your card. Assume it is off unless you have checked.

### 1.2 Set a budget alert

**Cost Management → Budgets → + Add** → scope your subscription → amount = your credit →
alerts at **50 / 75 / 90%** → your email.

Two minutes. With `spendingLimit: Off` this is the only thing between a forgotten VM and a
real charge.

### 1.3 Register the compute provider

A new subscription has no quotas visible until this is done. Open **Cloud Shell** (the
`>_` icon in the top bar), choose **Bash**, then:

```bash
az provider register --namespace Microsoft.Compute
az provider show --namespace Microsoft.Compute --query registrationState -o tsv
```

Wait for `Registered`.

### 1.4 Get GPU quota

**Portal search → Quotas → Compute →** set **Region** to one specific region (not "All").
Search `T4`, find **Standard NCASv3 Family vCPUs**.

If the **Adjustable** column says **Yes**, request an increase to `8` inline.

If it says **No**, or you get *"unable to adjust"* — which is normal on Sponsored
subscriptions — file a free support request instead:

**Help + support → Create a support request**
- Issue type: **Service and subscription limits (quotas)**
- Quota type: **Compute-VM (cores-vCPUs) subscription limit increases**
- Enter details: your region, **Standard NCASv3 Family** → `8`, and
  **Standard NCADSA100v4 Family** → `24`

> Academic research on recursive language-model training. Fine-tuning small models
> (135M–1B) for approximately 200 GPU-hours over the next month. Requesting 8 vCPU of
> NCASv3_T4 and 24 vCPU of NCADSA100v4.

Severity C. Turnaround is hours to a couple of days. **Nothing else can proceed until this
clears**, so file it before doing anything below.

If it is refused: try a different region (GPU availability varies a lot), ask for T4 only,
or use whatever shared GPU box the programme provides.

---

## 2. Create the VM

**Portal → Virtual machines → + Create → Azure virtual machine**

| Tab | Field | Value |
|---|---|---|
| Basics | Resource group | Create new → `research` |
| | VM name | `hdb-run` |
| | Region | **the region you got quota in** |
| | Image | *See all images* → **NVIDIA GPU-Optimized VMI** or **Data Science VM – Ubuntu** |
| | Size | `Standard_NC4as_T4_v3` for models 1–2; `Standard_NC24ads_A100_v4` for 3–5 |
| | Authentication | SSH public key, username `azureuser` |
| Disks | Data disk | **Create and attach** → **256 GiB Premium SSD** |
| Management | Auto-shutdown | **Enable**, set a daily time |

Use an image with CUDA preinstalled. Plain Ubuntu means installing NVIDIA drivers by hand.

**Spot** instances are heavily discounted and safe here — the runner resumes from
checkpoints, so an eviction costs you one partial chain.

Download the private key when offered. You cannot retrieve it later.

### Connect

```bash
chmod 600 ~/Downloads/hdb-run_key.pem
ssh -i ~/Downloads/hdb-run_key.pem azureuser@<public-ip>
nvidia-smi
```

`nvidia-smi` must print a GPU. If it errors, the image had no drivers — rebuild with a
different image rather than fighting it.

---

## 3. Set up the machine

```bash
# this repo
git clone https://github.com/guptaneil1/algoverse-summer-26.git
cd algoverse-summer-26
git checkout cross-model/add-model-families
pip install -e .

# the upstream training pipeline, which is not vendored here
git clone https://github.com/GeorgeDrayson/model_collapse.git ~/model_collapse
pip install -r ~/model_collapse/requirements.txt
```

### The wandb shim

Upstream calls `wandb.log` unconditionally while its init is guarded by a condition that
never fires, so it crashes without a shim. `FAILURE_LOG.md` F-006 and F-007 record this.
`run_pilot.py` takes `--shim-dir`, which it prepends to `PYTHONPATH`; the directory needs a
`sitecustomize.py` performing a disabled-mode init.

```bash
mkdir -p ~/shim
```

Ask the team for the exact `sitecustomize.py` used in the 2026-08-20 run rather than
writing a new one — it must match, or generation may behave differently.

### Verify before spending

```bash
cd ~/algoverse-summer-26
python -m pytest -q tests/runner tests/policies
python scripts/run_pilot.py --config configs/experiment/primary_pilot.json \
    --upstream-dir ~/model_collapse --dry-run
```

The dry run prints the commands it would execute. If it errors, fix that before starting a
real run.

---

## 4. Per-model preparation

Do this once per model. Replace `<SHORT>` and `<HF_ID>` from the table in §0 —
for example `smollm` and `HuggingFaceTB/SmolLM2-135M`.

### 4.1 Rebuild the corpora under this model's tokenizer

```bash
cd ~/algoverse-summer-26
export SHORT=smollm
export HF_ID=HuggingFaceTB/SmolLM2-135M

python scripts/build_base_corpus.py --partition base_train \
    --tokenizer "$HF_ID" --upstream-dir ~/model_collapse \
    --out data/corpora/${SHORT}_base.json

python scripts/build_base_corpus.py --partition prompts \
    --tokenizer "$HF_ID" --upstream-dir ~/model_collapse \
    --out data/corpora/${SHORT}_prompts.json

python scripts/build_base_corpus.py --partition test --eval \
    --tokenizer "$HF_ID" --upstream-dir ~/model_collapse \
    --out data/corpora/${SHORT}_test.json
```

`--eval` is required for the test partition: upstream loads train and test together and
rejects a column present in one and absent from the other.

### 4.2 Rebuild the manifests

```bash
python scripts/add_optimizer_token_counts.py \
    --tokenizer "$HF_ID" --out-dir data/manifests/${SHORT}
```

This refuses to overwrite `data/manifests/` with counts from a non-GPT-2 tokenizer, on
purpose: the frozen pilot budget is denominated in GPT-2 tokens.

### 4.3 Generate the pilot config

```bash
python scripts/make_model_pilot.py --model ${SHORT}
```

It prints the tokenizer efficiency, `T`, and `B`. **Sanity-check them.** A ratio far from
~0.8–1.2 against GPT-2 means something is wrong with the corpus build — stop and
investigate rather than running.

Then pin the model revision in `configs/experiment/pilot_${SHORT}.json`: the generated file
carries `PIN_BEFORE_RUNNING` for `revision` and `tokenizer_revision`. Get the commit SHA
from the model's Hugging Face page.

---

## 5. Run

```bash
tmux new -s run      # so an SSH drop does not kill the job
python scripts/run_pilot.py --config configs/experiment/pilot_${SHORT}.json \
    --upstream-dir ~/model_collapse --shim-dir ~/shim
```

Detach with `Ctrl-B` then `D`; reattach with `tmux attach -t run`.

### Multiple GPUs

Chains are independent, so sharding is linear. On a 2-GPU VM, in two shells:

```bash
python scripts/run_pilot.py --config configs/experiment/pilot_${SHORT}.json \
    --upstream-dir ~/model_collapse --shim-dir ~/shim \
    --shard-index 0 --shard-count 2 --cuda-device 0

python scripts/run_pilot.py --config configs/experiment/pilot_${SHORT}.json \
    --upstream-dir ~/model_collapse --shim-dir ~/shim \
    --shard-index 1 --shard-count 2 --cuda-device 1
```

Chains are dealt round-robin, so each shard gets a mix of arms and they finish together.

### Verify the whole grid

After all shards finish:

```bash
python scripts/run_pilot.py --config configs/experiment/pilot_${SHORT}.json \
    --output-dir runs/cross_model_${SHORT} --check-only
```

This asserts realised budget matching across the grid and **exits non-zero if it does not
hold**. A run that fails this is not reportable. Do not proceed to the next model until it
passes.

---

## 6. Publish the artifacts

Keep only what the v2 release kept — 38 MB for 25 chains, versus hundreds of gigabytes of
checkpoints.

```bash
cd ~/algoverse-summer-26
tar -czf ${SHORT}_results.tar.gz \
    runs/cross_model_${SHORT}/*/chain_result.json \
    runs/cross_model_${SHORT}/*/run_manifest.json \
    runs/cross_model_${SHORT}/*/reference_mode_scores.json
ls -lh ${SHORT}_results.tar.gz
```

Then, with the GitHub CLI (`gh auth login` first, device flow works over SSH):

```bash
gh release create cross-model-${SHORT}-$(date +%Y-%m-%d) \
    ${SHORT}_results.tar.gz \
    --repo guptaneil1/algoverse-summer-26 \
    --title "Cross-model results: ${SHORT}" \
    --notes "Five arms x five seeds, horizon 10. Budget from the frozen rule in configs/experiment/cross_model_budget.json. Config: configs/experiment/pilot_${SHORT}.json"
```

Also commit the generated config and manifests, so the run is reproducible:

```bash
git add configs/experiment/pilot_${SHORT}.json data/manifests/${SHORT}
git commit -m "Add ${SHORT} pilot config and manifests"
git push
```

### Then shut the VM down

**Portal → VM → Deallocate.** *Stopped* still bills. It must read **Deallocated**.

---

## 7. Costs and time

Scaled from the measured GPT-2 grid: 25 chains in 8.53 wall hours, decoding dominant, so
cost tracks parameter count. **Prices are approximate — check the Azure calculator.**

| Model | ~GPU-hours | T4 (~$0.53/hr) | A100 (~$3.67/hr) |
|---|---|---|---|
| SmolLM2-135M | 9 | ~$5 | ~$33 |
| Pythia-160M | 11 | ~$6 | ~$40 |
| Pythia-410M | 28 | ~$15 | ~$103 |
| Qwen2.5-0.5B | 34 | ~$18 | ~$125 |
| Pythia-1B | 68 | — | ~$250 |
| **Total** | **150** | | **~$550** |

Run 135M–410M on T4s; reserve the A100 for Pythia-1B. Sharding across GPUs cuts wall-clock
without changing cost.

---

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Quotas page empty | `Microsoft.Compute` unregistered | §1.3 |
| "Unable to adjust" quota | Sponsored subscription | Support request, §1.4 |
| VM creation fails on size | Quota not granted yet | Check the row reads `0 of 8` |
| `nvidia-smi` not found | Image has no drivers | Rebuild with an NVIDIA image |
| `wandb` crash on first generation | Missing shim | §3, and F-006/F-007 |
| Disk full mid-run | Checkpoints accumulating | `--save_total_limit` is set on this branch; confirm you are on it |
| `make_model_pilot.py` refuses | Manifests not built | Run §4.2 first |
| Tokenizer ratio looks wrong | Corpus built with the wrong tokenizer | Rebuild §4.1; the `--tokenizer` default is GPT-2 |
| Budget check fails | Realised spend outside tolerance | Do not report it. Record in `FAILURE_LOG.md` |

---

## 9. Checklist

- [ ] Credit balance and expiry noted; budget alert set
- [ ] `Microsoft.Compute` registered
- [ ] GPU quota granted
- [ ] VM created with auto-shutdown and a 256 GB data disk
- [ ] `nvidia-smi` shows a GPU
- [ ] Tests pass; `--dry-run` clean
- [ ] Shim obtained from the team, not improvised
- [ ] Per model: corpora, manifests, config, revision pinned
- [ ] Per model: run, then `--check-only` passes
- [ ] Per model: release uploaded, config and manifests committed
- [ ] VM **Deallocated**

---

## What this runbook does not cover

The front-loaded schedule arm. `configs/policy/schedule_only_frontloaded.json` exists on
this branch and mirrors the executed back-loaded schedule, but wiring it in needs an extra
arm in a pilot config, which is a change to a frozen file and should be a deliberate
decision rather than a step in a runbook. It is roughly five chains and it is the
experiment that makes the paper's timing claim testable — worth doing, separately.
