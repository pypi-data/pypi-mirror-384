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
        If the loaded file is a 3D array, it is split into a list of 2D arrays.
        Args:
            withTumor: If True, loads reconPhantom (with tumor), else reconLaser (without tumor).
            results_date: Date string (format "ddmm") to specify which results to load. If None, uses the most recent date in saveDir.
            optimizer: Optimizer name (as string or enum) to filter results. If None, uses the current optimizer of the instance.
            filePath: Optional. If provided, loads directly from this path (overrides saveDir and results_date).
        """
        if filePath is not None:
            # Mode chargement direct depuis un fichier
            recon_key = 'reconPhantom' if withTumor else 'reconLaser'
            recon_path = filePath
            if not os.path.exists(recon_path):
                raise FileNotFoundError(f"No reconstruction file found at {recon_path}.")
            # Charge les données
            data = np.load(recon_path, allow_pickle=True)
            # Découpe en liste de 2D si c'est un tableau 3D
            if isinstance(data, np.ndarray) and data.ndim == 3:
                if withTumor:
                    self.reconPhantom = [data[i, :, :] for i in range(data.shape[0])]
                else:
                    self.reconLaser = [data[i, :, :] for i in range(data.shape[0])]
            else:
                # Sinon, suppose que c'est déjà une liste de 2D
                if withTumor:
                    self.reconPhantom = data
                else:
                    self.reconLaser = data
            # Essayer de charger les indices
            base_dir, file_name = os.path.split(recon_path)
            indices_path = os.path.join(base_dir, "indices.npy")
            if os.path.exists(indices_path):
                indices_data = np.load(indices_path, allow_pickle=True)
                if isinstance(indices_data, np.ndarray) and indices_data.ndim == 3:
                    self.indices = [indices_data[i, :, :] for i in range(indices_data.shape[0])]
                else:
                    self.indices = indices_data
            else:
                self.indices = None
            print(f"Loaded reconstruction results and indices from {recon_path}")
        else:
            # Mode chargement depuis le répertoire de résultats
            if self.saveDir is None:
                raise ValueError("Save directory is not specified. Please set saveDir before loading.")
            # Determine optimizer name for path matching
            opt_name = optimizer.value if optimizer is not None else self.optimizer.value
            # Find the most recent results directory if no date is specified
            if results_date is None:
                dirs = [
                    d for d in os.listdir(self.saveDir)
                    if os.path.isdir(os.path.join(self.saveDir, d))
                    and re.match(r'results_\d{4}_' + re.escape(opt_name) + r'($|_)', d)
                ]
                if not dirs:
                    raise FileNotFoundError(f"No results directory found for optimizer '{opt_name}' in {self.saveDir}.")
                dirs.sort(reverse=True)  # Most recent first
                results_dir = os.path.join(self.saveDir, dirs[0])
            else:
                results_dir = os.path.join(self.saveDir, f'results_{results_date}_{opt_name}')
                if not os.path.exists(results_dir):
                    raise FileNotFoundError(f"Directory {results_dir} does not exist.")
            # Load reconstruction results
            recon_key = 'reconPhantom' if withTumor else 'reconLaser'
            recon_path = os.path.join(results_dir, f'{recon_key}.npy')
            if not os.path.exists(recon_path):
                raise FileNotFoundError(f"No reconstruction file found at {recon_path}.")
            data = np.load(recon_path, allow_pickle=True)
            # Découpe en liste de 2D si c'est un tableau 3D
            if isinstance(data, np.ndarray) and data.ndim == 3:
                if withTumor:
                    self.reconPhantom = [data[i, :, :] for i in range(data.shape[0])]
                else:
                    self.reconLaser = [data[i, :, :] for i in range(data.shape[0])]
            else:
                if withTumor:
                    self.reconPhantom = data
                else:
                    self.reconLaser = data
            # Try to load saved indices (if file exists)
            indices_path = os.path.join(results_dir, 'indices.npy')
            if os.path.exists(indices_path):
                indices_data = np.load(indices_path, allow_pickle=True)
                if isinstance(indices_data, np.ndarray) and indices_data.ndim == 3:
                    self.indices = [indices_data[i, :, :] for i in range(indices_data.shape[0])]
                else:
                    self.indices = indices_data
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

            



   
