# -*- coding: utf-8 -*-

import random

import numpy as np
import torch as th
import torch.nn as nn

from wxbtool.data.constants import (
    load_area_weight,
    load_lat2d,
    load_lon2d,
    load_lsm,
    load_orography,
    load_slt,
)
from wxbtool.data.dataset import WxDataset, WxDatasetClient
from wxbtool.util.evaluation import Evaluator


def cast(element):
    element = np.array(element, dtype=np.float32)
    tensor = th.FloatTensor(element)
    return tensor


class Model2d(nn.Module):
    def __init__(self, setting):
        super().__init__()
        self.setting = setting

        self.constant_cache = {}
        self.weight_cache = {}
        self.phi_cache = {}
        self.theta_cache = {}
        self.x_cache = {}
        self.y_cache = {}

        self.grid_equi = th.zeros(1, 48, 48, 2)
        self.grid_polr = th.zeros(1, 48, 48, 2)
        self.grid_equi_cache = {}
        self.grid_polr_cache = {}

        self.eva = Evaluator(setting.resolution, setting.root)

        self.dataset_train, self.dataset_test, self.dataset_eval = None, None, None
        self.train_size = -1
        self.test_size = -1
        self.eval_size = -1

        self.clipping_threshold = 3.0

        # Assume lsm, slt, oro as constant inputs
        self._constant_size = 3

    def prepare_constant(self):
        lsm = cast(load_lsm(self.setting.resolution, self.setting.root))
        slt = cast(load_slt(self.setting.resolution, self.setting.root))
        oro = cast(load_orography(self.setting.resolution, self.setting.root))
        aw = cast(load_area_weight(self.setting.resolution, self.setting.root))

        phi = cast(load_lat2d(self.setting.resolution, self.setting.root)) * np.pi / 180
        theta = (
            cast(load_lon2d(self.setting.resolution, self.setting.root)) * np.pi / 180
        )
        x, y = np.meshgrid(np.linspace(0, 1, num=32), np.linspace(0, 1, num=64))
        x = cast(x)
        y = cast(y)

        lsm.requires_grad = False
        slt.requires_grad = False
        oro.requires_grad = False
        aw.requires_grad = False
        phi.requires_grad = False
        theta.requires_grad = False
        x.requires_grad = False
        y.requires_grad = False

        dt = th.cos(phi)
        self.weight = dt / dt.mean()

        lsm = ((lsm - 0.33707827) / 0.45900375).view(1, 1, 32, 64)
        slt = ((slt - 0.67920434) / 1.1688842).view(1, 1, 32, 64)
        oro = ((oro - 379.4976) / 859.87225).view(1, 1, 32, 64)
        self.constant = th.cat((lsm, slt, oro), dim=1)
        self.phi = phi
        self.theta = theta
        self.x = x
        self.y = y

    def load_dataset(self, phase, mode, **kwargs):
        if mode == "server":
            self.dataset_train, self.dataset_eval, self.dataset_test = (
                WxDataset(
                    self.setting.root,
                    self.setting.resolution,
                    self.setting.years_train,
                    self.setting.vars,
                    self.setting.levels,
                    input_span=self.setting.input_span,
                    pred_shift=self.setting.pred_shift,
                    pred_span=self.setting.pred_span,
                    step=self.setting.step,
                    granularity=self.setting.granularity,
                    data_path_format=self.setting.data_path_format,
                    setting=self.setting,
                ),
                WxDataset(
                    self.setting.root,
                    self.setting.resolution,
                    self.setting.years_eval,
                    self.setting.vars,
                    self.setting.levels,
                    input_span=self.setting.input_span,
                    pred_shift=self.setting.pred_shift,
                    pred_span=self.setting.pred_span,
                    step=self.setting.step,
                    granularity=self.setting.granularity,
                    data_path_format=self.setting.data_path_format,
                    setting=self.setting,
                ),
                WxDataset(
                    self.setting.root,
                    self.setting.resolution,
                    self.setting.years_test,
                    self.setting.vars,
                    self.setting.levels,
                    input_span=self.setting.input_span,
                    pred_shift=self.setting.pred_shift,
                    pred_span=self.setting.pred_span,
                    step=self.setting.step,
                    granularity=self.setting.granularity,
                    data_path_format=self.setting.data_path_format,
                    setting=self.setting,
                ),
            )
        else:
            ds_url = kwargs["url"]
            self.dataset_train, self.dataset_eval, self.dataset_test = (
                WxDatasetClient(
                    ds_url,
                    "train",
                    self.setting.resolution,
                    self.setting.years_train,
                    self.setting.vars,
                    self.setting.levels,
                    input_span=self.setting.input_span,
                    pred_shift=self.setting.pred_shift,
                    pred_span=self.setting.pred_span,
                    step=self.setting.step,
                    granularity=self.setting.granularity,
                    data_path_format=self.setting.data_path_format,
                ),
                WxDatasetClient(
                    ds_url,
                    "eval",
                    self.setting.resolution,
                    self.setting.years_eval,
                    self.setting.vars,
                    self.setting.levels,
                    input_span=self.setting.input_span,
                    pred_shift=self.setting.pred_shift,
                    pred_span=self.setting.pred_span,
                    step=self.setting.step,
                    granularity=self.setting.granularity,
                    data_path_format=self.setting.data_path_format,
                ),
                WxDatasetClient(
                    ds_url,
                    "test",
                    self.setting.resolution,
                    self.setting.years_test,
                    self.setting.vars,
                    self.setting.levels,
                    input_span=self.setting.input_span,
                    pred_shift=self.setting.pred_shift,
                    pred_span=self.setting.pred_span,
                    step=self.setting.step,
                    granularity=self.setting.granularity,
                    data_path_format=self.setting.data_path_format,
                ),
            )

        self.train_size = len(self.dataset_train)
        self.eval_size = len(self.dataset_eval)
        self.test_size = len(self.dataset_test)

        import logging

        logger = logging.getLogger()
        if self.dataset_train:
            logger.info("train dataset key: %s", self.dataset_train.hashcode)
        if self.dataset_eval:
            logger.info("eval dataset key: %s", self.dataset_eval.hashcode)
        if self.dataset_test:
            logger.info("test dataset key: %s", self.dataset_test.hashcode)

    def get_constant(self, input, device):
        if device not in self.constant_cache:
            if not hasattr(self, "constant"):
                self.prepare_constant()
            self.constant_cache[device] = self.constant.to(device)
        return self.constant_cache[device]

    def get_weight(self, device):
        if device not in self.weight_cache:
            if not hasattr(self, "weight"):
                self.prepare_constant()
            self.weight_cache[device] = self.weight.to(device)
        return self.weight_cache[device]

    def get_phi(self, device):
        if device not in self.phi_cache:
            if not hasattr(self, "phi"):
                self.prepare_constant()
            self.phi_cache[device] = self.phi.to(device)
        return self.phi_cache[device]

    def get_theta(self, device):
        if device not in self.theta_cache:
            if not hasattr(self, "theta"):
                self.prepare_constant()
            self.theta_cache[device] = self.theta.to(device)
        return self.theta_cache[device]

    def get_x(self, device):
        if device not in self.x_cache:
            if not hasattr(self, "x"):
                self.prepare_constant()
            self.x_cache[device] = self.x.to(device)
        return self.x_cache[device]

    def get_y(self, device):
        if device not in self.y_cache:
            if not hasattr(self, "y"):
                self.prepare_constant()
            self.y_cache[device] = self.y.to(device)
        return self.y_cache[device]

    def get_grid_equi(self, device):
        if device not in self.grid_equi_cache:
            self.grid_equi_cache[device] = self.grid_equi.to(device)
        return self.grid_equi_cache[device]

    def get_grid_polr(self, device):
        if device not in self.grid_polr_cache:
            self.grid_polr_cache[device] = self.grid_polr.to(device)
        return self.grid_polr_cache[device]

    def constant_size(self):
        if not hasattr(self, "_constant_size"):
            self.prepare_constant()
        return self._constant_size


class Base2d(Model2d):
    def __init__(self, setting, enable_da=False):
        super().__init__(setting)
        self.enable_da = enable_da

    def update_da_status(self, batch):
        if self.enable_da and self.training:
            self.lng_shift = []
            self.flip_status = []
            for _ in range(batch):
                self.lng_shift.append(random.randint(0, 64))
                self.flip_status.append(random.randint(0, 1))

    def augment_data(self, data):
        if self.enable_da and self.training:
            augmented = []
            b, c, w, h = data.size()
            for _ in range(b):
                slice = data[_ : _ + 1]
                shift = self.lng_shift[_]
                flip = self.flip_status[_]
                slice = slice.roll(shift, dims=(3,))
                if flip == 1:
                    slice = th.flip(slice, dims=(2, 3))
                augmented.append(slice)
            data = th.cat(augmented, dim=0)
        return data

    def get_augmented_constant(self, input):
        constant = self.get_constant(input, input.device).repeat(
            input.size()[0], 1, 1, 1
        )
        constant = self.augment_data(constant)
        phi = self.get_phi(input.device).repeat(input.size()[0], 1, 1, 1)
        theta = self.get_theta(input.device).repeat(input.size()[0], 1, 1, 1)
        constant = th.cat((constant, phi, theta), dim=1)
        return constant

    def get_inputs(self, **kwargs):
        raise NotImplementedError()
        return {}, None

    def get_targets(self, **kwargs):
        raise NotImplementedError()
        return {}, None

    def get_results(self, **kwargs):
        raise NotImplementedError()
        return {}, None

    def forward(self, *args, **kwargs):
        raise NotImplementedError()
        return {}

    def lossfun(self, inputs, result, target):
        raise NotImplementedError()
        return 0.0


class Base3d(Base2d):
    def __init__(self, setting, enable_da=False):
        super().__init__(setting, enable_da)

    def augment_data(self, data):
        if self.enable_da and self.training:
            augmented = []
            b, c, t, w, h = data.size()
            for _ in range(b):
                slice = data[_ : _ + 1]
                shift = self.lng_shift[_]
                flip = self.flip_status[_]
                slice = slice.roll(shift, dims=(4,))
                if flip == 1:
                    slice = th.flip(slice, dims=(3, 4))
                augmented.append(slice)
            data = th.cat(augmented, dim=0)
        return data

    def get_augmented_constant(self, input):
        b, c, t, w, h = input.size()
        constant = self.get_constant(input, input.device).repeat(b, 1, t, 1, 1)
        constant = self.augment_data(constant)
        phi = self.get_phi(input.device).repeat(b, 1, t, 1, 1)
        theta = self.get_theta(input.device).repeat(b, 1, t, 1, 1)
        constant = th.cat((constant, phi, theta), dim=1)
        return constant

    def get_inputs(self, **kwargs):
        raise NotImplementedError()
        return {}, None

    def get_targets(self, **kwargs):
        raise NotImplementedError()
        return {}, None

    def get_results(self, **kwargs):
        raise NotImplementedError()
        return {}, None

    def forward(self, *args, **kwargs):
        raise NotImplementedError()
        return {}

    def lossfun(self, inputs, result, target):
        raise NotImplementedError()
        return 0.0
