import pandas as pd
import json
import os
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_csv_to_json():
    try:
        # Get the source and destination directories
        script_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(script_dir)
        source_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))), 'data')  # Where the CSV files are
        dest_data_dir = os.path.join(backend_dir, 'data')  # Where to save JSON files
        
        # Create destination directory if it doesn't exist
        os.makedirs(dest_data_dir, exist_ok=True)
        
        logger.info(f"Source data directory: {source_data_dir}")
        logger.info(f"Destination data directory: {dest_data_dir}")
        logger.info(f"Source directory contents: {os.listdir(source_data_dir)}")

        # Find all participants CSV files
        participants_files = [f for f in os.listdir(source_data_dir) if f.startswith('participants_') and f.endswith('.csv')]
        participants_files.sort()  # Sort to process oldest first
        
        logger.info(f"Found participants files: {participants_files}")
        
        # Group by name to count spaces and determine roles
        participant_stats = defaultdict(lambda: {
            'spaces': 0,
            'roles': set(),
            'twitter': '',
            'host_spaces': 0,
            'speaker_spaces': 0,
            'space_urls': set()  # Track unique spaces
        })
        
        # Process each participants file
        for participants_file in participants_files:
            logger.info(f"Processing {participants_file}...")
            participants_df = pd.read_csv(os.path.join(source_data_dir, participants_file))
            
            for _, row in participants_df.iterrows():
                name = row['name']
                role = row['role'].lower()  # Convert to lowercase
                if role == 'speakers':  # Fix plural form
                    role = 'speaker'
                
                # Only count unique spaces
                if row['space_url'] not in participant_stats[name]['space_urls']:
                    participant_stats[name]['spaces'] += 1
                    participant_stats[name]['space_urls'].add(row['space_url'])
                
                participant_stats[name]['roles'].add(role)
                
                # Count spaces by role
                if role == 'host':
                    participant_stats[name]['host_spaces'] += 1
                elif role == 'speaker':
                    participant_stats[name]['speaker_spaces'] += 1
                
                if pd.notna(row['twitter_link']):
                    participant_stats[name]['twitter'] = row['twitter_link']
        
        # Transform to final format
        participants_data = []
        name_to_id = {}
        for idx, (name, stats) in enumerate(participant_stats.items(), start=1):
            # Determine role
            roles = stats['roles']
            if len(roles) > 1:
                role = 'both'
            else:
                role = list(roles)[0]
            
            participant = {
                'id': str(idx),  # Generate sequential IDs
                'name': name,
                'role': role,
                'spaces': stats['spaces'],
                'host_spaces': stats['host_spaces'],
                'speaker_spaces': stats['speaker_spaces'],
                'twitter': stats['twitter']
            }
            participants_data.append(participant)
            name_to_id[name] = str(idx)
        
        logger.info(f"Processed {len(participants_data)} unique participants")
        
        # Save participants data
        with open(os.path.join(dest_data_dir, 'participants_data.json'), 'w') as f:
            json.dump(participants_data, f, indent=2)
        logger.info("Saved participants data to JSON")

        # Build network data from all participants
        logger.info("Building network data...")
        network_data = {
            'nodes': participants_data,
            'links': []
        }
        
        # Create links between participants in the same space
        space_participants = defaultdict(set)
        for participants_file in participants_files:
            participants_df = pd.read_csv(os.path.join(source_data_dir, participants_file))
            for _, row in participants_df.iterrows():
                space_participants[row['space_url']].add(row['name'])
        
        for space, participants in space_participants.items():
            participants = list(participants)
            for i in range(len(participants)):
                for j in range(i + 1, len(participants)):
                    link = {
                        'source': name_to_id[participants[i]],
                        'target': name_to_id[participants[j]],
                        'value': 1
                    }
                    network_data['links'].append(link)
        
        logger.info(f"Processed {len(network_data['nodes'])} nodes and {len(network_data['links'])} links")
        
        # Save network data
        with open(os.path.join(dest_data_dir, 'network_data.json'), 'w') as f:
            json.dump(network_data, f, indent=2)
        logger.info("Saved network data to JSON")
        
        return True
    except Exception as e:
        logger.error(f"Error converting CSV to JSON: {str(e)}")
        logger.error(f"Current directory: {os.getcwd()}")
        logger.error(f"Directory contents: {os.listdir('.')}")
        return False

if __name__ == '__main__':
    success = convert_csv_to_json()
    if not success:
        exit(1) 