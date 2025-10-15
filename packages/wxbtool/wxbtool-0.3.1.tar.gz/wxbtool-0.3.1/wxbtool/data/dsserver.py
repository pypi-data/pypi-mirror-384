# -*- coding: utf-8 -*-

import importlib
import logging
import os
import resource
import sys

import arrow
import flask
import msgpack
import msgpack_numpy as m

m.patch()

from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
from flask import Flask  # noqa: E402

rlimit = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (2048, rlimit[1]))
np.core.arrayprint._line_width = 150
np.set_printoptions(linewidth=np.inf)


datasets = {}


def init(opt):
    time_str = arrow.now().format("YYYYMMDD_HHmmss")
    model_path = Path(f"./dsserver/{time_str}")
    model_path.mkdir(exist_ok=True, parents=True)
    log_file = model_path / Path("dsserver.log")
    logging.basicConfig(level=logging.INFO, filename=log_file, filemode="w")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info(str(opt))

    try:
        sys.path.insert(0, os.getcwd())
        mdm = importlib.import_module(opt.module, package=None)
        setting = getattr(mdm, opt.setting)()
        spec = getattr(mdm, "Spec")(setting)
    except ImportError:
        exc_info = sys.exc_info()
        print("failure when loading model")
        import traceback

        traceback.print_exception(*exc_info)
        del exc_info
        sys.exit(1)

    spec.load_dataset("train", "server")
    spec.load_dataset("eval", "server")
    spec.load_dataset("test", "server")
    dtrain = spec.dataset_train
    deval = spec.dataset_eval
    dtest = spec.dataset_test
    datasets["train"] = dtrain
    datasets["eval"] = deval
    datasets["test"] = dtest

    logger.info("train dataset key: %s", dtrain.hashcode)
    logger.info("eval dataset key: %s", deval.hashcode)
    logger.info("test dataset key: %s", dtest.hashcode)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logger.addHandler(handler)
    gunicorn_logger = logging.getLogger("gunicorn.info")
    app.logger.handlers.extend(gunicorn_logger.handlers)
    logger.handlers.extend(app.logger.handlers)


app = Flask(__name__)
app.debug = False

route = app.route


@route("/<string:hash>/<string:mode>")
def length(hash, mode):
    ds = datasets[mode]
    if ds.hashcode != hash:
        return flask.current_app.response_class(
            "not found", status=404, mimetype="application/msgpack"
        )

    app.logger.info("query length[%s] %d", mode, len(ds))
    msg = msgpack.dumps(
        {
            "size": len(ds),
        }
    )

    return flask.current_app.response_class(
        msg, status=200, mimetype="application/msgpack"
    )


@route("/<string:hash>/<string:mode>/<int:idx>")
def seek(hash, mode, idx):
    ds = datasets[mode]
    if ds.hashcode != hash:
        return flask.current_app.response_class(
            "not found", status=404, mimetype="application/msgpack"
        )

    app.logger.info("query data[%s] at %d", mode, idx)
    inputs, targets, items = ds[idx]
    msg = msgpack.dumps(
        {
            "inputs": inputs,
            "targets": targets,
            "items": items,
        }
    )

    return flask.current_app.response_class(
        msg, status=200, mimetype="application/msgpack"
    )


def main(context, opt):
    import gunicorn.app.base

    init(opt)

    class StandaloneApplication(gunicorn.app.base.BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            config = {
                key: value
                for key, value in self.options.items()
                if key in self.cfg.settings and value is not None
            }
            for key, value in config.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    print("PID %s" % str(os.getpid()))
    print("serving... %s" % opt.module)
    print("bind: %s" % opt.bind)
    print("workers: %s" % opt.workers)

    if opt.test == "false":
        options = {
            "bind": opt.bind,
            "workers": opt.workers,
        }
        StandaloneApplication(app, options).run()
