import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from Data import Data
from Experiment import Experiment
from Scene import Scene
import os
from Main import main

class DataVisualizer:
    def __init__(self, data: Data):
        self.data = data
        self.experiment = data.experiment
        self.scene = data.scene