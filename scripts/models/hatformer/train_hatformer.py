"""Fine-tune HATFormer on our metadata.csv.

Plain-PyTorch trainer (no Lightning) so it runs in the project env as-is and on
CPU/MPS for smoke tests, while staying GPU-ready. Runs one EXPERIMENT at a time;
each experiment in the config specifies its own init checkpoint and training data:
    muharaf_ours : init hatformer-muharaf    + ours   (exp 1)
    synth_ours   : init hatformer-synthetic  + ours   (exp 2)

Usage:
    python scripts/models/hatformer/train_hatformer.py --experiment muharaf_ours
    python scripts/models/hatformer/train_hatformer.py --experiment synth_ours --smoke
"""
import argparse
import os
import shutil
import sys

import torch
import yaml
from torch.utils.data import DataLoader
from transformers import (
    PreTrainedTokenizerFast,
    VisionEncoderDecoderModel,
    get_inverse_sqrt_schedule,
)

# make `arman` importable whether run as a script or a module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from dataset import HatformerLineDataset, load_manifest_split     
from seed import set_seed 


def pick_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def char_error_rate(preds, refs):
    tot_e = tot_n = 0
    for p, r in zip(preds, refs):
        tot_e += _edit_distance(p, r)
        tot_n += max(1, len(r))
    return tot_e / max(1, tot_n)


def build_model_and_tokenizer(cfg, init_path, device):
    tok = PreTrainedTokenizerFast(tokenizer_file=cfg["tokenizer_path"])
    tok.add_special_tokens({
        "pad_token": "<pad>", "eos_token": "</s>", "cls_token": "<s>", "bos_token": "<s>",
    })
    model = VisionEncoderDecoderModel.from_pretrained(init_path)
    # match the original HATFormer training recipe (lightning.py): decoder is
    # teacher-forced starting from <s>, pad aligned to our tokenizer. Generation
    # still uses the checkpoint's generation_config.json.
    model.config.decoder_start_token_id = tok.bos_token_id
    model.config.pad_token_id = tok.pad_token_id
    model.config.vocab_size = model.config.decoder.vocab_size
    model.to(device)
    return model, tok


def make_loaders(cfg, exp, tok):
    tcfg = cfg["train"]
    train_df = load_manifest_split(
        cfg["manifest"], tcfg["split_train"],
    
    )
    val_df = load_manifest_split(
        cfg["manifest"], tcfg["split_val"]
    )
    if cfg.get("_limit"):
        train_df, val_df = train_df.head(cfg["_limit"]), val_df.head(max(2, cfg["_limit"] // 2))

    common = dict(tokenizer=tok, max_text_length=cfg["data"]["max_text_length"],
                  image_cfg=cfg["image"], root=cfg.get("root", "."))
    train_ds = HatformerLineDataset(train_df, **common)
    val_ds = HatformerLineDataset(val_df, **common)
    print(f"  train lines: {len(train_ds)} | val lines: {len(val_ds)}")

    nw = tcfg["num_workers"]
    train_dl = DataLoader(train_ds, batch_size=tcfg["batch_size"], shuffle=True,
                          num_workers=nw, persistent_workers=nw > 0, drop_last=False)
    val_dl = DataLoader(val_ds, batch_size=tcfg["batch_size"], shuffle=False, num_workers=nw,
                        persistent_workers=nw > 0)
    return train_dl, val_dl


@torch.no_grad()
def evaluate(model, tok, val_dl, device, cfg):
    model.eval()
    tcfg = cfg["train"]
    losses, preds, refs = [], [], []
    for bi, batch in enumerate(val_dl):
        pv = batch["pixel_values"].to(device)
        labels = batch["labels"].to(device)
        losses.append(model(pixel_values=pv, labels=labels,
                            interpolate_pos_encoding=True).loss.item())
        if bi < tcfg["val_max_batches"]:
            out = model.generate(pv, num_beams=tcfg["val_num_beams"], length_penalty=0,
                                 max_new_tokens=cfg["data"]["max_text_length"])
            gt = labels.clone()
            gt[gt == -100] = tok.pad_token_id
            preds += tok.batch_decode(out.tolist(), skip_special_tokens=True)
            refs += tok.batch_decode(gt.tolist(), skip_special_tokens=True)
    model.train()
    return sum(losses) / len(losses), char_error_rate(preds, refs), list(zip(preds[:3], refs[:3]))


def _safe_save(model, tok, path):
    """Save a checkpoint; on disk-full / any I/O error, warn and KEEP TRAINING
    instead of crashing, so a full disk doesn't throw away the whole run. Returns
    True on success; removes the half-written dir so it can't load back corrupt."""
    try:
        os.makedirs(path, exist_ok=True)
        model.save_pretrained(path)
        tok.save_pretrained(path)
        return True
    except OSError as e:
        shutil.rmtree(path, ignore_errors=True)
        print(f"  [WARN] checkpoint save failed ({e}). Training continues — "
              f"free disk space and the next improvement will save.")
        return False


def train(cfg, experiment_name):
    tcfg = cfg["train"]
    set_seed(tcfg["seed"])
    device = pick_device()
    exp = cfg["experiments"][experiment_name]
    init_path = cfg["checkpoints"][exp["init"]]
    out_dir = os.path.join(tcfg["output_dir"], experiment_name)
    os.makedirs(out_dir, exist_ok=True)
    print(f"== HATFormer fine-tune | experiment={experiment_name} | device={device} ==")
    print(f"  init: {exp['init']} ({init_path})  ->  out: {out_dir}")

    model, tok = build_model_and_tokenizer(cfg, init_path, device)
    train_dl, val_dl = make_loaders(cfg, exp, tok)

    opt = torch.optim.AdamW(model.parameters(), lr=tcfg["lr"], betas=tuple(tcfg["betas"]),
                            eps=tcfg["eps"], weight_decay=tcfg["weight_decay"])
    sched = get_inverse_sqrt_schedule(opt, num_warmup_steps=tcfg["warmup_steps"])

    step = 0
    best_cer = float("inf")
    model.train()
    done = False
    while not done:
        for batch in train_dl:
            pv = batch["pixel_values"].to(device)
            labels = batch["labels"].to(device)
            loss = model(pixel_values=pv, labels=labels, interpolate_pos_encoding=True).loss
            (loss / tcfg["grad_accum"]).backward()

            if (step + 1) % tcfg["grad_accum"] == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), tcfg["grad_clip"])
                opt.step()
                sched.step()
                opt.zero_grad()

            if step % tcfg["log_every_steps"] == 0:
                print(f"  step {step:>6} | loss {loss.item():.4f} | lr {sched.get_last_lr()[0]:.2e}")

            if step > 0 and step % tcfg["val_every_steps"] == 0:
                vloss, vcer, samples = evaluate(model, tok, val_dl, device, cfg)
                print(f"  [val] step {step} | loss {vloss:.4f} | CER {vcer:.4f}")
                for p, r in samples:
                    print(f"        pred: {p}\n        ref : {r}")
                if vcer < best_cer:
                    if _safe_save(model, tok, os.path.join(out_dir, "best")):
                        best_cer = vcer
                        print(f"  saved best (CER {best_cer:.4f})")

            step += 1
            if step >= tcfg["max_steps"]:
                done = True
                break

    vloss, vcer, _ = evaluate(model, tok, val_dl, device, cfg)
    print(f"== done | final val loss {vloss:.4f} | CER {vcer:.4f} | best CER {min(best_cer, vcer):.4f} ==")
    _safe_save(model, tok, os.path.join(out_dir, "last"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", default="muharaf_ours",
                    choices=["muharaf_ours", "synth_ours", "synth_mix"])
    ap.add_argument("--config", default="configs/ocr_hatformer.yaml")
    ap.add_argument("--max-steps", type=int)
    ap.add_argument("--batch-size", type=int)
    ap.add_argument("--smoke", action="store_true",
                    help="tiny run (few lines, few steps) to validate the loop")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    if args.max_steps:
        cfg["train"]["max_steps"] = args.max_steps
    if args.batch_size:
        cfg["train"]["batch_size"] = args.batch_size
    if args.smoke:
        cfg["_limit"] = 12
        cfg["train"].update(max_steps=6, batch_size=2, warmup_steps=2,
                            val_every_steps=3, val_max_batches=2, log_every_steps=1, num_workers=0)

    train(cfg, args.experiment)


if __name__ == "__main__":
    main()
