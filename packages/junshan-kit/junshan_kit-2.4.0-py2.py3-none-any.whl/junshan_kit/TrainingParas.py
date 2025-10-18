# Step 1 : training_group
def set_training_group():
    # <training_group>
    training_group = [
        # *********************************************************
        # ----------------- MNIST (ResNet18) ----------------------
        # ("ResNet18", "MNIST", "SGD"),
        # ("ResNet18", "MNIST", "ADAM"),
        # ("ResNet18", "MNIST", "SPSmax"),
        # ("ResNet18", "MNIST", "Bundle"),
        # ("ResNet18", "MNIST", "ALR-SMAG"),
        # ("ResNet18", "MNIST", "SPBM-TR"),
        # ("ResNet18", "MNIST", "SPBM-PF"),
        # ("ResNet18", "MNIST", "SPBM-PF-NoneLower"),
        # ("ResNet18", "MNIST", "SPBM-TR-NoneLower"),
        # ("ResNet18", "MNIST", "SPBM-TR-NoneSpecial"),
        # ---------------- CIFAR100 (ResNet18)---------------------
        # ("ResNet18", "CIFAR100", "SGD"),
        # ("ResNet18", "CIFAR100", "ADAM"),
        # ("ResNet18", "CIFAR100", "SPSmax"),
        # ("ResNet18", "CIFAR100", "Bundle"),
        # ("ResNet18", "CIFAR100", "ALR-SMAG"),
        # ("ResNet18", "CIFAR100", "SPBM-TR"),
        # ("ResNet18", "CIFAR100", "SPBM-PF"),
        # ("ResNet18", "CIFAR100", "SPBM-PF-NoneLower"),
        # ("ResNet18", "CIFAR100", "SPBM-TR-NoneLower"),
        # # ----------- CALTECH101_Resize_32 (ResNet18) -------------
        ("ResNet18", "CALTECH101_Resize_32", "SGD"),
        # ("ResNet18", "CALTECH101_Resize_32", "ADAM"),
        # ("ResNet18", "CALTECH101_Resize_32", "SPSmax"),
        # ("ResNet18", "CALTECH101_Resize_32", "Bundle"),
        # ("ResNet18", "CALTECH101_Resize_32", "ALR-SMAG"),
        # ("ResNet18", "CALTECH101_Resize_32", "SPBM-TR"),
        # ("ResNet18", "CALTECH101_Resize_32", "SPBM-PF"),
        # ("ResNet18", "CALTECH101_Resize_32", "SPBM-PF-NoneLower"),
        # ("ResNet18", "CALTECH101_Resize_32", "SPBM-TR-NoneLower"),

        # *********************************************************
        # ---------------- MNIST (ResNet34) -----------------------
        # ("ResNet34" ,"MNIST", "SGD"),
        # ("ResNet34" ,"MNIST", "ADAM"),
        # ("ResNet34" ,"MNIST", "SPSmax"),
        # ("ResNet34" ,"MNIST", "Bundle"),
        # ("ResNet34" ,"MNIST", "ALR-SMAG"),
        # ("ResNet34" ,"MNIST", "SPBM-TR"),
        # ("ResNet34" ,"MNIST", "SPBM-PF"),
        # ("ResNet34" ,"MNIST", "SPBM-PF-NoneLower"),
        # ("ResNet34" ,"MNIST", "SPBM-TR-NoneLower"),
        # ------------------ CIFAR100 (ResNet34)-------------------
        # ("ResNet34" ,"CIFAR100", "SGD"),
        # ("ResNet34" ,"CIFAR100", "ADAM"),
        # ("ResNet34" ,"CIFAR100", "SPSmax"),
        # ("ResNet34" ,"CIFAR100", "Bundle"),
        # ("ResNet34" ,"CIFAR100", "ALR-SMAG"),
        # ("ResNet34" ,"CIFAR100", "SPBM-TR"),
        # ("ResNet34" ,"CIFAR100", "SPBM-PF"),
        # ("ResNet34" ,"CIFAR100", "SPBM-PF-NoneLower"),
        # ("ResNet34" ,"CIFAR100", "SPBM-TR-NoneLower"),
        # ------------ CALTECH101_Resize_32 (ResNet34) ------------
        # ("ResNet34" ,"CALTECH101_Resize_32", "SGD"),
        # ("ResNet34" ,"CALTECH101_Resize_32", "ADAM"),
        # ("ResNet34" ,"CALTECH101_Resize_32", "SPSmax"),
        # ("ResNet34" ,"CALTECH101_Resize_32", "Bundle"),
        # ("ResNet34" ,"CALTECH101_Resize_32", "ALR-SMAG"),
        # ("ResNet34" ,"CALTECH101_Resize_32", "SPBM-TR"),
        # ("ResNet34" ,"CALTECH101_Resize_32", "SPBM-PF"),
        # ("ResNet34" ,"CALTECH101_Resize_32", "SPBM-PF-NoneLower"),
        # ("ResNet34" ,"CALTECH101_Resize_32", "SPBM-TR-NoneLower"),

        # *********************************************************
        # ------------------ MNIST (LeastSquares) -----------------
        # ("LeastSquares" ,"MNIST", "SGD"),
        # ("LeastSquares" ,"MNIST", "ADAM"),
        # ("LeastSquares" ,"MNIST", "SPSmax"),
        # ("LeastSquares" ,"MNIST", "Bundle"),
        # ("LeastSquares" ,"MNIST", "ALR-SMAG"),
        # ("LeastSquares" ,"MNIST", "SPBM-TR"),
        # ("LeastSquares" ,"MNIST", "SPBM-PF"),
        # ("LeastSquares" ,"MNIST", "SPBM-PF-NoneLower"),
        # ("LeastSquares" ,"MNIST", "SPBM-TR-NoneLower"),
        # ---------------- CIFAR100 (LeastSquares) ----------------
        # ("LeastSquares" ,"CIFAR100", "SGD"),
        # ("LeastSquares" ,"CIFAR100", "ADAM"),
        # ("LeastSquares" ,"CIFAR100", "SPSmax"),
        # ("LeastSquares" ,"CIFAR100", "Bundle"),
        # ("LeastSquares" ,"CIFAR100", "ALR-SMAG"),
        # ("LeastSquares" ,"CIFAR100", "SPBM-TR"),
        # ("LeastSquares" ,"CIFAR100", "SPBM-PF"),
        # ("LeastSquares" ,"CIFAR100", "SPBM-PF-NoneLower"),
        # ("LeastSquares" ,"CIFAR100", "SPBM-TR-NoneLower"),
        # ---------------- CIFAR100 (LeastSquares) ----------------
        # ("LeastSquares" ,"CALTECH101_Resize_32", "SGD"),
        # ("LeastSquares" ,"CALTECH101_Resize_32", "ADAM"),
        # ("LeastSquares" ,"CALTECH101_Resize_32", "SPSmax"),
        # ("LeastSquares" ,"CALTECH101_Resize_32", "Bundle"),
        # ("LeastSquares" ,"CALTECH101_Resize_32", "ALR-SMAG"),
        # ("LeastSquares" ,"CALTECH101_Resize_32", "SPBM-TR"),
        # ("LeastSquares" ,"CALTECH101_Resize_32", "SPBM-PF"),
        # ("LeastSquares" ,"CALTECH101_Resize_32", "SPBM-PF-NoneLower"),
        # ("LeastSquares" ,"CALTECH101_Resize_32", "SPBM-TR-NoneLower"),

        # *********************************************************
        # ------------- MNIST (LogRegressionBinary) ---------------
        # ("LogRegressionBinary" ,"MNIST", "SGD"),
        # ("LogRegressionBinary" ,"MNIST", "ADAM"),
        # ("LogRegressionBinary" ,"MNIST", "SPSmax"),
        # ("LogRegressionBinary" ,"MNIST", "Bundle"),
        # ("LogRegressionBinary" ,"MNIST", "ALR-SMAG"),
        # ("LogRegressionBinary" ,"MNIST", "SPBM-TR"),
        # ("LogRegressionBinary" ,"MNIST", "SPBM-PF"),
        # ("LogRegressionBinary" ,"MNIST", "SPBM-PF-NoneLower"),
        # ("LogRegressionBinary" ,"MNIST", "SPBM-TR-NoneLower"),
        # ------------- CIFAR100 (LogRegressionBinary) ------------
        # ("LogRegressionBinary" ,"CIFAR100", "SGD"),
        # ("LogRegressionBinary" ,"CIFAR100", "ADAM"),
        # ("LogRegressionBinary" ,"CIFAR100", "SPSmax"),
        # ("LogRegressionBinary" ,"CIFAR100", "Bundle"),
        # ("LogRegressionBinary" ,"CIFAR100", "ALR-SMAG"),
        # ("LogRegressionBinary" ,"CIFAR100", "SPBM-TR"),
        # ("LogRegressionBinary" ,"CIFAR100", "SPBM-PF"),
        # ("LogRegressionBinary" ,"CIFAR100", "SPBM-PF-NoneLower"),
        # ("LogRegressionBinary" ,"CIFAR100", "SPBM-TR-NoneLower"),
        # # --------------- RCV1 (LogRegressionBinary) --------------
        # ("LogRegressionBinary" ,"RCV1", "SGD"),
        # ("LogRegressionBinary" ,"RCV1", "ADAM"),
        # ("LogRegressionBinary" ,"RCV1", "SPSmax"),
        # ("LogRegressionBinary" ,"RCV1", "Bundle"),
        # ("LogRegressionBinary" ,"RCV1", "ALR-SMAG"),
        # ("LogRegressionBinary" ,"RCV1", "SPBM-TR"),
        # ("LogRegressionBinary" ,"RCV1", "SPBM-PF"),
        
        # # *********************************************************
        # # ------------ MNIST (LogRegressionBinaryL2) --------------
        # ("LogRegressionBinaryL2" ,"MNIST", "SGD"),
        # ("LogRegressionBinaryL2" ,"MNIST", "ADAM"),
        # ("LogRegressionBinaryL2" ,"MNIST", "SPSmax"),
        # ("LogRegressionBinaryL2" ,"MNIST", "Bundle"),
        # ("LogRegressionBinaryL2" ,"MNIST", "ALR-SMAG"),
        # ("LogRegressionBinaryL2" ,"MNIST", "SPBM-TR"),
        # ("LogRegressionBinaryL2" ,"MNIST", "SPBM-PF"),
        # # ------------- CIFAR100 (LogRegressionBinaryL2) ----------
        # ("LogRegressionBinaryL2" ,"CIFAR100", "SGD"),
        # ("LogRegressionBinaryL2" ,"CIFAR100", "ADAM"),
        # ("LogRegressionBinaryL2" ,"CIFAR100", "SPSmax"),
        # ("LogRegressionBinaryL2" ,"CIFAR100", "Bundle"),
        # ("LogRegressionBinaryL2" ,"CIFAR100", "ALR-SMAG"),
        # ("LogRegressionBinaryL2" ,"CIFAR100", "SPBM-TR"),
        # ("LogRegressionBinaryL2" ,"CIFAR100", "SPBM-PF"),
        # # --------------- RCV1 (LogRegressionBinaryL2) ------------
        # ("LogRegressionBinaryL2", "RCV1", "SGD"),
        # ("LogRegressionBinaryL2", "RCV1", "ADAM"),
        # ("LogRegressionBinaryL2", "RCV1", "SPSmax"),
        # ("LogRegressionBinaryL2", "RCV1", "Bundle"),
        # ("LogRegressionBinaryL2", "RCV1", "ALR-SMAG"),
        # ("LogRegressionBinaryL2", "RCV1", "SPBM-TR"),
        # ("LogRegressionBinaryL2", "RCV1", "SPBM-PF"),
        # # -------------- Duke (LogRegressionBinaryL2) -------------
        # ("LogRegressionBinaryL2" ,"Duke", "SGD"),
        # ("LogRegressionBinaryL2" ,"Duke", "ADAM"),
        # ("LogRegressionBinaryL2" ,"Duke", "SPSmax"),
        # ("LogRegressionBinaryL2" ,"Duke", "Bundle"),
        # ("LogRegressionBinaryL2" ,"Duke", "ALR-SMAG"),
        # ("LogRegressionBinaryL2" ,"Duke", "SPBM-TR"),
        # ("LogRegressionBinaryL2" ,"Duke", "SPBM-PF"),
        # # -------------- Ijcnn (LogRegressionBinaryL2) ------------
        # ("LogRegressionBinaryL2", "Ijcnn", "SGD"),
        # ("LogRegressionBinaryL2", "Ijcnn", "ADAM"),
        # ("LogRegressionBinaryL2", "Ijcnn", "SPSmax"),
        # ("LogRegressionBinaryL2", "Ijcnn", "Bundle"),
        # ("LogRegressionBinaryL2", "Ijcnn", "ALR-SMAG"),
        # ("LogRegressionBinaryL2", "Ijcnn", "SPBM-TR"),
        # ("LogRegressionBinaryL2", "Ijcnn", "SPBM-PF"),
        # # ----------------- w8a (LogRegressionBinaryL2) -----------
        # ("LogRegressionBinaryL2", "w8a", "SGD"),
        # ("LogRegressionBinaryL2", "w8a", "ADAM"),
        # ("LogRegressionBinaryL2", "w8a", "SPSmax"),
        # ("LogRegressionBinaryL2", "w8a", "Bundle"),
        # ("LogRegressionBinaryL2", "w8a", "ALR-SMAG"),
        # ("LogRegressionBinaryL2", "w8a", "SPBM-TR"),
        # ("LogRegressionBinaryL2", "w8a", "SPBM-PF"),
    ]
    # <training_group>

    return training_group

def batch_size() -> dict:
    batch_size = {
        # 15123/12560
        "Shuttle": 256,
        # 15000/5000
        "Letter": 256,
        # 528/462
        "Vowel": 52,
        # 60000/10000
        "MNIST": 256,
        # 50000/10000
        "CIFAR100": 256,
        # 8,677 (will be split into 7:3)---> 6073/2604
        "CALTECH101_Resize_32": 256,
        # 20,242 (will be split into 7:3)---> 14169/6073
        "RCV1": 256,
        # only 42 (38+4) examples (cancer data)
        "Duke": 10,
        # 35000 + 91701
        "Ijcnn": 64,
        # classes: 2   data: (49749 14,951)  features: 300
        "w8a": 128,
    }
    return batch_size


def epochs(OtherParas) -> dict:
    epochs = {
        # 15123/12560
        "Shuttle": 10,
        # 15000/5000
        "Letter": 10,
        # 528/462
        "Vowel": 10,
        # 60000/10000
        "MNIST": 50,
        # 50000/10000
        "CIFAR100": 50,
        # 8,677 (will be split into 7:3)---> 6073/2604
        "CALTECH101_Resize_32": 50,
        # 20,242 (will be split into 7:3)---> 14169/6073
        "RCV1": 10,
        # only 42 (38+4) examples (cancer data)
        "Duke": 10,
        # 35000 + 91701
        "Ijcnn": 10,
        # classes: 2   data: (49749 14,951)  features: 300
        "w8a": 10,
    }
    if OtherParas["debug"]:
        epochs = {k: 2 for k in epochs}

    return epochs


def split_train_data() -> dict:
    split_train_data = {
        # 20,242 + 0 (test data to large)
        "RCV1": 0.7,
        # only 42 (38+4) examples (Not need)
        "Duke": 1,
        # classes: 2   data: (35000, 91701) features: 22
        "Ijcnn": 1,
        # classes: 2   data: (49749 14,951)  features: 300
        "w8a": 1,
    }
    return split_train_data


def select_subset():
    select_subset = {
        "CALTECH101_Resize_32": True,
        "CIFAR100": True,
        "Duke": False,
        "Ijcnn": True,
        "MNIST": True,
        "RCV1": True,
        "w8a": True,
    }
    return select_subset


def subset_number_dict(OtherParas):
    subset_number_dict = {
        # Max: 60,000/10,000
        "MNIST": (1000, 5000),
        # Max: 50,000
        "CIFAR100": (2000, 10000),
        # Max: 8,677 (6073/2604)
        "CALTECH101_Resize_32": (2000, 2604),    #test max: 2604 
        # classes: 2   data: (35000, 91701) features: 22
        "Ijcnn": (1000, 1000),
        # classes: 2   data: (14169, 6,073)  features: 47,236
        "RCV1": (1000, 1000),
        # classes: 2   data: (49749 14,951)  features: 300
        "w8a": (1000, 1000),
    }

    if OtherParas["debug"]:
        subset_number_dict = {k: (50, 50) for k in subset_number_dict}
    return subset_number_dict


def validation() -> dict:
    validation = {
        # "MNIST": True,
        # "CIFAR100": True,
        # "CALTECH101_Resize_32": True
    }
    return validation


def validation_rate() -> dict:
    validation_rate = {
        "MNIST": 0.3,  # Max: 60,000/10,000
        "CIFAR100": 0.3,  # Max: 50,000
        "CALTECH101_Resize_32": 0.3,  # Max: 8,677 (6073/2604)
    }
    return validation_rate


def model_list() -> list:
    model_list = [
        "ResNet18",
        "ResNet34",
        "LeastSquares",
        "LogRegressionBinary",
        "LogRegressionBinaryL2",
    ]
    return model_list


def model_type() -> dict:
    model_type = {
        "ResNet18": "multi",
        "ResNet34": "multi",
        "LeastSquares": "multi",
        "LogRegressionBinary": "binary",
        "LogRegressionBinaryL2": "binary",
    }
    return model_type


def data_list() -> list:
    data_list = [
        # classes: 2   data: 42 (38+4)  features: 7,129
        "Duke",
        # classes: 2   data: (35000, 91701) features: 22
        "Ijcnn",
        # classes: 2   data: (49749 14,951)  features: 300
        "w8a",
        #
        "RCV1",
        "Shuttle",
        "Letter",
        "Vowel",
        "MNIST",
        "CIFAR100",
        "CALTECH101_Resize_32",
    ]
    return data_list

def optimizer_dict(OtherParas)->dict:
    optimizer_dict = {
    # --------------------------- ADAM ----------------------------
    "ADAM": {
        "params": {
            # "alpha": [2 * 1e-3],
            "alpha": (
                [0.5 * 1e-3, 1e-3, 2 * 1e-3]
                if OtherParas["SeleParasOn"]
                else [0.0005]
            ),
            "epsilon": [1e-8],
            "beta1": [0.9],
            "beta2": [0.999],
        },
    },
    # ----------------------- ALR-SMAG ---------------------------
    "ALR-SMAG": {
        "params": {
            "c": ([0.1, 0.5, 1, 5, 10] if OtherParas["SeleParasOn"] else [0.1]),
            "eta_max": (
                [2**i for i in range(-8, 9)]
                if OtherParas["SeleParasOn"]
                else [0.125]
            ),
            "beta": [0.9],
        },
    },
    # ------------------------ Bundle -----------------------------
    "Bundle": {
        "params": {
            "delta": (
                [2**i for i in range(-8, 9)]
                if OtherParas["SeleParasOn"]
                else [0.25]
            ),
            "cutting_number": [10],
        },
    },
    # --------------------------- SGD -----------------------------
    "SGD": {
        "params": {
            "alpha": (
                [2**i for i in range(-8, 9)] if OtherParas["SeleParasOn"] else [0.1]
            )
        }
    },
    # -------------------------- SPSmax ---------------------------
    "SPSmax": {
        "params": {
            "c": ([0.1, 0.5, 1, 5, 10] if OtherParas["SeleParasOn"] else [0.1]),
            "gamma": (
                [2**i for i in range(-8, 9)]
                if OtherParas["SeleParasOn"]
                else [0.125]),
        },
    },
    # ----------------------- SPBM-PF -----------------------------
    "SPBM-PF": {
        "params": {
            "M": [1e-5],
            "delta": (
                [2**i for i in range(9, 20)]
                if OtherParas["SeleParasOn"]
                else [1]
            ),
            "cutting_number": [10],
        },
    },
    # ----------------------- SPBM-TR -----------------------------
    "SPBM-TR": {
        "params": {
            "M": [1e-5],
            "delta": (
                [2**i for i in range(9, 20)]
                if OtherParas["SeleParasOn"]
                else [256]
            ),
            "cutting_number": [10],
        },
    },
    
    # ------------------- SPBM-TR-NoneLower -----------------------
    "SPBM-TR-NoneLower": {
        "params": {
            "M": [1e-5],
            "delta": (
                [2**i for i in range(0, 9)]
                if OtherParas["SeleParasOn"]
                else [256]
            ),
            "cutting_number": [10],
        },
    },
    # ------------------- SPBM-TR-NoneSpecial -----------------------
    "SPBM-TR-NoneSpecial": {
        "params": {
            "M": [1e-5],
            "delta": (
                [2**i for i in range(-8, 9)]
                if OtherParas["SeleParasOn"]
                else [1]
            ),
            "cutting_number": [10],
        },
    },
    # -------------------- SPBM-PF-NoneLower ----------------------
    "SPBM-PF-NoneLower": {
        "params": {
            "M": [1e-5],
            "delta": (
                [2**i for i in range(0, 9)]
                if OtherParas["SeleParasOn"]
                else [0]
            ),
            "cutting_number": [10],
        },
    },
    
    
    }
    return optimizer_dict

