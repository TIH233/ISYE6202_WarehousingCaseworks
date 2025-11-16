"""
Generate flow proportion data structure for layout planning.

For each part (P1-P20), this script generates:
- Daily demand
- Step sequence with machines and their proportions
"""

import pandas as pd
import numpy as np
import json
from scipy.stats import norm


def generate_flow_proportions(steps_df, allocation_data, hr_demand):
    """
    Generate flow proportion data structure for all parts.

    For each part:
    - Calculate daily demand (hourly * 16 hours/day)
    - Extract step sequence
    - For each step, find which machines handle it and their proportions

    Returns:
        dict: Nested dictionary with structure:
              {part: {daily_demand: float, step_1: {step_name: str, machines: {machine: proportion}}}}
    """
    flow_data = {}

    for idx, row in steps_df.iterrows():
        part = row['Part']

        # Calculate daily demand
        hourly_demand = hr_demand.loc[part, 'Hourly Demand']
        daily_demand = hourly_demand * 16  # 16 hours per day

        # Initialize part data
        part_data = {
            'daily_demand': float(daily_demand)
        }

        # Extract step sequence
        step_sequence = []
        for col in steps_df.columns[1:]:  # Skip 'Part' column
            step = row[col]
            if pd.notna(step) and step.strip() != '':
                step_sequence.append(step.strip())

        # For each step, find machines and calculate proportions
        for step_idx, step_name in enumerate(step_sequence, start=1):
            # Find all machines that handle this (part, step) combination
            machine_hours = {}

            for machine_type, machine_data in allocation_data.items():
                for alloc in machine_data['allocations']:
                    if alloc['product'] == part and alloc['step'] == step_name:
                        machine_hours[machine_type] = alloc['hours']

            # Calculate proportions
            total_hours = sum(machine_hours.values())

            if total_hours > 0:
                machine_proportions = {
                    machine: hours / total_hours
                    for machine, hours in machine_hours.items()
                }
            else:
                machine_proportions = {}

            # Add to part data
            part_data[f'step_{step_idx}'] = {
                'step_name': step_name,
                'machines': machine_proportions
            }

        flow_data[part] = part_data

    return flow_data


def main():
    # Load steps data
    print("Loading data...")
    steps_df = pd.read_csv('../Data/Steps.csv')

    # Recalculate hourly demand
    products = ['A1', 'A2', 'A3', 'B1', 'B2']
    demand_data = {
        'Weekly_Mean': [962, 1923, 2500, 1154, 1538],
        'Weekly_CV': [0.15, 0.2, 0.2, 0.12, 0.18]
    }
    demand_df = pd.DataFrame(demand_data, index=products)
    bom_df = pd.read_csv('../Data/BOM.csv', index_col=0).T

    Z_score = norm.ppf(0.995)
    demand_df['Weekly_std'] = demand_df['Weekly_Mean'] * demand_df['Weekly_CV']
    demand_df['Product_Capacity'] = np.ceil(demand_df['Weekly_Mean'] + demand_df['Weekly_std']*Z_score)

    part_demand = pd.DataFrame()
    part_demand['Part_Weekly_Capacity'] = bom_df.dot(demand_df['Product_Capacity'])
    part_demand['Part_Weekly_Capacity'] = np.ceil(part_demand['Part_Weekly_Capacity'])
    part_demand.index = part_demand.index.str.strip()

    hr_demand = part_demand / (5*16)
    hr_demand = np.ceil(hr_demand)
    hr_demand.rename(columns={'Part_Weekly_Capacity': 'Hourly Demand'}, inplace=True)

    # Load allocation data
    with open('Allocation.json', 'r') as f:
        allocation = json.load(f)

    # Generate flow proportions
    print("Generating flow proportions...")
    flow_proportions = generate_flow_proportions(steps_df, allocation, hr_demand)

    # Save to JSON file
    with open('flow_proportions.json', 'w') as f:
        json.dump(flow_proportions, f, indent=4)

    print(f"\nFlow proportion data generated and saved to 'flow_proportions.json'")
    print(f"Generated data for {len(flow_proportions)} parts")
    print("\nSample output for P1:")
    print(json.dumps(flow_proportions['P1'], indent=2))


if __name__ == '__main__':
    main()
