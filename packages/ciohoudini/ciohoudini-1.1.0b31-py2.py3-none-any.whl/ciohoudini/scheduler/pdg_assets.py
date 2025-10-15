"""
Module for managing assets in the Conductor plugin for Houdini.
"""

import hou
import pxr.UsdUtils
import re
import os
import platform
from ciopath.gpath_list import PathList, GLOBBABLE_REGEX
from ciopath.gpath import Path
from ciohoudini import common, rops
from ciohoudini.util import rop_error_handler

try:
    import ciocore.loggeria
    logger = ciocore.loggeria.get_conductor_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Failed to import ciocore.loggeria; using default logger.")

ADDITIONAL_PATH_PARMS = {
    # === LOPs (Solaris/USD) ===
    'Lop/reference::2.0': ('filepath1',),
    'Lop/usdrender_rop': ('lopoutput',),
    'Lop/layer': ('filepath',),
    'Lop/sublayer': ('filepath',),
    'Lop/payload': ('filepath',),
    'Lop/materiallibrary': ('filepath',),
    'Lop/file': ('filepath',),

    # === SOPs (Geometry / FX / Volumes) ===
    'Sop/file': ('file',),
    'Sop/alembic': ('fileName',),
    'Sop/vm_geo_alembic': ('attribfile',),
    'Sop/attribfrommap': ('file',),
    'Sop/volume': ('file',),
    'Sop/mdd': ('file',),
    'Sop/heightfield_file': ('file',),
    'Sop/pointcloudiso': ('file',),
    'Sop/bgeo': ('file',),
    'Sop/hfile': ('file',),
    'Sop/image': ('filename',),
    'Sop/trace': ('input',),
    'Sop/lineart': ('image',),
    'Sop/pic': ('filename',),

    # === SHOPs / MATs / VOPs (Shading & Lighting) ===
    'Shop/arnold_image': ('filename',),
    'Vop/arnold::image': ('filename',),
    'Shop/arnold_light': ('filename',),
    'Light/arnold_light': ('filename',),
    'Vop/texture': ('map',),
    'Vop/v_texture': ('map',),
    'Light/envlight': ('env_map',),
    'Vop/materialx/mtlximage': ('file',),
    'Vop/arnold::procedural': ('filename',),
    'Vop/arnold::volume': ('filename',),
    'Shop/pxrtexture': ('filename',),
    'Vop/pxrTexture': ('filename',),

    # === Redshift ===
    'Vop/redshift::TextureSampler': ('tex0', 'tex1', 'tex2', 'tex3'),
    'Light/redshift_lightDome': ('tex0',),
    'Light/redshift_IES': ('profile',),
    'Object/redshift_proxy': ('fileName',),
    'Sop/redshift_volume': ('fileName',),

    # === Karma ===
    'Light/karmadomelight::1.0': ('texture',),

    # === ROPs / Drivers ===
    'Driver/geometry': ('sopoutput',),
    'Driver/alembic': ('filename',),
    'Driver/filmboxfbx': ('output',),
    'Driver/mantra': ('vm_picture', 'vm_deepresolver_file'),
    'Driver/usd': ('usdoutput',),
    'Driver/karma': ('picture',),
    'Driver/Redshift_ROP': ('RS_outputFileNamePrefix',),
    'Driver/ifd': ('vm_picture',),
    'Driver/rop_vdbsequence': ('vdb_file_path',),

    # === COPs (Compositing) ===
    'Cop/file': ('filename',),
    'Cop/rop_file_output': ('copoutput',),
    'Cop/composite': ('inputfile',),
    'Cop/generate_thumbnail': ('thumbnail_path',),

    # === CHOPs (Channel / Audio) ===
    'Chop/file': ('file',),
    'Chop/sound': ('file',),
    'Chop/record': ('filename',),
}

# Define forbidden evaluated paths that would cause system-wide scans
forbidden_evaluated_paths = [
    # ========== UNIX/LINUX/MACOS ROOT PATHS ==========
    "/",  # Root directory
    "\\",  # Backslash (might be interpreted as root on some systems)
    "\\/",  # Mixed slashes
    "//",  # Double slash root

    # ========== WINDOWS DRIVE ROOTS ==========
    # Common drive letters
    "C:/", "C:\\", "C:",
    "D:/", "D:\\", "D:",
    "E:/", "E:\\", "E:",
    "F:/", "F:\\", "F:",
    "G:/", "G:\\", "G:",
    "H:/", "H:\\", "H:",
    "I:/", "I:\\", "I:",
    "J:/", "J:\\", "J:",
    "K:/", "K:\\", "K:",
    "L:/", "L:\\", "L:",
    "M:/", "M:\\", "M:",
    "N:/", "N:\\", "N:",
    "O:/", "O:\\", "O:",
    "P:/", "P:\\", "P:",
    "Q:/", "Q:\\", "Q:",
    "R:/", "R:\\", "R:",
    "S:/", "S:\\", "S:",
    "T:/", "T:\\", "T:",
    "U:/", "U:\\", "U:",
    "V:/", "V:\\", "V:",
    "W:/", "W:\\", "W:",
    "X:/", "X:\\", "X:",
    "Y:/", "Y:\\", "Y:",
    "Z:/", "Z:\\", "Z:",

    # ========== RELATIVE PATH PROBLEMATIC CASES ==========
    ".",  # Current directory
    "..",  # Parent directory
    "./",  # Current directory with slash
    "../",  # Parent directory with slash
    ".\\",  # Current directory with backslash
    "..\\",  # Parent directory with backslash

    # ========== WILDCARD-ONLY PATTERNS ==========
    "*",  # Single wildcard
    "**",  # Double wildcard (recursive)
    "*.*",  # All files pattern
    "/*",  # Root with wildcard
    "\\*",  # Root with wildcard (Windows)

    # ========== EMPTY OR WHITESPACE ==========
    "",  # Empty string
    " ",  # Single space
    "  ",  # Multiple spaces
    "\t",  # Tab character
    "\n",  # Newline

    # ========== MACOS SPECIFIC ==========
    "/Volumes/",  # Volumes root
    "/System/",  # System root
    "/Library/",  # Library root
    "/Users/",  # Users root (without specific user)

    # ========== LINUX SPECIFIC ==========
    "/home/",  # Home directory root (without specific user)
    "/usr/",  # Usr root
    "/var/",  # Var root
    "/opt/",  # Opt root
    "/mnt/",  # Mount point root

    # ========== WINDOWS SPECIFIC ==========
    "\\Windows\\",  # Windows system directory
    "\\Program Files\\",  # Program Files root
    "\\Users\\",  # Users root (without specific user)
    "/Windows/",  # Windows system directory (forward slash)
    "/Program Files/",  # Program Files root (forward slash)

    # ========== NETWORK PATHS ==========
    "\\\\",  # UNC path start (Windows network)
    "//",  # Network path (Unix/Samba)

    # ========== HOUDINI VARIABLES THAT DIDN'T EXPAND ==========
    "$HIP",  # Unexpanded HIP variable
    "$JOB",  # Unexpanded JOB variable
    "$HOME",  # Unexpanded HOME variable
    "`",  # Backtick (expression didn't evaluate)
    "``",  # Empty backtick expression
]

@rop_error_handler(error_message="Error resolving payload upload paths")
def resolve_payload(node, **kwargs):
    """
    Resolve the upload_paths field for the payload.
    """
    path_list = PathList()
    path_list.add(*auxiliary_paths(node))
    path_list.add(*extra_paths(node))
    path_list.add(*add_usd_file(node))

    #hda_files = collect_scene_hdas()
    #if hda_files:
    #    path_list.add(*hda_files)

    do_asset_scan = kwargs.get("do_asset_scan", False)
    if do_asset_scan:
        path_list.add(*scan_paths(node))

    if not path_list:
        return

    output_folder = ""
    expanded_path = expand_env_vars(node.parm('output_folder').eval())
    if expanded_path:
        output_folder = Path(expanded_path)

    current_assets = []
    seen = set()

    for path in path_list:
        path = str(path).replace("\\", "/")
        normalized = path.lower()
        if normalized not in seen:
            current_assets.append(path)
            seen.add(normalized)

    filtered_paths = [path for path in current_assets if not is_within_output_folder(path, output_folder)]

    if len(current_assets) > len(filtered_paths):
        node.parm("output_excludes").set(0)

    return {"upload_paths": filtered_paths}

@rop_error_handler(error_message="Error checking if path is within output folder")
def is_within_output_folder(path, output_folder):
    """
    Check if a path is within the output folder.
    """
    normalized_path = os.path.normpath(str(path))
    normalized_output_folder = os.path.normpath(str(output_folder))
    return normalized_path.startswith(normalized_output_folder)

@rop_error_handler(error_message="Error collecting auxiliary paths")
def auxiliary_paths(node, **kwargs):
    """
    Add the hip file, the OCIO file, and the render script to the list of assets.
    """
    path_list = PathList()
    path_list.add(hou.hipFile.path())
    ocio_file = os.environ.get("OCIO")
    if ocio_file:
        path_list.add(os.path.dirname(ocio_file))
    render_script = node.parm("render_script").eval()
    if render_script:
        render_script = "{}[{}]".format(render_script[:-1], render_script[-1])
        path_list.add(render_script)
    if path_list:
        path_list = _resolve_absolute_existing_paths(path_list)
    exclude_pattern = node.parm("asset_excludes").unexpandedString()
    if exclude_pattern:
        path_list.remove_pattern(exclude_pattern)
    return path_list

@rop_error_handler(error_message="Error while adding USD file")
def add_usd_file(node):
    """
    Add the USD file to the list of assets.
    """

    path_list = PathList()
    node_type = rops.get_node_type(node)
    node_list = rops.get_node_list("usd_filepath")
    if node_type in node_list:
        usd_file = rops.get_parameter_value(node, "usd_filepath", string_value=True)
        if usd_file:
            path_list.add(usd_file)
            if path_list:
                path_list = _resolve_absolute_existing_paths(path_list)

    return path_list

@rop_error_handler(error_message="Error collecting extra paths")
def extra_paths(node, **kwargs):
    """
    Collect extra paths from the node's extra assets list.
    """
    path_list = PathList()
    num = node.parm("extra_assets_list").eval()
    for i in range(1, num + 1):
        asset = node.parm("extra_asset_{:d}".format(i)).eval()
        asset = os.path.expandvars(asset)
        if asset:
            path_list.add(asset)
    if path_list:
        path_list = _resolve_absolute_existing_paths(path_list)
    return path_list

@rop_error_handler(error_message="Error reading scan configuration")
def read_scan_config(submitter_node):
    """
    Read configuration parameters for asset scanning.
    """
    regex_pattern = submitter_node.parm("asset_regex").unexpandedString()
    exclude_pattern = submitter_node.parm("asset_excludes").unexpandedString()
    REGEX = None
    if regex_pattern:
        REGEX = re.compile(regex_pattern, re.IGNORECASE)
    SEQUENCE_MARKER_REGEX = re.compile(r"\.\d+")
    sequence_like_token_regex = re.compile(r"<udim>|<u>|<v>|<u2>|<v2>|<obj_name>", re.IGNORECASE)
    return regex_pattern, exclude_pattern, REGEX, SEQUENCE_MARKER_REGEX, sequence_like_token_regex

@rop_error_handler(error_message="Error gathering parameters to scan")
def gather_parms_to_scan():
    """
    Gather parameters to scan for file references.
    """
    parms_to_scan = []
    parms_from_refs = _get_file_ref_parms()
    parms_to_scan.extend(parms_from_refs)
    parms_from_additional = _get_additional_file_ref_parms()
    parms_to_scan.extend(parms_from_additional)
    return parms_to_scan

@rop_error_handler(error_message="Error evaluating and expanding paths")
def evaluate_and_expand_paths(parms_to_scan):
    """
    Evaluate parameters and expand variables to collect raw paths.
    """
    raw_paths = PathList()
    processed_parms = set()
    raw_paths_temp = set()
    for parm in parms_to_scan:
        if parm is None or parm in processed_parms:
            continue
        processed_parms.add(parm)
        evaluated = parm.eval()
        if evaluated and isinstance(evaluated, str):
            expanded_str = hou.expandString(evaluated)
            if expanded_str:
                raw_paths_temp.add(expanded_str)
            else:
                raw_paths_temp.add(evaluated)
    for path_str in raw_paths_temp:
        raw_paths.add(path_str)
    return raw_paths

@rop_error_handler(error_message="Error scanning USD dependencies")
def scan_usd_dependencies(raw_paths):
    """
    Scan USD files for dependencies.
    """
    usd_dependencies = set()
    if pxr and pxr.UsdUtils:
        for file_path_obj in list(raw_paths):
            file_path = str(file_path_obj)
            is_usd = False
            if file_path and ('/' in file_path or '\\' in file_path):
                if os.path.isfile(file_path) and os.path.splitext(file_path)[-1].lower() in (".usd", ".usda", ".usdc", ".usdz"):
                    is_usd = True
            if is_usd:
                layers, assets, unresolved = pxr.UsdUtils.ComputeAllDependencies(file_path)
                for layer in layers:
                    if layer.realPath:
                        usd_dependencies.add(layer.realPath)
                usd_dependencies.update(set(assets))
        for dep_path in usd_dependencies:
            raw_paths.add(dep_path)
    return raw_paths

@rop_error_handler(error_message="Error filtering checked paths")
def filter_checked_paths(raw_paths):
    """
    Filter paths using check_path function.
    """
    checked_paths = PathList()
    for path_obj in raw_paths:
        path_str = str(path_obj)
        if check_path(path_str):
            checked_paths.add(path_obj)
    return checked_paths

@rop_error_handler(error_message="Error categorizing paths for resolution")
def categorize_paths_for_resolution(checked_paths, REGEX, SEQUENCE_MARKER_REGEX, sequence_like_token_regex):
    """
    Apply regex substitution and categorize paths for globbing or specific checks.
    """
    paths_for_globbing = PathList()
    paths_for_specific_check = PathList()
    if REGEX:
        for path_obj in checked_paths:
            path_str = str(path_obj)
            pth_sub_wildcarded = REGEX.sub(r"*", path_str)
            is_explicit_sequence = False
            if SEQUENCE_MARKER_REGEX.search(path_str) and pth_sub_wildcarded != path_str:
                is_explicit_sequence = True
            elif sequence_like_token_regex.search(path_str) and pth_sub_wildcarded != path_str:
                is_explicit_sequence = True
            if is_explicit_sequence:
                paths_for_globbing.add(pth_sub_wildcarded)
            else:
                paths_for_specific_check.add(path_str)
    else:
        paths_for_specific_check = checked_paths
    return paths_for_globbing, paths_for_specific_check

@rop_error_handler(error_message="Error resolving final paths")
def resolve_final_paths(paths_for_globbing, paths_for_specific_check):
    """
    Resolve paths with or without globbing.
    """
    final_resolved_paths = PathList()
    if paths_for_globbing:
        resolved_globbed_paths = _resolve_absolute_existing_paths(paths_for_globbing, perform_glob=True)
        final_resolved_paths.add(*list(resolved_globbed_paths))
    if paths_for_specific_check:
        resolved_specific_paths = _resolve_absolute_existing_paths(paths_for_specific_check, perform_glob=False)
        final_resolved_paths.add(*list(resolved_specific_paths))
    return final_resolved_paths

@rop_error_handler(error_message="Error applying exclude pattern")
def apply_exclude_pattern(final_resolved_paths, exclude_pattern):
    """
    Apply exclude pattern to filter out paths.
    """
    if exclude_pattern:
        final_resolved_paths.remove_pattern(exclude_pattern)
    return final_resolved_paths


@rop_error_handler(error_message="Error scanning paths for assets")
def scan_paths(submitter_node):
    """
    Scans the Houdini scene for assets referenced by various nodes, configured by the submitter node.
    """
    logger.debug("=" * 20 + " Starting Asset Scan " + "=" * 20)
    logger.debug(f"Submitter Node: {submitter_node.path()}")

    regex_pattern, exclude_pattern, REGEX, SEQUENCE_MARKER_REGEX, sequence_like_token_regex = read_scan_config(
        submitter_node)
    parms_to_scan = gather_parms_to_scan()
    raw_paths = evaluate_and_expand_paths(parms_to_scan)

    # ADD THIS: Log sample of raw paths to identify issues
    logger.debug(f"Raw paths count: {len(raw_paths)}")
    for idx, path in enumerate(list(raw_paths)[:5]):
        logger.debug(f"  Raw path sample {idx}: {path}")

    raw_paths = scan_usd_dependencies(raw_paths)

    # IMPORTANT: Filter early, before categorization and globbing
    checked_paths = filter_checked_paths(raw_paths)
    logger.debug(f"After check_path filter: {len(checked_paths)} paths")

    paths_for_globbing, paths_for_specific_check = categorize_paths_for_resolution(checked_paths, REGEX,
                                                                                   SEQUENCE_MARKER_REGEX,
                                                                                   sequence_like_token_regex)

    logger.debug(f"Paths for globbing: {len(paths_for_globbing)}")
    logger.debug(f"Paths for specific check: {len(paths_for_specific_check)}")

    final_resolved_paths = resolve_final_paths(paths_for_globbing, paths_for_specific_check)
    final_resolved_paths = apply_exclude_pattern(final_resolved_paths, exclude_pattern)

    logger.debug("=" * 20 + " Asset Scan Finished " + "=" * 20)
    logger.debug(f">>> Found {len(final_resolved_paths)} final asset paths.")
    return final_resolved_paths

@rop_error_handler(error_message="Error retrieving file reference parameters")
def _get_file_ref_parms_original():
    """
    Retrieve file reference parameters from the Houdini scene.
    """
    parms = []
    refs = hou.fileReferences()
    for parm, ref_path in refs:
        if parm:
            node = parm.node()
            print(f"Node: {node.path()}, Type: {node.type().name()}, Path: {ref_path}")
            node_type_name = parm.node().type().nameWithCategory()
            if not node_type_name.startswith("conductor::"):
                parms.append(parm)
    return parms


@rop_error_handler(error_message="Error retrieving file reference parameters")
def _get_file_ref_parms():
    """
    Retrieve file reference parameters from the Houdini scene.
    """
    parms = []
    refs = hou.fileReferences()

    for parm, ref_path in refs:
        if parm:
            node_type_name = parm.node().type().nameWithCategory()
            if not node_type_name.startswith("conductor::"):

                # Check if parameter evaluates to a forbidden path
                try:
                    evaluated = parm.eval()

                    # Skip if evaluated value is in forbidden list
                    if evaluated in forbidden_evaluated_paths:
                        logger.debug(
                            f"Skipping forbidden path - Node: {parm.node().path()}, Parm: {parm.name()}, Value: '{evaluated}'")
                        continue

                    # Additional check: Skip if it's a very short path (likely problematic)
                    if isinstance(evaluated, str) and len(evaluated) <= 3:
                        # Exception: Allow proper relative paths like "./", "../"
                        if evaluated not in ["./", "../", ".\\", "..\\"]:
                            if "/" in evaluated or "\\" in evaluated or ":" in evaluated:
                                logger.debug(
                                    f"Skipping suspiciously short path - Node: {parm.node().path()}, Parm: {parm.name()}, Value: '{evaluated}'")
                                continue

                    # Additional check: Skip if path is just a drive letter pattern
                    if isinstance(evaluated, str) and len(evaluated) == 2 and evaluated[1] == ':':
                        logger.debug(
                            f"Skipping drive letter only - Node: {parm.node().path()}, Parm: {parm.name()}, Value: '{evaluated}'")
                        continue

                except Exception as e:
                    logger.debug(f"Error evaluating parameter {parm.path()}: {e}")
                    continue

                parms.append(parm)

    return parms

@rop_error_handler(error_message="Error retrieving additional file reference parameters")
def _get_additional_file_ref_parms():
    """
    Retrieve additional file reference parameters based on node types.
    """
    parms = []
    all_categories = hou.nodeTypeCategories()
    for node_type_key, node_parms_tuple in ADDITIONAL_PATH_PARMS.items():
        category_name_str = None
        type_name_with_version = None
        if '/' in node_type_key:
            parts = node_type_key.split('/', 1)
            category_name_str = parts[0]
            type_name_with_version = parts[1]
        else:
            continue
        type_name_base = type_name_with_version.split('::')[0]
        category_obj = all_categories.get(category_name_str)
        if not category_obj:
            continue
        node_type_obj = hou.nodeType(category_obj, type_name_base)
        if node_type_obj is None:
            continue
        instances = node_type_obj.instances()
        if not instances:
            continue
        for node_instance in instances:
            for parm_name in node_parms_tuple:
                additional_parm = node_instance.parm(parm_name)

                if additional_parm:
                    evaluated = additional_parm.eval()
                    if evaluated in forbidden_evaluated_paths:
                        print(f"Skipping additional parm with value {evaluated}")
                        continue

                    parms.append(additional_parm)
    return parms

@rop_error_handler(error_message="Error clearing all assets")
def clear_all_assets(node, **kwargs):
    """
    Clear all extra assets from the node.
    """
    node.parm("extra_assets_list").set(0)

@rop_error_handler(error_message="Error browsing for files")
def browse_files(node, **kwargs):
    """
    Browse for files to add to the assets list.
    """
    files = hou.ui.selectFile(
        title="Browse for files to upload",
        collapse_sequences=True,
        file_type=hou.fileType.Any,
        multiple_select=True,
        chooser_mode=hou.fileChooserMode.Read,
    )
    if not files:
        return
    files = [f.strip() for f in files.split(";") if f.strip()]
    add_entries(node, *files)

@rop_error_handler(error_message="Error browsing for folder")
def browse_folder(node, **kwargs):
    """
    Browse for a folder to add to the assets list.
    """
    files = hou.ui.selectFile(title="Browse for folder to upload", file_type=hou.fileType.Directory)
    if not files:
        return
    files = [f.strip() for f in files.split(";") if f.strip()]
    add_entries(node, *files)

@rop_error_handler(error_message="Error adding asset entries")
def add_entries(node, *entries):
    """
    Add asset entries to the node's extra assets list.
    """
    path_list = PathList()
    num = node.parm("extra_assets_list").eval()
    for i in range(1, num + 1):
        asset = node.parm("extra_asset_{:d}".format(i)).eval()
        asset = os.path.expandvars(asset)
        if asset:
            path_list.add(asset)
    for entry in entries:
        path_list.add(entry)
    paths = [p.fslash() for p in path_list]
    node.parm("extra_assets_list").set(len(paths))
    for i, arg in enumerate(paths):
        index = i + 1
        node.parm("extra_asset_{:d}".format(index)).set(arg)

@rop_error_handler(error_message="Error removing asset")
def remove_asset(node, index):
    """
    Remove an asset from the extra assets list by index.
    """
    curr_count = node.parm("extra_assets_list").eval()
    for i in range(index + 1, curr_count + 1):
        from_parm = node.parm("extra_asset_{}".format(i))
        to_parm = node.parm("extra_asset_{}".format(i - 1))
        to_parm.set(from_parm.unexpandedString())
    node.parm("extra_assets_list").set(curr_count - 1)

@rop_error_handler(error_message="Error adding HDA paths")
def add_hdas(node, **kwargs):
    """
    Add HDA paths to the assets list.
    """
    hda_paths = [hda.libraryFilePath() for hda in common.get_plugin_definitions()]
    if not hda_paths:
        return
    add_entries(node, *hda_paths)


@rop_error_handler(error_message="Error resolving absolute existing paths")
def _resolve_absolute_existing_paths(path_list_input, perform_glob=True):
    """
    Resolve absolute paths and optionally perform globbing.
    """
    logger.debug(
        f"    >>> _resolve_absolute_existing_paths called with {len(path_list_input)} items. Perform Glob: {perform_glob}")

    # ADD THIS: Log what paths are coming in
    for idx, path in enumerate(path_list_input):
        if idx < 10:  # Log first 10 to avoid spam
            logger.debug(f"        Input path {idx}: {path}")

    hip = hou.getenv("HIP")
    job = hou.getenv("JOB")
    internals = ("op:", "temp:")
    resolved = PathList()

    for path_obj_or_str in path_list_input:
        if isinstance(path_obj_or_str, str):
            current_path = Path(path_obj_or_str)
        else:
            current_path = path_obj_or_str

        if current_path.relative:
            if not str(current_path).startswith(internals):
                if hip:
                    resolved.add(os.path.join(hip, str(current_path)))
                if job:
                    resolved.add(os.path.join(job, str(current_path)))
        else:
            resolved.add(current_path)

    resolved.remove_missing()

    # ADD THIS: Filter BEFORE globbing
    if perform_glob:
        logger.debug(f"    Pre-glob filtering: {len(resolved)} paths")

        # Filter out problematic paths BEFORE globbing
        pre_filtered = PathList()
        for path_obj in resolved:
            path_str = str(path_obj)
            if check_path(path_str):
                pre_filtered.add(path_obj)
            else:
                logger.debug(f"    PRE-GLOB FILTER: Skipped {path_str}")

        logger.debug(f"    After pre-glob filter: {len(pre_filtered)} paths remain")
        resolved = pre_filtered

        # Now glob only the safe paths
        resolved.glob()

    logger.debug(f"    <<< _resolve_absolute_existing_paths returning {len(resolved)} items.")
    return resolved

@rop_error_handler(error_message="Error expanding environment variables")
def expand_env_vars(path):
    """
    Expand environment variables in a path.
    """
    return os.path.expandvars(path)


def check_path(file_path):
    """
    Check if a file path is valid for inclusion across all platforms.
    CRITICAL: This runs BEFORE globbing to prevent scanning system directories.
    """
    if not file_path:
        return False

    # Normalize path separators
    file_path_normalized = file_path.replace("\\", "/")

    # ========== EARLY REJECTIONS (before expensive checks) ==========

    # Skip wildcard patterns that would glob system directories
    if "*" in file_path:
        # Check if wildcard path would scan system directories
        base_dir = file_path_normalized.split('*')[0].rstrip('/')
        if not base_dir or base_dir in ['/', '/System', '/Library', '/usr', 'C:', 'D:']:
            logger.debug(f"Rejecting broad wildcard pattern: {file_path}")
            return False

    # Skip Houdini internal paths immediately
    internals = ("op:", "temp:", "opdef:")
    if file_path_normalized.startswith(internals):
        return False

    # Skip temp directories immediately
    if file_path_normalized.startswith("/tmp/") or "houdini_temp" in file_path_normalized:
        return False

    # ========== PLATFORM-SPECIFIC SYSTEM DIRECTORY REJECTION ==========

    current_platform = platform.system()

    # Define system directories to reject
    system_dir_prefixes = []

    if current_platform == 'Windows':
        system_dir_prefixes = [
            '/Windows/', '\\Windows\\',
            '/Program Files/', '\\Program Files\\',
            '/Program Files (x86)/', '\\Program Files (x86)\\',
            '/ProgramData/', '\\ProgramData\\',
            '/System32/', '\\System32\\',
        ]
    elif current_platform == 'Darwin':  # macOS
        system_dir_prefixes = [
            '/System/',
            '/Library/Developer/',
            '/usr/share/man/',
            '/private/var/',
            '/dev/',
            '/Volumes/Data/System/',
            '/Volumes/Data/Library/',
            '/AppleInternal/',
        ]
    elif current_platform == 'Linux':
        system_dir_prefixes = [
            '/sys/',
            '/proc/',
            '/dev/',
            '/run/',
            '/usr/share/man/',
            '/lib/modules/',
            '/boot/',
        ]

    # Early rejection of system directories (before any file existence checks)
    for sys_dir in system_dir_prefixes:
        if sys_dir in file_path or file_path_normalized.startswith(sys_dir):
            return False

    # ========== COLON VALIDATION ==========

    if current_platform == 'Windows':
        colon_count = file_path.count(':')
        if colon_count > 1 or (colon_count == 1 and not (len(file_path) > 1 and file_path[1] == ':')):
            return False
    else:
        # Unix: reject ANY colons
        if ':' in file_path:
            return False

    # ========== HIP FOLDER CHECK ==========

    hip_folder = hou.getenv("HIP")
    if hip_folder:
        try:
            normalized_file_path = os.path.normpath(os.path.abspath(file_path))
            normalized_hip_folder = os.path.normpath(os.path.abspath(hip_folder))
            if normalized_file_path == normalized_hip_folder:
                return False
        except (OSError, ValueError):
            return False

    # ========== EXISTENCE CHECK (only for non-wildcard paths) ==========

    if '*' not in file_path:
        try:
            if not os.path.exists(file_path):
                return False
        except (OSError, ValueError):
            return False

    return True


@rop_error_handler(error_message="Error diagnosing scan paths")
def diagnose_scan_sources():
    """
    Diagnostic function to identify which parameters are returning problematic paths.
    Call this manually when debugging.
    """
    logger.info("=" * 60)
    logger.info("DIAGNOSTIC: Analyzing path sources")
    logger.info("=" * 60)

    parms_to_scan = gather_parms_to_scan()

    for parm in parms_to_scan[:20]:  # Check first 20
        if parm is None:
            continue

        try:
            evaluated = parm.eval()
            if evaluated and isinstance(evaluated, str):
                expanded_str = hou.expandString(evaluated)
                node_name = parm.node().path()
                parm_name = parm.name()

                logger.info(f"\nParameter: {node_name}.{parm_name}")
                logger.info(f"  Raw value: {evaluated}")
                logger.info(f"  Expanded: {expanded_str}")

                # Check if this would cause problems
                if '/' in expanded_str or '\\' in expanded_str:
                    if not check_path(expanded_str):
                        logger.warning(f"  ⚠️  PROBLEMATIC PATH DETECTED!")

        except Exception as e:
            logger.error(f"Error evaluating {parm.path()}: {e}")

    logger.info("=" * 60)

def collect_scene_hdas():
    """
    Collect only user/project HDA library files used in the current Houdini scene.
    Excludes system HDAs, built-in HDAs, and package HDAs.

    Returns:
        list: List of user HDA file paths that exist on disk
    """
    hda_paths = set()

    # Get system directories to exclude
    hfs = hou.getenv("HFS") or ""  # Houdini installation directory
    hh = hou.getenv("HH") or ""  # Houdini home directory
    houdini_user_prefs = hou.getenv("HOUDINI_USER_PREF_DIR") or ""

    # Normalize paths for comparison
    if hfs:
        hfs = os.path.normpath(hfs).lower().replace("\\", "/")
    if hh:
        hh = os.path.normpath(hh).lower().replace("\\", "/")
    if houdini_user_prefs:
        houdini_user_prefs = os.path.normpath(houdini_user_prefs).lower().replace("\\", "/")

    # Common system/package directories to exclude
    exclude_dirs = []

    # Add Houdini installation directories
    if hfs:
        exclude_dirs.extend([
            hfs,  # Main Houdini installation
            os.path.join(hfs, "houdini").lower().replace("\\", "/"),
            os.path.join(hfs, "otls").lower().replace("\\", "/"),
        ])

    # Add common package locations
    exclude_dirs.extend([
        "/applications/houdini",  # Mac Houdini installation
        "/opt/hfs",  # Linux Houdini installation
        "/opt/sidefx",  # Linux SideFX installation
        "c:/program files/side effects software",  # Windows
    ])

    # Package directories to exclude (case-insensitive patterns)
    exclude_patterns = [
        "sidefxlabs",
        "sidefx_packages",
        "aelib",
        "qlib",
        "mops",
        "conductor_scheduler",  # Exclude conductor's own HDAs
        "/packages/",  # Generic packages directory
        "/houdini/otls/",  # Built-in otls
    ]

    # Known system HDA filenames to exclude
    system_hda_names = [
        "OPlib",  # Built-in Houdini HDAs (OPlibSop.hda, OPlibTop.hda, etc.)
        "SideFX_Labs",  # SideFX Labs
        "conductor_scheduler",  # Conductor's own HDA
    ]

    logger.debug("Scanning scene for user HDAs...")
    logger.debug(f"Excluding system directories: {exclude_dirs[:3]}...")  # Show first 3 for debugging

    try:
        # Scan all nodes in the scene
        for node in hou.node("/").allSubChildren():
            try:
                node_type = node.type()
                definition = node_type.definition()

                # Check if this node uses an HDA
                if definition:
                    library_path = definition.libraryFilePath()

                    # Skip embedded HDAs (they don't need file uploads)
                    if not library_path or library_path.startswith("Embedded"):
                        continue

                    # Normalize the path
                    library_path = os.path.normpath(library_path).replace("\\", "/")
                    library_path_lower = library_path.lower()

                    # Check if file exists
                    if not os.path.exists(library_path):
                        logger.debug(f"Skipping non-existent HDA: {library_path}")
                        continue

                    # Get the filename without path
                    hda_filename = os.path.basename(library_path)

                    # Skip if it's a known system HDA by name
                    is_system_hda = False
                    for system_name in system_hda_names:
                        if hda_filename.startswith(system_name):
                            logger.debug(f"Skipping system HDA: {hda_filename}")
                            is_system_hda = True
                            break

                    if is_system_hda:
                        continue

                    # Skip if it's in a system directory
                    is_in_system_dir = False
                    for exclude_dir in exclude_dirs:
                        if exclude_dir and library_path_lower.startswith(exclude_dir.lower()):
                            logger.debug(f"Skipping HDA in system directory: {library_path}")
                            is_in_system_dir = True
                            break

                    if is_in_system_dir:
                        continue

                    # Skip if path contains excluded patterns
                    is_excluded_pattern = False
                    for pattern in exclude_patterns:
                        if pattern.lower() in library_path_lower:
                            logger.debug(f"Skipping HDA matching excluded pattern '{pattern}': {library_path}")
                            is_excluded_pattern = True
                            break

                    if is_excluded_pattern:
                        continue

                    # Additional check: Skip HDAs in Houdini's Frameworks directory (Mac)
                    if "/frameworks/houdini.framework/" in library_path_lower:
                        logger.debug(f"Skipping HDA in Houdini Frameworks: {library_path}")
                        continue

                    # Additional check: Skip HDAs in the user's preferences unless they're project HDAs
                    if houdini_user_prefs and library_path_lower.startswith(houdini_user_prefs):
                        # Could be a user HDA, but check if it's in a packages subdirectory
                        relative_to_prefs = library_path_lower[len(houdini_user_prefs):].lstrip("/")
                        if relative_to_prefs.startswith("packages/"):
                            logger.debug(f"Skipping HDA in user packages: {library_path}")
                            continue

                    # If we made it here, it's likely a user/project HDA
                    hda_paths.add(library_path)
                    logger.debug(f"Found user HDA: {node.path()} -> {library_path}")

            except Exception as e:
                # Skip nodes that might not have proper type definitions
                continue

    except Exception as e:
        logger.warning(f"Error scanning for HDAs: {e}")
        # Don't fail entirely if HDA scanning has issues

    hda_list = list(hda_paths)

    # Final validation: Make sure we're only including reasonable paths
    filtered_hdas = []
    for hda_path in hda_list:
        # Additional safety check - only include HDAs that seem like user files
        # Typically user HDAs are in project directories, documents, or specific work areas
        path_lower = hda_path.lower()

        # Skip anything that still looks like a system path
        looks_like_system = any([
            "/houdini/houdini" in path_lower,  # Houdini installation
            "/applications/houdini" in path_lower,  # Mac apps
            "/program files" in path_lower,  # Windows programs
            "/opt/hfs" in path_lower,  # Linux installation
            "/opt/sidefx" in path_lower,  # Linux SideFX
        ])

        if not looks_like_system:
            filtered_hdas.append(hda_path)
        else:
            logger.debug(f"Final filter: Removing system-looking HDA: {hda_path}")

    if filtered_hdas:
        logger.debug(f"Found {len(filtered_hdas)} user HDA file(s) in scene")
        for hda in filtered_hdas:
            logger.debug(f"  User HDA: {os.path.basename(hda)}")
            logger.debug(f"    Path: {hda}")
    else:
        logger.debug("No user HDA files found in scene")

    return filtered_hdas


# Alternative implementation with more aggressive filtering
def collect_scene_hdas_strict():
    """
    Stricter version that only includes HDAs from specific project directories.
    Use this if the standard version still includes unwanted HDAs.

    Returns:
        list: List of user HDA file paths that exist on disk
    """
    hda_paths = set()

    # Get project-related directories
    hip_dir = hou.getenv("HIP") or ""  # Current hip file directory
    job_dir = hou.getenv("JOB") or ""  # Job directory

    # Define allowed directories (where user HDAs should be)
    # You can customize this list based on your pipeline
    allowed_patterns = []

    # Add current project directory
    if hip_dir:
        hip_parent = os.path.dirname(hip_dir)
        allowed_patterns.extend([
            hip_dir,  # Current hip directory
            hip_parent,  # Parent of hip directory
            os.path.join(hip_parent, "hda"),  # Common HDA subdirectory
            os.path.join(hip_parent, "otls"),  # Common otls subdirectory
        ])

    # Add job directory if set
    if job_dir:
        allowed_patterns.extend([
            job_dir,
            os.path.join(job_dir, "hda"),
            os.path.join(job_dir, "otls"),
        ])

    # Add common user project locations
    user_home = os.path.expanduser("~")
    allowed_patterns.extend([
        os.path.join(user_home, "documents"),  # User documents
        os.path.join(user_home, "projects"),  # User projects
        os.path.join(user_home, "work"),  # Work directory
        "/mnt/",  # Network mounts (Linux)
        "/volumes/",  # Network mounts (Mac)
        "//",  # Network shares (Windows)
    ])

    # Normalize allowed patterns
    allowed_patterns = [os.path.normpath(p).lower().replace("\\", "/")
                        for p in allowed_patterns if p]

    logger.debug("Using strict HDA collection mode")
    logger.debug(f"Allowed directories: {allowed_patterns[:5]}...")  # Show first 5

    try:
        # Scan all nodes in the scene
        for node in hou.node("/").allSubChildren():
            try:
                node_type = node.type()
                definition = node_type.definition()

                # Check if this node uses an HDA
                if definition:
                    library_path = definition.libraryFilePath()

                    # Skip embedded HDAs
                    if not library_path or library_path.startswith("Embedded"):
                        continue

                    # Normalize the path
                    library_path = os.path.normpath(library_path).replace("\\", "/")
                    library_path_lower = library_path.lower()

                    # Check if file exists
                    if not os.path.exists(library_path):
                        continue

                    # Check if it's in an allowed directory
                    is_allowed = False
                    for allowed_dir in allowed_patterns:
                        if library_path_lower.startswith(allowed_dir):
                            is_allowed = True
                            logger.debug(f"HDA in allowed directory: {library_path}")
                            break

                    if is_allowed:
                        hda_paths.add(library_path)
                        logger.debug(f"Found user HDA: {node.path()} -> {library_path}")
                    else:
                        logger.debug(f"Skipping HDA outside allowed directories: {library_path}")

            except Exception:
                continue

    except Exception as e:
        logger.warning(f"Error scanning for HDAs: {e}")

    hda_list = list(hda_paths)

    if hda_list:
        logger.debug(f"Found {len(hda_list)} user HDA file(s) in scene (strict mode)")
        for hda in hda_list:
            logger.debug(f"  User HDA: {os.path.basename(hda)}")

    return hda_list