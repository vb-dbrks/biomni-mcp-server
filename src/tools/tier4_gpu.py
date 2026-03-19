"""Tier 4 — GPU tools consolidated into two MCP tools."""

from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP

from src.config import config
from src.job_runner import submit_notebook_job

NOTEBOOK_PATH = "/Workspace/biomni-tools/notebooks/tier4_gpu_template"


def _job_msg(tool_name: str, run_id: str) -> str:
    return (
        f"## {tool_name}\n\n"
        f"Job submitted (Run ID: **{run_id}**).\n\n"
        f"Use `manage_jobs(action='status', run_id='{run_id}')` to monitor."
    )


def register(mcp: FastMCP, workspace_client: WorkspaceClient) -> None:
    cluster_id = config.gpu_cluster_id

    @mcp.tool()
    async def run_medical_imaging(
        tool: str,
        image_path: str,
        output_volume_path: str = f"{config.volume_base}/imaging_output",
        task_id: str = "",
        model_type: str = "",
        diameter: float = 0.0,
    ) -> str:
        """Segment medical or microscopy images on GPU using nnUNet or Cellpose.

        Args:
            tool: 'nnunet' for medical image segmentation or 'cellpose' for cell segmentation.
            image_path: Path to image file in a Volume (NIfTI for nnunet, TIFF/PNG for cellpose).
            output_volume_path: Volume directory for segmentation output.
            task_id: nnUNet task ID (e.g. 'Task001_BrainTumour'). Required for nnunet.
            model_type: For nnunet: 2d, 3d_fullres, 3d_lowres. For cellpose: cyto, cyto2, nuclei.
            diameter: Expected cell diameter in pixels for cellpose (0 = auto).
        """
        if tool == "nnunet":
            if not task_id:
                return "**Error:** nnUNet requires a `task_id`."
            run_id = await submit_notebook_job(
                workspace_client, notebook_path=NOTEBOOK_PATH,
                parameters={
                    "tool": "nnunet_segment",
                    "image_path": image_path, "task_id": task_id,
                    "model_type": model_type or "3d_fullres",
                    "output_dir": output_volume_path,
                },
                cluster_id=cluster_id,
            )
            return _job_msg("nnUNet Segmentation (GPU)", run_id)

        elif tool == "cellpose":
            run_id = await submit_notebook_job(
                workspace_client, notebook_path=NOTEBOOK_PATH,
                parameters={
                    "tool": "cellpose_segment",
                    "image_path": image_path,
                    "model_type": model_type or "cyto2",
                    "diameter": str(diameter),
                    "output_dir": output_volume_path,
                },
                cluster_id=cluster_id,
            )
            return _job_msg("Cellpose Cell Segmentation (GPU)", run_id)

        else:
            return f"**Error:** Unknown tool `{tool}`. Use 'nnunet' or 'cellpose'."

    @mcp.tool()
    async def run_molecular_docking(
        tool: str,
        receptor_path: str,
        output_volume_path: str = f"{config.volume_base}/docking_output",
        ligand_smiles: str = "",
        ligand_pdbqt: str = "",
        num_poses: int = 10,
        center_x: float = 0.0,
        center_y: float = 0.0,
        center_z: float = 0.0,
        size_x: float = 20.0,
        size_y: float = 20.0,
        size_z: float = 20.0,
        exhaustiveness: int = 8,
    ) -> str:
        """Run molecular docking or binding site prediction on GPU.

        Args:
            tool: 'diffdock' (ML docking), 'vina' (AutoDock Vina), or 'autosite' (binding site prediction).
            receptor_path: Path to receptor file in a Volume (PDB for diffdock/autosite, PDBQT for vina).
            output_volume_path: Volume directory for docking results.
            ligand_smiles: SMILES string of ligand (required for diffdock).
            ligand_pdbqt: Path to ligand PDBQT file (required for vina).
            num_poses: Number of binding poses for diffdock (default 10).
            center_x: Search box center X for vina.
            center_y: Search box center Y for vina.
            center_z: Search box center Z for vina.
            size_x: Search box size X for vina (Angstroms).
            size_y: Search box size Y for vina (Angstroms).
            size_z: Search box size Z for vina (Angstroms).
            exhaustiveness: Search exhaustiveness for vina (default 8).
        """
        if tool == "diffdock":
            if not ligand_smiles:
                return "**Error:** DiffDock requires `ligand_smiles`."
            run_id = await submit_notebook_job(
                workspace_client, notebook_path=NOTEBOOK_PATH,
                parameters={
                    "tool": "diffdock_predict",
                    "protein_pdb_path": receptor_path,
                    "ligand_smiles": ligand_smiles,
                    "num_poses": str(num_poses),
                    "output_dir": output_volume_path,
                },
                cluster_id=cluster_id,
            )
            return _job_msg("DiffDock Binding Prediction (GPU)", run_id)

        elif tool == "vina":
            if not ligand_pdbqt:
                return "**Error:** AutoDock Vina requires `ligand_pdbqt`."
            run_id = await submit_notebook_job(
                workspace_client, notebook_path=NOTEBOOK_PATH,
                parameters={
                    "tool": "autodock_vina",
                    "receptor_pdbqt": receptor_path,
                    "ligand_pdbqt": ligand_pdbqt,
                    "center_x": str(center_x), "center_y": str(center_y),
                    "center_z": str(center_z),
                    "size_x": str(size_x), "size_y": str(size_y),
                    "size_z": str(size_z),
                    "exhaustiveness": str(exhaustiveness),
                    "output_dir": output_volume_path,
                },
                cluster_id=cluster_id,
            )
            return _job_msg("AutoDock Vina Docking (GPU)", run_id)

        elif tool == "autosite":
            run_id = await submit_notebook_job(
                workspace_client, notebook_path=NOTEBOOK_PATH,
                parameters={
                    "tool": "autosite_predict",
                    "receptor_pdb": receptor_path,
                    "output_dir": output_volume_path,
                },
                cluster_id=cluster_id,
            )
            return _job_msg("AutoSite Binding Site Prediction (GPU)", run_id)

        else:
            return f"**Error:** Unknown tool `{tool}`. Use 'diffdock', 'vina', or 'autosite'."
