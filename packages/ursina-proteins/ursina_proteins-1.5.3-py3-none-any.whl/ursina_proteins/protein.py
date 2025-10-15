from hashlib import md5
from math import sqrt
from os import path

import numpy as np
from Bio.PDB import PDBParser
from Bio.PDB.MMCIFParser import MMCIFParser
from scipy.interpolate import make_splrep, splev
from ursina import Color, Entity, Mesh, Vec3, color

# Geometry constants
PHI = (1 + sqrt(5)) / 2

ICOSAHEDRON_VERTS = [
    Vec3(-1, PHI, 0),
    Vec3(1, PHI, 0),
    Vec3(-1, -PHI, 0),
    Vec3(1, -PHI, 0),
    Vec3(0, -1, PHI),
    Vec3(0, 1, PHI),
    Vec3(0, -1, -PHI),
    Vec3(0, 1, -PHI),
    Vec3(PHI, 0, -1),
    Vec3(PHI, 0, 1),
    Vec3(-PHI, 0, -1),
    Vec3(-PHI, 0, 1),
]

ICOSAHEDRON_FACES = [
    (0, 11, 5),
    (0, 5, 1),
    (0, 1, 7),
    (0, 7, 10),
    (0, 10, 11),
    (1, 5, 9),
    (5, 11, 4),
    (11, 10, 2),
    (10, 7, 6),
    (7, 1, 8),
    (3, 9, 4),
    (3, 4, 2),
    (3, 2, 6),
    (3, 6, 8),
    (3, 8, 9),
    (4, 9, 5),
    (2, 4, 11),
    (6, 2, 10),
    (8, 6, 7),
    (9, 8, 1),
]

ICOSAHEDRON_NORMALS = [v.normalized() for v in ICOSAHEDRON_VERTS]


class Protein:
    """
    A class to represent a protein structure and render it as entities in Ursina.

    Attributes:
        structure: The parsed protein structure.
        helices: Dictionary mapping chain IDs to lists of helix segments.
        atoms_entity: Entity containing the mesh representation of atoms.
        helices_entity: Entity containing the mesh representation of helices.
        coils_entity: Entity containing the mesh representation of coils.
        entities: List of all structural entities (atoms, helices, coils).

    Class Attributes:
        ELEMENT_COLORS: Default color mapping for chemical elements.
        CHAIN_COLORS: Default color mapping for protein chains.
        PDB_CHAIN_ID_INDEX: Index of chain ID in PDB file line.
        PDB_START_RESIDUE_INDICES: Indices of start-of-helix residue in PDB file line.
        PDB_END_RESIDUE_INDICES: Indices of end-of-helix residue in PDB file line.
    """

    ELEMENT_COLORS = {
        "H": color.rgb(0.8, 0.8, 0.8),
        "C": color.rgb(0.2, 0.2, 0.2),
        "N": color.rgb(0, 0, 0.8),
        "O": color.rgb(0.8, 0, 0),
        "S": color.rgb(0.8, 0.8, 0),
        "P": color.rgb(1, 0.65, 0),
        "Cl": color.rgb(0, 0.8, 0),
        "Fe": color.rgb(0.7, 0.45, 0.2),
    }

    CHAIN_COLORS = {
        "A": color.rgb(1, 0, 0),
        "B": color.rgb(0, 1, 0),
        "C": color.rgb(0, 0, 1),
        "D": color.rgb(1, 1, 0),
        "E": color.rgb(1, 0.5, 0.8),
        "F": color.rgb(0.2, 0.7, 1),
        "G": color.rgb(1, 0.6, 0),
        "H": color.rgb(1, 0, 1),
    }

    PDB_CHAIN_ID_INDEX = 19
    PDB_START_RESIDUE_INDICES = (21, 25)
    PDB_END_RESIDUE_INDICES = (33, 37)

    def __init__(
        self,
        protein_filepath: str,
        legacy_pdb: bool = True,
        parser_quiet: bool = True,
        compute_atoms: bool = True,
        atoms_size: float = 0.1,
        helices_thickness: float = 4,
        coils_thickness: float = 1,
        chains_smoothness: float = 3,
        chain_id_color_map: dict[str, Color] = None,
        atom_element_color_map: dict[str, Color] = None,
        atom_vertices: list[Vec3] = None,
        atom_triangles: list[tuple[int]] = None,
        atom_normals: list[Vec3] = None,
        *args,
        **kwargs,
    ):
        """
        Initialize a Protein object from a protein file.

        Args:
            protein_filepath: Path to the protein file.
            legacy_pdb: Whether protein is in legacy PDB (or newer mmCIF) format (default: True).
            parser_quiet: Flag to enable/disable logging on parser (default: True).
            compute_atoms: Flag to enable/disable atoms computation (default: True).
            atoms_size: Size of individual atoms in the atoms mesh (default: 0.1).
            helices_thickness: Thickness of helix meshes (default: 4).
            coils_thickness: Thickness of coil meshes (default: 1).
            chains_smoothness: Smoothness factor for chain rendering (default: 3).
            chain_id_color_map: Color mapping for chains (default: None).
            atom_element_color_map: Color mapping for atoms (default: None).
            atom_vertices: Base vertices to use for atom geometry (default: None).
            atom_triangles: Base triangles to use for atom geometry (default: None).
            atom_normals: Base normals to use for atom geometry (default: None).
            *args: Arguments passed to constructor for each entity.
            **kwargs: Keyword arguments passed to constructor for each entity.
        """

        # Validation
        if chain_id_color_map is None:
            chain_id_color_map = dict()
        if atom_element_color_map is None:
            atom_element_color_map = dict()

        if not path.isfile(protein_filepath):
            raise FileNotFoundError(f"Protein file not found: {protein_filepath}")

        if helices_thickness <= 0 or coils_thickness <= 0 or atoms_size <= 0:
            raise ValueError("Thickness and size values must be positive")

        if chains_smoothness < 1:
            raise ValueError("Smoothness value must be at least 1")

        # Parse structure
        parser = PDBParser() if legacy_pdb else MMCIFParser()
        parser.QUIET = parser_quiet
        self.structure = parser.get_structure("protein", protein_filepath)
        self.helices = (
            self.get_pdb_helices(protein_filepath)
            if legacy_pdb
            else self.get_cif_helices(protein_filepath)
        )
        structure_center_of_mass = self.structure.center_of_mass()

        # Create entities
        self.entities = []

        if compute_atoms:
            self.atoms_entity = Entity(
                model=self.compute_atoms_mesh(
                    atoms_size,
                    atom_element_color_map,
                    atom_vertices if atom_vertices else ICOSAHEDRON_VERTS,
                    atom_triangles if atom_triangles else ICOSAHEDRON_FACES,
                    atom_normals if atom_normals else ICOSAHEDRON_NORMALS,
                ),
                origin=Vec3(*structure_center_of_mass),
                *args,
                **kwargs,
            )
            self.entities.append(self.atoms_entity)

        chain_meshes = self.compute_helices_and_coils_meshes(
            chain_id_color_map, chains_smoothness, helices_thickness, coils_thickness
        )
        self.helices_entity = Entity(
            model=chain_meshes[0],
            origin=Vec3(*structure_center_of_mass),
            *args,
            **kwargs,
        )
        self.coils_entity = Entity(
            model=chain_meshes[1],
            origin=Vec3(*structure_center_of_mass),
            *args,
            **kwargs,
        )
        self.entities.extend([self.helices_entity, self.coils_entity])

    def compute_atoms_mesh(
        self,
        atoms_size: float,
        element_color_map: dict[str, Color],
        base_vertices: list[Vec3],
        base_triangles: list[tuple[int]],
        base_normals: list[Vec3],
    ) -> Mesh:
        """
        Compute the mesh of atoms in the protein structure.

        This method creates an icosahedron for each atom in the protein structure
        and assigns colors based on the element type, combining them into one mesh.

        Args:
            atoms_size: Size of individual atoms.
            element_color_map: Color mapping for atom elements.
            base_vertices: Base vertices to use for atom geometry
            base_triangles: Base triangles to use for atom geometry
            base_normals: Base normals to use for atom geometry

        Returns:
            A Mesh object representing all atoms in the protein structure.
        """

        verts = []
        faces = []
        colors = []
        norms = []

        for index, atom in enumerate(self.structure.get_atoms()):
            # Vertices
            verts.extend(
                [(vert * atoms_size) + atom.get_coord() for vert in base_vertices]
            )

            # Faces (triangles)
            faces.extend(
                [
                    tuple(i + len(base_vertices) * index for i in face)
                    for face in base_triangles
                ]
            )

            # Colors
            colors.extend(
                [
                    element_color_map.get(
                        atom.element,
                        Protein.ELEMENT_COLORS.get(
                            atom.element, color.rgb(1, 0.7, 0.8)
                        ),
                    )
                    for _ in base_vertices
                ]
            )

            # Normals
            norms.extend(base_normals)

        return Mesh(vertices=verts, triangles=faces, colors=colors, normals=norms)

    def compute_helices_and_coils_meshes(
        self,
        id_color_map: dict[str, Color],
        smoothness: float,
        helices_thickness: float,
        coils_thickness: float,
    ) -> list[Mesh]:
        """
        Compute the meshes for helices and coils in the protein structure.

        This method creates line meshes for helices and coils, applying spline
        smoothing to the backbone coordinates and assigning colors based on chain IDs.
        A single mesh is created for each segment type (helix/coil) across all chains.

        Args:
            id_color_map: Color mapping for chain IDs.
            smoothness: Factor controlling the smoothness of the chains.
            helices_thickness: Thickness of helix meshes.
            coils_thickness: Thickness of coil meshes.

        Returns:
            A list containing two Mesh objects: one for helices and one for coils.
        """

        verts = {"helices": [], "coils": []}
        tris = {"helices": [], "coils": []}
        colors = {"helices": [], "coils": []}

        for chain in self.structure.get_chains():
            # Map of atom number to atom coordinate
            carbon_alpha_coords = {
                atom.get_parent().get_id()[1]: atom.coord
                for atom in chain.get_atoms()
                if atom.get_id() == "CA"
            }

            # Chain info
            chain_id = chain.get_id()
            chain_helices = self.helices.get(chain_id) or []
            chain_segments = parse_segments(
                chain_helices, len(carbon_alpha_coords), "helices", "coils"
            )

            # Render each segment (helices and coils)
            for segment_type, segments in chain_segments.items():
                for start, end in segments:
                    # Get coordinates of the segment's carbon alpha atoms
                    coords = [
                        coord
                        for i in range(start, end + 1)
                        if (coord := carbon_alpha_coords.get(i)) is not None
                    ]

                    tris_start = len(verts[segment_type])

                    # Vertices
                    x, y, z = zip(*coords)
                    splines = [
                        make_splrep(
                            range(len(values)), values, s=0, k=min(3, len(values) - 1)
                        )
                        for values in [x, y, z]
                    ]

                    # Calculate splined coordinates
                    step_values = np.linspace(
                        0,
                        len(coords) - 1,
                        round(len(coords) * smoothness),
                    )
                    smoothed_xyz = [splev(step_values, spline) for spline in splines]
                    smoothed_coords = list(zip(*smoothed_xyz))
                    verts[segment_type].extend(smoothed_coords)

                    # Colors
                    chain_color = id_color_map.get(
                        chain_id,
                        Protein.CHAIN_COLORS.get(
                            chain_id, Protein.color_from_id(chain_id)
                        ),
                    )
                    colors[segment_type].extend([chain_color for _ in smoothed_coords])

                    # Triangles
                    tris[segment_type].extend(
                        [
                            (i, i + 1)
                            for i in range(
                                tris_start, tris_start + len(smoothed_coords) - 1
                            )
                        ]
                    )

        return [
            Mesh(
                mode="line",
                vertices=verts[segment_type],
                triangles=tris[segment_type],
                colors=colors[segment_type],
                thickness=thickness,
            )
            for thickness, segment_type in zip(
                (helices_thickness, coils_thickness), ("helices", "coils")
            )
        ]

    def get_pdb_helices(self, protein_filepath: str) -> dict[str, list[tuple[int]]]:
        """
        Extract helix information for a protein from a PDB file.

        This method parses the HELIX records in a PDB file to identify
        the start and end residues of helices for each chain.

        Args:
            protein_filepath: Path to the PDB file.

        Returns:
            A dictionary mapping chain IDs to lists of helices,
            where each segment is represented as a tuple of start/end indices.
        """

        helices = dict()

        with open(protein_filepath, "r") as pdb_file:
            for line in pdb_file:
                if line.startswith("HELIX"):
                    chain_id = line[Protein.PDB_CHAIN_ID_INDEX]
                    start_residue = int(
                        line[
                            Protein.PDB_START_RESIDUE_INDICES[
                                0
                            ] : Protein.PDB_START_RESIDUE_INDICES[1]
                        ].strip()
                    )
                    end_residue = int(
                        line[
                            Protein.PDB_END_RESIDUE_INDICES[
                                0
                            ] : Protein.PDB_END_RESIDUE_INDICES[1]
                        ].strip()
                    )

                    if chain_id in helices:
                        helices[chain_id].append((start_residue, end_residue))
                    else:
                        helices[chain_id] = [(start_residue, end_residue)]

        return helices

    def get_cif_helices(
        self, protein_filepath: str
    ) -> dict[str, list[tuple[int, int]]]:
        helices = {}

        # Load CIF file into memory
        with open(protein_filepath, "r") as file:
            lines = [line.strip() for line in file if line.strip()]

        loop_start = None
        for i, line in enumerate(lines):
            # Heuristically check loop is data block
            if line.startswith("loop_") and any(
                "_struct_conf." in line for line in lines[i + 1 : i + 10]
            ):
                loop_start = i
                break
        if loop_start is None:
            return helices

        identifiers = []
        data_start = loop_start + 1
        for j, line in enumerate(lines[data_start:], start=data_start):
            # Get index where identifiers end and data begins
            if not line.startswith("_struct_conf."):
                data_start = j
                break
            # Get identifiers in order they appear in line
            identifiers.append(line.split(".")[1])

        # Create identifier-index map for more readable/semantic access and confirm key identifiers are present
        identifier_index_map = {
            identifier: k for k, identifier in enumerate(identifiers)
        }
        if (
            not {
                "conf_type_id",
                "beg_auth_asym_id",
                "beg_auth_seq_id",
                "end_auth_seq_id",
            }
            <= identifier_index_map.keys()
        ):
            return helices

        for line in lines[data_start:]:
            # End processing when next loop reached
            if line.startswith("loop_"):
                break

            parts = line.split()
            # Skip irrelevant lines
            if len(parts) < len(identifiers):
                continue
            if "HELX" not in parts[identifier_index_map["conf_type_id"]]:
                continue

            chain_id = parts[identifier_index_map["beg_auth_asym_id"]]
            start = int(parts[identifier_index_map["beg_auth_seq_id"]])
            end = int(parts[identifier_index_map["end_auth_seq_id"]])
            helices.setdefault(chain_id, []).append((start, end))

        return helices

    @staticmethod
    def color_from_id(id: str) -> Color:
        """
        Generate a deterministic color based on a string identifier.

        This method creates a consistent color for a given ID string by hashing
        the string and extracting RGB values from the hash.

        Args:
            id: String identifier to generate a color for.

        Returns:
            A Color object with RGB values derived from the hash of the input ID.
        """

        hash_value = int(md5(id.encode("utf-8")).hexdigest(), 16)
        r = (hash_value >> 16) & 0xFF
        g = (hash_value >> 8) & 0xFF
        b = hash_value & 0xFF
        return color.rgb(r / 255, g / 255, b / 255)


def parse_segments(
    segments: list[tuple[int]], size: int, in_segment_label: str, out_segment_label: str
) -> dict[str, list[tuple[int]]]:
    """
    Parse a list of segments and fill in the gaps between them.

    This utility function takes a list of segment indices and generates
    a complete segmentation by filling in the gaps between them.

    Args:
        segments: List of segments, each represented as a tuple of (start, end) indices.
        size: The total size to cover.
        in_segment_label: Label for the input segments.
        out_segment_label: Label for the gaps between input segments.

    Returns:
        A dictionary with two keys (in_segment_label and out_segment_label),
        each mapping to a list of (start, end) tuples representing the segments.
    """

    segments = sorted(segments)
    result = {in_segment_label: [], out_segment_label: []}
    current = 0

    for start, end in segments:
        if current < start:
            result[out_segment_label].append((current, start))
        result[in_segment_label].append((start, end))
        current = end

    if current <= size:
        result[out_segment_label].append((current, size))

    return result
