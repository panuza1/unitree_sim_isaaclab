"""Authoritative name-to-index mapping for the two six-joint Inspire hands.

Runtime articulation names are the source of truth.  The simulator must resolve
these names after USD loading instead of relying on USD/import ordering.
"""

RIGHT_INSPIRE_JOINT_NAMES = (
    "R_pinky_proximal_joint",
    "R_ring_proximal_joint",
    "R_middle_proximal_joint",
    "R_index_proximal_joint",
    "R_thumb_proximal_pitch_joint",
    "R_thumb_proximal_yaw_joint",
)
LEFT_INSPIRE_JOINT_NAMES = (
    "L_pinky_proximal_joint",
    "L_ring_proximal_joint",
    "L_middle_proximal_joint",
    "L_index_proximal_joint",
    "L_thumb_proximal_pitch_joint",
    "L_thumb_proximal_yaw_joint",
)
INSPIRE_JOINT_NAMES = RIGHT_INSPIRE_JOINT_NAMES + LEFT_INSPIRE_JOINT_NAMES


def resolve_inspire_joint_indices(runtime_joint_names):
    """Return right-first/left-second indices for a loaded articulation.

    Raises ``ValueError`` for missing or duplicated names so a changed USD
    cannot silently publish a wrong hand state.
    """
    names = list(runtime_joint_names)
    if len(set(names)) != len(names):
        raise ValueError("runtime articulation contains duplicate joint names")
    missing = [name for name in INSPIRE_JOINT_NAMES if name not in names]
    if missing:
        raise ValueError(f"missing Inspire joints: {', '.join(missing)}")
    return tuple(names.index(name) for name in INSPIRE_JOINT_NAMES)


def format_inspire_mapping(runtime_joint_names):
    indices = resolve_inspire_joint_indices(runtime_joint_names)
    right = list(zip(indices[:6], RIGHT_INSPIRE_JOINT_NAMES))
    left = list(zip(indices[6:], LEFT_INSPIRE_JOINT_NAMES))
    return right, left
