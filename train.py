import os

import pytorch_lightning as pl
import torch
import torch.nn as nn
torch.autograd.set_detect_anomaly(True)
from pytorch_lightning.callbacks import ModelCheckpoint, ModelSummary
from pytorch_lightning.strategies.ddp import DDPStrategy

from data import DetectionDataModule
from fasterRCNN import FasterRCNNwrap
from parameters import Parameters
pars = Parameters()

class_dict_9 = {
     'ECb' : 0, 'ECa' : 1, 'E' : 2, 
     'ECE' : 3, 'DISP' : 4, 'DL' : 5, 
     'EC_cat_k' : 6, 'SR' : 7, 'T' : 8, 'EC_cat_kd' : 9, 'EC_cat_ks' : 10
 }
key_list_8 = ["T", "ECb", "ECa", "ECE", "EC_cat_k", "DISP", "SR", "E", "EC_cat_kd", "EC_cat_ks"]
if not os.path.exists(pars.save_loc):
    os.mkdir(pars.save_loc)

### define parameters and other setups ###
pl.seed_everything(42)
torch.multiprocessing.set_sharing_strategy("file_system")
pars.print()

### load data ###
datamodule = DetectionDataModule(root=pars.det_data_dir, 
                min_noise_mag=pars.min_noise_mag, max_noise_mag=pars.max_noise_mag, min_sr=pars.min_sr)
train, val, test = datamodule.train_dataset, datamodule.val_dataset, datamodule.test_dataset
train.log(os.path.join(pars.save_loc, "train_idx.txt"))
val.log(os.path.join(pars.save_loc, "val_idx.txt"))
test.log(os.path.join(pars.save_loc, "test_idx.txt"))

checkpoint_callback = ModelCheckpoint(
    dirpath=pars.save_loc + "/ckpts", save_top_k=5, monitor='val_acc', mode="max", every_n_epochs=5
)
trainer = pl.Trainer(
    max_epochs=pars.max_epochs,
    logger=pl.loggers.TensorBoardLogger(pars.save_loc),
    accelerator="gpu",
    devices=2,
    default_root_dir="output",
    callbacks=[checkpoint_callback],
    strategy=DDPStrategy(find_unused_parameters=False),
    log_every_n_steps=5,
    detect_anomaly=True
    #profiler="pytorch", 
)

model_rcnn = FasterRCNNwrap(learning_rate=pars.lr, num_classes=pars.num_cls + 1)

checkpoint = torch.load(r'/home/muxin/output250704_01/ckpts/epoch=289-step=154570.ckpt', map_location='cpu')
model_rcnn.load_state_dict(checkpoint['state_dict'], strict=False)

print("begin training")
trainer.fit(model_rcnn, datamodule)
#trainer.fit(model_rcnn, datamodule, ckpt_path=r'/home/muxin/ML_RCNN/Muxin_DL_Redox_4_20_R/cache/det_train/output240802_04/ckpts/epoch=289-step=154570.ckpt')