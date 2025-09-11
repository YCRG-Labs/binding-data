#!/usr/bin/env python3
"""
Script to process AutoDock Vina log files into a consolidated CSV file.

This script reads all log files from binding-data/raw/ directory and extracts
docking results into a single CSV file with the following columns:
- ligand: ligand name extracted from the log file
- mode: docking mode number
- affinity: binding affinity in kcal/mol
- dist_from_rmsd_lb: distance from best mode (RMSD lower bound)
- best_mode_rmsd_ub: RMSD upper bound

Output is saved to binding-data/processed/processed_logs.csv
"""

import os
import re
import csv
from pathlib import Path

def extract_ligand_name(file_path):
    """Extract ligand name from the log file header."""
    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line_num == 22 and 'Ligand:' in line:
                    # Extract ligand name from line like "Ligand: Circumin.pdbqt"
                    ligand_match = re.search(r'Ligand:\s*(.+)\.pdbqt', line)
                    if ligand_match:
                        return ligand_match.group(1).strip()
                    break
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None
    return None

def process_log_file(file_path):
    """Process a single log file and extract docking results."""
    ligand_name = extract_ligand_name(file_path)
    if not ligand_name:
        print(f"Could not extract ligand name from {file_path}")
        return []
    
    results = []
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        # Find the start of the data table (after the header)
        data_start = None
        for i, line in enumerate(lines):
            if 'mode |   affinity | dist from best mode' in line:
                data_start = i + 2  # Skip the separator line
                break
        
        if data_start is None:
            print(f"Could not find data table in {file_path}")
            return []
        
        # Process each data line
        for i in range(data_start, len(lines)):
            line = lines[i].strip()
            if not line or line.startswith('-----'):
                continue
            
            # Parse the line: mode, affinity, rmsd_lb, rmsd_ub
            # Format: "   1       -6.314          0          0"
            parts = line.split()
            if len(parts) >= 4:
                try:
                    mode = int(parts[0])
                    affinity = float(parts[1])
                    dist_from_rmsd_lb = float(parts[2])
                    best_mode_rmsd_ub = float(parts[3])
                    
                    results.append({
                        'ligand': ligand_name,
                        'mode': mode,
                        'affinity': affinity,
                        'dist_from_rmsd_lb': dist_from_rmsd_lb,
                        'best_mode_rmsd_ub': best_mode_rmsd_ub
                    })
                except (ValueError, IndexError) as e:
                    print(f"Error parsing line {i+1} in {file_path}: {line}")
                    continue
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []
    
    return results

def main():
    """Main function to process all log files and create CSV output."""
    # Define paths
    raw_dir = Path("binding-data/raw/logs")
    output_file = Path("binding-data/processed/processed_logs.csv")
    
    # Check if raw directory exists
    if not raw_dir.exists():
        print(f"Error: {raw_dir} directory not found")
        return
    
    # Find all log files
    log_files = list(raw_dir.glob("*.txt"))
    if not log_files:
        print(f"No .txt files found in {raw_dir}")
        return
    
    print(f"Found {len(log_files)} log files to process:")
    for log_file in log_files:
        print(f"  - {log_file.name}")
    
    # Process all log files
    all_results = []
    for log_file in log_files:
        print(f"Processing {log_file.name}...")
        results = process_log_file(log_file)
        all_results.extend(results)
        print(f"  Extracted {len(results)} docking results")
    
    # Write results to CSV
    if all_results:
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['ligand', 'mode', 'affinity', 'dist_from_rmsd_lb', 'best_mode_rmsd_ub']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(all_results)
        
        print(f"\nSuccessfully processed {len(all_results)} total docking results")
        print(f"Output saved to: {output_file}")
        
        # Print summary statistics
        ligands = set(result['ligand'] for result in all_results)
        print(f"\nSummary:")
        print(f"  - Total ligands: {len(ligands)}")
        print(f"  - Total docking modes: {len(all_results)}")
        print(f"  - Ligands processed: {', '.join(sorted(ligands))}")
        
    else:
        print("No results to write")

if __name__ == "__main__":
    main()
