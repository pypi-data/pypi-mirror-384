from AOT_biomaps.AOT_Recon.AlgebraicRecon import AlgebraicRecon
from AOT_biomaps.AOT_Recon.ReconEnums import ReconType, ProcessType
from AOT_biomaps.AOT_Recon.AOT_Optimizers import CP_KL, CP_TV
from AOT_biomaps.AOT_Recon.ReconEnums import OptimizerType

import os
from datetime import datetime
import numpy as np
import re

class PrimalDualRecon(AlgebraicRecon):
    """
    This class implements the convex reconstruction process.
    It currently does not perform any operations but serves as a template for future implementations.
    """
    def __init__(self, theta=1.0, L=None, **kwargs):
        super().__init__(**kwargs)
        self.reconType = ReconType.Convex
        self.theta = theta # relaxation parameter (between 1 and 2)
        self.L = L # norme spectrale de l'opérateur linéaire défini par les matrices P et P^T

    def run(self, processType=ProcessType.PYTHON, withTumor=True):
        """
        This method is a placeholder for the convex reconstruction process.
        It currently does not perform any operations but serves as a template for future implementations.
        """
        if(processType == ProcessType.CASToR):
            self._convexReconCASToR(withTumor)
        elif(processType == ProcessType.PYTHON):
            self._convexReconPython(withTumor)
        else:
            raise ValueError(f"Unknown convex reconstruction type: {processType}")

    def _convexReconCASToR(self, withTumor):
        raise NotImplementedError("CASToR convex reconstruction is not implemented yet.")


    def checkExistingFile(self, date = None):
        """
        Check if the file already exists, based on current instance parameters.
        Returns:
            tuple: (bool: whether to save, str: the filepath)
        """
        if date is None:
            date = datetime.now().strftime("%d%m")
        results_dir = os.path.join(
            self.saveDir,
            f'results_{date}_{self.optimizer.value}_Alpha_{self.alpha}_Theta_{self.theta}_L_{self.L}'
        )
        os.makedirs(results_dir, exist_ok=True)

        if os.path.exists(os.path.join(results_dir,"reconIndices.npy")):
            return (True, results_dir)

        return (False, results_dir)

    def load(self, withTumor=True, results_date=None, optimizer=None, filePath=None):
        """
        Load the reconstruction results (reconPhantom or reconLaser) and indices as lists of 2D np arrays into self.
        Args:
            withTumor (bool): If True, loads reconPhantom (with tumor), else reconLaser (without tumor).
            results_date (str): Date string (format "ddmm") to specify which results to load. If None, uses the most recent date in saveDir.
            optimizer: Optimizer name (as string or enum) to filter results. If None, uses the current optimizer of the instance.
            filePath (str): Optional. If provided, loads directly from this path (overrides saveDir and results_date).
        """
        recon_key = 'reconPhantom' if withTumor else 'reconLaser'
        if filePath is not None:
            # Direct file loading mode
            if not os.path.exists(filePath):
                raise FileNotFoundError(f"No reconstruction file found at {filePath}.")
            if withTumor:
                self.reconPhantom = np.load(filePath, allow_pickle=True)  # Liste de np.array 2D
            else:
                self.reconLaser = np.load(filePath, allow_pickle=True)    # Liste de np.array 2D
            # Try to load indices (file with "_indices.npy" suffix)
            base_dir, file_name = os.path.split(filePath)
            file_base, _ = os.path.splitext(file_name)
            indices_path = os.path.join(base_dir, f"indices.npy")
            if os.path.exists(indices_path):
                self.indices = np.load(indices_path, allow_pickle=True)    # Liste de np.array 2D
            else:
                self.indices = None
            print(f"Loaded reconstruction results and indices from {filePath}")
        else:
            # Results directory loading mode
            if self.saveDir is None:
                raise ValueError("Save directory is not specified. Please set saveDir before loading.")
            # Determine optimizer name for path matching
            opt_name = optimizer.value if optimizer is not None else self.optimizer.value
            # Find the most recent results directory if no date is specified
            if results_date is None:
                # Look for directories in the format results_ddmm_OptimizerName
                dirs = [
                    d for d in os.listdir(self.saveDir)
                    if os.path.isdir(os.path.join(self.saveDir, d))
                    and re.match(r'results_\d{4}_' + re.escape(opt_name) + r'($|_)', d)
                ]
                if not dirs:
                    raise FileNotFoundError(f"No results directory found for optimizer '{opt_name}' in {self.saveDir}.")
                dirs.sort(reverse=True)  # Most recent first (reverse alphabetical order)
                results_dir = os.path.join(self.saveDir, dirs[0])
            else:
                results_dir = os.path.join(self.saveDir, f'results_{results_date}_{opt_name}')
                if not os.path.exists(results_dir):
                    raise FileNotFoundError(f"Directory {results_dir} does not exist.")
            # Load reconstruction results as list of 2D arrays
            recon_path = os.path.join(results_dir, f'{recon_key}.npy')
            if not os.path.exists(recon_path):
                raise FileNotFoundError(f"No reconstruction file found at {recon_path}.")
            if withTumor:
                self.reconPhantom = np.load(recon_path, allow_pickle=True)  # Liste de np.array 2D
            else:
                self.reconLaser = np.load(recon_path, allow_pickle=True)    # Liste de np.array 2D
            # Try to load saved indices (if file exists)
            indices_path = os.path.join(results_dir, 'indices.npy')
            if os.path.exists(indices_path):
                self.indices = np.load(indices_path, allow_pickle=True)    # Liste de np.array 2D
            else:
                self.indices = None
            print(f"Loaded reconstruction results and indices from {results_dir}")


    def _convexReconPython(self, withTumor):
        if withTumor:
            y=self.experiment.AOsignal_withTumor

        else:
            y=self.experiment.AOsignal_withoutTumor

        if self.optimizer == OptimizerType.CP_TV:
            if withTumor:
                self.reconPhantom, self.indices = CP_TV(
                    self.SMatrix, 
                    y=self.experiment.AOsignal_withTumor, 
                    alpha=self.alpha, 
                    theta=self.theta, 
                    numIterations=self.numIterations, 
                    isSavingEachIteration=self.isSavingEachIteration,
                    L=self.L, 
                    withTumor=withTumor,
                    device=None
                    )
            else:
                self.reconLaser, self.indices = CP_TV(
                    self.SMatrix, 
                    y=self.experiment.AOsignal_withoutTumor, 
                    alpha=self.alpha, 
                    theta=self.theta, 
                    numIterations=self.numIterations, 
                    isSavingEachIteration=self.isSavingEachIteration,
                    L=self.L, 
                    withTumor=withTumor,
                    device=None
                    )
        elif self.optimizer == OptimizerType.CP_KL:
            if withTumor:
                self.reconPhantom, self.indices = CP_KL(
                    self.SMatrix, 
                    y=self.experiment.AOsignal_withTumor, 
                    alpha=self.alpha, 
                    theta=self.theta, 
                    numIterations=self.numIterations, 
                    isSavingEachIteration=self.isSavingEachIteration,
                    L=self.L, 
                    withTumor=withTumor,
                    device=None
                )
            else:
                self.reconLaser, self.indices = CP_KL(
                    self.SMatrix, 
                    y=self.experiment.AOsignal_withoutTumor, 
                    alpha=self.alpha, 
                    theta=self.theta, 
                    numIterations=self.numIterations, 
                    isSavingEachIteration=self.isSavingEachIteration,
                    L=self.L, 
                    withTumor=withTumor,
                    device=None
                )
        else:
            raise ValueError(f"Optimizer value must be CP_TV or CP_KL, got {self.optimizer}")

            



   
