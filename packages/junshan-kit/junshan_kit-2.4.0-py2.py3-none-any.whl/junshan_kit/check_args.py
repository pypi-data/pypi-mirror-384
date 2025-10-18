import argparse
from junshan_kit import Models

def get_args():
    parser = argparse.ArgumentParser(description="Combined config argument example")

    allowed_models = ["LS", "LRL2","ResNet18"]
    allowed_optimizers = ["Adam", "SGD",]
    allowed_datasets = ["MNIST", "CIFAR100"]

    model_mapping = {
        "LS": "LeastSquares",
        "LRL2": "LogRegressionBinaryL2",
        "ResNet18": "ResNet18"
    }

    # Single combined argument that can appear multiple times
    parser.add_argument(
        "--train_group",
        type=str,
        nargs="+",                   # Allow multiple configs
        required=True,
        help = f"Format: model-dataset-optimizer (e.g., ResNet18-CIFAR10-Adam). model: {model_mapping}, \n datasets: {allowed_datasets}, optimizers: {allowed_optimizers},"
    )

    parser.add_argument(
    "--e",
    type=int,
    required=True,
    help="Number of training epochs. Example: --e 50"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for experiment reproducibility. Default: 42"
    )

    parser.add_argument(
        "--bs",
        type=int,
        required=True,
        help="Batch size for training. Example: --bs 128"
    )

    parser.add_argument(
        "--cuda",
        type=int,
        default=0,
        required=True,
        help="The number of cuda. Example: --cuda 1 (default=0) "
    )

    parser.add_argument(
        "--s",
        type=float, 
        default=1.0, 
        # required=True,
        help="Proportion of dataset to use for training split. Example: --s 0.8 (default=1.0)"
    )

    parser.add_argument(
    "--subset",
    type=float,
    nargs=2,
    # required=True,
    help = "Two subset ratios (train, test), e.g., --subset 0.7 0.3 or --subset 500 500"
    )

    args = parser.parse_args()
    args.model_mapping = model_mapping


    if args.subset is not None:
        check_subset_info(args, parser)


    check_args(args, parser, allowed_models, allowed_optimizers, allowed_datasets, model_mapping)

    return args

def check_subset_info(args, parser):
    total = sum(args.subset)
    if args.subset[0]>1:
        # CHECK
        for i in args.subset:
            if i < 1:
                parser.error(f"Invalid --subset {args.subset}: The number of subdata must > 1")    
    else:
        if abs(total - 1.0) != 0.0:  
            parser.error(f"Invalid --subset {args.subset}: the values must sum to 1.0 (current sum = {total:.6f})")


def check_args(args, parser, allowed_models, allowed_optimizers, allowed_datasets, model_mapping):
    # Parse and validate each train_group
    for cfg in args.train_group:
        try:
            model, dataset, optimizer = cfg.split("-")
        
            if model not in allowed_models:
                parser.error(f"Invalid model '{model}'. Choose from {allowed_models}")
            if optimizer not in allowed_optimizers:
                parser.error(f"Invalid optimizer '{optimizer}'. Choose from {allowed_optimizers}")
            if dataset not in allowed_datasets:
                parser.error(f"Invalid dataset '{dataset}'. Choose from {allowed_datasets}")

        except ValueError:
            parser.error(f"Invalid format '{cfg}'. Use model-dataset-optimizer")

    for cfg in args.train_group:
        model_name, dataset_name, optimizer_name = cfg.split("-")
        try:
            f = getattr(Models, f"Build_{model_mapping[model_name]}_{dataset_name}")
        except:
            print(getattr(Models, f"Build_{model_mapping[model_name]}_{dataset_name}"))