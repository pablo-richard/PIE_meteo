import numpy as np
from netCDF4 import Dataset
import os

from .history import History
from .grid import Grid
from ..test.test_cases import create_results_netcdf

#-------------------------------------------------------------------------------------------

class Simulation():

    def __init__(self, initialCDF, T, Nt, methods, output_folder, save_rate, backup_rate, verbose=0, methods_kwargs=None):
       
        # store the initial data
        self.history = History.fromCDF(initialCDF)
        self.params = initialCDF.__dict__
        self.grid = Grid(**self.params)
        
        tinit = initialCDF['t'][:].data
        tnext = np.array((Nt-len(tinit)) * [None])
        self.timeline = np.concatenate((tinit,tnext), axis=0)
        self.T = T
        self.Nt = Nt
        
        initialCDF.close()
        
        # checkout the methods
        self.methods = methods
        self.methods_kwargs = methods_kwargs if methods_kwargs is not None else len(methods)*[None]

        # handling the output netCDF files (save & backup)
        try:
            os.mkdir(output_folder)
        except FileExistsError:
            pass
        self.output_folder = output_folder
        self.save_rate = save_rate
        self.backup_rate = backup_rate
        create_results_netcdf(output_folder + '/results.nc', **self.__dict__)
        create_results_netcdf(output_folder + '/backup.nc', **self.__dict__) 

        # other parameters
        self.verbose = verbose


    def run(self):
        if self.verbose:
            print("          ------------------------")
            print("          |  RUNNING SIMULATION  |")
            print("          ------------------------")
        for iter_nb in range(self.Nt):
            print("\n\nIteration ", iter_nb, "...") if self.verbose else None
            # first handle saving
            if iter_nb % self.backup_rate == 0:
                backupCDF = Dataset(self.output_folder + '/backup.nc', 'r+', format='NETCDF4', parallel=False)
                self.history.save(backupCDF, backup=True)
                backupCDF.close()
                print("---> backup refreshed at iteration "+str(iter_nb)) if self.verbose else None
            if iter_nb % self.save_rate == 0:
                resultsCDF = Dataset(self.output_folder + '/results.nc', 'r+', format='NETCDF4', parallel=False)
                self.history.save(resultsCDF, backup=False)  
                resultsCDF.close()  
                print("---> saved results of iteration "+str(iter_nb)) if self.verbose else None

            # then perform forward
            self.forward()
    

    def forward(self):
        for method, kwargs in zip(self.methods, self.methods_kwargs):
            print("      *** Proceeding to method: "+method.__name__) if self.verbose > 1 else None
            method(**self.__dict__, **kwargs)
