import pandas as pd
import numpy as np
import pickle
import copy
from typing import Dict, List, Set, Tuple, Any
from plotting_configs import get_node_color, DEFAULT_NODE_COLOR

def load_cwns_data(data_dir = 'data/2022CWNS_NATIONAL_APR2024/'):
    """
    Load all CWNS data files from specified directory
    
    Args:
        data_dir: Directory containing CWNS data files
        
    Returns:
        Dictionary of DataFrames containing cleaned CWNS data
    """
    # Load base facilities data
    facilities_2022 = pd.read_csv(f'{data_dir}FACILITIES.csv', encoding='latin1', low_memory=False)[
        ['CWNS_ID', 'FACILITY_NAME', 'STATE_CODE']
    ]
    
    # Load and clean facility permits
    facility_permit = pd.read_csv(f'{data_dir}FACILITY_PERMIT.csv', encoding='latin1', low_memory=False)[['CWNS_ID', 'PERMIT_NUMBER']]
    facility_permit = facility_permit.groupby('CWNS_ID')['PERMIT_NUMBER'].agg(list).reset_index()
    
    # Load county data
    areas_county = pd.read_csv(f'{data_dir}AREAS_COUNTY.csv', encoding='latin1', low_memory=False)
    areas_county = areas_county[areas_county['COUNTY_PRIMARY_FLAG'] == 'Y'][['CWNS_ID', 'COUNTY_NAME']]
    
    # Load facility types
    facility_types = pd.read_csv(f'{data_dir}FACILITY_TYPES.csv', encoding='latin1', low_memory=False)
    facility_types = facility_types.drop('CHANGE_TYPE', axis=1).drop_duplicates()
    
    # Load flow data
    flow = pd.read_csv(f'{data_dir}FLOW.csv', encoding='latin1', low_memory=False)[['CWNS_ID','FLOW_TYPE','CURRENT_DESIGN_FLOW']]
    total_flow = flow[flow['FLOW_TYPE'] == 'Total Flow'][['CWNS_ID', 'CURRENT_DESIGN_FLOW']]
    
    # Load and merge population data
    pop_columns = ['CWNS_ID','TOTAL_RES_POPULATION_2022', 'TOTAL_RES_POPULATION_2042']
    pop_data = {
        'wastewater': pd.read_csv(f'{data_dir}POPULATION_WASTEWATER.csv', encoding='latin1', low_memory=False)[pop_columns],
        'confirmed': pd.read_csv(f'{data_dir}POPULATION_WASTEWATER_CONFIRMED.csv', encoding='latin1', low_memory=False)[pop_columns],
        'decentralized': pd.read_csv(f'{data_dir}POPULATION_DECENTRALIZED.csv', encoding='latin1', low_memory=False)[
            ['CWNS_ID', 'RESIDENTIAL_POP_2022', 'RESIDENTIAL_POP_2042']
        ].rename(columns={
            'RESIDENTIAL_POP_2022': 'TOTAL_RES_POPULATION_2022',
            'RESIDENTIAL_POP_2042': 'TOTAL_RES_POPULATION_2042'
        })[pop_columns]
    }
    
    pop_served_cwns = pd.concat([
        pop_data['confirmed'],
        pop_data['wastewater'],
        pop_data['decentralized']
    ]).drop_duplicates(subset='CWNS_ID', keep='first')
    
    return {
        'facilities': facilities_2022,
        'permits': facility_permit,
        'counties': areas_county,
        'types': facility_types,
        'flow': total_flow,
        'population': pop_served_cwns
    }


def clean_permit_numbers(facilities_df):
    """Clean permit numbers by removing common patterns and standardizing format"""
    patterns_to_remove = [
        r'WDR ', r'WDR-', r'WDR', r'Order WQ ', r'WDR Order No. ',
        r'Order No. ', r'Order ', r'NO. ', r'ORDER NO. ', r'NO.',
        r'ORDER ', r'DWQ- ', r'NO.·', r'. '
    ]
    replacements = {r'·': '-', r'\?': '-'}
    
    df = facilities_df.copy()
    df['PERMIT_NUMBER_cwns_clean'] = df['PERMIT_NUMBER'].astype(str).replace('|'.join(patterns_to_remove), '', regex=True)
    for old, new in replacements.items():
        df['PERMIT_NUMBER_cwns_clean'] = df['PERMIT_NUMBER_cwns_clean'].str.replace(old, new, regex=True)
    return df


def get_facility_type_order():
    """Return dictionary mapping facility types to their processing order"""
    return {
        # Brown collection types
        'Collection: Separate Sewers': 0,
        'Collection: Pump Stations': 0, 
        'Collection: Combined Sewers': 0,
        'Collection: Interceptor Sewers': 1,
        
        # Orange OWTS types
        'Onsite Wastewater Treatment System': 2,
        'Phase II MS4': 2,
        'Phase I MS4': 2,
        'Non-traditional MS4': 2,
        'Sanitary Landfills': 2,
        'Honey Bucket Lagoon': 2,
        
        # Blue treatment types
        'Treatment Plant': 3,
        'Biosolids Handling Facility': 3,
        'Clustered System': 3,
        
        # Grey storage types
        'Storage Tanks': 4,
        'Storage Facility': 4,
        
        # Purple reuse types
        'Water Reuse': 5,
        'Resource Extraction': 5,
        'Desalination - WW': 5,
        
        # Black other types
        'Other': 6
    }


def process_facility_types(facilities_df, discharges_df):
    """
    Process facilities with multiple types and create necessary connections
    
    Args:
        facilities_df: DataFrame containing facility information
        discharges_df: DataFrame containing discharge information
        
    Returns:
        Tuple containing:
        - Updated facilities DataFrame
        - Updated discharges DataFrame
        - List of new facility rows
    """
    treatment_plant_mapping = {}
    reuse_mapping = {}
    collection_mapping = {}
    all_new_facility_rows = []
    
    facility_types_order = get_facility_type_order()
    
    # Add DUMMY_ID column initialized to CWNS_ID if not exists
    if 'DUMMY_ID' not in facilities_df.columns:
        facilities_df['DUMMY_ID'] = copy.deepcopy([str(id) for id in facilities_df['CWNS_ID']])
    
    # Prepare discharges DataFrame
    discharges_df['DISCHARGES_TO_CWNSID'] = pd.to_numeric(discharges_df['DISCHARGES_TO_CWNSID'], errors='coerce').astype('Int64')
    discharges_df['CWNS_ID'] = pd.to_numeric(discharges_df['CWNS_ID'], errors='coerce').astype('Int64')
    discharges_df['DUMMY_ID'] = copy.deepcopy([str(id) for id in discharges_df['CWNS_ID']])
    discharges_df['DISCHARGES_TO_DUMMY_ID'] = copy.deepcopy([str(id) for id in discharges_df['DISCHARGES_TO_CWNSID']])

    # Handle facilities with multiple types
    facilities_processed = 0
    for cwns_id, group in facilities_df.groupby('CWNS_ID'):
        facilities_processed += 1
        if facilities_processed % 5000 == 0:
            print(f"{facilities_processed} out of {len(facilities_df['CWNS_ID'].unique())} facilities processed")
            
        if len(group) > 1:  # if there is more than one facility type
            # Sort facility types by priority, excluding pump stations
            sorted_types = sorted(
                group['FACILITY_TYPE'][group['FACILITY_TYPE'] != 'Collection: Pump Stations'].unique(), 
                key=lambda x: facility_types_order.get(x, 999)
            )
            
            # First create nodes for each facility type
            processed_types = {}
            if len(sorted_types) > 1:
                for t, fac_type in enumerate(sorted_types):
                    new_dummy_id = str(copy.deepcopy(cwns_id)) + 't' + str(t)
                    processed_types[fac_type] = new_dummy_id
                    
                    # Update DUMMY_ID and name for this facility type
                    mask = (facilities_df['CWNS_ID'] == cwns_id) & (facilities_df['FACILITY_TYPE'] == fac_type)
                    facilities_df.loc[mask, 'DUMMY_ID'] = new_dummy_id
                    
                    # Only update name if it doesn't already contain the facility type
                    mask_name = mask & ~facilities_df['FACILITY_NAME'].str.contains(f'({fac_type})', regex=False, na=False)
                    facilities_df.loc[mask_name, 'FACILITY_NAME'] = facilities_df.loc[mask_name, 'FACILITY_NAME'] + ' (' + fac_type +')'
                    
                    # Track IDs if found
                    if fac_type == 'Treatment Plant':
                        treatment_plant_mapping[copy.deepcopy(cwns_id)] = new_dummy_id
                    elif 'reuse' in fac_type.lower() or 'reclaim' in fac_type.lower():
                        reuse_mapping[copy.deepcopy(cwns_id)] = new_dummy_id
                    elif 'collection' in fac_type.lower():
                        collection_mapping[copy.deepcopy(cwns_id)] = new_dummy_id
                
                # Create connections between consecutive types
                for t in range(len(sorted_types)-1):
                    fac_type1 = sorted_types[t]
                    fac_type2 = sorted_types[t+1]
                    
                    # Add connection between the two facility types
                    new_discharge = pd.DataFrame({
                        'CWNS_ID': [copy.deepcopy(cwns_id)],
                        'DUMMY_ID': [processed_types[fac_type1]],
                        'DISCHARGES_TO_CWNSID': [copy.deepcopy(cwns_id)],
                        'DISCHARGES_TO_DUMMY_ID': [processed_types[fac_type2]],
                        'DISCHARGE_TYPE': [f'Internal connection from {fac_type1} to {fac_type2}'],
                        'PRESENT_DISCHARGE_PERCENTAGE': [100]
                    })
                    discharges_df = pd.concat([discharges_df, new_discharge], ignore_index=True)

    # Process final discharges
    for _, facility in facilities_df.iterrows():
        if pd.isna(facility['DUMMY_ID']):
            continue
            
        facility_discharges = discharges_df[discharges_df['DUMMY_ID'] == facility['DUMMY_ID']]
        facility_final_discharges = facility_discharges[facility_discharges['DISCHARGES_TO_CWNSID'].isna()]
        
        # Check if facility has both reuse and treatment plant types
        cwns_id = facility['CWNS_ID']
        facility_types = facilities_df[facilities_df['CWNS_ID'] == cwns_id]['FACILITY_TYPE'].unique()
        has_reuse_and_treatment = ('Treatment Plant' in facility_types) and any('reuse' in ft.lower() for ft in facility_types)
        
        # Process each discharge
        d_count = 0
        for d, discharge in facility_final_discharges.iterrows():
            d_count += 1
            
            # Special handling for facilities with reuse and treatment plant types
            if has_reuse_and_treatment:
                reuse_discharges = facility_final_discharges[
                    facility_final_discharges['DISCHARGE_TYPE'].str.contains('reuse', case=False, na=False)
                ]
                outfall_discharges = facility_final_discharges[
                    facility_final_discharges['DISCHARGE_TYPE'].str.contains('outfall', case=False, na=False)
                ]
                
                if not reuse_discharges.empty and not outfall_discharges.empty:
                    # Handle reuse and outfall types
                    discharge_type_lower = discharge['DISCHARGE_TYPE'].lower()
                    if 'reuse' in discharge_type_lower or 'outfall' in discharge_type_lower:
                        new_DUMMY_ID = facility['DUMMY_ID'] + 'd' + str(d_count)
                        new_facility_row = facility.copy()
                        new_facility_row['DUMMY_ID'] = new_DUMMY_ID
                        
                        # Create descriptive name combining parent facility and discharge type
                        parent_name = facility['FACILITY_NAME']
                        discharge_type = discharge['DISCHARGE_TYPE']
                        new_facility_row['FACILITY_NAME'] = f"{parent_name} - {discharge_type}"
                        
                        if 'reuse' in discharge_type_lower:
                            new_facility_row['FACILITY_TYPE'] = 'Reuse'
                        elif 'outfall' in discharge_type_lower:
                            new_facility_row['FACILITY_TYPE'] = 'Ocean Discharge' if 'Ocean' in discharge['DISCHARGE_TYPE'] else 'Other'
                        
                        new_facility_row['PERMIT_NUMBER'] = None
                        new_facility_row['CURRENT_DESIGN_FLOW'] = None
                        all_new_facility_rows.append(new_facility_row)
                        continue

            # Default handling for other cases
            new_DUMMY_ID = facility['DUMMY_ID'] + 'd' + str(d_count)
            new_facility_row = facility.copy()
            new_facility_row['DUMMY_ID'] = new_DUMMY_ID
            
            # Create descriptive name combining parent facility and discharge type
            parent_name = facility['FACILITY_NAME']
            discharge_type = discharge['DISCHARGE_TYPE']
            new_facility_row['FACILITY_NAME'] = f"{parent_name} - {discharge_type}"
            
            new_facility_row['FACILITY_TYPE'] = 'Reuse' if 'Reuse' in discharge['DISCHARGE_TYPE'] else 'Ocean Discharge' if 'Ocean' in discharge['DISCHARGE_TYPE'] else 'Other'
            new_facility_row['PERMIT_NUMBER'] = None
            new_facility_row['CURRENT_DESIGN_FLOW'] = None
            all_new_facility_rows.append(new_facility_row)
            discharges_df.loc[d, 'DISCHARGES_TO_DUMMY_ID'] = new_DUMMY_ID

    # Update external discharges
    update_external_discharges(
        discharges_df, 
        facilities_df,
        collection_mapping,
        reuse_mapping,
        treatment_plant_mapping
    )

    # Merge county and state information into discharges
    if 'STATE_CODE' in discharges_df.columns:
        discharges_df = discharges_df.drop('STATE_CODE', axis=1)
    
    location_info = facilities_df[['DUMMY_ID', 'COUNTY_NAME', 'STATE_CODE']].drop_duplicates()
    discharges_df = discharges_df.merge(location_info, on='DUMMY_ID', how='left', suffixes=('', '_facilities'))

    return facilities_df, discharges_df, all_new_facility_rows


def build_sewershed_map(facilities_df, discharges_df):
    """
    Build sewershed map from facilities and discharges data
    
    Args:
        facilities_df: DataFrame containing facility information
        discharges_df: DataFrame containing discharge information
        
    Returns:
        Dictionary containing sewershed mapping data
    """
    def add_connection(row: pd.Series) -> List:
        return [row['DUMMY_ID'], row['DISCHARGES_TO_DUMMY_ID'], row['PRESENT_DISCHARGE_PERCENTAGE']]
    
    sewershed_map = {}
    nodes_already_mapped = []

    # Loop through all discharge rows to add connections
    for _, row in discharges_df.iterrows():
        discharge_from_id = row["DUMMY_ID"]
        discharges_to = row["DISCHARGES_TO_DUMMY_ID"]

        # Skip if either ID is NA
        if pd.isna(discharge_from_id) or pd.isna(discharges_to):
            continue

        if (discharge_from_id not in nodes_already_mapped and discharges_to not in nodes_already_mapped): 
            # Create new sewershed
            new_sewershed_id = len(sewershed_map) + 1
            sewershed_map[new_sewershed_id] = {
                "nodes": set([discharge_from_id, discharges_to]),
                "connections": [add_connection(row)],
            }
            nodes_already_mapped.extend([discharge_from_id, discharges_to])
        else: 
            # Add to existing sewershed
            for sewershed_info in sewershed_map.values():
                if (discharge_from_id in sewershed_info["nodes"] or discharges_to in sewershed_info["nodes"]):
                    sewershed_info["nodes"].update([discharge_from_id, discharges_to])
                    sewershed_info["connections"].append(add_connection(row))
                    nodes_already_mapped.extend([discharge_from_id, discharges_to])
                    break

    # Consolidate sewersheds with redundant nodes
    print(f'{len(sewershed_map)} sewersheds before combining sewersheds w/ repetitive nodes')
    DUMMY_IDS = list(sewershed_map.keys())
    for i in range(len(DUMMY_IDS)):
        for j in range(i + 1, len(DUMMY_IDS)):
            id1, id2 = DUMMY_IDS[i], DUMMY_IDS[j]
            if id1 in sewershed_map and id2 in sewershed_map:
                if sewershed_map[id1]["nodes"] & sewershed_map[id2]["nodes"]:
                    # Merge sewersheds
                    sewershed_map[id1]["nodes"].update(sewershed_map[id2]["nodes"])
                    sewershed_map[id1]["connections"].extend(sewershed_map[id2]["connections"])
                    del sewershed_map[id2]
    print(f'{len(sewershed_map)} sewersheds after combining sewersheds w/ repetitive nodes')

    # Add state and county information
    new_sewershed_map = {}
    state_county_used = {}
    for sewershed_id, sewershed_info in sewershed_map.items():
        # Get location info for nodes
        node_info = []
        for node in sewershed_info["nodes"]:
            node_data = discharges_df[discharges_df['DUMMY_ID'] == node][['STATE_CODE', 'COUNTY_NAME']]
            if not node_data.empty:
                node_info.append(node_data.iloc[0].to_dict())
        
        # Get primary state and county
        if len(node_info) > 0:
            node_info_df = pd.DataFrame(node_info)
            state_counts = node_info_df["STATE_CODE"].value_counts()
            primary_state = state_counts.index[0] if len(state_counts) > 0 else "Unspecified"
            county_counts = node_info_df[node_info_df["STATE_CODE"] == primary_state]["COUNTY_NAME"].value_counts()
            primary_county = county_counts.index[0] if len(county_counts) > 0 else "Unspecified"
        else:
            primary_state = "Unspecified"
            primary_county = "Unspecified"
        
        # Create new sewershed name
        state_county_key = f"{primary_state}_{primary_county}"
        state_county_used[state_county_key] = state_county_used.get(state_county_key, 0) + 1
        new_name = f"{primary_state} - {primary_county} County Sewershed {state_county_used[state_county_key]}"
        
        # Add node data
        node_data = {}
        for node in sewershed_info["nodes"]:
            node_data[node] = {}
            facility_mask = facilities_df['DUMMY_ID'] == node
            if not facilities_df[facility_mask].empty:
                facility = facilities_df[facility_mask].iloc[0]
                for key in ['CURRENT_DESIGN_FLOW', 'TOTAL_RES_POPULATION_2022', 'PERMIT_NUMBER', 
                           'CWNS_ID', 'DUMMY_ID', 'FACILITY_NAME', 'FACILITY_TYPE']:
                    node_data[node][key] = facility[key]
                node_data[node]['color'] = get_node_color(facility['FACILITY_TYPE'], facility['FACILITY_NAME'])
            else:
                for key in ['CURRENT_DESIGN_FLOW', 'TOTAL_RES_POPULATION_2022', 'PERMIT_NUMBER', 
                           'CWNS_ID', 'DUMMY_ID', 'FACILITY_NAME', 'FACILITY_TYPE']:
                    node_data[node][key] = None
                node_data[node]['color'] = DEFAULT_NODE_COLOR
        
        sewershed_info["node_data"] = node_data
        new_sewershed_map[new_name] = sewershed_info
    sewershed_map = new_sewershed_map
    
    return sewershed_map


def update_external_discharges(discharges_df, facilities_df, collection_mapping, reuse_mapping, treatment_plant_mapping):
    """
    Update external discharges involving facilities with multiple types
    
    Args:
        discharges_df: DataFrame containing discharge information
        facilities_df: DataFrame containing facility information
        collection_mapping: Dictionary mapping collection facility IDs
        reuse_mapping: Dictionary mapping reuse facility IDs
        treatment_plant_mapping: Dictionary mapping treatment plant IDs
    """
    external_connection_mask = discharges_df['CWNS_ID'] != discharges_df['DISCHARGES_TO_CWNSID']
    for index, row in discharges_df[external_connection_mask].iterrows():
        cwns_id = copy.deepcopy(row['CWNS_ID'])
        discharge_to_id = copy.deepcopy(row['DISCHARGES_TO_CWNSID'])
        
        # Update source DUMMY_ID based on different cases
        
        # Case 1: Collection systems discharging to facility
        if (discharge_to_id in collection_mapping.keys() and 
            'collection' in facilities_df[facilities_df['CWNS_ID'] == cwns_id]['FACILITY_TYPE'].iloc[0].lower()):
            discharges_df.loc[index, 'DISCHARGES_TO_DUMMY_ID'] = collection_mapping[discharge_to_id]
        
        # Case 2: Facility discharging to reuse end-uses
        elif (cwns_id in reuse_mapping.keys() and 
              any(term in row['DISCHARGE_TYPE'].lower() for term in ['reuse', 'reclaim', 'recycle', 'pure'])):
            discharges_df.loc[index, 'DUMMY_ID'] = reuse_mapping[cwns_id]
        
        # Case 3: Facilities discharging to a separate pure water facility
        elif (cwns_id in reuse_mapping.keys() and 
              len(facilities_df[facilities_df['DUMMY_ID'] == row['DISCHARGES_TO_DUMMY_ID']]) > 0 and 
              any(term in facilities_df[facilities_df['DUMMY_ID'] == row['DISCHARGES_TO_DUMMY_ID']]['FACILITY_NAME'].iloc[0].lower() 
                  for term in ['reuse', 'pure'])):
            discharges_df.loc[index, 'DUMMY_ID'] = reuse_mapping[cwns_id]
        
        # Case 4: Facility discharging to another treatment plant, direct from the interceptor
        elif cwns_id in collection_mapping.keys():
            discharge_to_facilities = facilities_df[facilities_df['CWNS_ID'] == discharge_to_id]
            if not discharge_to_facilities.empty and discharge_to_facilities['FACILITY_TYPE'].iloc[0] == 'Treatment Plant':
                discharges_df.loc[index, 'DUMMY_ID'] = collection_mapping[cwns_id]
        
        # Case 5: Discharge to treatment plant
        elif discharge_to_id in treatment_plant_mapping.keys():
            discharges_df.loc[index, 'DISCHARGES_TO_DUMMY_ID'] = treatment_plant_mapping[discharge_to_id]
        
        # Case 6: Discharge from treatment plant
        elif cwns_id in treatment_plant_mapping.keys():
            discharges_df.loc[index, 'DUMMY_ID'] = treatment_plant_mapping[cwns_id]


def load_and_merge_cwns_data(data_dir = 'data/2022CWNS_NATIONAL_APR2024/', state = None):
    """
    Load and merge CWNS data for a specific state or all states.
    
    Args:
        data_dir: Directory containing CWNS data files
        state: Optional state code to filter data (e.g., 'CA' for California)
        
    Returns:
        DataFrame containing merged CWNS facilities data with all related information
    """
    # Load data
    data_dict = load_cwns_data(data_dir)
    facilities = data_dict['facilities']
    
    # Filter by state if specified
    if state:
        facilities = facilities[facilities['STATE_CODE'] == state]
    
    # Define which columns to keep from each dataframe
    merge_columns = {
        'permits': ['CWNS_ID', 'PERMIT_NUMBER'],
        'counties': ['CWNS_ID', 'COUNTY_NAME'],
        'types': ['CWNS_ID', 'FACILITY_TYPE'],
        'flow': ['CWNS_ID', 'CURRENT_DESIGN_FLOW'],
        'population': ['CWNS_ID', 'TOTAL_RES_POPULATION_2022', 'TOTAL_RES_POPULATION_2042']
    }
    
    # Merge all dataframes
    for df_name, columns in merge_columns.items():
        df = data_dict[df_name][columns]
        facilities = facilities.merge(df, on='CWNS_ID', how='left')
    
    # Clean permit numbers
    facilities = clean_permit_numbers(facilities)
    
    return facilities


def main(data_dir = 'data/2022CWNS_NATIONAL_APR2024/', 
         output_dir = 'processed_data/',
         state = None):
    """
    Main function to process CWNS data and create sewershed map
    
    Args:
        data_dir: Directory containing input CWNS data files
        output_dir: Directory for output files
        state: Optional state code to filter data (e.g., 'CA' for California)
    """
    # Load and merge CWNS data
    print("Loading and merging CWNS data...")
    facilities_2022 = load_and_merge_cwns_data(data_dir, state)
    
    if state:
        print(f"Found {len(facilities_2022)} facilities in {state}")
    
    # Load and process discharges
    print("Loading discharge data...")
    discharges = pd.read_csv(f'{data_dir}DISCHARGES.csv', encoding='latin1', low_memory=False)
    
    # Filter discharges by state if specified
    if state:
        state_facilities = set(facilities_2022['CWNS_ID'].unique())
        discharges = discharges[
            (discharges['CWNS_ID'].isin(state_facilities)) | 
            (discharges['DISCHARGES_TO_CWNSID'].isin(state_facilities))
        ]
        print(f"Found {len(discharges)} discharge connections involving {state} facilities")
    
    # Process facility types and build sewershed map
    facilities_2022, discharges, new_rows = process_facility_types(facilities_2022, discharges)
    
    print("Building sewershed map...")
    sewershed_map = build_sewershed_map(facilities_2022, discharges)
    
    # Save outputs
    print("Saving outputs...")
    output_prefix = f"{state}_" if state else ""
    
    output_columns = [
        'CWNS_ID', 'DUMMY_ID', 'FACILITY_NAME', 'PERMIT_NUMBER',
        'TOTAL_RES_POPULATION_2022', 'FACILITY_TYPE', 'CURRENT_DESIGN_FLOW',
        'COUNTY_NAME', 'STATE_CODE'
    ]
    
    facilities_2022[output_columns].to_csv(
        f'{output_dir}{output_prefix}facilities_2022_merged.csv', 
        index=False
    )
    
    with open(f'{output_dir}{output_prefix}sewershed_map.pkl', 'wb') as f:
        pickle.dump(sewershed_map, f)

if __name__ == "__main__":
    # main(state = "CA")
    main()