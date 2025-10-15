import pandas as pd

def find_heat_exchange_combinations(self):
    # Extract hot and cold streams above pinch
    hot_streams_above = self.stream_list_above[self.stream_list_above['StreamType'] == 'HS']
    cold_streams_above = self.stream_list_above[self.stream_list_above['StreamType'] == 'CS']

    # Find all combinations where mCpH <= mCpC for above pinch
    self.combinations_above = [
        (
            hot_stream['name'], 
            cold_stream['name'], 
            hot_stream['id'], 
            cold_stream['id'],
            min(abs(hot_stream['delta_H']), abs(cold_stream['delta_H']))  # Q_max
            )

                            for _, hot_stream in hot_streams_above.iterrows()
                            for _, cold_stream in cold_streams_above.iterrows()
                            if hot_stream['mCp'] <= cold_stream['mCp']]
   #print(f"Above pinch combinations-------------------------------------------\n: {self.combinations_above}")
    # Extract hot and cold streams below pinch
    hot_streams_below = self.stream_list_below[self.stream_list_below['StreamType'] == 'HS']
    cold_streams_below = self.stream_list_below[self.stream_list_below['StreamType'] == 'CS']

    # Find all combinations where mCpHS >= mCpCS for below pinch
    self.combinations_below = [
        (
            hot_stream['name'], 
            cold_stream['name'], 
            hot_stream['id'], 
            cold_stream['id'],
            min(abs(hot_stream['delta_H']), abs(cold_stream['delta_H']))  # Q_max
            )
                            for _, hot_stream in hot_streams_below.iterrows()
                            for _, cold_stream in cold_streams_below.iterrows()
                            if hot_stream['mCp'] >= cold_stream['mCp']]

    # Create DataFrame for above pinch combinations
    self.combinations_above = pd.DataFrame(self.combinations_above, columns=['HS_name', 'CS_name', 'HS_id', 'CS_id', 'Q_max']
                                           ).sort_values(by="Q_max", ascending=False).reset_index(drop=True)
    self.combinations_above['Location'] = 'above'  # Add column for 'above'
    self.combinations_above['id'] = range(1, len(self.combinations_above) + 1)  # Assign local IDs starting from 1

    # Create DataFrame for below pinch combinations
    self.combinations_below = pd.DataFrame(self.combinations_below, columns=['HS_name', 'CS_name', 'HS_id', 'CS_id', 'Q_max']
                                           ).sort_values(by="Q_max", ascending=False).reset_index(drop=True)
    self.combinations_below['Location'] = 'below'  # Add column for 'below'
    self.combinations_below['id'] = range(len(self.combinations_above) + 1, len(self.combinations_above) + len(self.combinations_below) + 1)  # Continue IDs from where above ends

    # Combine the results into a single DataFrame
    self.df_combined = pd.concat([self.combinations_above, self.combinations_below], ignore_index=True)

    return self.df_combined



