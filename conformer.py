import os
import time
import threading
from rdkit import Chem
from rdkit.Chem import AllChem

# ----------------------------
# Paths
# ----------------------------
input_folder = r"C:\Users\User\Desktop\Conformers\converted_pdb"
output_pdb_folder = os.path.join(input_folder, "conformers_pdb")
output_pdbqt_folder = os.path.join(input_folder, "conformers_pdbqt")

os.makedirs(output_pdb_folder, exist_ok=True)
os.makedirs(output_pdbqt_folder, exist_ok=True)

num_confs = 100
prune_rms_thresh = 0.5  # Å

# ----------------------------
# Function to write PDBQT via OpenBabel
# ----------------------------
def write_pdbqt(input_pdb, output_pdbqt):
    cmd = f'obabel "{input_pdb}" -O "{output_pdbqt}"'
    os.system(cmd)

# ----------------------------
# Process one ligand
# ----------------------------
def process_ligand(ligand_file):
    try:
        base = os.path.splitext(os.path.basename(ligand_file))[0]
        print(f"Processing {base}...")

        mol = Chem.MolFromPDBFile(ligand_file, removeHs=False)
        if mol is None:
            print(f"Skipping {base}, RDKit could not read molecule.")
            return

        mol = Chem.AddHs(mol)
        params = AllChem.ETKDGv3()
        params.pruneRmsThresh = prune_rms_thresh

        conf_ids = AllChem.EmbedMultipleConfs(mol, numConfs=num_confs, params=params)
        if len(conf_ids) == 0:
            print(f"No conformers generated for {base}.")
            return

        # Generate PDB and PDBQT for each conformer
        for idx, cid in enumerate(conf_ids, start=1):
            AllChem.UFFOptimizeMolecule(mol, confId=cid)

            pdb_file = os.path.join(output_pdb_folder, f"{base}_conf_{idx}.pdb")
            pdbqt_file = os.path.join(output_pdbqt_folder, f"{base}_conf_{idx}.pdbqt")

            # Write PDB
            writer = Chem.PDBWriter(pdb_file)
            writer.write(mol, confId=cid)
            writer.close()

            # Convert to PDBQT
            write_pdbqt(pdb_file, pdbqt_file)

        print(f"Finished {base}, {len(conf_ids)} conformers written.")

    except Exception as e:
        print(f"Error processing {ligand_file}: {e}")

# ----------------------------
# Main loop
# ----------------------------
def process_all():
    ligands = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith(".pdb")]
    total = len(ligands)
    print(f"Found {total} ligands to process.")

    for i, ligand in enumerate(ligands, start=1):
        print(f"\nLigand {i}/{total}: {os.path.basename(ligand)}")
        thread = threading.Thread(target=process_ligand, args=(ligand,))
        thread.start()
        thread.join(timeout=600)  # 10 min timeout per ligand
        if thread.is_alive():
            print(f"Timeout reached for {ligand}, skipping.")
            continue

    print("All ligands processed.")

# ----------------------------
# Run script
# ----------------------------
if __name__ == "__main__":
    start = time.time()
    process_all()
    print(f"Total runtime: {(time.time()-start)/60:.1f} min")
