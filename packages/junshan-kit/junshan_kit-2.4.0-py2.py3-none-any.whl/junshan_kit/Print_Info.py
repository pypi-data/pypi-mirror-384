


# -------------------------------------------------------------
def training_group(training_group):
    print(f"--------------------- training_group ------------------")
    for g in training_group:
        print(g)
    print(f"-------------------------------------------------------")


def training_info(use_color, data_name, optimizer_name, folder_path, hyperparams, Paras, model_name):
    if use_color:
        print("\033[90m" + "-" * 115 + "\033[0m")
        print(
            f"\033[32m✅ \033[34mDataset:\033[32m {data_name}, \t\033[34mBatch-size:\033[32m {Paras['batch_size'][data_name]}, \t\033[34m(training, val, test) = \033[32m ({Paras['training_samples']}, {Paras['val_samples']}, {Paras['test_samples']}), \t\033[34m device:\033[32m {Paras['device']}"
        )
        print(
            f"\033[32m✅ \033[34mOptimizer:\033[32m {optimizer_name}, \t\033[34mParams:\033[32m {hyperparams}"
        )
        print(
            f'\033[32m✅ \033[34mmodel:\033[32m {model_name}, \t\033[34mmodel type:\033[32m {Paras["model_type"][model_name]},\t\033[34m loss_fn:\033[32m {Paras["loss_fn"]},\t\033[34m Subset:\033[32m {Paras["select_subset"][data_name]}'
        )
        print(f"\033[32m✅ \033[34mfolder_path:\033[32m {folder_path}")
        print("\033[90m" + "-" * 115 + "\033[0m")

    else:
        print("-" * 115)
        print(
            f"✅ Dataset: {data_name}, \tBatch-size: {Paras['batch_size'][data_name]}, \t(training, val, test) = ({Paras['training_samples']}, {Paras['val_samples']}, {Paras['test_samples']}), \tdevice: {Paras['device']}"
        )
        print(f"✅ Optimizer: {optimizer_name}, \tParams: {hyperparams}")
        print(
            f'✅ model: {model_name}, \t model type: {Paras["model_type"][model_name]}, loss_fn: {Paras["loss_fn"]}'
        )
        print(f"✅ folder_path: {folder_path}")
        print("-" * 115)
        
# <Step_7_2>

def print_per_epoch_info(use_color, epoch, Paras, epoch_loss, training_loss, training_acc, test_loss, test_acc, run_time):
    epochs = Paras["epochs"][Paras["data_name"]]
    # result = [(k, f"{v:.4f}") for k, v in run_time.items()]
    if use_color:
        print(
            f'\033[34m epoch = \033[32m{epoch+1}/{epochs}\033[0m,\t\b'
            f'\033[34m epoch_loss = \033[32m{epoch_loss[epoch+1]:.4e}\033[0m,\t\b'
            f'\033[34m train_loss = \033[32m{training_loss[epoch+1]:.4e}\033[0m,\t\b'
            f'\033[34m train_acc = \033[32m{100 * training_acc[epoch+1]:.2f}%\033[0m,\t\b'
            f'\033[34m test_acc = \033[32m{100 * test_acc[epoch+1]:.2f}%\033[0m,\t\b'
            f'\033[34m time (ep, tr, te) = \033[32m({run_time["epoch"]:.2f}, {run_time["train"]:.2f}, {run_time["test"]:.2f})\033[0m')
    else:
        print(
        f'epoch = {epoch+1}/{epochs},\t'
        f'epoch_loss = {epoch_loss[epoch+1]:.4e},\t'
        f'train_loss = {training_loss[epoch+1]:.4e},\t'
        f'train_acc = {100 * training_acc[epoch+1]:.2f}%,\t'
        f'test_acc = {100 * test_acc[epoch+1]:.2f}%,\t'
        f'time (ep, tr, te) = ({run_time["epoch"]:.2f}, {run_time["train"]:.2f}, {run_time["test"]:.2f})')