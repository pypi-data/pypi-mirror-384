import datetime
import os
import platform
import re
import socket
import sys
import tempfile

import numpy as np
from skrobot.model import Link
from skrobot.model import RobotModel
from skrobot.utils.mesh import simplify_vertex_clustering
from skrobot.utils.mesh import split_mesh_by_face_color
import trimesh
import yaml

import urdfeus
from urdfeus.common import collect_all_joints_of_robot
from urdfeus.common import is_fixed_joint
from urdfeus.common import is_linear_joint
from urdfeus.common import meter2millimeter
from urdfeus.grouping_joint import create_config
from urdfeus.read_yaml import read_config_from_yaml
from urdfeus.templates import get_euscollada_string


def validate_euslisp_identifier(name):
    """
    Validate if a string is a valid EusLisp identifier.

    EusLisp identifiers must:
    - Start with a letter or underscore
    - Contain only letters, digits, underscores, and hyphens
    - Not be empty
    - Not contain spaces or special characters except underscore and hyphen
    """
    if not name:
        return False, "Name cannot be empty"

    # Check if it starts with a letter or underscore
    if not re.match(r'^[a-zA-Z_]', name):
        return False, "Name must start with a letter or underscore"

    # Check if it contains only valid characters
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False, "Name can only contain letters, digits, underscores, and hyphens"

    # Check for reserved words (common EusLisp keywords)
    reserved_words = {
        'and', 'or', 'not', 'if', 'then', 'else', 'cond', 'case', 'let', 'let*',
        'defun', 'defclass', 'defmethod', 'lambda', 'quote', 'setq', 'setf',
        'progn', 'prog1', 'prog2', 'when', 'unless', 'while', 'do', 'dolist',
        'dotimes', 'loop', 'return', 'throw', 'catch', 'unwind-protect',
        'eval', 'apply', 'funcall', 'car', 'cdr', 'cons', 'list', 'append',
        'nil', 't', 'pi', 'reset',
    }

    if name.lower() in reserved_words:
        return False, f"'{name}' is a reserved EusLisp keyword"

    return True, "Valid EusLisp identifier"


def print_link(
    link: Link,
    simplify_vertex_clustering_voxel_size=None,
    add_link_suffix: bool = True,
    inertial=None,
    fp=sys.stdout,
):
    if add_link_suffix:
        link_name = link.name + "_lk"
    else:
        link_name = link.name
    print(f"     ;; link: {link_name}", file=fp)
    print("     (let ((geom-lst (list ", end="", file=fp)

    geom_counter = 0
    if link.visual_mesh is not None and len(link.visual_mesh) > 0:
        print(
            f"(send self :_make_instance_{link.name}_geom{geom_counter})", end="", file=fp
        )
        geom_counter += 1

    print(")))", file=fp)
    print("       (dolist (g (cdr geom-lst)) (send (car geom-lst) :assoc g))", file=fp)
    print(f"       (setq {link_name}", file=fp)
    print("             (instance bodyset-link", file=fp)
    print("                       :init (make-cascoords)", file=fp)
    print(f"                       :bodies geom-lst", file=fp)  # NOQA
    print(f'                       :name "{link.name}"))', file=fp)
    weight = 0.0
    centroid_x, centroid_y, centroid_z = 0, 0, 0
    ixx, ixy, ixz = 0, 0, 0
    iyx, iyy, iyz = 0, 0, 0
    izx, izy, izz = 0, 0, 0
    if inertial is not None:
        weight = inertial.mass * 1000.0  # kg -> g
        centroid_x, centroid_y, centroid_z = 1000 * inertial.origin[:3, 3]  # m -> mm
        ixx, ixy, ixz, iyx, iyy, iyz, izx, izy, izz = 1e9 * inertial.inertia.reshape(
            -1
        )  # kg m^2 -> g mm^2
    print(
        f"       (progn (send {link_name} :weight {weight}) (setq ({link_name} . acentroid) (float-vector {centroid_x} {centroid_y} {centroid_z})) (send {link_name} :inertia-tensor #2f(({ixx} {ixy} {ixz})({iyx} {iyy} {iyz})({izx} {izy} {izz}))))",
        file=fp,
    )

    print(f"       ;; global coordinates for {link_name}", file=fp)
    print("       (let ((world-cds (make-coords :pos ", end="", file=fp)
    x, y, z = meter2millimeter * link.worldpos()
    print(f"(float-vector {x:.6f} {y:.6f} {z:.6f})", end="", file=fp)

    qw, qx, qy, qz = link.copy_worldcoords().quaternion
    print(
        f"\n                                     :rot (quaternion2matrix (float-vector {qw:.6f} {qx:.6f} {qy:.6f} {qz:.6f}))",
        end="",
        file=fp,
    )
    print(")))\n", end="", file=fp)
    print(f"         (send {link_name} :transform world-cds)))", file=fp)
    print("\n", end="", file=fp)


def print_joint(joint, add_joint_suffix=True, add_link_suffix=True, fp=sys.stdout):
    linear = is_linear_joint(joint)

    joint_name = joint.name
    if add_joint_suffix:
        if is_fixed_joint(joint):
            joint_name += "_fixed_jt"
        else:
            joint_name += "_jt"

    print("\n", end="", file=fp)
    print(f"     ;; joint: {joint_name}", file=fp)
    print(f"     (setq {joint_name}", file=fp)
    print(
        f"           (instance {'linear-joint' if linear else 'rotational-joint'} :init",
        file=fp,
    )
    print(f'                     :name "{joint.name}"', file=fp)
    if add_link_suffix:
        print(
            f"                     :parent-link {joint.parent_link.name}_lk :child-link {joint.child_link.name}_lk",
            file=fp,
        )
    else:
        print(
            f"                     :parent-link {joint.parent_link.name} :child-link {joint.child_link.name}",
            file=fp,
        )

    x, y, z = joint.axis
    if x == 0.0 and y == 0.0 and z == 0.0:
        print("                     :axis (float-vector 1 1 1) ;; fixed joint??", file=fp)
    else:
        print(
            f"                     :axis (float-vector {x:.16f} {y:.16f} {z:.16f})",
            file=fp,
        )

    min_val = joint.min_angle
    max_val = joint.max_angle
    print("                     ", end="", file=fp)
    if np.isinf(min_val) or np.isinf(max_val):
        print(":min *-inf* :max *inf*", file=fp)
    else:
        if linear:
            min_angle = meter2millimeter * min_val
            max_angle = meter2millimeter * max_val
        else:
            min_angle = np.rad2deg(min_val)
            max_angle = np.rad2deg(max_val)
        min_str = "*-inf*" if min_val == -float("inf") else str(min_angle)
        max_str = "*inf*" if max_val == float("inf") else str(max_angle)
        print(f":min {min_str} :max {max_str}", file=fp)
    print(f"                     :max-joint-velocity {joint.max_joint_velocity}", file=fp)
    print(f"                     :max-joint-torque {joint.max_joint_torque}", end="", file=fp)
    print("))", file=fp)


def print_mimic_joints(robot, fp=sys.stdout):
    print("\n     ;; mimic joint re-definition\n", file=fp)
    mimic_joint_list = {}

    for j in robot.urdf_robot_model.joints:
        if j.mimic is None:
            continue
        joint_a = robot.__dict__[j.mimic.joint]
        joint_b = robot.__dict__[j.name]
        multiplier = j.mimic.multiplier
        offset = j.mimic.offset

        if joint_a not in mimic_joint_list:
            mimic_joint_list[joint_a] = []
        mimic_joint_list[joint_a].append((joint_b, multiplier, offset))

    for mimic_joint, joints in mimic_joint_list.items():
        linear = is_linear_joint(mimic_joint)
        print(f"     ;; re-define {mimic_joint.name} as mimic-joint", file=fp)
        print("     (let (tmp-mimic-joint)", file=fp)
        joint_type = "linear-mimic-joint" if linear else "rotational-mimic-joint"
        print(
            f"       (setq tmp-mimic-joint (replace-object (instance {joint_type} :init :parent-link (make-cascoords) :child-link (make-cascoords) :max-joint-velocity 0 :max-joint-torque 0) {mimic_joint.name}_jt))",
            file=fp,
        )
        print(f"       (setq {mimic_joint.name}_jt tmp-mimic-joint))", file=fp)
        print(f"     (setq ({mimic_joint.name}_jt . mimic-joints)", file=fp)
        print("           (list", file=fp)
        for joint, multiplier, offset in joints:
            print(
                f"            (instance mimic-joint-param :init {joint.name}_jt :multiplier {multiplier} :offset {offset})",
                end="",
                file=fp,
            )
        print("))", file=fp)
        print(f"     ;; set offset as default-coords", file=fp)  # NOQA
        print(f"     (dolist (j ({mimic_joint.name}_jt . mimic-joints))", file=fp)
        print("       (cond ((derivedp (send j :joint) rotational-joint)", file=fp)
        print(
            "              (send (send j :joint :child-link) :rotate (send j :offset) ((send j :joint) . axis)))",
            file=fp,
        )
        print("             ((derivedp (send j :joint) linear-joint)", file=fp)
        print(
            "              (send (send j :joint :child-link) :translate (scale (* 1000 (send j :offset)) ((send j :joint) . axis))))",
            file=fp,
        )
        print(
            '             (t (error "unsupported mimic joint ~A" (send j :joint))))',
            file=fp,
        )
        print(
            "       (setq ((send j :joint) . default-coords) (send j :joint :child-link :copy-coords)))",
            file=fp,
        )


def print_geometry(link, simplify_vertex_clustering_voxel_size=None, fp=sys.stdout):
    x, y, z = link.translation
    name = link.name + "_geom" + str(0)
    print(f"  (:_make_instance_{name} ()", file=fp)
    print("    (let (geom glv qhull", file=fp)
    print("          (local-cds (make-coords :pos ", end="", file=fp)
    print(
        f"(float-vector {x * meter2millimeter:.6f} {y * meter2millimeter:.6f} {z * meter2millimeter:.6f})",
        end="",
        file=fp,
    )

    qw, qx, qy, qz = link.quaternion

    print("\n", end="", file=fp)
    print(f"                                  :rot (quaternion2matrix ", end="", file=fp)  # NOQA
    print(f"(float-vector {qw:.6f} {qx:.6f} {qy:.6f} {qz:.6f}))", end="", file=fp)
    print(")))", file=fp)
    print("      (setq glv", file=fp)
    print("       (instance gl::glvertices :init", end="", file=fp)
    if link.visual_mesh is not None and len(link.visual_mesh) > 0:
        # TODO(someone): use g.scale
        print_mesh(link, simplify_vertex_clustering_voxel_size, fp=fp)
    else:
        print("))", file=fp)
    print("      (send glv :transform local-cds)", file=fp)
    print("      (send glv :calc-normals)", file=fp)

    # TODO(someone) qhull
    gname = link.name
    print(
        f'      (setq geom (instance collada-body :init :replace-obj nil :name "{gname}"))',
        file=fp,
    )
    print("      (when glv", file=fp)
    print("        (setq (geom . gl::aglvertices) glv)", file=fp)
    print("        (send geom :assoc glv))", file=fp)
    print("      geom))", file=fp)


def print_mesh(link, simplify_vertex_clustering_voxel_size=None, fp=sys.stdout):
    print("\n                 (list ;; mesh list", file=fp)
    mesh = trimesh.util.concatenate(link.visual_mesh)
    if simplify_vertex_clustering_voxel_size:
        mesh = simplify_vertex_clustering(mesh, simplify_vertex_clustering_voxel_size)[0]
    for input_mesh in split_mesh_by_face_color(mesh):
        print("                  (list ;; mesh description", file=fp)
        print("                   (list :type :triangles)", file=fp)
        print("                   (list :material (list", file=fp)
        print(
            f"                    (list :ambient (float-vector {input_mesh.visual.main_color[0] / 255.0} {input_mesh.visual.main_color[1]/ 255.0} {input_mesh.visual.main_color[2]/ 255.0} {input_mesh.visual.main_color[3]/ 255.0}))",
            file=fp,
        )
        print(
            f"                    (list :diffuse (float-vector {input_mesh.visual.main_color[0]/ 255.0} {input_mesh.visual.main_color[1]/ 255.0} {input_mesh.visual.main_color[2]/ 255.0} {input_mesh.visual.main_color[3]/ 255.0}))",
            end="",
            file=fp,
        )
        print("))", file=fp)
        print("                   (list :indices #i(", end="", file=fp)
        print(" ".join(map(str, input_mesh.faces.reshape(-1))), end="", file=fp)
        print("))", file=fp)
        print(
            f"                   (list :vertices (let ((mat (make-matrix {len(input_mesh.vertices)} 3))) (fvector-replace (array-entity mat) #f(",
            end="",
            file=fp,
        )
        vertices = np.array(input_mesh.vertices)
        vertices = link.inverse_transformation().transform_vector(vertices)
        vertices = meter2millimeter * vertices
        # Modified the vertex printing format to reduce mesh file size, considering the unit is in millimeters (mm).
        # Since the coordinates are in mm, having them formatted to just one decimal place is sufficiently precise for most applications.
        # This change not only preserves the necessary precision for mm-scale measurements but also effectively compresses the data,
        # resulting in a smaller file size due to reduced numerical precision in the vertex coordinates.
        print(
            " ".join(f"{x:.1f}" for x in vertices.reshape(-1)),
            end="",
            file=fp,
        )
        print(")) mat))", end="", file=fp)
        # TODO(someone) normal
        print(")", end="", file=fp)
    print(")))", file=fp)


def print_end_coords(
    robot,
    config_yaml_path=None,
    add_link_suffix=True,
    add_joint_suffix=True,
    fp=sys.stdout,
):
    limbs = []
    if config_yaml_path is not None:
        limbs = read_config_from_yaml(robot, config_yaml_path, fp=fp)
    else:
        print("     ;; links", file=fp)
        if add_link_suffix:
            print(f"     (setq links (list ", end="", file=fp)  # NOQA
        else:
            print(f"     (setq links (list ", end="", file=fp)  # NOQA

        if add_link_suffix:
            for link in robot.link_list:
                print(f" {link.name}_lk", end="", file=fp)
        else:
            for link in robot.link_list:
                print(f" {link.name}", end="", file=fp)

        print("))", file=fp)
        print("", file=fp)
        print("     ;; joint-list", file=fp)
        print("     (setq joint-list (list", end="", file=fp)
        if add_joint_suffix:
            for joint in robot.joint_list:
                print(f" {joint.name}_jt", end="", file=fp)
        else:
            for joint in robot.joint_list:
                print(f" {joint.name}", end="", file=fp)
        print("))", file=fp)
        print("", file=fp)

        print("     ;; init-ending\n", file=fp)
        print("     (send self :init-ending) ;; :urdf\n", file=fp)
        print(
            "     ;; overwrite bodies to return draw-things links not (send link :bodies)\n",
            file=fp,
        )
        print(
            "     (setq bodies (flatten (mapcar #'(lambda (b) (if (find-method b :bodies) (send b :bodies))) (list",
            end="",
            file=fp,
        )
        for link in robot.link_list:
            if add_link_suffix:
                print(f" {link.name}_lk", end="", file=fp)
            else:
                print(f" {link.name}", end="", file=fp)
        print("))))\n", file=fp)

        print("     (when (member :reset-pose (send self :methods))", file=fp)
        print("           (send self :reset-pose)) ;; :set reset-pose\n", file=fp)
        print("     self)) ;; end of :init", file=fp)

    print("\n", end="", file=fp)
    print("  ;; all joints", file=fp)
    # Assuming URDFDOM_1_0_0_API is a boolean variable
    for joint in collect_all_joints_of_robot(robot):
        joint_name = joint.name
        if add_joint_suffix:
            if is_fixed_joint(joint):
                print(
                    f"  (:{joint_name} (&rest args) (forward-message-to {joint_name}_fixed_jt args))",
                    file=fp,
                )
            else:
                print(
                    f"  (:{joint_name} (&rest args) (forward-message-to {joint_name}_jt args))",
                    file=fp,
                )
        else:
            print(
                f"  (:{joint_name} (&rest args) (forward-message-to {joint_name} args))",
                file=fp,
            )

    if add_link_suffix:
        print("\n  ;; all links forwarding", file=fp)
        print("  (:links (&rest args)", file=fp)
        print("   (if (null args) (return-from :links (send-super :links)))", file=fp)
        print("   (let ((key (car args))\n           (nargs (cdr args)))", file=fp)
        print(
            "     (unless (keywordp key)\n         (return-from :links (send-super* :links args)))\n       (case key",
            file=fp,
        )

        for link in robot.link_list:
            link_name = link.name
            print(
                f"       (:{link_name} (forward-message-to {link_name}_lk nargs))",
                file=fp,
            )
        print("       (t (send-super* :links args)))))", file=fp)

    print("\n  ;; all links", file=fp)
    for link in robot.link_list:
        link_name = link.name
        if add_link_suffix:
            print(
                f"  (:{link_name}_lk (&rest args) (forward-message-to {link_name}_lk args))",
                file=fp,
            )
        else:
            print(
                f"  (:{link_name} (&rest args) (forward-message-to {link_name} args))",
                file=fp,
            )

    if config_yaml_path is not None:
        with open(config_yaml_path) as file:
            doc = yaml.load(file, Loader=yaml.FullLoader)
        for limb_name in limbs:
            try:
                limb_doc = doc[limb_name]
            except Exception as _:
                continue
            for limb_dict in limb_doc:
                for urdf_joint_name, alias_joint_name in limb_dict.items():
                    # Handle both formats: 'symbol' and ':symbol'
                    # Always ensure we have exactly one ':' at the beginning
                    if alias_joint_name.startswith(':'):
                        # Already has ':', use as-is but strip extra ':'
                        clean_alias = alias_joint_name.lstrip(':')
                    else:
                        # No ':', use as-is
                        clean_alias = alias_joint_name
                    print(
                        f"  (:{clean_alias} (&rest args) (forward-message-to {urdf_joint_name}_jt args))",
                        file=fp,
                    )
    return limbs


def print_unique_limbs(limb_names, fp=sys.stdout):
    print("\n  ;; non-default limbs\n", file=fp)
    for limb in limb_names:
        if (
            limb == "torso"
            or limb == "larm"
            or limb == "rarm"
            or limb == "lleg"
            or limb == "rleg"
            or limb == "head"
        ):
            continue
        print(
            f"  (:{limb} (&rest args) (unless args (setq args (list nil))) (send* self :limb :{limb} args))",
            file=fp,
        )
        print(f"  (:{limb}-end-coords () {limb}-end-coords)", file=fp)
        print(f"  (:{limb}-root-link () {limb}-root-link)", file=fp)


def urdf2eus(
    urdf_path,
    config_yaml_path=None,
    simplify_vertex_clustering_voxel_size=None,
    robot_name=None,
    fp=sys.stdout,
):
    tmp_yaml_path = None
    if config_yaml_path is None:
        tmp_yaml_fd, tmp_yaml_path = tempfile.mkstemp(suffix=".yaml", prefix="urdf2eus_")
        try:
            create_config(urdf_path, tmp_yaml_path)
            config_yaml_path = tmp_yaml_path
        finally:
            os.close(tmp_yaml_fd)
    r = RobotModel()
    with open(urdf_path) as f:
        r.load_urdf_file(f)
    limb_slot_names = []  # Initialize here for broader scope

    # Use custom robot name if provided, otherwise use URDF name
    if robot_name is None:
        robot_name = r.urdf_robot_model.name
    else:
        # Validate the custom robot name
        is_valid, error_msg = validate_euslisp_identifier(robot_name)
        if not is_valid:
            raise ValueError(f"Invalid robot name '{robot_name}': {error_msg}")

    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(
        f""";; DO NOT EDIT THIS FILE
;;
;; this file is automatically generated from {urdf_path} on ({sys.platform} {socket.gethostname()} {platform.platform()}) at {current_time_str}
;; urdfeus version is {urdfeus.__version__}
;;
""",
        file=fp,
    )

    print(get_euscollada_string(), file=fp)

    joint_names = []
    for joint in collect_all_joints_of_robot(r):
        joint_name = joint.name
        if is_fixed_joint(joint):
            joint_name += "_fixed_jt"
        else:
            joint_name += "_jt"
        joint_names.append(joint_name)

    add_link_suffix = True
    link_list = []
    for link in r.link_list:
        if add_link_suffix:
            link_name = link.name + "_lk"
        else:
            link_name = link.name
        link_list.append(link_name)

    print("\n\n", end="", file=fp)
    print(
        f"(defun {robot_name} () (setq *{robot_name}* (instance {robot_name}-robot :init)))",
        file=fp,
    )
    print("\n\n", end="", file=fp)
    print(f"(defclass {robot_name}-robot", file=fp)
    print("  :super euscollada-robot", file=fp)
    print("  :slots (;; link names", file=fp)
    print("          " + " ".join(link_list), file=fp)
    print("          ;; joint names", file=fp)
    print("          " + " ".join(joint_names), file=fp)
    print("          ;; sensor names", file=fp)
    print("          ;; non-default limb names", file=fp)
    if config_yaml_path is not None:
        import io
        dummy_fp = io.StringIO()
        limb_names_from_yaml = read_config_from_yaml(r, config_yaml_path, fp=dummy_fp)
        # robot-model parent class already defines these slots, so exclude them
        parent_class_slots = ["torso", "larm", "rarm", "lleg", "rleg", "head"]
        for limb in limb_names_from_yaml:
            if limb in parent_class_slots:
                continue
            # Add only non-standard limbs to avoid duplication with parent class
            limb_slot_names.append(limb)
            print(f"          {limb} {limb}-end-coords {limb}-root-link", file=fp)
    print("          ))", file=fp)
    print("\n\n", end="", file=fp)
    print(f"(defmethod {robot_name}-robot", file=fp)
    print("  (:init", file=fp)
    print("   (&rest args)", file=fp)
    print("   (let ()", file=fp)
    print(f'     (send-super* :init :name "{robot_name}" args)', file=fp)
    print("\n\n", file=fp)

    for link in r.link_list:
        print_link(link, inertial=r.urdf_robot_model.link_map[link.name].inertial, fp=fp)

    add_link_suffix = True
    checked_pairs = {}
    for link in r.link_list:
        for child_link in link.child_links:
            if checked_pairs.get((link.name, child_link.name)) or checked_pairs.get(
                (child_link.name, link.name)
            ):
                continue
            if add_link_suffix:
                print(f"     (send {link.name}_lk :assoc {child_link.name}_lk)", file=fp)
            else:
                print(f"     (send {link.name} :assoc {child_link.name})", file=fp)
            checked_pairs[(link.name, child_link.name)] = True
    if add_link_suffix:
        print(f"     (send self :assoc {r.root_link.name}_lk)", file=fp)
    else:
        print(f"     (send self :assoc {r.root_link.name})", file=fp)

    for j in collect_all_joints_of_robot(r):
        print_joint(j, fp=fp)
    print_mimic_joints(r, fp=fp)
    limb_names = print_end_coords(r, config_yaml_path, fp=fp)

    # Use limb_slot_names for non-standard limbs if YAML was provided
    # Otherwise use limb_names from print_end_coords
    if config_yaml_path is not None and limb_slot_names:
        print_unique_limbs(limb_slot_names, fp=fp)
    else:
        print_unique_limbs(limb_names, fp=fp)

    for link in r.link_list:
        print_geometry(link, simplify_vertex_clustering_voxel_size, fp=fp)
    print("  )", file=fp)
    print(file=fp)
    print(
        f'(provide :{robot_name} "({socket.gethostname()} {platform.platform()}) at {current_time_str}")',
        file=fp,
    )

    if tmp_yaml_path and os.path.exists(tmp_yaml_path):
        os.remove(tmp_yaml_path)
