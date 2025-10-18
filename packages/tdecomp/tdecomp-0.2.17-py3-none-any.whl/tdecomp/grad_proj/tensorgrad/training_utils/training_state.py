"""
Snippet to load all artifacts of training state as Modules
without constraining to use inside a default Trainer
"""
from typing import Union
from pathlib import Path

import torch
from torch import nn
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP


def load_training_state(save_dir: Union[str, Path], 
                        save_name: str,
                        model: nn.Module,
                        optimizer: nn.Module=None,
                        scheduler: nn.Module=None,
                        regularizer: nn.Module=None,
                        map_location: dict=None,
                        distributed: bool=False) -> dict:
    
    """load_training_state returns model and optional other training modules
    saved from prior training for downstream use

    Parameters
    ----------
    save_dir : Union[str, Path]
        directory from which to load training state (model, optional optimizer, scheduler, regularizer)
    save_name : str
        name of model to load
    model : nn.Module
        model to save
    optimizer : nn.Module, optional
        optimizer object to save, by default None
    scheduler : nn.Module, optional
        scheduler object to save, by default None
    regularizer : nn.Module, optional
        regularizer object to save, by default None
    map_location : dict, optional
        mapping dictionary keyed `{device_from: device_to}`, by default None
        dictionary instructs torch to load a model from a checkpoint on rank `device_from`
        and send it to `device_to`

    Returns
    -------
    dict of training state
        keyed `{'model': model, etc}`
        
    """
    if isinstance(save_dir, str):
        save_dir = Path(save_dir)

    if not map_location:
        if dist.is_initialized():
            map_location = {"cuda:0" : f"cuda:{dist.get_rank()}"}

    if isinstance(save_dir, str):
        save_dir = Path(save_dir)
    
    torch.cuda.empty_cache()

    if distributed:
        device_id = dist.get_rank()
        save_pth = save_dir / f"{save_name}_state_dict.pt"
        model.load_state_dict(torch.load(save_pth.absolute().as_posix(), map_location="cpu"))
        model = model.to(device=f"cuda:{device_id}")
    else:
        model = model.from_checkpoint(save_dir, save_name, map_location=map_location)

    manifest_pth = save_dir / "manifest.pt"
    
    if manifest_pth.exists():
        manifest = torch.load(manifest_pth)
        print(manifest)
        epoch = manifest["epoch"]
    else:
        epoch = 0

    
    # load optimizer if state exists
    if optimizer is not None:
        optimizer_pth = save_dir / "optimizer.pt"
        if optimizer_pth.exists():
            optimizer.load_state_dict(torch.load(optimizer_pth.absolute().as_posix(), map_location=map_location))
        else:
            print(f"Warning: requested to load optimizer state, but no saved optimizer state exists in {save_dir}.")
    
    if scheduler is not None:
        scheduler_pth = save_dir / "scheduler.pt"
        if scheduler_pth.exists():
            scheduler.load_state_dict(torch.load(scheduler_pth.absolute().as_posix(), map_location=map_location))
        else:
            print(f"Warning: requested to load scheduler state, but no saved scheduler state exists in {save_dir}.")
    
    if regularizer is not None:
        regularizer_pth = save_dir / "regularizer.pt"
        if regularizer_pth.exists():
            regularizer.load_state_dict(torch.load(regularizer_pth.absolute().as_posix(), map_location=map_location))
        else:
            print(f"Warning: requested to load regularizer state, but no saved regularizer state exists in {save_dir}.")
    
    return model, optimizer, scheduler, regularizer, epoch


def save_training_state(save_dir: Union[str, Path], save_name: str,
                        model: nn.Module,
                        optimizer: nn.Module = None,
                        scheduler: nn.Module = None,
                        regularizer: nn.Module = None,
                        epoch: int=None) -> None:
    """save_training_state returns model and optional other training modules
    saved from prior training for downstream use

    Parameters
    ----------
    save_dir : Union[str, Path]
        directory from which to load training state (model, optional optimizer, scheduler, regularizer)
    save_name : str
        name of model to load
    """

    manifest = {}

    if isinstance(save_dir, str):
        save_dir = Path(save_dir)
    local_rank = 0
    if dist.is_initialized():
        local_rank = dist.get_rank()

    if local_rank == 0:
        if isinstance(model, torch.nn.parallel.DistributedDataParallel):
            save_dir.mkdir(exist_ok=True, parents=True)
            model_pth = save_dir / f"{save_name}_state_dict.pt"
            torch.save(model.module.state_dict(), model_pth.as_posix())
            #model.module.save_checkpoint(save_dir, save_name)
        else:
            model.save_checkpoint(save_dir, save_name)
        manifest['model'] = save_name
    
        # save optimizer if state exists
        if optimizer is not None:
            optimizer_pth = save_dir / "optimizer.pt"
            torch.save(optimizer.state_dict(), optimizer_pth)
            manifest['optimizer'] = "optimizer.pt"
        
        if scheduler is not None:
            scheduler_pth = save_dir / "scheduler.pt"
            torch.save(scheduler.state_dict(), scheduler_pth)
            manifest['scheduler'] = "scheduler.pt"
        
        if regularizer is not None:
            regularizer_pth = save_dir / "regularizer.pt"
            torch.save(regularizer.state_dict(), regularizer_pth)
            manifest['regularizer'] = "regularizer.pt"

        if epoch is not None:
            manifest["epoch"] = epoch
        
        torch.save(manifest, save_dir / "manifest.pt")
        
        print(f"Rank {local_rank} successfully saved training state to {save_dir}")
