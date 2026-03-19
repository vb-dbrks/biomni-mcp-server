"""Tier 4 tools — GPU workloads via Container Services cluster."""

from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP

from src.config import config
from src.job_runner import submit_notebook_job

NOTEBOOK_PATH = "/Workspace/biomni-tools/notebooks/tier4_gpu_template"


def _job_submitted_msg(tool_name: str, run_id: str) -> str:
    return (
        f"## {tool_name}\n\n"
        f"Job submitted (Run ID: **{run_id}**).\n\n"
        f"Use `check_job_status('{run_id}')` to monitor progress."
    )


def register(mcp: FastMCP, workspace_client: WorkspaceClient) -> None:
    cluster_id = config.gpu_cluster_id

    # ── nnUNet ─────────────────────────────────────────────────────────

    @mcp.tool()
    async def segment_with_nn_unet(
        image_path: str,
        task_id: str,
        model_type: str = "3d_fullres",
        output_volume_path: str = f"{config.volume_base}/nnunet_output",
    ) -> str:
        """Segment medical images using nnUNet on GPU cluster.

        Args:
            image_path: Path to NIfTI image file in a Volume.
            task_id: nnUNet task ID (e.g. 'Task001_BrainTumour').
            model_type: Model configuration — 2d, 3d_fullres, 3d_lowres, 3d_cascade_fullres.
            output_volume_path: Volume directory for segmentation output.
        """
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "nnunet_segment",
                "image_path": image_path,
                "task_id": task_id,
                "model_type": model_type,
                "output_dir": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg("nnUNet Segmentation (GPU)", run_id)

    # ── DiffDock ───────────────────────────────────────────────────────

    @mcp.tool()
    async def run_diffdock_with_smiles(
        protein_pdb_path: str,
        ligand_smiles: str,
        num_poses: int = 10,
        output_volume_path: str = f"{config.volume_base}/diffdock_output",
    ) -> str:
        """Predict protein-ligand binding poses using DiffDock on GPU.

        Args:
            protein_pdb_path: Path to protein PDB file in a Volume.
            ligand_smiles: SMILES string of the ligand molecule.
            num_poses: Number of binding poses to generate (default 10).
            output_volume_path: Volume directory for docking results.
        """
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "diffdock_predict",
                "protein_pdb_path": protein_pdb_path,
                "ligand_smiles": ligand_smiles,
                "num_poses": str(num_poses),
                "output_dir": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg("DiffDock Binding Prediction (GPU)", run_id)

    # ── Cellpose ───────────────────────────────────────────────────────

    @mcp.tool()
    async def segment_cells_with_deep_learning(
        image_path: str,
        model_type: str = "cyto2",
        diameter: float = 0.0,
        output_volume_path: str = f"{config.volume_base}/cellpose_output",
    ) -> str:
        """Segment cells in microscopy images using Cellpose on GPU.

        Args:
            image_path: Path to microscopy image file in a Volume (TIFF, PNG, etc.).
            model_type: Cellpose model — cyto, cyto2, nuclei, etc.
            diameter: Expected cell diameter in pixels (0 = auto-estimate).
            output_volume_path: Volume directory for segmentation masks.
        """
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "cellpose_segment",
                "image_path": image_path,
                "model_type": model_type,
                "diameter": str(diameter),
                "output_dir": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg("Cellpose Cell Segmentation (GPU)", run_id)

    # ── AutoDock Vina + AutoSite ───────────────────────────────────────

    @mcp.tool()
    async def docking_autodock_vina(
        receptor_pdbqt: str,
        ligand_pdbqt: str,
        center_x: float = 0.0,
        center_y: float = 0.0,
        center_z: float = 0.0,
        size_x: float = 20.0,
        size_y: float = 20.0,
        size_z: float = 20.0,
        exhaustiveness: int = 8,
        output_volume_path: str = f"{config.volume_base}/vina_output",
    ) -> str:
        """Perform molecular docking using AutoDock Vina on GPU cluster.

        Args:
            receptor_pdbqt: Path to receptor PDBQT file in a Volume.
            ligand_pdbqt: Path to ligand PDBQT file in a Volume.
            center_x: X coordinate of search box center.
            center_y: Y coordinate of search box center.
            center_z: Z coordinate of search box center.
            size_x: Search box size in X (Angstroms).
            size_y: Search box size in Y (Angstroms).
            size_z: Search box size in Z (Angstroms).
            exhaustiveness: Search exhaustiveness (higher = slower, more accurate).
            output_volume_path: Volume directory for docking results.
        """
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "autodock_vina",
                "receptor_pdbqt": receptor_pdbqt,
                "ligand_pdbqt": ligand_pdbqt,
                "center_x": str(center_x),
                "center_y": str(center_y),
                "center_z": str(center_z),
                "size_x": str(size_x),
                "size_y": str(size_y),
                "size_z": str(size_z),
                "exhaustiveness": str(exhaustiveness),
                "output_dir": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg("AutoDock Vina Docking (GPU)", run_id)

    @mcp.tool()
    async def run_autosite(
        receptor_pdb: str,
        output_volume_path: str = f"{config.volume_base}/autosite_output",
    ) -> str:
        """Identify potential binding sites on a protein using AutoSite.

        Args:
            receptor_pdb: Path to receptor PDB file in a Volume.
            output_volume_path: Volume directory for binding site predictions.
        """
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "autosite_predict",
                "receptor_pdb": receptor_pdb,
                "output_dir": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg("AutoSite Binding Site Prediction (GPU)", run_id)
