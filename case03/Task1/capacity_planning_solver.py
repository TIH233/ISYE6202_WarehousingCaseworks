import pandas as pd
import numpy as np
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, PULP_CBC_CMD


class CapacityPlanningSolver:
    """
    MIP solver for capacity planning optimization.

    Parameters for solve() method:
    ---------------------------
    part_demand : dict
        Dictionary mapping part names to demand quantities.
        Example: {'P1': 30610.0, 'P2': 15934.0, ...}

    step_df : pd.DataFrame
        DataFrame with parts as index and step columns.
        Each cell contains the step name for that part.
        Example columns: 'Step 1', 'Step 2', ...

    productivity_df : pd.DataFrame
        DataFrame with same structure as step_df containing productivity values (eta_ps).
        Typically calculated as 60 / timecost.

    K_m : dict
        Installation cost per machine type.
        Example: {'A': 50000, 'B': 60000, 'AB': 75000, ...}

    C_m_lab : dict
        Labor cost per machine-hour for each machine type.
        Example: {'A': 58.75, 'B': 58.75, ...}

    A_eff : float
        Effective available hours per machine in the planning period.
        Typically: calendar_hours * OEE

    eligibility : dict of dict
        Eligibility matrix E_ms indicating which machines can perform which steps.
        Example: {'A': {'A': 1, 'B': 0, ...}, 'AB': {'A': 1, 'B': 1, ...}, ...}
    """

    def __init__(self):
        """Initialize the solver."""
        self.model = None
        self.y_vars = None  # Machine quantity variables
        self.x_vars = None  # Machine-hour allocation variables
        self.results = None

    def _build_demand_matrix(self, part_demand, step_df):
        """
        Build D_ps matrix: required processing units for product p at step s.

        Returns:
            dict: (part, step) -> demand
        """
        D_ps = {}

        for part in step_df.index:
            part_clean = part.strip()
            if part_clean not in part_demand:
                continue

            demand = part_demand[part_clean]

            for col in step_df.columns:
                step = step_df.loc[part, col]
                if pd.notna(step):
                    step_clean = step.strip()
                    D_ps[(part_clean, step_clean)] = demand

        return D_ps

    def _extract_all_steps(self, step_df):
        """Extract unique steps from step DataFrame."""
        all_steps = set()
        for col in step_df.columns:
            for step in step_df[col].dropna().unique():
                all_steps.add(step.strip())
        return sorted(list(all_steps))

    def _build_model(self, part_demand, step_df, productivity_df, K_m, C_m_lab, A_eff, eligibility):
        """Build the optimization model."""

        # Build demand matrix
        D_ps = self._build_demand_matrix(part_demand, step_df)

        # Extract sets
        machines = list(K_m.keys())
        parts = [p.strip() for p in step_df.index]
        steps = self._extract_all_steps(step_df)

        # Initialize
        self.model = LpProblem("Capacity_Planning", LpMinimize)

        # Decision Variables
        # y_m: number of machines of type m
        self.y_vars = LpVariable.dicts("y", machines, lowBound=0, cat='Integer')

        # x_mps: machine-hours of type m allocated to product p at step s
        self.x_vars = LpVariable.dicts("x",
                                       [(m, p, s) for m in machines for p in parts for s in steps],
                                       lowBound=0, cat='Continuous')

        # Objective Function
        # min Z = sum(K_m * y_m) + sum(C_m^lab * sum(x_mps))
        installation_cost = lpSum([K_m[m] * self.y_vars[m] for m in machines])

        operational_cost = lpSum([
            C_m_lab[m] * lpSum([self.x_vars[(m, p, s)] for p in parts for s in steps])
            for m in machines
        ])

        self.model += installation_cost + operational_cost, "Total_Cost"

        # Constraints

        # 1. Demand satisfaction: sum_m (eta_ps * x_mps) >= D_ps for all p, s
        for (p, s), demand in D_ps.items():
            # Get productivity eta_ps
            try:
                part_steps = step_df.loc[p]
                step_col = None
                for col in step_df.columns:
                    if pd.notna(part_steps[col]) and part_steps[col].strip() == s:
                        step_col = col
                        break

                if step_col:
                    eta_ps = productivity_df.loc[p, step_col]

                    # Only include machines that can perform this step
                    eligible_machines = [m for m in machines if eligibility[m][s] == 1]

                    if eligible_machines:
                        self.model += (
                            lpSum([eta_ps * self.x_vars[(m, p, s)] for m in eligible_machines]) >= demand,
                            f"Demand_{p}_{s}"
                        )
            except Exception as e:
                print(f"Warning: Could not process constraint for {p}, {s}: {e}")
                continue

        # 2. Capacity coupling: sum_p sum_s (x_mps) <= A_eff * y_m for all m
        for m in machines:
            self.model += (
                lpSum([self.x_vars[(m, p, s)] for p in parts for s in steps]) <= A_eff * self.y_vars[m],
                f"Capacity_{m}"
            )

        # 3. Eligibility: x_mps = 0 when E_ms = 0
        for m in machines:
            for p in parts:
                for s in steps:
                    if eligibility[m][s] == 0:
                        self.model += self.x_vars[(m, p, s)] == 0, f"Eligibility_{m}_{p}_{s}"

        return D_ps, machines, parts, steps

    def solve(self, part_demand, step_df, productivity_df, K_m, C_m_lab, A_eff, eligibility,
              solver_time_limit=300, verbose=True):
        """
        Solve the capacity planning optimization problem.

        Parameters:
        -----------
        part_demand : dict
            Demand for each part
        step_df : pd.DataFrame
            Process steps for each part
        productivity_df : pd.DataFrame
            Productivity (units/hour) for each part-step
        K_m : dict
            Installation cost for each machine type
        C_m_lab : dict
            Labor cost per hour for each machine type
        A_eff : float
            Effective available hours per machine
        eligibility : dict of dict
            Machine-step eligibility matrix
        solver_time_limit : int, optional
            Time limit for solver in seconds (default: 300)
        verbose : bool, optional
            Print detailed output (default: True)

        Returns:
        --------
        dict : Dictionary containing solution results with keys:
            - 'status': Solution status string
            - 'total_cost': Total cost
            - 'installation_cost': Installation cost component
            - 'operational_cost': Operational cost component
            - 'machine_allocation': DataFrame with machine quantities and utilization
            - 'y_vars': Machine quantity decision variables
            - 'x_vars': Machine-hour allocation decision variables
            - 'model': The PuLP model object
        """

        if verbose:
            print("=" * 80)
            print("CAPACITY PLANNING OPTIMIZATION")
            print("=" * 80)
            print("\nBuilding optimization model...")

        # Build the model
        D_ps, machines, parts, steps = self._build_model(
            part_demand, step_df, productivity_df, K_m, C_m_lab, A_eff, eligibility
        )

        if verbose:
            print(f"Model Statistics:")
            print(f"  - Variables: {len(self.model.variables())}")
            print(f"  - Constraints: {len(self.model.constraints)}")
            print(f"  - Demand-step combinations: {len(D_ps)}")
            print(f"\nSolving MIP model...")

        # Solve the model
        solver = PULP_CBC_CMD(msg=verbose, timeLimit=solver_time_limit)
        self.model.solve(solver)

        # Check solution status
        status = LpStatus[self.model.status]

        if verbose:
            print(f"\nSolution Status: {status}")

        if self.model.status != 1:  # Not optimal
            if verbose:
                print("Warning: Optimal solution not found!")
            return {
                'status': status,
                'total_cost': None,
                'installation_cost': None,
                'operational_cost': None,
                'machine_allocation': None,
                'y_vars': self.y_vars,
                'x_vars': self.x_vars,
                'model': self.model
            }

        # Extract results
        total_cost = self.model.objective.value()
        installation_total = sum(K_m[m] * self.y_vars[m].varValue
                                for m in machines if self.y_vars[m].varValue > 0)
        operational_total = total_cost - installation_total

        # Build machine allocation DataFrame
        machine_results = []
        for m in sorted(machines):
            qty = self.y_vars[m].varValue
            if qty > 0:
                # Calculate utilization
                total_hours = sum(self.x_vars[(m, p, s)].varValue
                                for p in parts
                                for s in steps
                                if (m, p, s) in self.x_vars)

                available_hours = A_eff * qty
                utilization = (total_hours / available_hours * 100) if available_hours > 0 else 0

                machine_results.append({
                    'Machine': m,
                    'Quantity': int(qty),
                    'Installation_Cost': K_m[m] * qty,
                    'Utilization_%': utilization,
                    'Hours_Used': total_hours,
                    'Hours_Available': available_hours
                })

        machine_allocation_df = pd.DataFrame(machine_results)

        # Print results if verbose
        if verbose:
            print("\n" + "=" * 80)
            print("OPTIMAL SOLUTION")
            print("=" * 80)
            print(f"\nTotal Cost: ${total_cost:,.2f}")
            print(f"  - Installation Cost: ${installation_total:,.2f}")
            print(f"  - Operational Cost: ${operational_total:,.2f}")

            print("\n" + "-" * 80)
            print("MACHINE ALLOCATION")
            print("-" * 80)
            print(f"{'Machine':<12} {'Quantity':<10} {'Install Cost':<15} {'Utilization':<12}")
            print("-" * 80)

            for _, row in machine_allocation_df.iterrows():
                print(f"{row['Machine']:<12} {row['Quantity']:<10} "
                      f"${row['Installation_Cost']:<14,.0f} {row['Utilization_%']:<11.1f}%")

            print("-" * 80)
            print(f"Total Machines: {machine_allocation_df['Quantity'].sum()}")

        # Store and return results
        self.results = {
            'status': status,
            'total_cost': total_cost,
            'installation_cost': installation_total,
            'operational_cost': operational_total,
            'machine_allocation': machine_allocation_df,
            'y_vars': self.y_vars,
            'x_vars': self.x_vars,
            'model': self.model
        }

        return self.results

    def get_machine_allocation(self):
        """Return the machine allocation DataFrame from the last solve."""
        if self.results is None:
            raise ValueError("No solution available. Run solve() first.")
        return self.results['machine_allocation']

    def get_total_cost(self):
        """Return the total cost from the last solve."""
        if self.results is None:
            raise ValueError("No solution available. Run solve() first.")
        return self.results['total_cost']

    def save_results(self, filepath):
        """Save the machine allocation results to CSV."""
        if self.results is None:
            raise ValueError("No solution available. Run solve() first.")
        self.results['machine_allocation'].to_csv(filepath, index=False)
        print(f"Results saved to: {filepath}")
