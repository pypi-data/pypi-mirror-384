import torchvision,torch, random
import numpy as np
import torchvision.transforms as transforms
from torch.utils.data import random_split, Subset
from sklearn.datasets import load_svmlight_file
from torch.utils.data import Dataset
from torch.utils.data import TensorDataset
from torch.utils.data import DataLoader
import bz2


class LibSVMDataset_bz2(Dataset):
    def __init__(self, path, data_name = None, Paras = None):
        with bz2.open(path, 'rb') as f:
            X, y = load_svmlight_file(f) # type: ignore

        self.X, self.path = X, path
        
        y = np.asanyarray(y)

        if data_name is not None:
            data_name = data_name.lower()

            # Binary classification, with the label -1/1
            if data_name in ["rcv1"]:
                y = (y > 0).astype(int)  # Convert to 0/1
            
            # Multi-category, labels usually start with 1
            elif data_name in [""]:  
                y = y - 1  # Start with 0

        else:
            # Default policy: Try to avoid CrossEntropyLoss errors
            if np.min(y) < 0:  # e.g. [-1, 1]
                y = (y > 0).astype(int)
            elif np.min(y) >= 1:
                y = y - 1

        self.y = y

    def __len__(self):
        return self.X.shape[0]

    def __getitem__(self, idx):
        xi = torch.tensor(self.X.getrow(idx).toarray(), dtype=torch.float32).squeeze(0)
        yi = torch.tensor(self.y[idx], dtype=torch.float32)
        return xi, yi
    
    def __repr__(self):
        num_samples = len(self.y)
        num_features = self.X.shape[1]
        num_classes = len(np.unique(self.y))
        return (f"LibSVMDataset_bz2(\n"
                f"  num_samples = {num_samples},\n"
                f"  num_features = {num_features},\n"
                f"  num_classes = {num_classes}\n"
                f"  path = {self.path}\n"
                f")")


def get_libsvm_bz2_data(train_path, test_path, data_name, Paras, split = True):
    
    transform = "-1 → 0 for binary, y-1 for multi-class"
    train_data = LibSVMDataset_bz2(train_path)

    if data_name in ["Duke", "Ijcnn"]:
        test_data = LibSVMDataset_bz2(test_path)
        split = False
    else:
        test_data = Subset(train_data, [])
        
    
    if split:
        total_size = len(train_data)
        train_size = int(Paras["train_ratio"] * total_size)
        test_size = total_size - train_size

        train_dataset, test_dataset = random_split(train_data, [train_size, test_size])

    else:
        train_dataset = train_data
        # # Empty test dataset, keep the structure consistent
        # test_dataset = Subset(train_data, []) 
        test_dataset = test_data

    # print(test_dataset) 
    # assert False

    return train_dataset, test_dataset, transform


# one——hot
class OneHot(Dataset):
    def __init__(self, subset, num_classes):
        self.subset = subset
        self.num_classes = num_classes

    def __len__(self):
        return len(self.subset)

    def __getitem__(self, idx):
        x, y = self.subset[idx]
        y_onehot = torch.nn.functional.one_hot(torch.tensor(y), num_classes=self.num_classes).float()
        return x, y_onehot
# one_hot

# <LibSVMDataset>
class LibSVMDataset(Dataset):
    def __init__(self, data_path, data_name=None):
        X_sparse, y = load_svmlight_file(data_path) # type: ignore
        self.X = torch.from_numpy(X_sparse.toarray()).float() # type: ignore

        # Automatically process labels
        y = np.asarray(y)

        if data_name is not None:
            data_name = data_name.lower()
            
            # Binary classification, with the label -1/1
            if data_name in ["a9a", "w8a", "ijcnn1"]:  
                y = (y > 0).astype(int)  # Convert to 0/1
            
            # Multi-category, labels usually start with 1
            elif data_name in ["letter", "shuttle"]:  
                y = y - 1  # Start with 0
            
        else:
            # Default policy: Try to avoid CrossEntropyLoss errors
            if np.min(y) < 0:  # e.g. [-1, 1]
                y = (y > 0).astype(int)
            elif np.min(y) >= 1:
                y = y - 1

        self.y = torch.from_numpy(y).long()

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

# <LibSVMDataset>

# <get_libsvm_data>
def _load_libsvm_dataset(train_path, test_path, data_name):
    train_dataset = LibSVMDataset(train_path, data_name)
    test_dataset = LibSVMDataset(test_path, data_name)
    # libSVM typically features numerical characteristics and does not require image transformation
    transform = None  

    return train_dataset, test_dataset, transform
# <get_libsvm_data>
# <ToTensor>
def get_libsvm_data(train_path, test_path, data_name):
    # laod data
    train_dataset, test_dataset, transform = _load_libsvm_dataset(train_path, test_path, data_name)
    train_data = TensorDataset(train_dataset.X, train_dataset.y)
    test_data = TensorDataset(test_dataset.X, test_dataset.y)

    return train_data, test_data, transform
# <ToTensor>

# <mnist>
def MNIST(Paras, model_name):
    """
    Load the MNIST dataset and return both the training and test sets,
    along with the transformation applied (ToTensor).
    """
    transform = torchvision.transforms.ToTensor()

    train_dataset = torchvision.datasets.MNIST(
        root='./exp_data/MNIST',
        train=True,
        download=True,
        transform=transform
    )

    test_dataset = torchvision.datasets.MNIST(
        root='./exp_data/MNIST',
        train=False,
        download=True,
        transform=transform
    )
# <binary_condition>
    if Paras["model_type"][model_name] == "binary":
# <binary_condition>
        train_mask = (train_dataset.targets == 0) | (train_dataset.targets == 1)
        test_mask = (test_dataset.targets == 0) | (test_dataset.targets == 1)

        train_indices = torch.nonzero(train_mask, as_tuple=True)[0]
        test_indices = torch.nonzero(test_mask, as_tuple=True)[0]

        train_dataset = torch.utils.data.Subset(train_dataset, train_indices.tolist())
        test_dataset = torch.utils.data.Subset(test_dataset, test_indices.tolist())

    return train_dataset, test_dataset, transform
# <mnist>

# <cifar100>
def CIFAR100(Paras, model_name):
    """
    Load the CIFAR-100 dataset with standard normalization and return both
    the training and test sets, along with the transformation applied.
    """
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5071, 0.4867, 0.4408],   
                            std=[0.2675, 0.2565, 0.2761])     
    ])

    train_dataset = torchvision.datasets.CIFAR100(
        root='./exp_data/CIFAR100',
        train=True,
        download=True,
        transform=transform
    )

    test_dataset = torchvision.datasets.CIFAR100(
        root='./exp_data/CIFAR100',
        train=False,
        download=True,
        transform=transform
    )
    if Paras["model_type"][model_name] == "binary":
        train_mask = (torch.tensor(train_dataset.targets) == 0) | (torch.tensor(train_dataset.targets) == 1)
        test_mask = (torch.tensor(test_dataset.targets) == 0) | (torch.tensor(test_dataset.targets) == 1)

        train_indices = torch.nonzero(train_mask, as_tuple=True)[0]
        test_indices = torch.nonzero(test_mask, as_tuple=True)[0]

        train_dataset = torch.utils.data.Subset(train_dataset, train_indices.tolist())
        test_dataset = torch.utils.data.Subset(test_dataset, test_indices.tolist())

    return train_dataset, test_dataset, transform
# <cifar100>


# <caltech101_Resize_32>
def convert_to_rgb(img):
    return img.convert("RGB")  # Explicitly define to avoid lambda

def caltech101_Resize_32(seed, train_ratio=0.7, split=True):
    def set_seed(seed=42):
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        np.random.seed(seed)
        random.seed(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    set_seed(seed)
    transform = transforms.Compose([
        # transforms.Lambda(convert_to_rgb),  
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize((32, 32)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],  
                            std=[0.229, 0.224, 0.225])
    ])
    
    full_dataset = torchvision.datasets.Caltech101(
        root='./exp_data/Caltech101',
        download=True,
        transform=transform
    )

    if split:
        total_size = len(full_dataset)
        train_size = int(train_ratio * total_size)
        test_size = total_size - train_size

        train_dataset, test_dataset = random_split(full_dataset, [train_size, test_size])

    else:
        train_dataset = full_dataset
        # Empty test dataset, keep the structure consistent
        test_dataset = Subset(full_dataset, [])  

    return train_dataset, test_dataset, transform

# <caltech101_Resize_32>