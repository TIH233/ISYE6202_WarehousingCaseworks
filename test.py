import pandas as pd
import pulp

# 1. Inputs

print(f"load packages")

# The number of minutes that a fractal center (f=4) needs to handle each week
# Sum the total minute requirements of the 20 centers of 'parts organization' and then divide by 4.
process_requirements = {
    'A': (30607.00 + 19915.0 + 13511.00 + 4377.0) / 4,
    'B': (153035.00 + 14514.5 + 27022.00 + 15735.0 + 7295.0) / 4,
    'C': (15303.50 + 7966.0 + 6220.5 + 7867.5 + 2918.0 + 15495.0) / 4,
    'D': (76517.50 + 39830.0 + 24882.0 + 40533.00 + 36715.0 + 17508.0 + 72310.0) / 4,
    'E': (20660.0 + 7553.75 + 16755.0 + 9949.50 + 29180.0 + 14340.0 + 8962.5 + 26755.00 + 2266.5) / 4,
    'F': (30990.0 + 23457.0 + 11607.75 + 14340.0 + 16132.5 + 40132.50 + 3777.5 + 22582.5) / 4,
    'G': (3377.75 + 16755.0 + 8754.0 + 7170.0 + 5377.5 + 13377.50 + 1511.0) / 4,
    'H': (15932.0 + 16888.75 + 5836.0 + 12086.00 + 14340.0 + 46821.25 + 7555.0 + 90330.0) / 4,
    'I': (38258.75 + 12441.0 + 18357.5 + 7295.0 + 25825.0 + 6043.00 + 16755.0 + 8291.25 + 8754.0 + 17925.0 + 8962.5 + 22582.5) / 4,
    'J': (76517.50 + 39830.0 + 20735.0 + 16049.0 + 41320.0 + 3021.50 + 40212.0 + 13266.00 + 17925.0 + 7555.0 + 45165.0) / 4,
    'K': (5377.5 + 21566.25 + 16293.0) / 4,
    'L': (21510.0 + 21566.25 + 124410.25 + 43448.0) / 4,
    'M': (25095.0 + 64698.75 + 182956.25 + 65172.0) / 4
}
ALL_PROCESSES = list(process_requirements.keys())

# The effective working minutes per machine per week
EFFECTIVE_MINS_PER_WEEK = 4233.60

# Equipment specifications, costs and capabilities
machine_data = {
    # A-D 
    "A": {"cost": 150000, "processes": ["A"]},
    "B": {"cost": 200000, "processes": ["B"]},
    "C": {"cost": 250000, "processes": ["C"]},
    "D": {"cost": 300000, "processes": ["D"]},
    "AB": {"cost": 250000, "processes": ["A", "B"]},
    "AC": {"cost": 280000, "processes": ["A", "C"]},
    "CD": {"cost": 350000, "processes": ["C", "D"]},
    "ABC": {"cost": 300000, "processes": ["A", "B", "C"]},
    "ABCD": {"cost": 400000, "processes": ["A", "B", "C", "D"]},
    # E-G 
    "E": {"cost": 400000, "processes": ["E"]},
    "F": {"cost": 400000, "processes": ["F"]},
    "G": {"cost": 400000, "processes": ["G"]},
    "EF": {"cost": 450000, "processes": ["E", "F"]},
    "EG": {"cost": 450000, "processes": ["E", "G"]},
    "FG": {"cost": 450000, "processes": ["F", "G"]},
    "EFG": {"cost": 500000, "processes": ["E", "F", "G"]},
    # H-J 
    "H": {"cost": 1000000, "processes": ["H"]},
    "I": {"cost": 500000, "processes": ["I"]},
    "J": {"cost": 500000, "processes": ["J"]},
    "IJ": {"cost": 750000, "processes": ["I", "J"]},
    # K-M 
    "K": {"cost": 80000, "processes": ["K"]},
    "L": {"cost": 100000, "processes": ["L"]},
    "M": {"cost": 50000, "processes": ["M"]},
    "KL": {"cost": 140000, "processes": ["K", "L"]},
    "KM": {"cost": 100000, "processes": ["K", "M"]},
    "LM": {"cost": 120000, "processes": ["L", "M"]},
    "KLM": {"cost": 150000, "processes": ["K", "L", "M"]}
}
MACHINE_NAMES = list(machine_data.keys())


# 2. initialize
prob = pulp.LpProblem("Fractal_F1_Machine_Mix", pulp.LpMinimize)

# 3. decision variable
n_machines = pulp.LpVariable.dicts(
    "N",
    MACHINE_NAMES,
    lowBound=0,
    cat='Integer'
)
time_allocations = pulp.LpVariable.dicts(
    "T",
    [(m, p) for m in MACHINE_NAMES for p in machine_data[m]["processes"]],
    lowBound=0,
    cat='Continuous'
)

# 4. obj.
prob += pulp.lpSum([
    machine_data[m]["cost"] * n_machines[m] for m in MACHINE_NAMES
]), "Total_Equipment_Cost"

# 5. Define constraints

# 约束 1: 工艺需求必须满足 (Demand Satisfaction)
for p in ALL_PROCESSES:
    prob += pulp.lpSum([
        time_allocations[(m, p)] for m in MACHINE_NAMES
        if p in machine_data[m]["processes"]
    ]) >= process_requirements[p], f"Meet_Demand_for_{p}"

# 约束 2: 设备产能不能超 (Capacity Limitation)
for m in MACHINE_NAMES:
    prob += pulp.lpSum([
        time_allocations[(m, p)] for p in machine_data[m]["processes"]
    ]) <= EFFECTIVE_MINS_PER_WEEK * n_machines[m], f"Capacity_Limit_for_{m}"

# --- 6. Solve the Model ---
solver_to_use = pulp.PULP_CBC_CMD(msg=False) # msg=False to turn off verbose logs
prob.solve(solver_to_use)

# --- 7. Print the Results ---
print(f"--- Solve Complete ---")

# We compare prob.status to pulp.LpStatusOptimal (which is 1)
print(f"Status: {pulp.LpStatus[prob.status]}")

if prob.status == pulp.LpStatusOptimal: # <-- This is the fix
    
    # Print Total Cost
    total_cost_f1 = pulp.value(prob.objective)
    print(f"\n--- Optimal Equipment Plan for 'Fractal Center F1' ---")
    print(f"Minimum Equipment Investment for a Single Center (F1): ${total_cost_f1:,.2f}")
    
    # Calculate Total Factory Investment
    total_factory_cost = total_cost_f1 * 4 # f=4
    print(f"Total Factory Equipment Investment (F1, F2, F3, F4): ${total_factory_cost:,.2f}")

    print("\n--- Optimal Machine Mix for F1 Center ---")
    total_machines_f1 = 0
    machine_mix_f1 = {}
    for m in MACHINE_NAMES:
        if n_machines[m].varValue is not None:
            count = int(round(n_machines[m].varValue))
            if count > 0:
                print(f"  {m}: {count} units")
                total_machines_f1 += count
                machine_mix_f1[m] = count
                
    print(f"  ---------------------")
    print(f"  Total Machines in F1 Center: {total_machines_f1} units")
    print(f"  Total Factory Machines (f=4): {total_machines_f1 * 4} units")

    print("\n--- Time Allocations for F1 Center (showing > 0) ---")
    time_allocations_f1 = {}
    for (m, p) in time_allocations:
        if time_allocations[(m, p)].varValue is not None and time_allocations[(m, p)].varValue > 0.1:
            alloc_time = time_allocations[(m, p)].varValue
            print(f"  {m} -> {p}: {alloc_time:,.1f} minutes")
            if (m,p) not in time_allocations_f1:
                time_allocations_f1[(m,p)] = 0
            time_allocations_f1[(m,p)] += alloc_time

else:
    print("Optimal solution not found. Please check the solver logs.")