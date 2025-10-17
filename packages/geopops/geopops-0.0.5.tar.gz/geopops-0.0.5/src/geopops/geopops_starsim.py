import pandas as pd
import starsim as ss
import pandas as pd
from scipy.io import mmread
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class ForStarsim:
    """Creates and initializes Starsim People objects from GeoPops data.
    
    This class orchestrates the creation of Starsim People objects using processed
    GeoPops data. It follows the same pattern as other GeoPops classes.
    """
    
    def __init__(self, config_dict=None, config_path=None, base_dir=None):
        """Create a Starsim runner.
        
        Args:
            config_dict: Optional dict with configuration. If provided, takes precedence over config_path.
            config_path: Optional path to a JSON config file. Defaults to config.json in package directory.
            base_dir: Optional base dir to use for relative paths. Defaults to package directory.
        """
        # Use package directory as base, same as census.py
        self.base_dir = base_dir if base_dir is not None else BASE_DIR
        
        if config_dict is not None:
            self.config = config_dict
        else:
            cfg_path = config_path if config_path is not None else os.path.join(self.base_dir, "config.json")
            if not os.path.exists(cfg_path):
                raise FileNotFoundError(f"config.json file not found at {cfg_path}. Please create this file with the required configuration.")
            with open(cfg_path, "r") as f:
                self.config = json.load(f)
        
        # Set path from config (no hardcoded default)
        self.path = self.config.get("path")
        
        self.run_all()
    
    def run_all(self):
        """Run the complete Starsim setup process."""
        print("Creating Starsim People object from GeoPops data")
        
        # Make people dataframe
        adj_mat_keys = pd.read_csv(f'{self.path}/pop_export/adj_mat_keys.csv')
        people = pd.read_csv(f'{self.path}/pop_export/people.csv')
        ppl_df = adj_mat_keys.merge(people, on=['p_id','hh_id','cbg_id'], how='left')
        
        # Age groups
        ppl_df.loc[ppl_df['age'] >= 0, 'agegroup'] = 0.0
        ppl_df.loc[ppl_df['age'] >= 10, 'agegroup'] = 1.0
        ppl_df.loc[ppl_df['age'] >= 20, 'agegroup'] = 2.0
        ppl_df.loc[ppl_df['age'] >= 30, 'agegroup'] = 3.0
        ppl_df.loc[ppl_df['age'] >= 40, 'agegroup'] = 4.0
        ppl_df.loc[ppl_df['age'] >= 50, 'agegroup'] = 5.0
        ppl_df.loc[ppl_df['age'] >= 60, 'agegroup'] = 6.0
        ppl_df.loc[ppl_df['age'] >= 70, 'agegroup'] = 7.0
        ppl_df.loc[ppl_df['age'] >= 80, 'agegroup'] = 8.0
        ppl_df.loc[ppl_df['age'] >= 90, 'agegroup'] = 9.0
        
        # Student status
        ppl_df.loc[~ppl_df['sch_grade'].isna(), 'student'] = 1.0
        
        # Race/ethnicity
        ppl_df.loc[ppl_df['race_black_alone'] == 0, 'race'] = 0.0
        ppl_df.loc[ppl_df['hispanic'] == 1, 'race'] = 1.0
        ppl_df.loc[ppl_df['white_non_hispanic'] == 1, 'race'] = 2.0
        
        # State/county
        cbg_idxs = pd.read_csv(f'{self.path}/pop_export/cbg_idxs.csv')
        ppl_df = ppl_df.merge(cbg_idxs, on='cbg_id', how='left')
        ppl_df['state'] = ppl_df['cbg_geocode'].astype(str).str[:2]
        ppl_df['county'] = ppl_df['cbg_geocode'].astype(str).str[:5]
        
        # Will need to overwrite starsim age and female states
        age = ss.FloatArr('age', default=ss.BaseArr(ppl_df['age'].values))
        female = ss.FloatArr('female', default=ss.BaseArr(ppl_df['female'].values))
        
        # Other GeoPops attributes to add as starsim states
        agegroup = ss.FloatArr('agegroup', default=ss.BaseArr(ppl_df['agegroup'].values))
        race = ss.FloatArr('race', default=ss.BaseArr(ppl_df['race'].values))
        cbg = ss.FloatArr('cbg_geocode', default=ss.BaseArr(ppl_df['cbg_geocode'].values))
        working = ss.FloatArr('working', default=ss.BaseArr(ppl_df['working'].values))
        student = ss.FloatArr('student', default=ss.BaseArr(ppl_df['student'].values))
        
        # Create the people object
        self.ppl = ss.People(n_agents=len(ppl_df), extra_states=[agegroup, race, cbg, working, student])
        
        # Add the age state to the existing people object 
        self.ppl.states.append(age, overwrite=True)
        setattr(self.ppl, age.name, age)
        age.link_people(self.ppl)
        
        # Add the female state to the existing people object 
        self.ppl.states.append(female, overwrite=True)
        setattr(self.ppl, female.name, female)
        female.link_people(self.ppl)
        
        # Initialize sim and save ppl object 
        self.sim = ss.Sim(people=self.ppl).init()
        
        # Create output directory if it doesn't exist
        os.makedirs(f'{self.path}/pop_export/starsim', exist_ok=True)
        ss.save(f'{self.path}/pop_export/starsim/ppl.pkl', self.ppl)
        print("Starsim People object created and saved successfully")
        
         # Make networks
        def newLayer(file):
            #file = f'{self.path}/adj_upper_triang_wp.mtx' # uncomment this if you'd like to go through line by line
            m = mmread(file) # Read in the mtx file
            mat_data = {'p1': m.col, 'p2': m.row}
            mat = pd.DataFrame(data=mat_data) # Join p1 and p2 in a dataframe
            mat['beta'] = 1 # Add the column 'beta'. This is the weight of the link between p1 and p2
            return mat
         
         # read in matrix files
        net_h = newLayer(f'{self.path}/pop_export/adj_upper_triang_hh.mtx')
        net_s = newLayer(f'{self.path}/pop_export/adj_upper_triang_sch.mtx')
        net_w = newLayer(f'{self.path}/pop_export/adj_upper_triang_wp.mtx')
        net_g = newLayer(f'{self.path}/pop_export/adj_upper_triang_gq.mtx')

         # export csv files
        net_h.to_csv(f'{self.path}/pop_export/starsim/net_h.csv') 
        net_s.to_csv(f'{self.path}/pop_export/starsim/net_s.csv')
        net_w.to_csv(f'{self.path}/pop_export/starsim/net_w.csv')
        net_g.to_csv(f'{self.path}/pop_export/starsim/net_g.csv')

        print("Network csv files created and saved successfully")


def main():
    """Main function for command-line usage."""
    runner = ForStarsim()
    return runner 