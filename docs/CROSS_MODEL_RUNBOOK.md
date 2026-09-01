# Cross-model runbook

**Written for someone who has never used a terminal.** Every command is given in full, with
what you should see afterwards. Nothing is assumed.

You need three things: this laptop, an account on this GitHub repository, and an Azure
account with credit. Nothing gets installed on your laptop except what is already there.

**How to use this document.** Do the steps in order. Do not skip ahead. After each command
there is a "you should see" line — if what you see is different, stop and look at
[Part 7](#part-7--when-something-goes-wrong) rather than continuing.

**Two rules that will save you money and time:**

1. When a command is running, the terminal may sit still for minutes or hours. **That is
   normal.** Do not press Ctrl-C. Do not close the window.
2. When you finish for the day, follow [§6.7](#67-turn-the-computer-off) exactly. The cloud
   computer bills by the hour whether or not you are using it.

---

## Contents

- [Part 0 — What you are actually doing](#part-0--what-you-are-actually-doing)
- [Part 1 — Opening a terminal](#part-1--opening-a-terminal)
- [Part 2 — Setting up Azure](#part-2--setting-up-azure)
- [Part 3 — Creating the cloud computer](#part-3--creating-the-cloud-computer)
- [Part 4 — Connecting to it](#part-4--connecting-to-it)
- [Part 5 — Installing the project](#part-5--installing-the-project)
- [Part 6 — Running one model](#part-6--running-one-model)
- [§6.8 — Running several models at once](#68-running-several-models-at-once)
- [Part 7 — When something goes wrong](#part-7--when-something-goes-wrong)
- [Part 8 — Costs](#part-8--costs)

---

## Part 0 — What you are actually doing

The team already ran this experiment on one AI model called GPT-2. You are going to run the
**same experiment** on four more models, so the results can be compared.

You will not do the science. A program does that. Your job is:

1. Rent a computer with a graphics card from Microsoft Azure
2. Copy the project onto it
3. Start the program and wait
4. Save the results back to GitHub
5. Turn the computer off

The models, in the order you will run them:

| Order | Model | Roughly how long | Why this order |
|---|---|---|---|
| 1 | SmolLM2-135M | 9 hours | Cheapest. If something is broken, it breaks here for about $5 |
| 2 | Pythia-160M | 11 hours | |
| 3 | Pythia-410M | 28 hours | |
| 4 | Qwen2.5-0.5B | 34 hours | |
| 5 | Pythia-1B | 68 hours | Most expensive. Only if the first four worked |

**Do not reorder these.** The first one is deliberately the cheapest so that mistakes are
cheap.

### You do not have to run them one after another

Those hours add up to about 150, which sounds like weeks. It is not, because **the models
are completely independent of each other**. Nothing in model 2 needs anything from model 1.

So once model 1 has worked, you can rent a **separate computer for each remaining model and
run them all at the same time**. Four machines running for 34 hours costs the same as one
machine running for 136 hours — you are billed per machine-hour either way — but you get
your results in a day and a half instead of most of a week.

The plan:

1. Run **SmolLM2-135M alone first**, start to finish. This proves everything works.
2. Then start **one computer per remaining model, all at once.** They do not interact.

[§6.8](#68-running-several-models-at-once) covers this. It is the same instructions
repeated, not anything new.

> If you are curious why this is safe: each run is 25 independent "chains", and no chain
> uses another chain's output. The original GPT-2 experiment was itself run split across
> four graphics cards for exactly this reason.

### You need nothing from anyone

Everything is in this document or in the repository. You do not need any files, passwords,
or setup from another person. The only thing someone else must do is give your GitHub
account access to this repository, which is one click on their side.

---

## Part 1 — Opening a terminal

A "terminal" is a window where you type commands instead of clicking. You already have one.

### On Windows

1. Press the **Windows key** on your keyboard
2. Type `powershell`
3. Press **Enter**

A dark blue or black window opens with text ending in `>`. That `>` is the **prompt**. It
means the terminal is waiting for you.

### On Mac

1. Press **Command + Space**
2. Type `terminal`
3. Press **Enter**

A window opens with text ending in `$` or `%`. That is your prompt.

### How to run a command

When this document shows a box like this:

```bash
echo hello
```

You: click into the terminal window, type it exactly, press **Enter**.

To paste instead of typing: copy the text, then **right-click** inside the terminal window
(Windows) or press **Command+V** (Mac). Ctrl+V often does not work in terminals.

Try it now. Type `echo hello` and press Enter.

**You should see:**
```
hello
```
and then the prompt again, waiting.

If you got that, you know everything about terminals you need for this document.

### The single most important thing

After you press Enter, one of two things happens:

- **The prompt comes back** → the command finished, do the next one
- **The prompt does not come back** → it is still working. **Wait.** Some commands here take
  hours.

Never assume a command has frozen. It has not.

---

## Part 2 — Setting up Azure

All of this happens in your web browser at **https://portal.azure.com**. Sign in.

### 2.1 Check how much credit you have and when it expires

1. In the search bar at the very top, type `Subscriptions`
2. Click **Subscriptions** in the results
3. Click the name of your subscription (probably **Azure subscription 1**)
4. Look at the **Overview** page

Find the credit amount and an **expiry date**. Write both down.

> If the expiry is about 30 days away, you are on a clock and should start soon. If it is
> about a year, you have time.

### 2.2 Set a spending alert

This matters. On most of these subscriptions, **when the credit runs out, charges continue
and go to your card.** Nothing stops automatically.

1. Search bar → type `Cost Management` → click **Cost Management**
2. In the left menu click **Budgets**
3. Click **+ Add**
4. Fill in:
   - **Name:** `research-budget`
   - **Reset period:** Monthly
   - **Amount:** your credit amount, e.g. `200`
5. Click **Next**
6. Set **Alert conditions** to `50`, then add rows for `75` and `90`
7. Put your email in **Alert recipients**
8. Click **Create**

Do not skip this.

### 2.3 Turn on the compute service

New Azure accounts have graphics cards switched off. You have to turn the service on.

1. Look at the **very top bar** of the Azure page
2. Find the icon that looks like **`>_`** — it is to the right of the search box
3. Click it. A panel opens at the bottom
4. If it asks **Bash or PowerShell**, click **Bash**
5. If it says *"You have no storage mounted"*, click **No storage account required** if
   offered, otherwise **Create storage**
6. Wait about 30 seconds until you see a prompt like `user@Azure:~$`

Now type this and press Enter:

```bash
az provider register --namespace Microsoft.Compute
```

**You should see:** nothing. It returns silently. That is correct.

Wait one minute, then type:

```bash
az provider show --namespace Microsoft.Compute --query registrationState -o tsv
```

**You should see:**
```
Registered
```

If it says `Registering`, wait another minute and run the same command again.

### 2.4 Ask for permission to use a graphics card

Azure will not let you rent a graphics card until you ask. This is the step that takes the
longest, so do it now.

1. Search bar → `Quotas` → click **Quotas**
2. In the left menu click **My quotas**
3. At the top, click the **Region** filter and pick **one** region, for example **East US**
   (not "All")
4. In the search box above the table, type `T4`
5. Look for a row called **Standard NCASv3 Family vCPUs**

Now look at the **Adjustable** column on that row:

**If it says Yes:**
- Hover over the row, click the **pencil** icon on the right
- Enter `20`
- Click **Submit**

> Why 20 and not 4? Each computer uses 4, and asking once for enough to run four
> computers at the same time saves you waiting for a second approval later.

**If it says No, or you get an error saying "unable to adjust":**

This is normal on sponsored accounts. You have to ask a person instead:

1. Search bar → `Help + support`
2. Click **+ Create a support request**
3. Fill in:
   - **Issue type:** Service and subscription limits (quotas)
   - **Subscription:** your subscription
   - **Quota type:** Compute-VM (cores-vCPUs) subscription limit increases
4. Click **Next**
5. Click **Enter details**, then fill in:
   - **Deployment model:** Resource Manager
   - **Location:** your region
   - **Quota:** Standard NCASv3 Family vCPUs → **New limit:** `20`
   - Add a second row: Standard NCADSA100v4 Family vCPUs → **New limit:** `24`
6. In the description box, paste:

> Academic research on recursive language-model training. Fine-tuning small models
> (135M–1B) for approximately 200 GPU-hours over the next month. Requesting 20 vCPU of
> NCASv3_T4, enough to run four small machines concurrently, and 24 vCPU of
> NCADSA100v4.

7. **Severity:** C
8. Click **Create**

**Now wait.** This takes anywhere from an hour to two days. You cannot continue until it is
approved. You will get an email.

To check: go back to **Quotas → My quotas**, search `T4`, and look at the row. When it
reads **`0 of 20`** instead of **`0 of 0`**, you are approved.

---

## Part 3 — Creating the cloud computer

Only do this once quota is approved.

1. Search bar → `Virtual machines` → click it
2. Click **+ Create** → **Azure virtual machine**

Fill in the **Basics** tab:

| Field | What to put |
|---|---|
| Resource group | Click **Create new**, type `research`, click OK |
| Virtual machine name | `hdb-run` |
| Region | **The same region you asked for quota in** |
| Image | Click **See all images**, search `NVIDIA GPU-Optimized VMI`, pick it |
| Size | Click **See all sizes**, search `NC4as_T4_v3`, pick **Standard_NC4as_T4_v3** |
| Authentication type | **SSH public key** |
| Username | `azureuser` |
| SSH public key source | **Generate new key pair** |
| Key pair name | `hdb-key` |

Click the **Disks** tab:
- Under Data disks click **Create and attach a new disk**
- **Size:** click *Change size*, choose **256 GiB**, **Premium SSD**
- Click OK

Click the **Management** tab:
- Find **Auto-shutdown** and switch it **On**
- Set a time a few hours from now
- This is a safety net so you cannot leave it running by accident

Click **Review + create**, then **Create**.

**A box will pop up offering to download a private key.** Click **Download private key and
create resource**. It saves a file called `hdb-key.pem`, usually into your Downloads folder.

**You cannot download this file again. Do not lose it.**

Wait 2–5 minutes for "Your deployment is complete".

Click **Go to resource**. On that page find **Public IP address** — a number like
`20.121.45.67`. Write it down.

---

## Part 4 — Connecting to it

Go back to your terminal from Part 1.

### 4.1 Fix the key file permissions

The key file has to be private or SSH refuses to use it.

**On Windows**, type this as one line (replace `YourName` with your Windows username):

```powershell
icacls "C:\Users\YourName\Downloads\hdb-key.pem" /inheritance:r /grant:r "$($env:USERNAME):(R)"
```

**You should see:** `Successfully processed 1 files.`

**On Mac:**

```bash
chmod 600 ~/Downloads/hdb-key.pem
```

**You should see:** nothing. That is correct.

### 4.2 Connect

Replace `20.121.45.67` with your actual Public IP address:

**Windows:**
```powershell
ssh -i "C:\Users\YourName\Downloads\hdb-key.pem" azureuser@20.121.45.67
```

**Mac:**
```bash
ssh -i ~/Downloads/hdb-key.pem azureuser@20.121.45.67
```

The first time it asks:

```
Are you sure you want to continue connecting (yes/no)?
```

Type `yes` and press Enter.

**You should see** a welcome message and a new prompt ending in:
```
azureuser@hdb-run:~$
```

**You are now typing on the cloud computer, not your laptop.** Everything from here happens
there.

### 4.3 Check the graphics card is there

```bash
nvidia-smi
```

**You should see** a table with `Tesla T4` in it.

If you see `command not found`, the machine was built from the wrong image. Delete the VM
and redo Part 3, making sure you pick the NVIDIA image.

---

## Part 5 — Installing the project

Type these one at a time, waiting for the prompt each time.

### 5.1 Download the project

```bash
git clone https://github.com/guptaneil1/algoverse-summer-26.git
```

It will ask for your GitHub **username** and then a **password**. For the password you must
use a **personal access token**, not your real password:

1. In your browser go to https://github.com/settings/tokens
2. Click **Generate new token** → **classic**
3. Tick the **repo** box
4. Click **Generate token**
5. Copy the long string it shows you — you cannot see it again
6. Paste it as the password (right-click to paste; nothing appears as you type, that is
   normal)

Then:

```bash
cd algoverse-summer-26
git checkout cross-model/add-model-families
pip install -e . --no-deps
```

### 5.2 Download the training pipeline

The exact version matters — a newer one may behave differently from the original
experiment, which would make your results not comparable.

```bash
cd ~
git clone https://github.com/GeorgeDrayson/model_collapse.git
cd ~/model_collapse
git checkout feb8511479a2e2dc868e1caf3f63cb99f1fcc746
cd ~
```

**You should see** a message mentioning "detached HEAD". That is correct and expected.

Now install what it needs. These versions are pinned deliberately:

```bash
pip install -r ~/model_collapse/requirements.txt
pip install transformers==4.48.3 datasets==3.2.0 accelerate==1.2.1 \
    huggingface_hub jsonschema pytest pyarrow hf_transfer
```

This takes several minutes and prints a great deal of text. Wait for the prompt.

### 5.3 Create the small helper file

The training pipeline crashes without this. Copy the **whole block** below, including the
first and last lines, paste it into the terminal, and press Enter:

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

Check it worked:

```bash
ls ~/shim
```

**You should see:** `sitecustomize.py`

> What this does, if you are curious: the training pipeline reports to a dashboard service
> called wandb, and crashes if it was not started properly. This file switches it off. You
> do not need to understand it, but it must exist.

### 5.4 Check everything works before spending money

```bash
cd ~/algoverse-summer-26
export PYTHONPATH=src
python -m pytest -q tests/runner tests/policies
```

**You should see** something ending in `passed`, for example `307 passed, 13 skipped`.

If you see `failed`, stop. Do not continue. Go to Part 7.

---

## Part 6 — Running one model

This section is for **one** model. When it is finished, come back and do it again for the
next one.

Start with SmolLM2-135M.

### 6.1 Tell the terminal which model

Copy both lines together:

```bash
export SHORT=smollm
export HF_ID=HuggingFaceTB/SmolLM2-135M
```

For later models, use these pairs instead:

| Model | `SHORT` | `HF_ID` |
|---|---|---|
| SmolLM2-135M | `smollm` | `HuggingFaceTB/SmolLM2-135M` |
| Pythia-160M | `pythia` | `EleutherAI/pythia-160m` |
| Pythia-410M | `pythia410` | `EleutherAI/pythia-410m` |
| Qwen2.5-0.5B | `qwen` | `Qwen/Qwen2.5-0.5B` |
| Pythia-1B | `pythia1b` | `EleutherAI/pythia-1b` |

> If you disconnect and come back, you must set these two lines again.

### 6.2 Prepare the data for this model

Three commands. Each takes a few minutes.

```bash
cd ~/algoverse-summer-26
export PYTHONPATH=src

python scripts/build_base_corpus.py --partition base_train --limit 400 \
    --tokenizer "$HF_ID" --upstream-dir ~/model_collapse \
    --out data/corpora/${SHORT}_base.json

python scripts/build_base_corpus.py --partition prompts --limit 400 \
    --tokenizer "$HF_ID" --upstream-dir ~/model_collapse \
    --out data/corpora/${SHORT}_prompts.json

python scripts/build_base_corpus.py --partition test --eval \
    --tokenizer "$HF_ID" --upstream-dir ~/model_collapse \
    --out data/corpora/${SHORT}_test.json
```

> `--limit 400` is not optional. The original experiment used exactly the first 400
> articles, and leaving it off would build a much larger corpus that is not comparable.
> The `test` one has no limit, which is also deliberate.

Then:

```bash
python scripts/add_optimizer_token_counts.py \
    --tokenizer "$HF_ID" --out-dir data/manifests/${SHORT}
```

**You should see** several lines ending with `hash unchanged`.

### 6.3 Create the settings file

```bash
python scripts/make_model_pilot.py --model ${SHORT}
```

**You should see** something like:

```
wrote configs/experiment/pilot_smollm.json
  model                    HuggingFaceTB/SmolLM2-135M
  tokenizer efficiency     0.87xxxx x GPT-2 on the same corpus
  total optimizer tokens   14,5xx,xxx
  lifetime human budget    65x,xxx
```

**Check the "tokenizer efficiency" number.** It should be between roughly **0.7 and 1.3**.
If it is far outside that, something went wrong in 6.2 — stop and ask for help rather than
running.

### 6.4 Start the run

First start a session that survives disconnection:

```bash
tmux new -s run
```

The screen clears and you get a green bar at the bottom. Now start the run:

```bash
cd ~/algoverse-summer-26
python scripts/run_pilot.py --config configs/experiment/pilot_${SHORT}.json \
    --upstream-dir ~/model_collapse --shim-dir ~/shim
```

It will print progress for many hours.

**To leave it running and close your laptop:** press **Ctrl+B**, let go, then press **D**.
You are back at the normal prompt and the job continues on the cloud computer.

You can now close the terminal, shut your laptop, and go to bed.

**To check on it later:** connect again (§4.2) and type:

```bash
tmux attach -t run
```

### 6.5 Check the results are valid

When the run has finished:

```bash
python scripts/run_pilot.py --config configs/experiment/pilot_${SHORT}.json \
    --output-dir runs/cross_model_${SHORT} --check-only
```

**You should see** a message saying budget matching holds.

If it fails, **the results are not usable.** Do not upload them. Go to Part 7.

### 6.6 Save the results to GitHub

```bash
cd ~/algoverse-summer-26
tar -czf ${SHORT}_results.tar.gz \
    runs/cross_model_${SHORT}/*/chain_result.json \
    runs/cross_model_${SHORT}/*/run_manifest.json \
    runs/cross_model_${SHORT}/*/reference_mode_scores.json
ls -lh ${SHORT}_results.tar.gz
```

**You should see** a file of roughly 30–50 MB.

Now log in to GitHub from the machine:

```bash
gh auth login
```

Choose: **GitHub.com** → **HTTPS** → **Yes** → **Login with a web browser**. It shows a
code. Copy it, open the link it gives on your laptop, paste the code.

Then upload:

```bash
gh release create cross-model-${SHORT}-$(date +%Y-%m-%d) \
    ${SHORT}_results.tar.gz \
    --repo guptaneil1/algoverse-summer-26 \
    --title "Cross-model results: ${SHORT}" \
    --notes "Five arms x five seeds, horizon 10."
```

**You should see** a link to the release. Open it in your browser to confirm the file is
there.

Also save the settings so someone can repeat the run:

```bash
git add configs/experiment/pilot_${SHORT}.json data/manifests/${SHORT}
git commit -m "Add ${SHORT} pilot config and manifests"
git push
```

### 6.7 Turn the computer off

**This is the step people forget and it costs real money.**

1. In your browser, go to the Azure portal
2. Search `Virtual machines`, click **hdb-run**
3. Click **Stop** at the top
4. Wait until the status reads **Stopped (deallocated)**

**"Stopped" alone is not enough.** It must say **deallocated**. If it does not, click Stop
again.

When you want to run the next model, click **Start** on the same page, get the new Public
IP (it changes), and go back to §4.2. Your files are all still there.

---

### 6.8 Running several models at once

**Only do this after SmolLM2-135M has finished and uploaded successfully.** The point of
running it alone first is to find problems on one cheap machine rather than four.

Once it has worked, the remaining models can all run simultaneously. There is nothing
clever to it: you make more computers and do the same thing on each.

**For each remaining model:**

1. Do **Part 3** again, giving the machine a name that says which model it is —
   `hdb-pythia`, `hdb-pythia410`, `hdb-qwen`. Do not call them all `hdb-run` or you will
   lose track of which is which.
2. Do **Part 4** and **Part 5** on it, exactly as before.
3. Do **Part 6**, using that model's `SHORT` and `HF_ID` from the table in §6.1.

Each machine works on one model and knows nothing about the others. You can start all of
them within about an hour, then leave them.

**Write down which machine is doing which model.** Something like:

```
hdb-pythia      20.121.45.68    Pythia-160M     started Tue 3pm
hdb-pythia410   20.121.45.69    Pythia-410M     started Tue 3pm
hdb-qwen        20.121.45.70    Qwen2.5-0.5B    started Tue 4pm
```

You will be connecting to several machines and it is genuinely easy to run the wrong
command on the wrong one.

**Two warnings:**

- **You are now paying for every machine, every hour.** Four small machines is about
  $2/hour together. The total cost is the same as running them one at a time, but it
  arrives four times faster, so watch your budget alert emails.
- **You must deallocate every one of them** (§6.7). Four forgotten machines cost four
  times as much as one.

**Keep the three Pythia models on the same machine size.** They are the size comparison, so
all three must use `Standard_NC4as_T4_v3`. Changing hardware between them would mean two
things varied at once and the comparison would not mean anything.

> **The advanced option, if you are comfortable:** a single machine with several graphics
> cards can split one model's work across them using `--shard-index` and `--shard-count`.
> The original GPT-2 run did this. It is faster per model but more fiddly, and separate
> machines get you the same finish time with simpler instructions. Stick with separate
> machines unless you have a reason not to.

---

## Part 7 — When something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| Quotas page is empty | Compute service not turned on | Redo §2.3 |
| "Unable to adjust" on quota | Sponsored account | File the support request, §2.4 |
| VM creation fails on size | Quota not approved yet | Check the row says `0 of 20` |
| `Permission denied (publickey)` | Key file permissions | Redo §4.1 |
| `command not found: nvidia-smi` | Wrong VM image | Delete the VM, redo Part 3 with the NVIDIA image |
| `Authentication failed` on git clone | Used your password | Use a personal access token, §5.1 |
| Anything mentioning `wandb` | Helper file missing or mistyped | Redo §5.3, pasting the whole block including the `PY` lines |
| `No space left on device` | Disk full | Check you are on the `cross-model/add-model-families` branch |
| `make_model_pilot.py` says "CANNOT BUILD CONFIG" | Data not prepared | Do §6.2 first |
| Terminal seems frozen | It is working | **Wait.** Do not press Ctrl-C |
| Laptop disconnected mid-run | Nothing, if you used tmux | Reconnect, `tmux attach -t run` |
| Budget check fails in §6.5 | Run is not valid | Do not upload. Report it to the team |

### If you are stuck

Copy the **last 20 lines** of what the terminal printed and send them to the team. Do not
paraphrase — the exact text is what makes it diagnosable.

---

## Part 8 — Costs

Prices are approximate. Check the Azure pricing calculator for your region.

| Model | Hours | On a T4 (~$0.53/hr) | On an A100 (~$3.67/hr) |
|---|---|---|---|
| SmolLM2-135M | 9 | ~$5 | ~$33 |
| Pythia-160M | 11 | ~$6 | ~$40 |
| Pythia-410M | 28 | ~$15 | ~$103 |
| Qwen2.5-0.5B | 34 | ~$18 | ~$125 |
| Pythia-1B | 68 | — | ~$250 |

Run the first four on a T4. For Pythia-1B, create a second VM with size
`Standard_NC24ads_A100_v4` instead.

**Important:** run all three Pythia models on the **same VM size**. They are the size
comparison, so if one runs on a T4 and another on an A100 you have changed two things at
once.

---

## Checklist

- [ ] Credit amount and expiry written down
- [ ] Budget alert set at 50/75/90%
- [ ] `Microsoft.Compute` says `Registered`
- [ ] Quota approved (row reads `0 of 20`)
- [ ] VM created, auto-shutdown on, 256 GB disk
- [ ] `hdb-key.pem` saved somewhere safe
- [ ] `nvidia-smi` shows a GPU
- [ ] Tests pass
- [ ] Per model: data prepared, config made, efficiency number sane
- [ ] Per model: run finished, `--check-only` passed
- [ ] Per model: release uploaded, config committed
- [ ] **Every** VM shows **Stopped (deallocated)** — check each one

---

## What this does not cover

The front-loaded schedule experiment. The settings file for it
(`configs/policy/schedule_only_frontloaded.json`) is on this branch, but adding it to a run
means editing a frozen configuration, which should be a deliberate team decision rather
than a step in a runbook. It is about five chains and it is the experiment that makes the
paper's claim about timing testable. Worth doing — but separately, and with the team.
