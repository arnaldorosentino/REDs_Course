import py_dss_interface
import os
import pathlib
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random

from REDsProject.hc_steps import HCSteps
from REDsProject.feeder_condition import FeederCondition

script_path = os.path.dirname(os.path.abspath(__file__))
dss_file = pathlib.Path(script_path).joinpath("../feeders", "30BUS", "30-Bus_HostingCapacity.dss")

dss = py_dss_interface.DSS()

# Compile OpenDSS feeder model
dss.text(f"compile [{dss_file}]")

# Set Feeder Condition
FeederCondition.set_load_level_condition(dss, load_mult=0.2)

# Calculate HC
gen_fixed_size = 2000

buses = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17","18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30"]

buses_used = list()
hosting_capacity_values = []

for _ in range(10000):
    random.shuffle(buses)
    
    # Compile OpenDSS feeder model
    dss.text(f"compile [{dss_file}]")
         
    #Reseting the value for each iteration
    hosting_capacity_value = 0
    
    for bus in buses:
        dss.circuit.set_active_bus(bus)
        kv = dss.bus.kv_base * np.sqrt(3)

        gen_bus = dss.bus.name
        gen_kv = kv
        gen_kw = gen_fixed_size

        # Add generator at bus
        HCSteps.add_fixed_size_gen(dss, gen_bus, gen_kv, gen_fixed_size)

        HCSteps.solve_powerflow(dss)

        if HCSteps.check_overvoltage_violation(dss):
            break
        else:
            hosting_capacity_value += gen_kw
            
    hosting_capacity_values.append(hosting_capacity_value)

# Results of simulation

# Plot of HC for each simulation
plt.plot(hosting_capacity_values, marker='o')
plt.xlabel('Simulation')
plt.ylabel('Hosting Capacity Value (kW)')
plt.title('Hosting Capacity Values')
plt.grid(True)
plt.show()

# Histogram
sns.histplot(hosting_capacity_values, kde=True)
plt.xlabel('Hosting Capacity Value (kW)')
plt.ylabel('Frequency')
plt.title('Distribution of Hosting Capacity Values')
plt.show()

#Statistic Values
median_value = np.median(hosting_capacity_values)
max_value = np.max(hosting_capacity_values)
min_value = np.min(hosting_capacity_values)

print(f'HC Median_Value:{median_value}')
print(f'HC Median_Value:{max_value}')
print(f'HC Median_Value:{min_value}')