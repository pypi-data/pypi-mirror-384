try:
    import torch
    from torch import nn
    import lightning.pytorch as pl
    from transformers.models.bert.modeling_bert import BertEmbeddings
    from timm.layers import trunc_normal_
    from ._vilt.modules import heads, objectives, vilt_utils
    from ._vilt.modules import vision_transformer_prompts as vit
    deepmodule_installed = True
except ImportError:
    deepmodule_installed = False
    deepmodule_error = "Module 'deep' needs to be installed. See https://imml.readthedocs.io/stable/main/installation.html#optional-dependencies"

LightningModuleBase = pl.LightningModule if deepmodule_installed else object


class MissingAwarePrompt(LightningModuleBase):
    r"""
    Multimodal Prompting with Missing Modalities for Visual Recognition.

    This class implements a prompting-based approach to handle missing modalities in multimodal visual recognition.
    The method allows for flexible modality usage at training and inference time, enabling robustness
    to missing visual or textual input.

    It is built using Lightning. Dataloaders must return a dictionary with the keys:
    - 'image': a tensor representing the image modality,
    - 'text': tokenized input for the text modality,
    - 'label': ground-truth labels.

    Parameters
    ----------
    bert_config : BertConfig
        Configuration object for the BERT model used to process the text modality.
    classifier : nn.Sequential
        A neural network classifier that maps the fused multimodal representation to output predictions.
    model : str, default="vit_base_patch32_384"
        Name of the vision model backbone (e.g., a Vision Transformer variant).
    load_path : str, default=""
        Path to a pretrained checkpoint to load the model weights from. You can download the pre-trained ViLT model
        weights from https://github.com/dandelin/ViLT.
    test_only : bool, default=False
        Whether to run the model in evaluation-only mode without training.
    finetune_first : bool, default=False
        Whether to finetune only the backbone initially before training prompts.
    prompt_type : str, default="input"
        Type of prompt injection. One of ['input', 'attention'].
    prompt_length : int, default=16
        Number of prompt tokens.
    learnt_p : bool, default=True
        If True, the prompt embeddings are learnable parameters.
    prompt_layers : list, default=None
        List of layer indices. If None, prompt_layers is [0,1,2,3,4,5].
    multi_layer_prompt : bool, default=True
        If True, prompts are injected into multiple layers of the transformer model.
    loss_name : str, default="accuracy"
        Name of loss functions to be used during training. One of ["accuracy", "F1_scores", "AUROC"]
    learning_rate : float, default=1e-2
        Initial learning rate for the optimizer.
    weight_decay : float, default=2e-2
        Weight decay for the optimizer.
    lr_mult : float, default=1
        Multiplier applied to lr for downstream heads.
    end_lr : float, default=0
        Final learning rate after polynomial decay.
    decay_power : float, default=1
        Power for polynomial learning rate decay scheduling.
    optim_type : str, default="adamw"
        Optimizer type to use (e.g., 'adamw', 'sgd').
    warmup_steps : int, default=2500
        Number of warm-up steps for the learning rate scheduler.

    References
    ----------
    .. [#mappaper] Lee, Yi-Lun, et al. "Multimodal prompting with missing modalities for visual recognition."
                   Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 2023.
    .. [#mapcode] https://github.com/YiLunLee/missing_aware_prompts
    .. [#viltpaper] Kim, Wonjae, Bokyung Son, and Ildoo Kim. "Vilt: Vision-and-language transformer without
                    convolution or region supervision." International conference on machine learning. PMLR, 2021.
    .. [#viltcode] https://github.com/dandelin/ViLT

    Example
    --------
    >>> from imml.classify import MissingAwarePrompt
    >>> from transformers.models.bert.modeling_bert import BertConfig
    >>> from lightning import Trainer
    >>> from torch import nn
    >>> from torch.utils.data import DataLoader
    # create your dataset (follow this tutorial: https://github.com/YiLunLee/missing_aware_prompts/blob/main/DATA.md)
    >>> train_data = ...
    >>> train_dataloader = DataLoader(dataset=train_data)
    >>> trainer = Trainer(max_epochs=2, logger=False, enable_checkpointing=False)
    >>> hidden_size = 768
    >>> mlp_ratio = 4
    >>> cls_num = 2
    >>> bert_config = BertConfig(
            vocab_size=30522,
            hidden_size=hidden_size,
            num_hidden_layers=12,
            num_attention_heads=12,
            intermediate_size=hidden_size * mlp_ratio,
            max_position_embeddings=40,
            hidden_dropout_prob=0.1,
            attention_probs_dropout_prob=0.1,
        )
    >>> classifier = nn.Sequential(
                nn.Linear(hidden_size, hidden_size * 2),
                nn.LayerNorm(hidden_size * 2),
                nn.GELU(),
                nn.Linear(hidden_size * 2, cls_num),
            )
    >>> estimator = Missing_Aware_Prompt(bert_config=bert_config, classifier=classifier)
    >>> trainer.fit(estimator, train_dataloader)
    """

    def __init__(self, bert_config, classifier, model: str = "vit_base_patch32_384", load_path : str = "",
                 test_only: bool = False, finetune_first: bool = False, prompt_type : str = "input",
                 prompt_length : int = 16, learnt_p: bool = True, prompt_layers: list = None,
                 multi_layer_prompt: bool = True, loss_name : str = "accuracy",
                 learning_rate: float = 1e-2, weight_decay: float = 2e-2,
                 lr_mult: float = 1, end_lr: float = 0,
                 decay_power: float = 1, optim_type: str = "adamw", warmup_steps : int = 2500):

        if not deepmodule_installed:
            raise ImportError(deepmodule_error)

        super().__init__()
        self.save_hyperparameters()

        self.text_embeddings = BertEmbeddings(bert_config)
        self.text_embeddings.apply(objectives.init_weights)

        self.token_type_embeddings = nn.Embedding(2, bert_config.hidden_size)
        self.token_type_embeddings.apply(objectives.init_weights)

        self.transformer = getattr(vit, model)(pretrained= load_path == "")

        self.loss_name = loss_name if loss_name is not None else "accuracy"
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.lr_mult = lr_mult
        self.end_lr = end_lr
        self.decay_power = decay_power
        self.optim_type = optim_type
        self.warmup_steps = warmup_steps

        self.pooler = heads.Pooler(bert_config.hidden_size)
        self.pooler.apply(objectives.init_weights)

        # ===================== Downstream ===================== #
        if (
                (load_path != "")
                and not test_only
                and not finetune_first
        ):
            #
            ckpt = torch.load(load_path, map_location="cpu")
            state_dict = ckpt["state_dict"]
            if bert_config.max_text_len != 40:
                state_dict['text_embeddings.position_ids'] = torch.Tensor(range(bert_config.max_text_len)).long().view(1,
                                                                                                                     -1)
                pos_emb = state_dict['text_embeddings.position_embeddings.weight']
                pos_emb = torch.nn.functional.interpolate(pos_emb.view(1, 1, 40, 768),
                                                          size=(bert_config.max_text_len, 768), mode='bilinear').squeeze()
                state_dict['text_embeddings.position_embeddings.weight'] = pos_emb
            self.load_state_dict(state_dict, strict=False)

        self.classifier = classifier
        self.classifier.apply(objectives.init_weights)

        if load_path != "" and finetune_first:
            ckpt = torch.load(load_path, map_location="cpu")
            state_dict = ckpt["state_dict"]
            self.load_state_dict(state_dict, strict=False)
            print("use pre-finetune model")

        self.prompt_type = prompt_type
        self.prompt_length = prompt_length
        self.learnt_p = learnt_p
        self.prompt_layers = prompt_layers if prompt_layers is not None else [0,1,2,3,4,5]
        self.multi_layer_prompt = multi_layer_prompt
        prompt_num = len(self.prompt_layers) if self.multi_layer_prompt else 1

        complete_prompt = torch.zeros(prompt_num, prompt_length, bert_config.hidden_size)
        complete_prompt[:, 0:1, :].fill_(1)
        if self.learnt_p and self.prompt_type == 'attention':
            complete_prompt[:, prompt_length // 2:prompt_length // 2 + 1, :].fill_(1)
        self.complete_prompt = nn.Parameter(complete_prompt)

        missing_text_prompt = torch.zeros(prompt_num, prompt_length, bert_config.hidden_size)
        missing_text_prompt[:, 2:3, :].fill_(1)
        if self.learnt_p and self.prompt_type == 'attention':
            missing_text_prompt[:, prompt_length // 2 + 2:prompt_length // 2 + 3, :].fill_(1)
        self.missing_text_prompt = nn.Parameter(missing_text_prompt)

        missing_img_prompt = torch.zeros(prompt_num, prompt_length, bert_config.hidden_size)
        missing_img_prompt[:, 1:2, :].fill_(1)
        if self.learnt_p and self.prompt_type == 'attention':
            missing_img_prompt[:, prompt_length // 2 + 1:prompt_length // 2 + 2, :].fill_(1)
        self.missing_img_prompt = nn.Parameter(missing_img_prompt)

        if not self.learnt_p:
            self.complete_prompt.requires_grad = False
            self.missing_text_prompt.requires_grad = False
            self.missing_img_prompt.requires_grad = False

        print(self.complete_prompt)
        print(self.missing_img_prompt)
        print(self.missing_text_prompt)

        for param in self.transformer.parameters():
            param.requires_grad = False
        for param in self.text_embeddings.parameters():
            param.requires_grad = False
        for param in self.token_type_embeddings.parameters():
            param.requires_grad = False

        vilt_utils.set_metrics(self)

        # ===================== load downstream (test_only) ======================

        if load_path != "" and "test_only":
            ckpt = torch.load(load_path, map_location="cpu")
            state_dict = ckpt["state_dict"]
            self.load_state_dict(state_dict, strict=False)
        self.records = {}


    def infer(
            self,
            batch,
            mask_text=False,
            mask_image=False,
            image_token_type_idx=1,
            image_embeds=None,
            image_masks=None,
            is_train=None,
    ):
        if f"image_{image_token_type_idx - 1}" in batch:
            imgkey = f"image_{image_token_type_idx - 1}"
        else:
            imgkey = "image"

        do_mlm = "_mlm" if mask_text else ""
        text_ids = batch[f"text_ids{do_mlm}"]
        text_labels = batch[f"text_labels{do_mlm}"]
        text_masks = batch[f"text_masks"]
        text_embeds = self.text_embeddings(text_ids)
        img = batch[imgkey][0]

        if image_embeds is None and image_masks is None:

            (
                image_embeds,
                image_masks,
                patch_index,
                image_labels,
            ) = self.transformer.visual_embed(
                img,
                max_image_len=self.hparams.bert_config.max_image_len,
                mask_it=mask_image,
            )

            # deal with zero input images
        #             for idx in range(len(img)):
        #                 if len(torch.unique(img[idx])) <= 2:
        #                     image_embeds[idx,1:].fill_(0)
        #                     image_masks[idx,1:].fill_(0)
        #                     image_embeds[idx,1:].fill_(1)

        else:
            patch_index, image_labels = (
                None,
                None,
            )

        text_embeds, image_embeds = (
            text_embeds + self.token_type_embeddings(torch.zeros_like(text_masks)),
            image_embeds
            + self.token_type_embeddings(
                torch.full_like(image_masks, image_token_type_idx)
            ),
        )

        # instance wise missing aware prompts
        prompts = None
        for idx in range(len(img)):
            if batch["missing_type"][idx] == 0:
                prompt = self.complete_prompt
            elif batch["missing_type"][idx] == 1:
                prompt = self.missing_text_prompt
            elif batch["missing_type"][idx] == 2:
                prompt = self.missing_img_prompt

            if prompt.size(0) != 1:
                prompt = prompt.unsqueeze(0)

            if prompts is None:
                prompts = prompt
            else:
                prompts = torch.cat([prompts, prompt], dim=0)

        if self.learnt_p:
            if self.prompt_type == 'attention':
                prompt_masks = torch.ones(prompts.shape[0], self.prompt_length // 2, dtype=prompts.dtype,
                                          device=prompts.device).long()
            elif self.prompt_type == 'input':
                prompt_masks = torch.ones(prompts.shape[0], self.prompt_length * len(self.prompt_layers),
                                          dtype=prompts.dtype, device=prompts.device).long()
        else:
            prompt_masks = torch.ones(prompts.shape[0], self.prompt_length, dtype=prompts.dtype,
                                      device=prompts.device).long()

        co_masks = torch.cat([prompt_masks, text_masks, image_masks], dim=1)
        co_embeds = torch.cat([text_embeds, image_embeds], dim=1)
        x = co_embeds.detach()

        for i, blk in enumerate(self.transformer.blocks):
            if i in self.prompt_layers:
                if self.multi_layer_prompt:
                    x, _attn = blk(x, mask=co_masks,
                                   prompts=prompts[:, self.prompt_layers.index(i)],
                                   learnt_p=self.learnt_p,
                                   prompt_type=self.prompt_type)
                else:
                    x, _attn = blk(x, mask=co_masks, prompts=prompts, learnt_p=self.learnt_p)
            else:
                x, _attn = blk(x, mask=co_masks)

        x = self.transformer.norm(x)

        if self.prompt_type == 'input':
            total_prompt_len = len(self.prompt_layers) * prompts.shape[-2]
        elif self.prompt_type == 'attention':
            total_prompt_len = prompts.shape[-2]

        text_feats, image_feats = (
            x[:, total_prompt_len: total_prompt_len + text_embeds.shape[1]],
            x[:, total_prompt_len + text_embeds.shape[1]:],
        )
        if self.prompt_type == 'input':
            cls_feats = self.pooler(x[:, total_prompt_len:total_prompt_len + 1])
        #         cls_feats = self.pooler(x[:,:prompts.size(1)].mean(dim=1,keepdim=True))
        elif self.prompt_type == 'attention':
            cls_feats = self.pooler(x)

        ret = {
            "text_feats": text_feats,
            "image_feats": image_feats,
            "cls_feats": cls_feats,
            "raw_cls_feats": x[:, 0],
            "image_labels": image_labels,
            "image_masks": image_masks,
            "text_labels": text_labels,
            "text_ids": text_ids,
            "text_masks": text_masks,
            "patch_index": patch_index,
        }

        return ret

    def forward(self, batch):
        ret = objectives.compute_loss(self, batch)
        return ret

    def training_step(self, batch, batch_idx=None):
        output = self(batch)
        total_loss = sum([v for k, v in output.items() if "loss" in k])

        return total_loss

    def training_epoch_end(self, outs):
        vilt_utils.epoch_wrapup(self)

    def validation_step(self, batch, batch_idx=None):
        output = self(batch)

    def validation_epoch_end(self, outs):
        vilt_utils.epoch_wrapup(self)

    def test_step(self, batch, batch_idx=None):
        output = self(batch)
        ret = dict()
        return ret

    def predict_step(self, batch, batch_idx=None):
        infer = self.infer(batch, mask_text=False, mask_image=False)
        imgcls_logits = self.classifier(infer["cls_feats"])
        return imgcls_logits

    def test_epoch_end(self, outs):
        vilt_utils.epoch_wrapup(self)

    def configure_optimizers(self):
        return vilt_utils.set_schedule(self)
