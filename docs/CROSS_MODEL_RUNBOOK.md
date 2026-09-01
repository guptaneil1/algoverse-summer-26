# Cross-model runbook

**Written for someone who has never used a terminal.** Every command is given in full,
along with what you should see afterwards. Nothing is assumed.

---

## Read this first

### What you need

- This laptop and a web browser
- An account on this GitHub repository *(someone on the team grants this — one click on
  their side)*
- A Microsoft Azure account with credit on it, and nothing else set up

Nothing gets installed on your laptop. All the real work happens on computers you rent
from Azure by the hour.

### What you are doing

The team ran an experiment on one AI model, GPT-2. You are running the **same experiment**
on four more models so the results can be compared. A program does the science. Your job
is to rent computers, start the program, and save the results.

### How long it takes

| | |
|---|---|
| Your actual attention | **about 2 hours**, in short bursts |
| Waiting for Azure permission | 4 hours to 2 days |
| Computers working (laptop can be closed) | about 3 days |

The models run **at the same time**, not one after another, so the total is roughly the
length of the longest one rather than the sum of all five.

### Three rules

1. **When a command seems frozen, it is working.** Some take hours. Do not press Ctrl-C.
   Do not close the window.
2. **After each command, check the "you should see" line.** If yours differs, stop and go
   to [Part 8](#part-8--when-something-goes-wrong). Do not carry on and hope.
3. **Turn the computers off properly when done** ([§7.4](#74-turn-everything-off)). They
   bill by the hour whether or not you are using them.

---

## Contents

| | |
|---|---|
| [Part 1](#part-1--opening-a-terminal) | Opening a terminal |
| [Part 2](#part-2--setting-up-azure) | Setting up Azure |
| [Part 3](#part-3--renting-a-computer) | Renting a computer |
| [Part 4](#part-4--connecting-to-it) | Connecting to it |
| [Part 5](#part-5--setting-it-up-one-command) | Setting it up |
| [Part 6](#part-6--running-the-first-model) | Running the first model |
| [Part 7](#part-7--running-the-other-four) | Running the other four |
| [Part 8](#part-8--when-something-goes-wrong) | When something goes wrong |
| [Part 9](#part-9--costs) | Costs |
| [Appendix A](#appendix-a--doing-the-setup-by-hand) | Doing the setup by hand |

---

## Part 1 — Opening a terminal

A terminal is a window where you type commands instead of clicking. You already have one.

**Windows:** press the **Windows key**, type `powershell`, press **Enter**.
A dark window opens with text ending in `>`.

**Mac:** press **Command + Space**, type `terminal`, press **Enter**.
A window opens with text ending in `$` or `%`.

That symbol at the end is the **prompt**. It means the terminal is waiting for you.

### Running a command

When this document shows a box like this:

```bash
echo hello
```

Click into the terminal, type it, press **Enter**.

To paste instead: copy the text, then **right-click** in the terminal (Windows) or press
**Command+V** (Mac). Ctrl+V usually does not work in terminals.

Try it now.

**You should see:**
```
hello
```
and then the prompt again.

That is everything you need to know about terminals.

### The one thing that trips people up

After you press Enter, either:

- **the prompt comes back** → it finished, move on
- **the prompt does not come back** → it is still working, **wait**

Nothing here is ever frozen. Some steps take hours.

---

## Part 2 — Setting up Azure

All in your browser at **https://portal.azure.com**. Sign in.

Your account has credit and nothing else configured. These four steps fix that.

### 2.1 Check your credit and its expiry

1. Top search bar → type `Subscriptions` → click **Subscriptions**
2. Click your subscription (probably **Azure subscription 1**)
3. Read the **Overview** page

Write down the **amount** and the **expiry date**.

> If it expires in about 30 days you are on a clock. If about a year, you have time.

### 2.2 Set a spending alert

**Do not skip this.** On most of these accounts, when the credit runs out **charges
continue and go to the card on file.** Nothing stops automatically.

1. Search bar → `Cost Management` → click it
2. Left menu → **Budgets** → **+ Add**
3. **Name** `research-budget`, **Reset period** Monthly, **Amount** `1200`
4. Click **Next**
5. Add alert conditions at `50`, `75` and `90` percent
6. Put your email in **Alert recipients**
7. **Create**

### 2.3 Switch on the compute service

Brand-new Azure accounts have graphics cards disabled.

1. In the **top bar**, find the **`>_`** icon (right of the search box) and click it
2. If asked, choose **Bash**
3. If it mentions storage, choose **No storage account required** if offered, otherwise
   **Create storage**
4. Wait ~30 seconds for a prompt like `user@Azure:~$`

```bash
az provider register --namespace Microsoft.Compute
```

**You should see:** nothing at all. That is correct.

Wait a minute, then:

```bash
az provider show --namespace Microsoft.Compute --query registrationState -o tsv
```

**You should see:**
```
Registered
```

If it says `Registering`, wait a minute and run it again.

### 2.4 Ask for permission to use graphics cards

**This is the slowest step. Do it now, before anything else.** Nothing can start until it
is approved.

1. Search bar → `Quotas` → click it
2. Left menu → **My quotas**
3. Set the **Region** filter to **one** region — **East US** is a good default. Not "All"
4. In the table's search box type `T4`
5. Find the row **Standard NCASv3 Family vCPUs**

Look at the **Adjustable** column on that row.

**If it says Yes:** hover the row, click the **pencil**, enter `20`, **Submit**.

**If it says No, or you get "unable to adjust":** normal on these accounts. Ask a human:

1. Search bar → `Help + support` → **+ Create a support request**
2. **Issue type:** Service and subscription limits (quotas)
3. **Quota type:** Compute-VM (cores-vCPUs) subscription limit increases
4. **Next** → **Enter details**:
   - **Deployment model:** Resource Manager
   - **Location:** your region
   - **Standard NCASv3 Family vCPUs** → `20`
   - **Standard NCADSA100v4 Family vCPUs** → `24`
5. Description — paste this:

> Academic research on recursive language-model training. Fine-tuning small models
> (135M–1B parameters) for approximately 200 GPU-hours over the next month. Requesting
> 20 vCPU of NCASv3_T4 to run four small machines concurrently, and 24 vCPU of
> NCADSA100v4 for the largest model.

6. **Severity:** C → **Create**

> Why 20 and not 4? Each machine uses 4. Asking once for enough to run four at the same
> time avoids waiting for a second approval later.

**Now wait.** An hour to two days. You will get an email.

To check: **Quotas → My quotas**, search `T4`. When the row reads **`0 of 20`** instead of
**`0 of 0`**, you are approved.

---

## Part 3 — Renting a computer

Only once quota is approved.

Search bar → `Virtual machines` → **+ Create** → **Azure virtual machine**

**Basics tab:**

| Field | Value |
|---|---|
| Resource group | **Create new** → `research` |
| Virtual machine name | `hdb-smollm` *(name it after the model)* |
| Region | **the region you got quota in** |
| Image | **See all images** → search `NVIDIA GPU-Optimized VMI` → select it |
| Size | **See all sizes** → search `NC4as_T4_v3` → **Standard_NC4as_T4_v3** |
| Authentication type | **SSH public key** |
| Username | `azureuser` |
| SSH public key source | **Generate new key pair** |
| Key pair name | `hdb-key` |

**Disks tab:** Data disks → **Create and attach a new disk** → **256 GiB**,
**Premium SSD** → OK

**Management tab:** switch **Auto-shutdown** on, pick a time a few hours ahead. A safety
net against leaving it running.

**Review + create** → **Create**.

A box offers a private key. Click **Download private key and create resource**. It saves
`hdb-key.pem`, usually to Downloads.

> **You cannot download this file again. Do not lose it.** The same key works for every
> machine you create later, so keep it somewhere sensible.

Wait 2–5 minutes, then **Go to resource**. Find **Public IP address** — something like
`20.121.45.67`. Write it down.

---

## Part 4 — Connecting to it

Back to your terminal from Part 1.

### 4.1 Lock down the key file

SSH refuses to use a key other people could read.

**Windows** — one line, replacing `YourName` with your Windows username:

```powershell
icacls "C:\Users\YourName\Downloads\hdb-key.pem" /inheritance:r /grant:r "$($env:USERNAME):(R)"
```

**You should see:** `Successfully processed 1 files.`

**Mac:**

```bash
chmod 600 ~/Downloads/hdb-key.pem
```

**You should see:** nothing. Correct.

### 4.2 Connect

Replace the IP with yours.

**Windows:**
```powershell
ssh -i "C:\Users\YourName\Downloads\hdb-key.pem" azureuser@20.121.45.67
```

**Mac:**
```bash
ssh -i ~/Downloads/hdb-key.pem azureuser@20.121.45.67
```

First time it asks `Are you sure you want to continue connecting (yes/no)?` — type `yes`,
press Enter.

**You should see** a welcome message and a prompt ending:
```
azureuser@hdb-smollm:~$
```

**From here you are typing on the rented computer, not your laptop.**

---

## Part 5 — Setting it up (one command)

```bash
curl -fsSL https://raw.githubusercontent.com/guptaneil1/algoverse-summer-26/cross-model/add-model-families/scripts/bootstrap_vm.sh | bash -s -- smollm
```

That single command checks the graphics card, downloads the project and the training
pipeline at the exact versions the original experiment used, installs everything, runs the
tests, prepares the data, and writes the settings file.

**It takes 15–30 minutes** and prints a lot. Wait for it.

It asks for your **GitHub username** and then a **password**. For the password you need a
token, not your real password:

1. In your browser: https://github.com/settings/tokens
2. **Generate new token** → **classic**
3. Tick the **repo** box → **Generate token**
4. Copy the long string — you cannot see it again
5. Right-click in the terminal to paste. **Nothing appears as you type. That is normal.**

**You should see**, at the end:

```
================================================================================
READY.
```

If it stops with an error instead, go to [Part 8](#part-8--when-something-goes-wrong).

If you would rather do this by hand, or need to debug it,
[Appendix A](#appendix-a--doing-the-setup-by-hand) lists every individual step.

### One number to check before spending money

Just above `READY.` the script prints **tokenizer efficiency**. It should be roughly
between **0.7 and 1.3**.

If it is far outside that, **stop.** Something went wrong preparing the data and running
would waste hours of paid GPU time. Ask the team.

### Pin the model version

```bash
nano configs/experiment/pilot_smollm.json
```

Find the two lines saying `PIN_BEFORE_RUNNING`. Replace both with the commit hash from
https://huggingface.co/HuggingFaceTB/SmolLM2-135M/commits/main — click the topmost commit
and copy its long hash.

Save with **Ctrl+O**, **Enter**, then **Ctrl+X**.

---

## Part 6 — Running the first model

Run SmolLM2-135M **on its own first**. It is the cheapest, so if anything is broken it
breaks here for about $5 rather than on a machine costing fifty times that.

### 6.1 Start it

```bash
tmux new -s run
```

The screen clears and a green bar appears at the bottom. `tmux` keeps the job alive when
you disconnect.

```bash
cd ~/algoverse-summer-26 && export PYTHONPATH=src
python scripts/run_pilot.py --config configs/experiment/pilot_smollm.json \
    --upstream-dir ~/model_collapse --shim-dir ~/shim
```

### 6.2 Watch it for twenty minutes

Almost every problem shows up in the first few minutes. Once it is working through the
first generation without errors, the setup is proven.

**This is the moment to start the other four** — see
[Part 7](#part-7--running-the-other-four). You do not need this one to finish, only to
start.

### 6.3 Leave it running

Press **Ctrl+B**, let go, then press **D**.

You are back at the normal prompt and the job continues. You can close the terminal, shut
your laptop, and go to bed.

To look at it later: connect (§4.2), then `tmux attach -t run`.

### 6.4 When it finishes, check it is valid

```bash
cd ~/algoverse-summer-26 && export PYTHONPATH=src
python scripts/run_pilot.py --config configs/experiment/pilot_smollm.json \
    --output-dir runs/cross_model_smollm --check-only
```

**You should see** a message confirming budget matching holds.

**If it fails, the results are not usable.** Do not upload them. Tell the team.

### 6.5 Save the results to GitHub

```bash
cd ~/algoverse-summer-26
tar -czf smollm_results.tar.gz \
    runs/cross_model_smollm/*/chain_result.json \
    runs/cross_model_smollm/*/run_manifest.json \
    runs/cross_model_smollm/*/reference_mode_scores.json
ls -lh smollm_results.tar.gz
```

**You should see** a file of roughly 30–50 MB.

Log in to GitHub from the machine:

```bash
gh auth login
```

Choose **GitHub.com** → **HTTPS** → **Yes** → **Login with a web browser**. It shows a
code; copy it, open the link it prints on your laptop, paste the code.

```bash
gh release create cross-model-smollm-$(date +%Y-%m-%d) \
    smollm_results.tar.gz \
    --repo guptaneil1/algoverse-summer-26 \
    --title "Cross-model results: smollm" \
    --notes "Five arms x five seeds, horizon 10."
```

**You should see** a link. Open it to confirm the file is there.

Then save the settings so the run can be repeated:

```bash
git add configs/experiment/pilot_smollm.json data/manifests/smollm
git commit -m "Add smollm pilot config and manifests"
git push
```

---

## Part 7 — Running the other four

Do this **once SmolLM2 has started cleanly** (§6.2). You do not need it to finish.

The models are completely independent — nothing in one uses anything from another — so all
four run at the same time on separate machines. Four machines for 34 hours costs the same
as one machine for 136 hours, but the results arrive far sooner.

### 7.1 For each model, repeat Parts 3–6

| Model | Machine name | Word to use in commands | Machine size |
|---|---|---|---|
| Pythia-160M | `hdb-pythia` | `pythia` | `Standard_NC4as_T4_v3` |
| Pythia-410M | `hdb-pythia410` | `pythia410` | `Standard_NC4as_T4_v3` |
| Qwen2.5-0.5B | `hdb-qwen` | `qwen` | `Standard_NC4as_T4_v3` |
| Pythia-1B | `hdb-pythia1b` | `pythia1b` | `Standard_NC24ads_A100_v4` |

For each:

1. **Part 3** — create the machine with the name and size above. Reuse your existing
   `hdb-key` rather than generating a new one.
2. **Part 4** — connect.
3. **Part 5** — one command, with that model's word:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/guptaneil1/algoverse-summer-26/cross-model/add-model-families/scripts/bootstrap_vm.sh | bash -s -- pythia
   ```
   Then pin the version, using that model's page on Hugging Face.
4. **Part 6** — start it in `tmux`, detach, move to the next machine.

All four can be started within about an hour.

### 7.2 Two things that matter

**All three Pythia models must use `Standard_NC4as_T4_v3` — except Pythia-1B.** The three
Pythia models are a size comparison. Pythia-1B is too large for a T4, so it uses the A100
machine, which is what the second quota request was for. Note this in your handover to the
team, since it means one comparison ran on different hardware.

**Pythia-1B takes about 68 hours** and sets the finish time for everything. Start it early.

### 7.3 Keep a note of which is which

You will be connecting to five machines. Write it down:

```
hdb-smollm      20.121.45.67    SmolLM2-135M     started Tue 2pm
hdb-pythia      20.121.45.68    Pythia-160M      started Tue 3pm
hdb-pythia410   20.121.45.69    Pythia-410M      started Tue 3pm
hdb-qwen        20.121.45.70    Qwen2.5-0.5B     started Tue 4pm
hdb-pythia1b    20.121.45.71    Pythia-1B        started Tue 4pm
```

Running the right command on the wrong machine is the easiest mistake here.

### 7.4 Turn everything off

**The step people forget, and it costs real money.**

For **each** machine:

1. Azure portal → search `Virtual machines` → click the machine
2. **Stop** at the top
3. Wait until the status reads **Stopped (deallocated)**

**"Stopped" alone is not enough.** It must say **deallocated**. Five forgotten machines
bill five times over.

To use a machine again, click **Start**, get the **new** Public IP (it changes), and
reconnect with §4.2. Your files are still there.

---

## Part 8 — When something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| Quotas table is empty | Compute service not switched on | Redo §2.3 |
| "Unable to adjust" on quota | Normal on this account type | File the support request, §2.4 |
| VM creation fails on size | Quota not approved yet | Check the row reads `0 of 20` |
| `Permission denied (publickey)` | Key file permissions | Redo §4.1 |
| `nvidia-smi: command not found` | Wrong machine image | Delete it, redo Part 3 with the NVIDIA image |
| `Authentication failed` cloning | Used your real password | Use a token, Part 5 |
| Anything mentioning `wandb` | Setup incomplete | Rerun the Part 5 command; safe to repeat |
| `No space left on device` | Disk filling up | Check the 256 GB disk was attached in Part 3 |
| `CANNOT BUILD CONFIG` | A previous step did not finish | Rerun the Part 5 command |
| Tokenizer efficiency looks wrong | Data prepared incorrectly | **Stop.** Ask the team |
| Terminal seems frozen | It is working | **Wait.** Do not press Ctrl-C |
| Laptop disconnected mid-run | Nothing, if you used `tmux` | Reconnect, `tmux attach -t run` |
| `--check-only` fails | Run is not valid | Do not upload. Tell the team |

**The Part 5 command is safe to run again.** It skips anything already done, so if it fails
halfway, fix the cause and rerun the identical command.

### If you are stuck

Send the team the **last 20 lines** the terminal printed, copied exactly. Not a
description — the exact text is what makes it diagnosable.

---

## Part 9 — Costs

Prices approximate; check the Azure pricing calculator for your region.

| Model | Machine | Hours | Cost |
|---|---|---|---|
| SmolLM2-135M | T4 | 9 | ~$5 |
| Pythia-160M | T4 | 11 | ~$6 |
| Pythia-410M | T4 | 28 | ~$15 |
| Qwen2.5-0.5B | T4 | 34 | ~$18 |
| Pythia-1B | A100 | 68 | ~$250 |
| **Total** | | | **~$295** |

Comfortably inside $1,200, with room for mistakes and reruns.

Running them concurrently does not change the total — billing is per machine-hour either
way — but you spend it faster, so watch the budget alert emails.

---

## Checklist

- [ ] Credit amount and expiry written down
- [ ] Budget alert set at 50 / 75 / 90%
- [ ] `Microsoft.Compute` reads `Registered`
- [ ] Quota approved — row reads `0 of 20`
- [ ] `hdb-key.pem` saved somewhere safe
- [ ] SmolLM2 machine created, auto-shutdown on, 256 GB disk
- [ ] Part 5 command finished with `READY.`
- [ ] Tokenizer efficiency between 0.7 and 1.3
- [ ] Model version pinned in the settings file
- [ ] SmolLM2 started and watched for 20 minutes
- [ ] Other four machines created and started
- [ ] Note kept of which machine runs which model
- [ ] Per model: `--check-only` passed
- [ ] Per model: release uploaded, settings committed
- [ ] **Every** machine reads **Stopped (deallocated)**

---

## Appendix A — Doing the setup by hand

The Part 5 command does all of this. Use this only if it fails and you need to find out
where, or if you want to see what it does.

Run each in order, waiting for the prompt each time.

```bash
# the project
cd ~
git clone https://github.com/guptaneil1/algoverse-summer-26.git
cd algoverse-summer-26
git checkout cross-model/add-model-families
pip install -e . --no-deps

# the training pipeline, pinned to the commit the original experiment used
cd ~
git clone https://github.com/GeorgeDrayson/model_collapse.git
cd ~/model_collapse
git checkout feb8511479a2e2dc868e1caf3f63cb99f1fcc746
cd ~

# dependencies, at the versions the original experiment used
pip install -r ~/model_collapse/requirements.txt
pip install transformers==4.48.3 datasets==3.2.0 accelerate==1.2.1 \
    huggingface_hub jsonschema pytest pyarrow hf_transfer
```

The training pipeline reports to a dashboard service that crashes if not started properly.
This switches it off. Paste the **whole block** including the `PY` lines:

```bash
mkdir -p ~/shim && cat > ~/shim/sitecustomize.py <<'PY'
import os, sys, sysconfig
try:
    import importlib.util
    _p = os.path.join(sysconfig.get_paths()["stdlib"], "sitecustomize.py")
    if os.path.exists(_p):
        _s = importlib.util.spec_from_file_location("_d", _p)
        _m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
except Exception:
    pass
if os.environ.get("STAGE_A_WANDB_SHIM") == "1":
    try:
        import wandb
        wandb.init(mode="disabled")
    except Exception as e:
        sys.stderr.write("SHIM FAILED %s\n" % e)
PY
```

Then the tests and the data preparation:

```bash
cd ~/algoverse-summer-26
export PYTHONPATH=src
python -m pytest -q tests/runner tests/policies

export SHORT=smollm
export HF_ID=HuggingFaceTB/SmolLM2-135M

python scripts/build_base_corpus.py --partition base_train --limit 400 \
    --tokenizer "$HF_ID" --upstream-dir ~/model_collapse \
    --out data/corpora/${SHORT}_base.json

python scripts/build_base_corpus.py --partition prompts --limit 400 \
    --tokenizer "$HF_ID" --upstream-dir ~/model_collapse \
    --out data/corpora/${SHORT}_prompts.json

python scripts/build_base_corpus.py --partition test --eval \
    --tokenizer "$HF_ID" --upstream-dir ~/model_collapse \
    --out data/corpora/${SHORT}_test.json

python scripts/add_optimizer_token_counts.py \
    --tokenizer "$HF_ID" --out-dir data/manifests/${SHORT}

python scripts/make_model_pilot.py --model ${SHORT}
```

`--limit 400` is not optional: the original experiment used exactly the first 400 articles,
and without it you would build a much larger corpus that is not comparable.

For the other models substitute:

| `SHORT` | `HF_ID` |
|---|---|
| `smollm` | `HuggingFaceTB/SmolLM2-135M` |
| `pythia` | `EleutherAI/pythia-160m` |
| `pythia410` | `EleutherAI/pythia-410m` |
| `qwen` | `Qwen/Qwen2.5-0.5B` |
| `pythia1b` | `EleutherAI/pythia-1b` |

---

## What this does not cover

A further experiment, a "front-loaded schedule", is prepared on this branch
(`configs/policy/schedule_only_frontloaded.json`) but is not part of these instructions.
Adding it means changing a settings file that is deliberately frozen, which should be a
team decision rather than a runbook step. It is about five chains and it is the experiment
that makes the paper's claim about timing testable — worth doing, separately.
