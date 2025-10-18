import torchvision,torch, random
import numpy as np
from torchvision.models import resnet18,resnet34, ResNet18_Weights, ResNet34_Weights
import torch.nn as nn


# ---------------- Build ResNet18 - Caltech101 -----------------------
def Build_ResNet18_CALTECH101_Resize_32():
    
    """
    1. Modify the first convolutional layer for smaller input (e.g., 32x32 instead of 224x224)
    Original: kernel_size=7, stride=2, padding=3 → changed to 3x3 kernel, stride=1, padding=1

    2. Adjust the final fully connected layer to match the number of Caltech101 classes (101)
    """
    model = resnet18(weights=None)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False) # 1
    model.fc = nn.Linear(model.fc.in_features, 101) # 2

    return model


# ---------------- Build ResNet18 - CIFAR100 -----------------------
def Build_ResNet18_CIFAR100():
    """
    1. Modify the first convolutional layer for smaller input (e.g., 32x32 instead of 224x224)  
    Original: kernel_size=7, stride=2, padding=3 → changed to 3x3 kernel, stride=1, padding=1

    2. Adjust the final fully connected layer to match the number of CIFAR-100 classes (100)
    """
    
    model = resnet18(weights=None)
    # model = resnet18(weights=ResNet18_Weights.DEFAULT)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)  # 1
    model.fc = nn.Linear(model.fc.in_features, 100)  # 2

    return model


# ---------------- Build ResNet18 - MNIST ----------------------------
def Build_ResNet18_MNIST():
    """
    1. Modify the first convolutional layer to accept grayscale input (1 channel instead of 3)  
    Original: in_channels=3 → changed to in_channels=1

    2. Adjust the final fully connected layer to match the number of MNIST classes (10)
    """
    
    model = resnet18(weights=None)
    model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)  # 1
    model.fc = nn.Linear(model.fc.in_features, 10)  # 2

    return model


# ---------------- Build ResNet34 - CIFAR100 -----------------------
def Build_ResNet34_CIFAR100():
    
    model = resnet34(weights=None)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False) 
    model.fc = nn.Linear(model.fc.in_features, 100)  
    return model

# ---------------- Build ResNet18 - MNIST ----------------------------
def Build_ResNet34_MNIST():
    # Do not load the pre-trained weights
    model = resnet34(weights=None)  

    model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)  
    model.fc = nn.Linear(model.fc.in_features, 10)  

    return model

# ---------------- Build ResNet34 - Caltech101 -----------------------
def Build_ResNet34_CALTECH101_Resize_32():
    
    model = resnet34(weights=None)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    model.fc = nn.Linear(model.fc.in_features, 101)
    return model


#**************************************************************
# ---------------------- LeastSquares -------------------------
#**************************************************************
# ---------------- LeastSquares - MNIST -----------------------
def Build_LeastSquares_MNIST():
    """
    1. flatten MNIST images (1x28x28 → 784)
    2. Use a linear layer for multi-classification
    """
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(28 * 28, 10))

# ---------------- LeastSquares - CIFAR100 --------------------
def Build_LeastSquares_CIFAR100():
    """
    1. flatten MNIST images (3 * 32 * 32 → 784)
    2. Use a linear layer for multi-classification
    """
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(3 * 32 * 32, 100))

# ---------------- LeastSquares - Caltech101 ------------------
def Build_LeastSquares_CALTECH101_Resize_32():
    return nn.Sequential(
        nn.Flatten(),
        nn.Linear(3*32*32, 101)
    )


#*************************************************************
# --------------- LogRegressionBinary ------------------------
#*************************************************************
# -------------- LogRegressionBinary - MNIST ------------------
def Build_LogRegressionBinary_MNIST():
    """
    1. flatten MNIST images (1x28x28 → 784)
    2. Use a linear layer for binary classification
    """
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(28 * 28, 1))


# --------------- LogRegressionBinary - CIFAR100 --------------
def Build_LogRegressionBinary_CIFAR100():
    """
    1. flatten CIFAR100 images 
    2. Use a linear layer for binary classification
    """
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(3* 32 * 32, 1))

# -------------- LogRegressionBinary - RCV1 ------------------
def Build_LogRegressionBinary_RCV1():
    """
    1. Use a linear layer for binary classification
    """
    return nn.Sequential(                    
        nn.Linear(47236, 1))

# <LogRegressionBinaryL2>
#**************************************************************
# ------------- LogRegressionBinaryL2 -------------------------
#**************************************************************
def Build_LogRegressionBinaryL2_RCV1():
    """
    1. Use a linear layer for binary classification
    """
    return nn.Sequential(                    
        nn.Linear(47236, 1))
# <LogRegressionBinaryL2>

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_MNIST():
    """
    1. flatten MNIST images (1x28x28 -> 784)
    2. Use a linear layer for binary classification
    """
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(28 * 28, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_CIFAR100():
    """
    1. flatten CIFAR100 images 
    2. Use a linear layer for binary classification
    """
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(3* 32 * 32, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_Duke():
    """
    Use a linear layer for binary classification
    """
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(7129, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_Ijcnn():
    """
    Use a linear layer for binary classification
    """
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(22, 1))

# ---------------------------------------------------------
def Build_LogRegressionBinaryL2_w8a():
    """
    Use a linear layer for binary classification
    """
    return nn.Sequential(
        nn.Flatten(),                      
        nn.Linear(300, 1))




