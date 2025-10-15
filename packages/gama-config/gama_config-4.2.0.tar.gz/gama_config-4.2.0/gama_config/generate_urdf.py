from math import radians
from gama_config.gama_vessel import GamaVesselConfig, Variant
from greenstream_config import Offsets, get_cameras_urdf
from gr_urchin import URDF, Joint, Material, Link, xyz_rpy_to_matrix, Visual, Mesh, Geometry, Box


class Actuator(Offsets):
    name: str = ""


def generate_urdf(
    config: GamaVesselConfig,
    ins_offset: Offsets,
    visual_offset: Offsets = Offsets(
        roll=radians(-90), pitch=0.0, yaw=0.0, forward=0.0, left=0.0, up=0.0
    ),
    actuator_offsets: list[Actuator] = [],
    mesh_path: str | None = None,
    waterline=0.0,  # meters between the waterline and the base_link
    radar_height=0.0,
    radar_yaw_offset=0.0,
    add_optical_frame: bool = True,
    center_of_gravity: Offsets = Offsets(
        roll=0.0, pitch=0.0, yaw=0.0, forward=0.0, left=0.0, up=0.0
    ),
):
    file_path = f"/tmp/vessel_{config.variant.value}_{config.mode.value}.urdf"
    camera_links, camera_joints = get_cameras_urdf(config.cameras or [], add_optical_frame)

    actuator_links = []
    actuator_joints = []
    for actuator in actuator_offsets:
        actuator_links.append(
            Link(
                name=actuator.name,
                inertial=None,
                visuals=[
                    Visual(
                        name=actuator.name,
                        geometry=Geometry(box=Box([0.1, 0.1, 0.1])),
                        material=Material(name="grey"),
                    )
                ],
                collisions=None,
            )
        )
        actuator_joints.append(
            Joint(
                name=f"base_to_{actuator.name}",
                parent="base_link",
                child=actuator.name,
                joint_type="fixed",
                origin=xyz_rpy_to_matrix(
                    [
                        actuator.forward,
                        actuator.left,
                        actuator.up,
                        actuator.roll,
                        actuator.pitch,
                        actuator.yaw,
                    ]
                ),
            )
        )

    urdf = URDF(
        name="origins",
        materials=[
            Material(name="grey", color=[0.75, 0.75, 0.75, 0.6]),
            Material(name="blue", color=[0, 0.12, 0.25, 0.9]),
        ],
        links=[
            Link(name="ins_link", inertial=None, visuals=None, collisions=None),
            Link(name="center_of_gravity", inertial=None, visuals=None, collisions=None),
            Link(
                name="waterline",
                inertial=None,
                visuals=[
                    Visual(
                        name="waterline",
                        geometry=Geometry(box=Box([10.0, 10.0, 0.01])),
                        material=Material(name="blue"),
                    )
                ],
                collisions=None,
            ),
            Link(
                name="base_link",
                inertial=None,
                visuals=(
                    [
                        Visual(
                            name="visual",
                            geometry=Geometry(
                                mesh=Mesh(
                                    filename=mesh_path, combine=False, lazy_filename=mesh_path
                                )
                            ),
                            origin=xyz_rpy_to_matrix(
                                [
                                    visual_offset.forward,
                                    visual_offset.left,
                                    visual_offset.up,
                                    visual_offset.roll,
                                    visual_offset.pitch,
                                    visual_offset.yaw,
                                ]
                            ),
                            material=Material(name="grey"),
                        ),
                    ]
                    if mesh_path
                    else None
                ),
                collisions=None,
            ),
            *actuator_links,
            *camera_links,
        ],
        joints=[
            Joint(
                name="base_to_ins",
                parent="base_link",
                child="ins_link",
                joint_type="fixed",
                origin=xyz_rpy_to_matrix(
                    [
                        ins_offset.forward,
                        ins_offset.left,
                        ins_offset.up,
                        ins_offset.roll,
                        ins_offset.pitch,
                        ins_offset.yaw,
                    ]
                ),
            ),
            Joint(
                name="base_to_waterline",
                parent="base_link",
                child="waterline",
                joint_type="fixed",
                origin=xyz_rpy_to_matrix([0, 0, -waterline, 0, 0, 0]),
            ),
            Joint(
                name="base_to_center_of_gravity",
                parent="base_link",
                child="center_of_gravity",
                joint_type="fixed",
                origin=xyz_rpy_to_matrix(
                    [
                        center_of_gravity.forward,
                        center_of_gravity.left,
                        center_of_gravity.up,
                        center_of_gravity.roll,
                        center_of_gravity.pitch,
                        center_of_gravity.yaw,
                    ]
                ),
            ),
            *actuator_joints,
            *camera_joints,
        ],
    )
    # Add a radar
    if config.variant == Variant.ARMIDALE or config.variant == Variant.FREMANTLE:
        urdf._links.append(
            Link(
                name="radar",
                inertial=None,
                visuals=[],
                collisions=None,
            )
        )
        urdf._joints.append(
            Joint(
                name="baselink_to_radar",
                parent="base_link",
                child="radar",
                joint_type="fixed",
                origin=xyz_rpy_to_matrix([0.0, 0.0, radar_height, 0.0, 0.0, radar_yaw_offset]),
            )
        )

    urdf.save(file_path)

    # stringify urdf response for robot description
    with open(file_path) as infp:
        robot_description = infp.read()

    return robot_description
