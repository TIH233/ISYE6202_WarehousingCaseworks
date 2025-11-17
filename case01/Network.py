import pandas as pd

class FulfillmentNetwork:
    def __init__(self, demand_df, fc_distance_df, zip3_market_df, zip3_coords_df, fc_list):
        self.demand_df = demand_df
        self.fc_distance_df = fc_distance_df
        self.zip3_market_df = zip3_market_df
        self.zip3_coords_df = zip3_coords_df
        self.fc_list = fc_list
        
        # Distance buckets (miles): <50, 51-150, 151-300, 301-600, 601-1000, 1001-1400, 1401-1800, >1800
        self.distance_buckets = [(0, 50), (51, 150), (151, 300), (301, 600), 
                                  (601, 1000), (1001, 1400), (1401, 1800), (1801, float('inf'))]
        self.bucket_labels = ['<50', '51-150', '151-300', '301-600', 
                              '601-1000', '1001-1400', '1401-1800', '>1800']
        
        self.zip3_fc_allocation = None
        self.demand_by_fc_market = None
        self.clusters = None
        
    def get_distance_bucket(self, distance):
        for i, (low, high) in enumerate(self.distance_buckets):
            if low <= distance <= high:
                return self.bucket_labels[i]
        return self.bucket_labels[-1]
    
    def allocate_demand_to_fcs(self, primary_pct=0.9, secondary_pct=0.1):
        """90% to closest FC, 10% distributed to other FCs in same/next distance bucket"""
        allocations = []
        
        for zip3 in self.fc_distance_df['ZIP3'].unique():
            zip3_distances = {}
            for fc in self.fc_list:
                if fc in self.fc_distance_df.columns:
                    distance = self.fc_distance_df.loc[
                        self.fc_distance_df['ZIP3'] == zip3, fc].values[0]
                    zip3_distances[fc] = distance
            
            if not zip3_distances:
                continue
            
            closest_fc = min(zip3_distances.items(), key=lambda x: x[1])
            closest_fc_name, closest_distance = closest_fc[0], closest_fc[1]
            closest_bucket = self.get_distance_bucket(closest_distance)
            # bucket_index = self.bucket_labels.index(closest_bucket)
            
            secondary_fcs = [fc for fc, dist in zip3_distances.items() 
                            if fc != closest_fc_name and 
                            self.get_distance_bucket(dist) == closest_bucket]

            
            allocations.append({
                'ZIP3': zip3, 'FC': closest_fc_name, 'allocation_pct': primary_pct,
                'distance': closest_distance, 'distance_bucket': closest_bucket, 'is_primary': True
            })
            
            if secondary_fcs:
                secondary_share = secondary_pct / len(secondary_fcs)
                for fc in secondary_fcs:
                    allocations.append({
                        'ZIP3': zip3, 'FC': fc, 'allocation_pct': secondary_share,
                        'distance': zip3_distances[fc], 
                        'distance_bucket': self.get_distance_bucket(zip3_distances[fc]),
                        'is_primary': False
                    })
        
        self.zip3_fc_allocation = pd.DataFrame(allocations)
        return self.zip3_fc_allocation
    
    def aggregate_demand_by_fc_market(self):
        """Daily demand aggregated by FC and market type"""
        demand_allocated = self.demand_df.merge(
            self.zip3_fc_allocation[['ZIP3', 'FC', 'allocation_pct']], on='ZIP3', how='inner')
        
        demand_allocated['allocated_demand'] = (
            demand_allocated['Mean_Demand'] * demand_allocated['allocation_pct'])
        
        demand_allocated = demand_allocated.merge(self.zip3_market_df, on='ZIP3', how='left')
        
        self.demand_by_fc_market = demand_allocated.groupby(
            ['Day', 'FC', 'market_type'])['allocated_demand'].sum().reset_index()
        
        return self.demand_by_fc_market
    
    def create_fulfillment_clusters(self):
        primary_assignments = self.zip3_fc_allocation[
            self.zip3_fc_allocation['is_primary']][['ZIP3', 'FC', 'distance_bucket']].copy()
        
        fc_count_per_zip = self.zip3_fc_allocation.groupby('ZIP3')['FC'].nunique().reset_index()
        fc_count_per_zip.columns = ['ZIP3', 'num_fcs']
        
        clusters = primary_assignments.merge(self.zip3_coords_df, on='ZIP3', how='left')
        clusters = clusters.merge(fc_count_per_zip, on='ZIP3', how='left')
        clusters = clusters.merge(self.zip3_market_df, on='ZIP3', how='left')
        
        self.clusters = clusters
        return self.clusters
    
    def compute_single_fc_demand_proportion(self):
        demand_with_allocation = self.demand_df.merge(
            self.zip3_fc_allocation.groupby('ZIP3')['FC'].nunique().reset_index(),
            on='ZIP3', how='left')
        demand_with_allocation.columns = ['Day', 'ZIP3', 'Mean_Demand', 'CI_99_Min', 
                                          'CI_99_Max', 'Range_99', 'num_fcs']
        
        total_demand = demand_with_allocation['Mean_Demand'].sum()
        single_fc_demand = demand_with_allocation[
            demand_with_allocation['num_fcs'] == 1]['Mean_Demand'].sum()
        
        proportion = single_fc_demand / total_demand if total_demand > 0 else 0
        print(f"Proportion of demand served by single FC only: {proportion:.2%}")
        return proportion
    
    def compute_distance_bucket_distribution(self):
        demand_with_distance = self.demand_df.merge(
            self.zip3_fc_allocation[self.zip3_fc_allocation['is_primary']][
                ['ZIP3', 'distance_bucket']], on='ZIP3', how='left')
        
        bucket_distribution = demand_with_distance.groupby(
            'distance_bucket')['Mean_Demand'].sum().reset_index()
        bucket_distribution['percentage'] = (
            bucket_distribution['Mean_Demand'] / bucket_distribution['Mean_Demand'].sum() * 100)
        
        bucket_order = {label: i for i, label in enumerate(self.bucket_labels)}
        bucket_distribution['order'] = bucket_distribution['distance_bucket'].map(bucket_order)
        bucket_distribution = bucket_distribution.sort_values('order')
        
        return bucket_distribution


if __name__ == "__main__":
    print("FulfillmentNetwork class defined")