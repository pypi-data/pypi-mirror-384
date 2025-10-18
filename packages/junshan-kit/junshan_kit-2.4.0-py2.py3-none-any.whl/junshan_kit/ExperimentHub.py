import sys, os, torch, random
import numpy as np
import torch.nn as nn
from torch.utils.data import Subset

# # 获取当前脚本所在目录
# script_dir = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.join(script_dir, 'src'))

from junshan_kit import datahub, Models, TrainingParas

# -------------------------------------
def set_seed(seed=42):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def device(Paras):
    device = torch.device(f"{Paras['cuda']}" if torch.cuda.is_available() else "cpu")
    Paras["device"] = device
    use_color = sys.stdout.isatty()
    Paras["use_color"] = use_color

    return Paras

# -------------------------------------
class Train_Steps:
    def __init__(self, args) -> None:
        self.args = args

    def _model_map(self, model_name):
        model_mapping = self.args.model_mapping

        return model_mapping[model_name]
    
    def get_train_group(self):
        training_group = []
        for cfg in self.args.train_group:
            model, dataset, optimizer = cfg.split("-")
            training_group.append((self._model_map(model), dataset, optimizer))

        return training_group
    
    def set_paras(self, results_folder_name, py_name, time_str, OtherParas):
        Paras = {
        # Name of the folder where results will be saved.
        "results_folder_name": results_folder_name,
        # Whether to draw loss/accuracy figures.
        "DrawFigs": "ON",
        # Whether to use log scale when drawing plots.
        "use_log_scale": "ON",
        # Print loss every N epochs.
        "epoch_log_interval": 1,
        # Timestamp string for result saving.
        "time_str": time_str,
        # Random seed
        "seed": OtherParas['seed'],
        # Device used for training.
        "cuda": f"cuda:{self.args.cuda}",

        # batch-size 
        "batch_size": self.args.bs,

        # epochs
        "epochs": self.args.e,

        # split_train_data
        "split_train_data": self.args.s,

        # select_subset
        "select_subset": self.args.subset,

        # subset_number_dict
        "subset_number_dict": TrainingParas.subset_number_dict(OtherParas),

        # validation
        "validation": TrainingParas.validation(),

        # validation_rate
        "validation_rate": TrainingParas.validation_rate(),

        # model list
        "model_list" : TrainingParas.model_list(),

        # model_type
        "model_type": TrainingParas.model_type(),

        # data_list
        "data_list": TrainingParas.data_list(),

        # optimizer_dict
        "optimizer_dict": TrainingParas.optimizer_dict(OtherParas)
        }
        Paras["py_name"] = py_name
        
        return Paras
    
    # <Step_3> : Chosen_loss
    def chosen_loss(self, model_name, Paras):
        # ---------------------------------------------------
        # There have an addition parameter
        if model_name == "LogRegressionBinaryL2":
            Paras["lambda"] = 1e-3
        # ---------------------------------------------------

        if model_name in ["LeastSquares"]:
            loss_fn = nn.MSELoss()

        else:
            if Paras["model_type"][model_name] == "binary":
                loss_fn = nn.BCEWithLogitsLoss()

            elif Paras["model_type"][model_name] == "multi":
                loss_fn = nn.CrossEntropyLoss()

            else:
                loss_fn = nn.MSELoss()
                print("\033[91m The loss function is error!\033[0m")
                assert False
        Paras["loss_fn"] = loss_fn

        return loss_fn, Paras
    
    # <Step_4> : import data --> step.py
    def load_data(self, model_name, data_name, Paras):
        # load data
        train_path = f"./exp_data/{data_name}/training_data"
        test_path = f"./exp_data/{data_name}/test_data"
        # Paras["train_ratio"] = 1.0
        # Paras["select_subset"].setdefault(data_name, False)
        # Paras["validation"].setdefault(data_name, False)

        if data_name == "MNIST":
            train_dataset, test_dataset, transform = datahub.MNIST(Paras, model_name)

        elif data_name == "CIFAR100":
            train_dataset, test_dataset, transform = datahub.CIFAR100(Paras, model_name)

        elif data_name == "CALTECH101_Resize_32":
            Paras["train_ratio"] = 0.7
            train_dataset, test_dataset, transform = datahub.caltech101_Resize_32(
                Paras["seed"], Paras["train_ratio"], split=True
            )

        elif data_name in ["Vowel", "Letter", "Shuttle", "w8a"]:
            Paras["train_ratio"] = Paras["split_train_data"][data_name]
            train_dataset, test_dataset, transform = datahub.get_libsvm_data(
                train_path + ".txt", test_path + ".txt", data_name
            )

        elif data_name in ["RCV1", "Duke", "Ijcnn"]:
            Paras["train_ratio"] = Paras["split_train_data"][data_name]
            train_dataset, test_dataset, transform = datahub.get_libsvm_bz2_data(
                train_path + ".bz2", test_path + ".bz2", data_name, Paras
            )

        else:
            transform = None
            print(f"The data_name is error!")
            assert False

        return train_dataset, test_dataset, transform
    # <Step_4>

    # <subset> : Step 5.1 -->step.py
    def set_subset(self, data_name, Paras, train_dataset, test_dataset):
        if self.args.subset[0]>1:
            train_num = self.args.subset[0]
            test_num = self.args.subset[1]
            train_subset_num = min(train_num, len(train_dataset))
            test_subset_num = min(test_num, len(test_dataset))

            train_subset_indices = list(range(int(train_subset_num)))
            train_dataset = Subset(train_dataset, train_subset_indices)

            test_subset_indices = list(range(int(test_subset_num)))
            test_dataset = Subset(test_dataset, test_subset_indices)
            
        else:
            train_ratios= self.args.subset[0]
            test_ratios= self.args.subset[1]

            train_subset_indices = list(range(int(train_ratios * len(train_dataset))))
            train_dataset = Subset(train_dataset, train_subset_indices)

            test_subset_indices = list(range(int(test_ratios * len(test_dataset))))
            test_dataset = Subset(test_dataset, test_subset_indices)

        return train_dataset, test_dataset


