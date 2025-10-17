"""
modified based on Bonito train
"""

import math
import os, sys
import re
from glob import glob
from functools import partial
from time import perf_counter
from collections import OrderedDict
from datetime import datetime
from torch.optim.lr_scheduler import OneCycleLR
from densecall.schedule import linear_warmup_cosine_decay, one_cycle_lr_scheduler
from densecall.util import accuracy, decode_ref, permute, concat, match_names, load_model
import densecall
from torch.utils.tensorboard import SummaryWriter
from torch.nn import functional as F
from torch import nn
import torch
import numpy as np
from accelerate import Accelerator
from tqdm import tqdm



def load_state(dirname, device, model, scheduler, optim=None):
    """
    Load a model state dict from disk
    """
    model.to(device)
    if hasattr(model, "module"):
        model = model.module

    weight_no = optim_no = sche_no = None

    optim_files = glob(os.path.join(dirname, "optim_*.tar"))
    optim_nos = {int(re.sub(".*_([0-9]+).tar", "\\1", w)) for w in optim_files}

    weight_files = glob(os.path.join(dirname, "weights_*.tar"))
    weight_nos = {int(re.sub(".*_([0-9]+).tar", "\\1", w)) for w in weight_files}

    if optim is not None:
        weight_no = optim_no = sche_no = max(optim_nos & weight_nos, default=None)
    else:
        weight_no = max(weight_nos, default=None)
    # print(optim_no)
    to_load = []
    if weight_no:
        to_load.append(("weights", model))
    if optim_no:
        to_load.append(("optim", optim))
    # if sche_no:
    #     to_load.append(("scheduler", scheduler))

    if to_load:
        print("[picking up %s state from epoch %s]" % (", ".join([n for n, _ in to_load]), weight_no))
        for name, obj in to_load:

            state_dict = torch.load(os.path.join(dirname, "%s_%s.tar" % (name, weight_no)), map_location=device, weights_only=True)
            if name == "weights":
                state_dict = {k2: state_dict[k1] for k1, k2 in match_names(state_dict, obj).items()}
                new_state_dict = OrderedDict()
                for k, v in state_dict.items():
                    name = k.replace("module.", "")
                    new_state_dict[name] = v
                # state_dict = new_state_dict

            try:
                obj.load_state_dict(new_state_dict)

            except:

                obj.load_state_dict(state_dict)

        epoch = weight_no
    else:
        epoch = 0

    return epoch


class ClipGrad:
    def __init__(self, quantile=0.5, factor=2.0, buffer_size=100):
        self.buffer = np.full(buffer_size, fill_value=1e3)
        self.quantile = quantile
        self.factor = factor
        self.i = 0

    def append(self, grad_norm):
        self.buffer[self.i] = grad_norm
        self.i = (self.i + 1) % len(self.buffer)

    def __call__(self, parameters):
        max_norm = self.factor * np.quantile(self.buffer, self.quantile)
        grad_norm = torch.nn.utils.clip_grad_norm_(parameters, max_norm=max_norm).item()
        if not math.isnan(grad_norm):
            self.append(grad_norm)
        return grad_norm


class Trainer:
    def __init__(
        self,
        model,
        device,
        train_loader,
        valid_loader,
        criterion=None,
        use_amp=True,
        lr_scheduler_fn=None,
        restore_optim=False,
        save_optim_every=1,
        grad_accum_split=1,
        pretrain_grad_accum_split=1,
        pretrain_epochs=100,
        pretrain=False,
        pretrained_file=None,
        quantile_grad_clip=False,
        config=None,
        teacher_model = None,
        compile = False
    ):
        self.config = config
        self.compile = compile
        self.model = model.to(device)
        self.device = device
        self.train_loader = train_loader
        self.valid_loader = valid_loader
        self.criterion = criterion or model.loss
        self.use_amp = use_amp
        self.lr_scheduler_fn = linear_warmup_cosine_decay(warmup_steps=self.config.get('general', {}).get('warmup_steps', 500))
        self.restore_optim = restore_optim
        self.save_optim_every = save_optim_every
        self.grad_accum_split = grad_accum_split
        self.pretrain_grad_accum_split = pretrain_grad_accum_split
        self.pretrain_epochs = pretrain_epochs
        self.pretrain = pretrain
        self.pretrained_file = pretrained_file
        self.scaler = torch.amp.GradScaler(enabled=use_amp)
        self.optimizer = None
        self.global_step = 0
        
        self.teacher_model = teacher_model
        

        if quantile_grad_clip:
            self.clip_grad = ClipGrad()
        else:
            self.clip_grad = lambda parameters: torch.nn.utils.clip_grad_norm_(parameters, max_norm=2.0).item()

    def chunk_pass(self, y_len, chunks, filter_mean_dwell=3, filter_max_dwell=10):

        chunk_length = chunks.shape[-1]
        mean_dwell = chunk_length / y_len
        max_dwell = torch.max(y_len)
        mean_dwell_dev_from_median = torch.abs(mean_dwell - self.median_meandwell)
        if chunk_length / (y_len * self.model.stride) <= 1.1:
            return True
        if mean_dwell_dev_from_median > filter_mean_dwell * self.mad_meandwell:
            return True
        if max_dwell > filter_max_dwell * self.median_meandwell:
            return True
        return False


    def train_one_step(self, batch, lr_scheduler):
            
        self.optimizer.zero_grad()
        losses = None
        N = batch[0].shape[0]

        for batch_ in zip(*map(lambda t: t.chunk(self.grad_accum_split, dim=0), batch)):
            data_, data_lengths_, targets_, lengths_, *args = (x.to(self.device, non_blocking=True) for x in batch_)
            with torch.autocast(device_type="cuda", enabled=self.use_amp):
                scores_ = self.model(data_, *args)
                try:
                    losses_ = self.criterion(scores_, data_lengths_, targets_, lengths_)
                except:
                    losses_ = self.criterion(scores_, targets_, lengths_)

                if not isinstance(losses_, dict):
                    losses_ = {"loss": losses_}
                    
                if self.teacher_model:
                    with torch.no_grad():
                        teacher_outputs = self.teacher_model(data_, *args)
                        if type(teacher_outputs) is tuple:
                            teacher_outputs = teacher_outputs[0]
                            
                    alpha = 0.3
                    temperature = 2
                    student_outputs = scores_[0] if type(scores_) is tuple else scores_
                    soft_targets = torch.softmax(teacher_outputs / temperature, dim=-1).detach()
                    soft_student_outputs = F.log_softmax(student_outputs / temperature, dim=-1)
                    distillation_loss = nn.KLDivLoss(reduction='batchmean')(soft_student_outputs, soft_targets) * (temperature * temperature)
                    losses_["distillation_loss"] = distillation_loss
                    losses_["total_loss"] = losses_.get("total_loss", losses_["loss"])*alpha + distillation_loss*(1-alpha)

                total_loss = losses_.get("total_loss", losses_["loss"]) / self.grad_accum_split
                    
            self.scaler.scale(total_loss).backward()

            losses = {k: ((v.item() / self.grad_accum_split) if losses is None else (v.item() / self.grad_accum_split) + losses[k]) for k, v in losses_.items()}

           
        self.scaler.unscale_(self.optimizer)            
        grad_norm = self.clip_grad(self.model.parameters())
        self.scaler.step(self.optimizer)
        self.scaler.update()


        return losses, grad_norm

    def train_one_epoch(self, loss_log, lr_scheduler):

        t0 = perf_counter()
        chunks = 0
        self.model.train()
        progress_bar = tqdm(total=len(self.train_loader), desc="[0/{}]".format(len(self.train_loader.sampler)), ascii=True, leave=True, ncols=100, bar_format="{l_bar}{bar}| [{elapsed}{postfix}]")
        smoothed_loss = None
        train_loopcount = 0
        total_samples = len(self.train_loader.sampler)
        with progress_bar:
            # with torch.profiler.profile(
            #         schedule=torch.profiler.schedule(wait=1, warmup=4, active=3, repeat=1),
            #         on_trace_ready=torch.profiler.tensorboard_trace_handler('./profiler'),
            #         record_shapes=True,
            #         profile_memory=True,
            #         with_stack=True
            # ) as prof:
                for batch in self.train_loader:
                    self.model.train()

                    if batch[0].shape[1] != 1:
                        batch[0] = torch.unsqueeze(batch[0], 1)
                    chunks += batch[0].shape[0]

                    losses, grad_norm = self.train_one_step(batch, lr_scheduler)

                    smoothed_loss = losses["loss"] if smoothed_loss is None else (0.01 * losses["loss"] + 0.99 * smoothed_loss)

                    progress_bar.set_postfix(loss="%.4f" % smoothed_loss)
                    progress_bar.set_description("[{}/{}]".format(chunks, total_samples))
                    progress_bar.update()

                    for loss_type in losses:
                        pass
                        self.writer.add_scalar(f"Train/{loss_type}", losses[loss_type], global_step=self.global_step)

                    self.writer.add_scalar("Train/lr", self.optimizer.param_groups[0]["lr"], global_step=self.global_step)

                    self.global_step += 1

                    if loss_log is not None:
                        lr = lr_scheduler.get_last_lr() if lr_scheduler is not None else [pg["lr"] for pg in optim.param_groups]
                        if len(lr) == 1:
                            lr = lr[0]
                        loss_log.append({"chunks": chunks, "time": perf_counter() - t0, "grad_norm": grad_norm, "lr": lr, **losses})

                    train_loopcount += 1

                    if lr_scheduler is not None:
                        lr_scheduler.step()  # for cosine
                        
                    #prof.step()

        return smoothed_loss, perf_counter() - t0

    @torch.no_grad()
    def validate_one_step(self, batch):
        if batch[0].shape[1] != 1:
            batch[0] = torch.unsqueeze(batch[0], 1)
        data, data_lengths, targets, lengths, *args = batch
        data = data.to(self.device)
        targets = targets.to(self.device)
        data_lengths = data_lengths.to(self.device)
        lengths = lengths.to(self.device)
        with torch.autocast(device_type="cuda", enabled=self.use_amp):

            scores = self.model.forward(data, *(x.to(self.device, non_blocking=True) for x in args))
            try:
                losses = self.criterion(scores, data_lengths, targets, lengths)
            except:
                losses = self.criterion(scores, targets, lengths)

            # scores, predicted_log_probs = self.model.joint_forward(data, data_lengths, targets, lengths)
            # losses = self.criterion(scores, predicted_log_probs, data_lengths, targets, lengths)
            
            if not isinstance(losses, dict):
                    losses = {"loss": losses}
                    
           
            losses = {k: v.item() for k, v in losses.items()} if isinstance(losses, dict) else losses.item()
            
              

            if hasattr(self.model, "decode_batch"):
                seqs = self.model.decode_batch(scores)
                
            elif hasattr(self.model, "joint_decode"):
                seqs = self.model.joint_decode(scores)
            else:
                if type(scores) is tuple:
                    scores = scores[0]    
                seqs = [self.model.decode(x, beamsize=5) for x in permute(scores, "TNC", "NTC")]

        refs = [decode_ref(target, self.model.alphabet) for target in targets]

        n_pre = getattr(self.model, "n_pre_context_bases", 0)
        n_post = getattr(self.model, "n_post_context_bases", 0)
        if n_pre > 0 or n_post > 0:
            refs = [ref[n_pre : len(ref) - n_post] for ref in refs]
        accs = [accuracy(ref, seq, min_coverage=0.5) if len(seq) else 0.0 for ref, seq in zip(refs, seqs)]

        return seqs, refs, accs, losses

    def validate_one_epoch(self, lr_scheduler):
        self.model.eval()
        with torch.no_grad():
            seqs, refs, accs, losses = zip(*(self.validate_one_step(batch) for batch in self.valid_loader))
        seqs, refs, accs = (sum(x, []) for x in (seqs, refs, accs))
        loss = np.mean([(x["loss"] if isinstance(x, dict) else x) for x in losses])

        return loss, np.mean(accs), np.median(accs)

    def init_optimizer(self, lr, **kwargs):
        if isinstance(lr, (list, tuple)):
            if len(list(self.model.children())) != len(lr):
                raise ValueError("Number of lrs does not match number of model children")
            param_groups = [{"params": list(m.parameters()), "lr": v} for (m, v) in zip(self.model.children(), lr)]
            self.optimizer = torch.optim.AdamW(param_groups, lr=lr[0], **kwargs)
        else:
            try:
                from densecall.conformer.optimize import get_optimizer
                self.optimizer  = get_optimizer(self.config['general']['optimizer'], self.model, lr=lr, wd=self.config['general']['wd'])
                
                # from densecall.conformer.muon_optimizer import SingleDeviceMuonWithAuxAdam, create_muon_param_groups
                # param_groups = create_muon_param_groups(self.model, muon_lr=lr)
                # self.optimizer = SingleDeviceMuonWithAuxAdam(param_groups)
                print("[Using optimizer]", self.config['general']['optimizer'])
            except Exception as e:
                print("[Using optimizer]", 'adamw')
                print("[Error]", e)
                self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, eps=1e-4, **kwargs)


    def get_lr_scheduler(self, epochs, last_epoch=0):

        return self.lr_scheduler_fn(self.optimizer, self.train_loader, epochs, last_epoch)

    def get_last_epoch_no(self, workdir):
        weight_files = glob(os.path.join(workdir, "weights_*.tar"))
        if len(weight_files) == 0:
            return 0
        weight_nos = {int(re.sub(".*_([0-9]+).tar", "\\1", w)) for w in weight_files}
        return max(weight_nos, default=None)

    def run_mlm_training(self, workdir, epochs=100):
        """
        Perform masked language model (MLM) training.

        :param self: Trainer class instance
        :param workdir: Working directory
        :param epochs: Number of training epochs, default is 100
        """
        from densecall.conformer.wav2vec2 import Wav2Vec2Model

        print("[run_mlm_training]")
        model = Wav2Vec2Model(self.config).to(self.device)

        latest_file = self._find_latest_pretrained_file(workdir)
        
        if latest_file:
            print(f"Loaded latest pretrained model from {latest_file}")
            checkpoint = torch.load(latest_file, map_location=self.device)
            model.load_state_dict(checkpoint["model_state_dict"])
            optim, scheduler = self._init_optimizer_and_scheduler(model, epochs, checkpoint)
            start_epoch = checkpoint["epoch"] + 1
            self.global_step = checkpoint["global_step"] + 1
        else:
            print("No pretrained model files found in the work directory. Initializing from scratch.")
            optim, scheduler = self._init_optimizer_and_scheduler(model, epochs)
            start_epoch = 0

        
        accelerator = None #Accelerator(mixed_precision='no')
        # model, optim, scheduler, self.train_loader, self.valid_loader = accelerator.prepare(
        #     model, optim, scheduler, self.train_loader, self.valid_loader
        # )
        
        for epoch in range(start_epoch, epochs):

            train_loss = self._train_one_mlm_epoch(model, optim, scheduler, accelerator)
            valid_loss = 0 #self._valid_one_mlm_epoch(model, epoch)

            print("[pretrain epoch {}] directory={} train_loss={:.4f} valid_loss={:.4f} lr={:.3e}".format(epoch, workdir, train_loss, valid_loss, optim.param_groups[0]["lr"]))

            model_path = os.path.join(workdir, f"wav2vec2_pretrained_epoch_{epoch}.pth")

            #accelerator.wait_for_everyone()
            #unwrapped_model = accelerator.unwrap_model(model)

            torch.save(
                {
                    "epoch": epoch,
                    "global_step": self.global_step,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optim.state_dict(),
                    "scheduler_state_dict": scheduler.state_dict(),
                },
                model_path,
            )
            

        self.global_step = 0



    def _find_latest_pretrained_file(self, workdir):
        """
        Find the latest pre-trained model file.

        :param workdir: Working directory
        :return: Path to the latest pre-trained model file, None if not found
        """
        if self.pretrained_file:
            return self.pretrained_file
        
        pretrained_files = glob(os.path.join(workdir, "wav2vec2_pretrained_epoch_*.pth"))
        if pretrained_files:
            epoch_file_pairs = [(int(re.search(r"wav2vec2_pretrained_epoch_(\d+).pth", f).group(1)), f) for f in pretrained_files if re.search(r"wav2vec2_pretrained_epoch_(\d+).pth", f)]
            if epoch_file_pairs:
                _, latest_file = max(epoch_file_pairs)
                return latest_file
        return None

    def _init_optimizer_and_scheduler(self, model, epochs, checkpoint=None):
        """
        Initialize the optimizer and scheduler.

        :param model: Model instance
        :param epochs: Number of training epochs
        :param checkpoint: Checkpoint dictionary, optional
        :return: Optimizer and scheduler instances
        """
        # from densecall.conformer.optimize import get_optimizer
        # optim = get_optimizer(model, lr=3e-4, keywords=["feature_extractor", "fc", "embed","quantizer", "project_hid", "project_q"])
        optim = torch.optim.AdamW(model.parameters(), lr=5e-4, eps=1e-6, weight_decay=0.1)
        total_steps = epochs * len(self.train_loader)
        warmup_steps = 2000 #int(total_steps * 0.3)
        print("[total_steps]", total_steps)
        print("[warmup_steps]", warmup_steps)

        # print(model)
        def cosine_linear_decay(step):
            if step < warmup_steps:
                return float(step) / float(max(1, warmup_steps))
            else:
                progress = float(step - warmup_steps) / float(max(1, total_steps - warmup_steps))
                return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))

        scheduler = torch.optim.lr_scheduler.LambdaLR(optim, lr_lambda=cosine_linear_decay)

        if checkpoint:
            if "optimizer_state_dict" in checkpoint:
                optim.load_state_dict(checkpoint["optimizer_state_dict"])
            if "scheduler_state_dict" in checkpoint:
                scheduler.load_state_dict(checkpoint["scheduler_state_dict"])

        return optim, scheduler

    def multiply_grads(self, params, c):
        """Multiplies grads by a constant *c*."""
        for p in params:
            if p.grad is not None:
                if torch.is_tensor(c):
                    c = c.to(p.grad.device)
                p.grad.data.mul_(c)

    def compute_gradient_norm(self, params, scale=1):
        """Compute grad norm given a gradient scale."""
        total_norm = 0.0
        for p in params:
            if p.grad is not None:
                param_norm = (p.grad.detach().data / scale).norm(2)
                total_norm += param_norm.item() ** 2
        total_norm = total_norm**0.5
        return total_norm




    def _train_one_mlm_epoch2(self, model, optim, scheduler, accelerator, max_gumbel_temperature=2, min_gumbel_temperature=0.5, gumbel_temperature_decay=0.999995):
        """
        Perform one epoch of MLM training.

        :param model: Model instance
        :param optim: Optimizer instance
        :param scheduler: Scheduler instance
        :param epoch: Current epoch number
        :param workdir: Working directory
        :return: Smoothed loss value
        """
        

        chunks = 0
        progress_bar = tqdm(total=len(self.train_loader), desc="[0/{}]".format(len(self.train_loader.sampler)), ascii=True, leave=True, ncols=100, bar_format="{l_bar}{bar}| [{elapsed}{postfix}]")

        train_all_loss = []

        for batch in self.train_loader:
            model.train()
            optim.zero_grad()
            chunks += batch[0].shape[0]
            if batch[0].shape[1] != 1:
                batch[0] = torch.unsqueeze(batch[0], 1)
                
            N, _, T = batch[0].shape

            for batch_ in zip(*map(lambda t: t.chunk(self.pretrain_grad_accum_split, dim=0), batch)):
                data_ = batch_[0]


                loss, contrastive_loss, diversity_loss, codevector_perplexity, mask_time_indices = model.calculate_loss(data_)
                sub_attention_mask  = torch.ones_like(mask_time_indices)
                num_losses = mask_time_indices.sum()
                percent_masked = (num_losses / sub_attention_mask.sum()).item()


                loss = loss / self.pretrain_grad_accum_split

                accelerator.backward(loss)  # 使用 Accelerator 进行反向传播


                if accelerator.state.num_processes > 1:
                    num_losses = accelerator.gather(num_losses).sum()
                    gradient_multiplier = accelerator.state.num_processes / num_losses
                    self.multiply_grads(model.module.parameters(), gradient_multiplier)
                else:
                    self.multiply_grads(model.parameters(), 1 / num_losses)
                
            scale = (
                    accelerator.scaler._scale.item()
                    if hasattr(accelerator, "scaler") and accelerator.scaler is not None
                    else 1
                )

            grad_norm = self.compute_gradient_norm(model.parameters(), scale)

            log_loss = (loss.detach().item() * self.pretrain_grad_accum_split) / num_losses
            train_all_loss.append(log_loss)
            

            optim.step()  # 更新优化器
            scheduler.step()

            self.writer.add_scalar("PreTrain/%_mask_idx", percent_masked, global_step=self.global_step)
            self.writer.add_scalar("PreTrain/grad_norm", grad_norm, global_step=self.global_step)
            self.writer.add_scalar("PreTrain/loss", log_loss, global_step=self.global_step)
            self.writer.add_scalar("PreTrain/contrastive_loss",  contrastive_loss / num_losses, global_step=self.global_step)
            self.writer.add_scalar("PreTrain/diversity_loss", diversity_loss / num_losses, global_step=self.global_step)
            self.writer.add_scalar("PreTrain/ppl", codevector_perplexity, global_step=self.global_step)
            self.writer.add_scalar("PreTrain/lr", optim.param_groups[0]["lr"], global_step=self.global_step)

            progress_bar.set_postfix(loss="%.4f" % log_loss)
            progress_bar.set_description("[{}/{}]".format(chunks, len(self.train_loader.sampler)))
            progress_bar.update()

            if model.use_quantizer:
                gumbel_temperature = max(
                    max_gumbel_temperature * gumbel_temperature_decay**self.global_step,
                    min_gumbel_temperature,
                )

                model.set_gumbel_temperature(gumbel_temperature)
                self.writer.add_scalar("PreTrain/gumbel_temperature", gumbel_temperature, global_step=self.global_step)

            self.global_step += 1

        return torch.mean(torch.tensor(train_all_loss))
    
    def _valid_one_mlm_epoch(self, model, epoch):
        """
        Perform one epoch of MLM training.

        :param model: Model instance
        :param optim: Optimizer instance
        :param scheduler: Scheduler instance
        :param epoch: Current epoch number
        :param workdir: Working directory
        :return: Smoothed loss value
        """

        valid_all_loss = []

        for batch in self.valid_loader:
            model.eval()
            if batch[0].shape[1] != 1:
                batch[0] = torch.unsqueeze(batch[0], 1)
            with torch.no_grad():
                for batch_ in zip(*map(lambda t: t.chunk(self.pretrain_grad_accum_split, dim=0), batch)):
                    data_ = batch_[0].to(self.device)
                    loss, contrastive_loss, diversity_loss, codevector_perplexity, mask_time_indices = model.calculate_loss(data_)
                    num_losses = mask_time_indices.sum()
                    loss = loss / self.pretrain_grad_accum_split

            log_loss = (loss.detach().item() * self.pretrain_grad_accum_split) #/ num_losses
            valid_all_loss.append(log_loss)

            self.writer.add_scalar("PreValid/loss", log_loss, global_step=epoch)
            self.writer.add_scalar("PreValid/contrastive_loss",  contrastive_loss / num_losses, global_step=epoch)
            self.writer.add_scalar("PreValid/diversity_loss", diversity_loss / num_losses, global_step=epoch)
            self.writer.add_scalar("PreValid/ppl", codevector_perplexity, global_step=epoch)


        return torch.mean(torch.tensor(valid_all_loss))
    
    def _train_one_mlm_epoch(self, model, optim, scheduler, accelerator, max_gumbel_temperature=2, min_gumbel_temperature=0.5, gumbel_temperature_decay=0.999995):
        """
        Perform one epoch of MLM training.

        :param model: Model instance
        :param optim: Optimizer instance
        :param scheduler: Scheduler instance
        :param epoch: Current epoch number
        :param workdir: Working directory
        :return: Smoothed loss value
        """
        chunks = 0
        progress_bar = tqdm(total=len(self.train_loader), desc="[0/{}]".format(len(self.train_loader.sampler)), ascii=True, leave=True, ncols=100, bar_format="{l_bar}{bar}| [{elapsed}{postfix}]")

        train_all_loss = []

        for i, batch in enumerate(self.train_loader):
            model.train()
            optim.zero_grad()
            chunks += batch[0].shape[0]
            if batch[0].shape[1] != 1:
                batch[0] = torch.unsqueeze(batch[0], 1)
            total_num_losses = 0
            N, _, T = batch[0].shape

              # 启用自动混合精度
            for batch_ in zip(*map(lambda t: t.chunk(self.pretrain_grad_accum_split, dim=0), batch)):
                with torch.autocast(device_type="cuda", enabled=self.use_amp):
                    data_ = batch_[0].to(self.device)
                    loss, contrastive_loss, diversity_loss, codevector_perplexity, mask_time_indices  = model.calculate_loss(data_)
                    sub_attention_mask  = torch.ones_like(mask_time_indices)
                    num_losses = mask_time_indices.sum()
                    percent_masked = (num_losses / sub_attention_mask.sum()).item()
                    total_num_losses += num_losses.item()
                    loss = loss / self.pretrain_grad_accum_split
            
                self.scaler.scale(loss).backward()  # 使用 GradScaler 缩放损失并反向传播


            self.scaler.unscale_(optim)  # 取消梯度缩放
            grad_norm = self.compute_gradient_norm(model.parameters(), 1)

            log_loss = (loss.detach().item() * self.pretrain_grad_accum_split) #/ num_losses
            train_all_loss.append(log_loss)

            self.scaler.step(optim)  # 使用 GradScaler 更新优化器
            self.scaler.update()  # 更新缩放因子
            scheduler.step()

            self.writer.add_scalar("PreTrain/%_mask_idx", percent_masked, global_step=self.global_step)
            self.writer.add_scalar("PreTrain/grad_norm", grad_norm, global_step=self.global_step)
            self.writer.add_scalar("PreTrain/loss", log_loss, global_step=self.global_step)
            self.writer.add_scalar("PreTrain/contrastive_loss",  contrastive_loss, global_step=self.global_step)
            self.writer.add_scalar("PreTrain/diversity_loss", diversity_loss, global_step=self.global_step)
            self.writer.add_scalar("PreTrain/ppl", codevector_perplexity, global_step=self.global_step)
            self.writer.add_scalar("PreTrain/lr", optim.param_groups[0]["lr"], global_step=self.global_step)

            progress_bar.set_postfix(loss="%.4f" % log_loss)
            progress_bar.set_description("[{}/{}]".format(chunks, len(self.train_loader.sampler)))
            progress_bar.update()

            if model.use_quantizer:
                gumbel_temperature = max(
                    max_gumbel_temperature * gumbel_temperature_decay**self.global_step,
                    min_gumbel_temperature,
                )

                model.set_gumbel_temperature(gumbel_temperature)
                self.writer.add_scalar("PreTrain/gumbel_temperature", gumbel_temperature, global_step=self.global_step)

            self.global_step += 1

        return torch.mean(torch.tensor(train_all_loss))

    def load_pretrained_model(self, workdir):
            
        if hasattr(self.model, 'quantizer'):
            del self.model.quantizer
        if hasattr(self.model, 'project_hid'):
            del self.model.project_hid
        if hasattr(self.model, 'project_q'):
            del self.model.project_q
            
        latest_file = self._find_latest_pretrained_file(workdir) if not self.pretrained_file else self.pretrained_file
        if not latest_file:
            print(f"[No pretrained model found in {workdir}]")
            return

        checkpoint = torch.load(latest_file, map_location=self.device)
        pretrained_state_dict = checkpoint["model_state_dict"]
        
        
        model_state_dict = self.model.state_dict()
        matched_state_dict = {k: v for k, v in pretrained_state_dict.items() if k in model_state_dict and model_state_dict[k].shape == v.shape}

        unmatched_keys = [k for k in pretrained_state_dict if k not in matched_state_dict]
        if unmatched_keys:
            print(f"Unmatched keys in pretrained state dict: {unmatched_keys}")
    
        model_state_dict.update(matched_state_dict)
        self.model.load_state_dict(model_state_dict)
        

            
        # cnn_strides = self.config['feature_extractor']['conv_stride_finetune']
        # for inx, single_cnn in enumerate(self.model.feature_extractor.conv_layers):
        #     single_cnn.conv.stride=(cnn_strides[inx],) 

        #self.model.feature_extractor._freeze_parameters()
        # for param in self.model.feature_extractor.parameters():
        #     param.requires_grad = False

        # for name, param in self.model.named_parameters():
        #     print(name, param.requires_grad)


        print(f"[Successfully loaded pretrained model from {latest_file}]")
        

    def fit(self, workdir, epochs=1, lr=2e-3, **optim_kwargs):
        
        timestamp = datetime.now().strftime("%Y%m%d")
        self.writer = SummaryWriter(log_dir=f"{workdir}/runs_{timestamp}", purge_step=0)

        last_epoch = self.get_last_epoch_no(workdir)
        if self.optimizer is None:
            self.init_optimizer(lr, **optim_kwargs)

        lr_scheduler = self.get_lr_scheduler(epochs, last_epoch=last_epoch)

        last_epoch = load_state(workdir, self.device, self.model, lr_scheduler, self.optimizer if self.restore_optim else None)

        if self.restore_optim:
            print("[override learning rate to new value]")
            for i, pg in enumerate(self.optimizer.param_groups):
                pg["initial_lr"] = pg["lr"] = lr[i] if isinstance(lr, (list, tuple)) else lr

        if self.pretrain:
            self.run_mlm_training(workdir, epochs=self.pretrain_epochs)
            print("Pretrain done, exit...")
            print("fine tune model without --pretrain --new")
            sys.exit(0)


        self.load_pretrained_model(workdir)
        
        print("alphabet:", self.model.alphabet)
        print("Trainable parameters:", sum(p.numel() for p in self.model.parameters() if p.requires_grad))

        if self.compile:
            self.model = torch.compile(self.model)
            if self.teacher_model:
                self.teacher_model = torch.compile(self.teacher_model)

        # for name, p in self.model.named_parameters():
        #     if p.requires_grad:
        #         print(f"{name:<60} {str(p.shape):<20} {p.dtype}  {p.device}")
        #print(self.model)    
        for epoch in range(1 + last_epoch, epochs + 1):
            try:
                with densecall.io.CSVLogger(os.path.join(workdir, "losses_{}.csv".format(epoch))) as loss_log:
                    train_loss, duration = self.train_one_epoch(loss_log, lr_scheduler)

                model_state = self.model.module.state_dict() if hasattr(self.model, "module") else self.model.state_dict()
                torch.save(model_state, os.path.join(workdir, "weights_%s.tar" % epoch))
                if epoch % self.save_optim_every == 0:
                    torch.save(self.optimizer.state_dict(), os.path.join(workdir, "optim_%s.tar" % epoch))
                    torch.save(lr_scheduler.state_dict(), os.path.join(workdir, "scheduler_%s.tar" % epoch))

                val_loss, val_mean, val_median = self.validate_one_epoch(lr_scheduler)
            except KeyboardInterrupt:
                break

            print("[epoch {}] directory={} loss={:.4f} mean_acc={:.3f}% median_acc={:.3f}%".format(epoch, workdir, val_loss, val_mean, val_median))

            self.writer.add_scalar("Val/mean_acc", val_mean, global_step=epoch)
            self.writer.add_scalar("Val/median_acc", val_median, global_step=epoch)
            self.writer.add_scalar(f"Val/loss", val_loss, global_step=epoch)


            with densecall.io.CSVLogger(os.path.join(workdir, "training.csv")) as training_log:
                training_log.append(
                    {
                        "time": datetime.today(),
                        "duration": int(duration),
                        "epoch": epoch,
                        "train_loss": train_loss,
                        "validation_loss": val_loss,
                        "validation_mean": val_mean,
                        "validation_median": val_median,
                    }
                )
