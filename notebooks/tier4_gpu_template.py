# Databricks notebook source
# MAGIC %md
# MAGIC # Biomni Tier 4: GPU Tool Execution
# MAGIC
# MAGIC This notebook is called by the Biomni MCP server to execute
# MAGIC GPU-accelerated tools on a Container Services cluster.

# COMMAND ----------

# Parameters (set by notebook task base_parameters)
dbutils.widgets.text("tool", "")
dbutils.widgets.text("image_path", "")
dbutils.widgets.text("task_id", "")
dbutils.widgets.text("model_type", "")
dbutils.widgets.text("protein_pdb_path", "")
dbutils.widgets.text("ligand_smiles", "")
dbutils.widgets.text("num_poses", "10")
dbutils.widgets.text("diameter", "0.0")
dbutils.widgets.text("receptor_pdbqt", "")
dbutils.widgets.text("ligand_pdbqt", "")
dbutils.widgets.text("center_x", "0.0")
dbutils.widgets.text("center_y", "0.0")
dbutils.widgets.text("center_z", "0.0")
dbutils.widgets.text("size_x", "20.0")
dbutils.widgets.text("size_y", "20.0")
dbutils.widgets.text("size_z", "20.0")
dbutils.widgets.text("exhaustiveness", "8")
dbutils.widgets.text("receptor_pdb", "")
dbutils.widgets.text("output_dir", "")

tool = dbutils.widgets.get("tool")
output_dir = dbutils.widgets.get("output_dir")

# COMMAND ----------

import json
import os
import subprocess

os.makedirs(output_dir, exist_ok=True)

# COMMAND ----------

def run_nnunet_segment(image_path, task_id, model_type, output_dir):
    """Segment medical images using nnUNet."""
    env = os.environ.copy()
    env["nnUNet_results"] = "/Volumes/bioinformatics/tools/reference_data/models/nnunet"
    cmd = [
        "nnUNetv2_predict",
        "-i", image_path,
        "-o", output_dir,
        "-d", task_id,
        "-c", model_type,
        "--disable_tta",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True,
                            timeout=7200, env=env)
    return f"nnUNet segmentation complete.\n{result.stdout}\nOutput: {output_dir}"


def run_diffdock_predict(protein_pdb_path, ligand_smiles, num_poses, output_dir):
    """Predict protein-ligand binding poses using DiffDock."""
    # Write input CSV for DiffDock
    input_csv = os.path.join(output_dir, "input.csv")
    with open(input_csv, "w") as f:
        f.write("complex_name,protein_path,ligand_description,protein_sequence\n")
        f.write(f"complex_0,{protein_pdb_path},{ligand_smiles},\n")

    cmd = [
        "python", "-m", "inference",
        "--config", "default_inference_args.yaml",
        "--protein_ligand_csv", input_csv,
        "--out_dir", output_dir,
        "--samples_per_complex", str(num_poses),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True,
                            timeout=3600)
    return f"DiffDock prediction complete.\n{result.stdout}\nOutput: {output_dir}"


def run_cellpose_segment(image_path, model_type, diameter, output_dir):
    """Segment cells using Cellpose."""
    from cellpose import models, io

    model = models.Cellpose(model_type=model_type, gpu=True)
    imgs = io.imread(image_path)
    diam = float(diameter) if float(diameter) > 0 else None
    masks, flows, styles, diams = model.eval(
        imgs, diameter=diam, channels=[0, 0]
    )
    out_path = os.path.join(output_dir, "masks.tif")
    io.imsave(out_path, masks)
    return f"Cellpose segmentation complete.\nCells detected: {masks.max()}\nOutput: {out_path}"


def run_autodock_vina(receptor_pdbqt, ligand_pdbqt, center_x, center_y,
                      center_z, size_x, size_y, size_z, exhaustiveness,
                      output_dir):
    """Perform molecular docking using AutoDock Vina."""
    output_pdbqt = os.path.join(output_dir, "docked.pdbqt")
    log_file = os.path.join(output_dir, "vina.log")
    cmd = [
        "vina",
        "--receptor", receptor_pdbqt,
        "--ligand", ligand_pdbqt,
        "--center_x", str(center_x),
        "--center_y", str(center_y),
        "--center_z", str(center_z),
        "--size_x", str(size_x),
        "--size_y", str(size_y),
        "--size_z", str(size_z),
        "--exhaustiveness", str(exhaustiveness),
        "--out", output_pdbqt,
        "--log", log_file,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True,
                            timeout=3600)
    return f"AutoDock Vina docking complete.\n{result.stdout}\nOutput: {output_pdbqt}"


def run_autosite_predict(receptor_pdb, output_dir):
    """Identify binding sites using AutoSite."""
    cmd = [
        "autosite",
        "-r", receptor_pdb,
        "-o", output_dir,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True,
                            timeout=1800)
    return f"AutoSite prediction complete.\n{result.stdout}\nOutput: {output_dir}"

# COMMAND ----------

GPU_TOOLS = {
    "nnunet_segment": run_nnunet_segment,
    "diffdock_predict": run_diffdock_predict,
    "cellpose_segment": run_cellpose_segment,
    "autodock_vina": run_autodock_vina,
    "autosite_predict": run_autosite_predict,
}

# Collect parameters from widgets
widget_names = [
    "image_path", "task_id", "model_type",
    "protein_pdb_path", "ligand_smiles", "num_poses", "diameter",
    "receptor_pdbqt", "ligand_pdbqt",
    "center_x", "center_y", "center_z",
    "size_x", "size_y", "size_z", "exhaustiveness",
    "receptor_pdb", "output_dir",
]
params = {k: dbutils.widgets.get(k) for k in widget_names if dbutils.widgets.get(k)}

tool_fn = GPU_TOOLS[tool]
result = tool_fn(**params)
print(result)

# COMMAND ----------

dbutils.notebook.exit(json.dumps({"status": "success", "output_dir": output_dir, "message": result}))
