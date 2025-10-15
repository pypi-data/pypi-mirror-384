import os
import json
import traceback
import pdg
import hou
import socket
import datetime
import time
import re
import hdefereval
# import logging
import ciocore.loggeria

from ciopath.gpath_list import PathList
from ciohoudini import (
    project,
    instances,
    software,
    environment,
    frames,
    rops,
    util,
)
from ciohoudini.submission_dialog import SubmissionDialog
from ciohoudini.scheduler import pdg_assets
from ciohoudini.scheduler.pdg_utils import connect_to_conductor, configure_threading_environment, get_all_houdini_paths, get_houdini_path_additions

# Configure logger
logger = ciocore.loggeria.get_conductor_logger()


# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


def is_valid_upload_path(path):
    """Check if a path is valid for upload to Conductor

    Args:
        path: The path to validate

    Returns:
        bool: True if the path is valid for upload, False otherwise
    """
    if not path:
        return False

    # Convert to string and strip quotes if present
    path_str = str(path).strip().strip('"').strip("'")

    # Skip Houdini internal opdef: paths (test geometry, internal assets)
    if path_str.startswith("opdef:"):
        logger.debug(f"Skipping Houdini internal asset: {path_str}")
        return False

    # Skip op: paths (Houdini operator references)
    if path_str.startswith("op:"):
        logger.debug(f"Skipping Houdini operator reference: {path_str}")
        return False

    # Skip temp: paths (Houdini temp references)
    if path_str.startswith("temp:"):
        logger.debug(f"Skipping Houdini temp reference: {path_str}")
        return False

    # Skip & paths (Houdini channel references)
    if path_str.startswith("&"):
        logger.debug(f"Skipping Houdini channel reference: {path_str}")
        return False

    # Check if it's a valid file system path
    if not os.path.exists(path_str):
        logger.debug(f"Skipping non-existent path: {path_str}")
        return False

    return True


def filter_upload_paths(paths):
    """Filter a list of paths to remove invalid entries

    Args:
        paths: List or set of paths to filter

    Returns:
        list: Filtered list of valid paths
    """
    filtered = []
    seen = set()

    for path in paths:
        if is_valid_upload_path(path):
            # Normalize the path
            path_str = str(path).strip().strip('"').strip("'")
            normalized = os.path.normpath(path_str).replace("\\", "/")

            # Avoid duplicates
            if normalized.lower() not in seen:
                filtered.append(normalized)
                seen.add(normalized.lower())

    return filtered


class PDGConductorScheduler:
    """PDG Conductor Scheduler for managing work item submission to Conductor"""

    def __init__(self, scheduler_context, node_path=None, topnet_path=None):
        """Initialize the scheduler with context

        Args:
            scheduler_context: The PDG scheduler context (self from the original script)
            node_path: Optional path to the conductor scheduler node
            topnet_path: Optional path to the TOP network container
        """
        self.context = scheduler_context
        self.script_dir = None

        # Initialize node attributes
        self.node_path = node_path
        self.node = None
        self.topnet_path = topnet_path
        self.topnet = None
        self.render_dir = None


        # Set the conductor scheduler node if path provided
        if self.node_path:
            self.node = hou.node(self.node_path)
            if not self.node:
                logger.warning(f"Could not find node at path: {self.node_path}")

        # Set the TOP network if path provided
        if self.topnet_path:
            self.topnet = hou.node(self.topnet_path)
            if not self.topnet:
                logger.warning(f"Could not find TOP network at path: {self.topnet_path}")
            # Verify it's actually a TOP network container
            elif not (hasattr(self.topnet, 'childTypeCategory') and
                      self.topnet.childTypeCategory() and
                      self.topnet.childTypeCategory().name() == "Top"):
                logger.warning(f"Node at {self.topnet_path} is not a TOP network container")
                self.topnet = None

        self.set_render_dir()


    def set_render_dir(self):
        self.render_dir = rops.get_parameter_value(self.node, "override_image_output")

        # self.render_dir = util.clean_path_without_stripping(self.render_dir)
        try:
            # Convert Houdini-style path to OS-compatible path
            self.render_dir = os.path.normpath(self.render_dir)
            # Ensure consistent forward slashes
            self.render_dir = self.render_dir.replace("\\", "/")
            if self.render_dir:
                self.render_dir = os.path.expandvars(self.render_dir)
        except Exception as e:
            logger.warning(f"Error collecting self.render_dir: {e}")

        logger.debug(f"Render directory: {self.render_dir}")
        logger.debug(f"Render directory exists: {os.path.exists(self.render_dir)}")


    def save_hip_file_safe(self, hip_file_path):
        """Thread-safe method to save HIP file

        Args:
            hip_file_path: Path where to save the HIP file

        Returns:
            bool: True if successful, False otherwise
        """

        def save_hip():
            try:
                hou.hipFile.save(hip_file_path)
                return True
            except Exception as e:
                logger.error(f"ERROR saving HIP file: {e}")
                return False

        # Check if we're already on the main thread
        if hou.isUIAvailable():
            # We need to use the main thread for GUI operations
            try:
                result = hdefereval.executeInMainThreadWithResult(save_hip)
                return result
            except Exception as e:
                logger.error(f"ERROR in executeInMainThreadWithResult: {e}")
                # Fallback: try saving directly if hdefereval fails
                try:
                    return save_hip()
                except:
                    return False
        else:
            # In batch mode (no UI), save directly
            return save_hip()

    def get_next_version_number(self, base_path):
        """Get the next available version number for the hip file

        Args:
            base_path: The base path (e.g., "/path/to/file.hip" or "/path/to/file_pdg_v0001.hip")

        Returns:
            int: The next available version number
        """
        dir_path = os.path.dirname(base_path)
        base_name_with_ext = os.path.basename(base_path)
        base_name = os.path.splitext(base_name_with_ext)[0]

        # Check if the file already has a version pattern and extract the base name
        existing_version_match = re.match(r"(.*)_pdg_v(\d{4})$", base_name)
        if existing_version_match:
            # File already has version, extract the base name without version
            clean_base_name = existing_version_match.group(1)
            current_version = int(existing_version_match.group(2))
        else:
            # File doesn't have version yet
            clean_base_name = base_name
            current_version = 0

        # Pattern to match existing versioned files with this base name
        pattern = f"{re.escape(clean_base_name)}_pdg_v(\\d{{4}})\\.hip"

        max_version = current_version

        # Check if directory exists and scan for existing versions
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                match = re.match(pattern, filename)
                if match:
                    version = int(match.group(1))
                    max_version = max(max_version, version)

        # Return the next version number
        return max_version + 1

    def create_versioned_hip_filename(self, original_hip_path):
        """Create a versioned hip filename based on the original path

        Args:
            original_hip_path: The original hip file path

        Returns:
            str: The versioned hip file path
        """
        dir_path = os.path.dirname(original_hip_path)
        base_name_with_ext = os.path.basename(original_hip_path)
        base_name = os.path.splitext(base_name_with_ext)[0]

        # Check if the file already has a version pattern
        existing_version_match = re.match(r"(.*)_pdg_v(\d{4})$", base_name)
        if existing_version_match:
            # File already has version, use the clean base name
            clean_base_name = existing_version_match.group(1)
        else:
            # File doesn't have version yet, use the full base name
            clean_base_name = base_name

        # Get the next version number using the clean base name
        next_version = self.get_next_version_number(original_hip_path)

        # Create the versioned filename
        versioned_filename = f"{clean_base_name}_pdg_v{next_version:04d}.hip"
        versioned_path = os.path.join(dir_path, versioned_filename)

        logger.debug(f"Original hip file: {original_hip_path}")
        logger.debug(f"Versioned hip file: {versioned_path}")
        logger.debug(f"Version number: {next_version}")

        return versioned_path

    def get_local_ip(self):
        """Try to get the local machine's IP address that's accessible from the network"""
        try:
            # Method 1: Connect to an external server and get the local address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            try:
                # Method 2: Get hostname and resolve it
                hostname = socket.gethostname()
                return socket.gethostbyname(hostname)
            except:
                # Fallback - you should replace this with your actual IP
                logger.warning("Could not determine local IP, using fallback 192.168.1.100")
                return "192.168.1.100"  # REPLACE WITH YOUR ACTUAL IP

    def get_topnet_path(self, pdg_node):
        """Get the path to the TOP network containing this PDG node

        Args:
            pdg_node: The PDG node whose TOP network we're looking for

        Returns:
            str or None: Path to the TOP network container, or None if not found
        """
        # If we already have a valid topnet_path, return it
        if self.topnet_path and self.topnet:
            logger.debug(f"Using cached TOP network path: {self.topnet_path}")
            return self.topnet_path

        # Try to get the TOP node from the PDG node
        try:
            topnode = pdg_node.topNode()
            if not topnode:
                logger.warning("Could not get TOP node from PDG node")
                return None

            # Get the Houdini node from the TOP node
            current_node = topnode
            if hasattr(topnode, 'houdiniNode'):
                current_node = topnode.houdiniNode
            elif hasattr(topnode, 'parent'):
                current_node = topnode.parent()

            if not current_node:
                logger.warning("Could not get Houdini node from TOP node")
                return None

            # Now traverse up the hierarchy to find the TOP network container
            logger.debug(f"Starting search for TOP network from: {current_node.path()}")

            while current_node is not None:
                # Check if this is a TOP network container
                # TOP network containers can contain TOP nodes (childTypeCategory is "Top")
                if (hasattr(current_node, 'childTypeCategory') and
                        current_node.childTypeCategory() and
                        current_node.childTypeCategory().name() == "Top"):
                    # Found the TOP network container
                    self.topnet_path = current_node.path()
                    self.topnet = current_node
                    logger.debug(f"Found TOP network container: {self.topnet_path}")
                    logger.debug(f"  Type: {current_node.type().name()}")
                    return self.topnet_path

                # Move up to parent
                current_node = current_node.parent()

            logger.error("Could not find TOP network container in parent hierarchy")
            return None

        except Exception as e:
            logger.error(f"Error finding TOP network path: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

    def log_work_item_details(self, work_item):
        """Log detailed information about a work item"""
        logger.debug("────────────────────────────────────────────────────────────")
        logger.debug("Work Item Details:")
        logger.debug(f"  Name: {work_item.name}")
        logger.debug(f"  ID: {work_item.id}")
        logger.debug(f"  Index: {work_item.index}")

        # Safely get state
        try:
            state = str(work_item.state) if hasattr(work_item, 'state') else 'unknown'
            logger.debug(f"  State: {state}")
        except:
            logger.warning("  State: <error reading state>")

        logger.debug(f"  Node: {work_item.node.name}")

        # Safely get cook type
        try:
            cook_type = str(work_item.cookType) if hasattr(work_item, 'cookType') else 'unknown'
            logger.debug(f"  Cook Type: {cook_type}")
        except:
            logger.warning("  Cook Type: <error reading cook type>")

        # Safely get boolean properties
        try:
            is_static = work_item.isStatic if hasattr(work_item, 'isStatic') else 'unknown'
            logger.debug(f"  Is Static: {is_static}")
        except:
            logger.warning("  Is Static: <error>")

        try:
            is_frozen = work_item.isFrozen if hasattr(work_item, 'isFrozen') else 'unknown'
            logger.debug(f"  Is Frozen: {is_frozen}")
        except:
            logger.warning("  Is Frozen: <error>")

        try:
            priority = work_item.priority if hasattr(work_item, 'priority') else 'unknown'
            logger.debug(f"  Priority: {priority}")
        except:
            logger.warning("  Priority: <error>")

        try:
            has_frame = work_item.hasFrame if hasattr(work_item, 'hasFrame') else False
            logger.debug(f"  Has Frame: {has_frame}")
            if has_frame:
                logger.debug(f"  Frame: {work_item.frame}")
        except:
            logger.warning("  Has Frame: <error>")

        # Log attributes
        logger.debug("  Attributes:")
        try:
            for attr_name in work_item.attribNames():
                try:
                    # Try different methods to get attribute value
                    if hasattr(work_item, 'stringAttribValue'):
                        # Try string first as it's most common
                        attr_value = work_item.stringAttribValue(attr_name)
                        if attr_value:
                            logger.debug(f"    {attr_name}: {attr_value}")
                            continue

                    # Try generic attribValue
                    if hasattr(work_item, 'attribValue'):
                        attr_value = work_item.attribValue(attr_name)
                        logger.debug(f"    {attr_name}: {attr_value}")
                    else:
                        logger.warning(f"    {attr_name}: <no attribValue method>")
                except:
                    logger.warning(f"    {attr_name}: <unable to read>")
        except Exception as e:
            logger.error(f"  [ERROR] Could not get attribute names: {str(e)}")

        # Log dependencies
        try:
            dependencies = work_item.dependencies if hasattr(work_item, 'dependencies') else []
            if dependencies:
                logger.debug(f"  Dependencies ({len(dependencies)}):")
                for dep in dependencies:
                    dep_state = str(dep.state) if hasattr(dep, 'state') else 'unknown'
                    logger.debug(f"    - {dep.name} (ID: {dep.id}, State: {dep_state})")
        except Exception as e:
            logger.error(f"  [ERROR] Could not get dependencies: {str(e)}")

        # Log dependents
        try:
            dependents = work_item.dependents if hasattr(work_item, 'dependents') else []
            if dependents:
                logger.debug(f"  Dependents ({len(dependents)}):")
                for dep in dependents:
                    dep_state = str(dep.state) if hasattr(dep, 'state') else 'unknown'
                    logger.debug(f"    - {dep.name} (ID: {dep.id}, State: {dep_state})")
        except Exception as e:
            logger.error(f"  [ERROR] Could not get dependents: {str(e)}")

        logger.debug("────────────────────────────────────────────────────────────")

    def log_node_details(self, node):
        """Log detailed information about a PDG node"""
        logger.debug("┌────────────────────────────────────────────────────────────┐")
        logger.debug("│ PDG Node Details:                                            │")
        logger.debug("├────────────────────────────────────────────────────────────┤")
        logger.debug(f"│ Name: {node.name:<54} │")

        # Safely get node type
        try:
            node_type = node.type.name if hasattr(node, 'type') and hasattr(node.type, 'name') else 'unknown'
            logger.debug(f"│ Type: {node_type:<54} │")
        except:
            logger.warning("│ Type: <unknown>                                             │")

        # Safely get node path
        try:
            hou_node = node.houdiniNode if hasattr(node, 'houdiniNode') else None
            node_path = hou_node.path() if hou_node else 'N/A'
            # Truncate if too long
            if len(node_path) > 54:
                node_path = node_path[:51] + "..."
            logger.debug(f"│ Path: {node_path:<54} │")
        except:
            logger.warning("│ Path: <not available>                                       │")

        # Safely get node state
        try:
            node_state = str(node.state) if hasattr(node, 'state') else 'unknown'
            logger.debug(f"│ State: {node_state:<53} │")
        except:
            logger.warning("│ State: <unknown>                                            │")

        # Safely get work item counts
        try:
            wi_count = len(node.workItems) if hasattr(node, 'workItems') else 0
            logger.debug(f"│ Work Item Count: {wi_count:<43} │")
        except:
            logger.warning("│ Work Item Count: <error>                                    │")

        try:
            static_wi_count = len(node.staticWorkItems) if hasattr(node, 'staticWorkItems') else 0
            logger.debug(f"│ Static Work Items: {static_wi_count:<41} │")
        except:
            logger.warning("│ Static Work Items: <error>                                  │")

        # Safely get boolean states
        try:
            is_cooking = str(node.isCooking) if hasattr(node, 'isCooking') else 'unknown'
            logger.debug(f"│ Is Cooking: {is_cooking:<48} │")
        except:
            logger.warning("│ Is Cooking: <unknown>                                       │")

        try:
            is_generated = str(node.isGenerated) if hasattr(node, 'isGenerated') else 'unknown'
            logger.debug(f"│ Is Generated: {is_generated:<46} │")
        except:
            logger.warning("│ Is Generated: <unknown>                                     │")

        try:
            is_cooked = str(node.isCooked) if hasattr(node, 'isCooked') else 'unknown'
            logger.debug(f"│ Is Cooked: {is_cooked:<49} │")
        except:
            logger.warning("│ Is Cooked: <unknown>                                        │")

        logger.debug("└────────────────────────────────────────────────────────────┘")

    def log_pdg_graph_state(self, work_item):
        """Log the entire PDG graph state"""
        logger.debug("╔═══════════════════════════════════════════════════════════════╗")
        logger.debug("║                    PDG GRAPH STATE SNAPSHOT                    ║")
        logger.debug(
            f"║                 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}                 ║")
        logger.debug("╚═══════════════════════════════════════════════════════════════╝")

        # Get the graph context
        graph = work_item.node.context
        logger.debug(f"Graph Name: {graph.name}")

        # Try to get graph info
        try:
            graph_hou_node = graph.houdiniNode if hasattr(graph, 'houdiniNode') else None
            graph_path = graph_hou_node.path() if graph_hou_node else '<not available>'
            logger.debug(f"Graph Path: {graph_path}")
        except:
            logger.warning("Graph Path: <not available>")

        # Iterate through all nodes in the graph
        all_nodes = []
        try:
            # Different ways to get nodes depending on PDG version
            if hasattr(graph, 'nodes'):
                for node in graph.nodes:
                    all_nodes.append(node)
            elif hasattr(graph, 'nodeByName'):
                # Alternative: try to get nodes through the current node's graph
                current_node = work_item.node
                # This is a workaround - we'll just log the current node and its connections
                logger.debug("[INFO] Using alternative node discovery method")
                all_nodes = [current_node]

                # Try to find connected nodes through dependencies
                processed_nodes = set()
                nodes_to_process = [current_node]

                while nodes_to_process:
                    node = nodes_to_process.pop(0)
                    if node.name in processed_nodes:
                        continue
                    processed_nodes.add(node.name)

                    # Get dependencies and dependents
                    for wi in node.workItems:
                        for dep in wi.dependencies:
                            if dep.node not in all_nodes and dep.node.name not in processed_nodes:
                                all_nodes.append(dep.node)
                                nodes_to_process.append(dep.node)
                        for dep in wi.dependents:
                            if dep.node not in all_nodes and dep.node.name not in processed_nodes:
                                all_nodes.append(dep.node)
                                nodes_to_process.append(dep.node)
        except Exception as e:
            logger.warning(f"[WARNING] Could not iterate nodes: {str(e)}")
            # Fallback to just the current node
            all_nodes = [work_item.node]

        logger.debug(f"Total Nodes Found: {len(all_nodes)}")
        logger.debug("")

        # Log each node's state
        for idx, node in enumerate(all_nodes):
            logger.debug(f"Node [{idx + 1}/{len(all_nodes)}]:")
            self.log_node_details(node)

            # Log work items for this node
            try:
                work_items = node.workItems
                if work_items:
                    logger.debug(f"  Work Items ({len(work_items)}):")
                    for wi_idx, wi in enumerate(work_items[:5]):  # Limit to first 5 for brevity
                        state_str = str(wi.state) if hasattr(wi, 'state') else 'unknown'
                        logger.debug(f"    [{wi_idx + 1}] {wi.name} - State: {state_str}, ID: {wi.id}")
                    if len(work_items) > 5:
                        logger.debug(f"    ... and {len(work_items) - 5} more work items")
            except Exception as e:
                logger.error(f"  [ERROR] Could not get work items: {str(e)}")
            logger.debug("")

    def check_first_to_schedule(self, work_item):
        """Check if this is the first work item to be scheduled

        Args:
            work_item: The current work item

        Returns:
            bool: True if first to schedule, False otherwise
        """
        logger.debug("Checking if this is the first work item to be scheduled...")
        first_to_schedule = True

        current_node_work_items = work_item.node.workItems
        logger.debug(f"Current node ({work_item.node.name}) has {len(current_node_work_items)} work items")

        for wi in current_node_work_items:
            logger.debug(f"  Checking work item: {wi.name} (ID: {wi.id})")
            conductor_batch_id = wi.stringAttribValue("conductor_batch_job_id")
            logger.debug(f"    conductor_batch_job_id: {conductor_batch_id}")

            if wi != work_item and conductor_batch_id:
                first_to_schedule = False
                logger.debug(f"    Found already scheduled item, not first to schedule")
                break

        logger.debug(f"Is first to schedule: {first_to_schedule}")
        return first_to_schedule

    def collect_work_items_for_batch(self, work_item):
        """Collect all work items from the node that are ready to be scheduled

        Args:
            work_item: The current work item

        Returns:
            list: List of work items ready for batching
        """
        work_item_chain = []
        current_node_work_items = work_item.node.workItems

        logger.info(f"First to schedule - collecting all ready items from node {work_item.node.name}")

        for wi in current_node_work_items:
            logger.debug(f"  Evaluating work item: {wi.name} (ID: {wi.id}, State: {wi.state})")

            # Check if work item is ready (not already submitted)
            conductor_batch_id = wi.stringAttribValue("conductor_batch_job_id")
            logger.debug(f"    conductor_batch_job_id: {conductor_batch_id}")

            if not conductor_batch_id:
                logger.debug(f"    Adding {wi.name} to work_item_chain")
                work_item_chain.append(wi)

                # Log dependencies
                deps = wi.dependencies
                if deps:
                    logger.debug(f"    Dependencies for {wi.name}:")
                    for dep in deps:
                        logger.debug(f"      - {dep.name} (State: {dep.state})")
            else:
                logger.debug(f"    Skipping {wi.name} - already has batch job ID")

        return work_item_chain

    def prepare_batch_job(self, work_item_chain, topnet_path, wrapper_script_source):
        """Prepare a batch job with multiple work items

        Args:
            work_item_chain: List of work items to batch
            topnet_path: Path to the TOP network
            wrapper_script_source: Path to the wrapper script

        Returns:
            tuple: (tasks_data, upload_paths, job_title)
        """
        logger.info("╔═══════════════════════════════════════════════════════════╗")
        logger.info("║              CREATING BATCH JOB                            ║")
        logger.info(f"║              Tasks: {len(work_item_chain):<39}║")
        logger.info("╚═══════════════════════════════════════════════════════════╝")

        # Get the multiple_machines parameter
        use_multiple_machines = rops.get_parameter_value(self.node, "multiple_machines")
        logger.debug(f"Use multiple machines: {use_multiple_machines}")

        # Mark all items as pending
        for idx, item in enumerate(work_item_chain):
            logger.debug(f"Marking item {idx + 1}/{len(work_item_chain)} as pending: {item.name}")
            item.setStringAttrib("conductor_batch_job_id", "pending")

        # Collect upload paths - ensure all are absolute
        all_upload_paths = PathList()
        all_upload_paths.add(str(self.context.workingDir(False)))
        all_upload_paths.add(str(self.context.scriptDir(False)))
        all_upload_paths.add(str(self.context.tempDir(False)))  # Add temp dir
        all_upload_paths.add(wrapper_script_source)

        # Add the entire pdgtemp directory structure
        pdgtemp_dir = os.path.join(str(self.context.workingDir(False)), "pdgtemp")
        if os.path.exists(pdgtemp_dir):
            all_upload_paths.add(pdgtemp_dir)
            logger.debug(f"Added pdgtemp directory to uploads: {pdgtemp_dir}")

        logger.debug("Initial upload paths:")
        for path in all_upload_paths:
            logger.debug(f"  - {path}")

        # Create common directories with absolute paths
        self.usd_dir = os.path.abspath(os.path.join(str(self.context.workingDir(False)), "usd"))
        self.geo_dir = os.path.abspath(os.path.join(str(self.context.workingDir(False)), "geo"))
        self.render_output_dir = os.path.abspath(os.path.join(str(self.context.workingDir(False)), "render"))
        self.images_dir = os.path.abspath(os.path.join(str(self.context.workingDir(False)), "images"))
        self.scripts_dir = os.path.abspath(os.path.join(str(self.context.workingDir(False)), "scripts"))
        self.logs_dir = os.path.abspath(os.path.join(str(self.context.workingDir(False)), "logs"))
        self.data_dir = os.path.abspath(os.path.join(str(self.context.workingDir(False)), "data"))
        """
        for dir_path in [self.usd_dir, self.geo_dir, self.render_output_dir, self.images_dir, self.scripts_dir,
                         self.logs_dir, self.data_dir]:
            all_upload_paths.add(dir_path)
        for dir_path in [self.render_dir, self.usd_dir, self.geo_dir, self.render_output_dir, self.images_dir,
                         self.scripts_dir, self.logs_dir, self.data_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                logger.debug(f"Created directory: {dir_path}")
        """

        # Save hip file for farm with versioning
        hip_file_path = hou.hipFile.path()
        if not hip_file_path:
            # Fallback if no HIP file is loaded (shouldn't happen in practice)
            hip_dir = str(self.context.workingDir(False))
            hip_file_path = os.path.join(hip_dir, f"pdg_graph_{work_item_chain[0].node.name}.hip")


        # Filter out invalid paths (opdef:, op:, temp:, etc.)
        current_assets = filter_upload_paths(all_upload_paths)
        logger.debug(f"Filtered upload paths: {len(all_upload_paths)} -> {len(current_assets)}")

        # Create tasks for each work item
        tasks_data = []

        if use_multiple_machines:
            # Original behavior: one work item per machine (frame)
            logger.debug("Creating tasks for multiple machines...")
            for idx, item in enumerate(work_item_chain):
                logger.debug(f"Processing work item {idx + 1}/{len(work_item_chain)}: {item.name}")

                # Debug information
                logger.debug(f"  Debug - Work Item Info:")
                logger.debug(f"    item.name: {item.name}")
                logger.debug(f"    item.node.name: {item.node.name}")
                logger.debug(f"    item.id: {item.id}")
                logger.debug(f"    item.index: {item.index}")

                self.log_work_item_details(item)

                # Serialize this work item
                self.context.createJobDirsAndSerializeWorkItems(item)
                logger.debug(f"  Serialized work item")

                # Add paths from item attributes
                upload_attr = item.stringAttribValue("conductor_upload_paths")
                if upload_attr:
                    logger.debug(f"  Found conductor_upload_paths attribute: {upload_attr}")
                    for p in upload_attr.split(";"):
                        if os.path.exists(p):
                            all_upload_paths.add(p)
                            logger.debug(f"    Added: {p}")

                # Process output files
                self.process_output_files(item, all_upload_paths)

                # Get the actual node name
                actual_node_name = item.node.name

                script_path = re.sub("^[a-zA-Z]:", "", wrapper_script_source).replace("\\", "/")
                working_dir_path = str(self.context.workingDir(False))
                # Create task command - using item_index for multiple machines
                try:
                    hip_file_path = util.prepare_path(hip_file_path)
                    working_dir_path = util.prepare_path(working_dir_path)
                except Exception as e:
                    logger.warning(f"Error setting paths: {e}")
                task_command = f'hython "{script_path}" --hip_file {hip_file_path} --topnet_path {topnet_path} --item_index {item.index} --working_dir {working_dir_path} --output_dir "{self.render_dir}"'

                task = {
                    "name": f"PDG_{actual_node_name}_{item.name}",
                    "command": task_command,
                    "frames": str(idx + 1),  # Use 1-based frame numbering for multiple machines
                }

                tasks_data.append(task)
                logger.debug(f"  Added task to batch: {task['name']}")
                logger.debug(f"  Task command uses node: {actual_node_name}")
                logger.debug(f"  Frame number: {idx + 1}")

        else:
            # New behavior: all work items to single machine
            logger.info("Creating single task for all work items on one machine...")

            # Serialize all work items
            for idx, item in enumerate(work_item_chain):
                # logger.debug(f"Serializing work item {idx + 1}/{len(work_item_chain)}: {item.name}")
                self.context.createJobDirsAndSerializeWorkItems(item)

                # Add paths from item attributes
                upload_attr = item.stringAttribValue("conductor_upload_paths")
                if upload_attr:
                    for p in upload_attr.split(";"):
                        if os.path.exists(p):
                            all_upload_paths.add(p)

                # Process output files
                self.process_output_files(item, all_upload_paths)

            # Create single task command with --use_single_machine flag
            actual_node_name = work_item_chain[0].node.name

            script_path = re.sub("^[a-zA-Z]:", "", wrapper_script_source).replace("\\", "/")
            working_dir_path = str(self.context.workingDir(False))
            try:
                hip_file_path = util.prepare_path(hip_file_path)
                working_dir_path = util.prepare_path(working_dir_path)
            except Exception as e:
                logger.warning(f"Error setting paths: {e}")

            task_command = f'hython "{script_path}" --hip_file {hip_file_path} --topnet_path {topnet_path} --use_single_machine --working_dir {working_dir_path} --output_dir "{self.render_dir}"'

            task = {
                "name": f"PDG_Batch_{actual_node_name}_SingleMachine",
                "command": task_command,
                "frames": "1",  # Single frame for single machine
            }

            tasks_data.append(task)
            logger.debug(f"  Added single task for all {len(work_item_chain)} work items")
            logger.debug(f"  Task command uses --use_single_machine flag")
            logger.debug(f"  Frame: 1 (single machine execution)")

        # Get versioned HIP filename for job title
        hip_filename = os.path.splitext(os.path.basename(hip_file_path))[0]
        job_title = f"PDG_Batch_{work_item_chain[0].node.name}_{hip_filename}"

        logger.info("Batch job summary:")
        logger.info(f"  Title: {job_title}")
        logger.info(f"  Tasks data: {tasks_data}")
        logger.info(f"  Tasks: {len(tasks_data)}")
        logger.info(f"  Upload paths: {len(current_assets)}")
        logger.info(f"  Mode: {'Multiple machines' if use_multiple_machines else 'Single machine'}")

        return tasks_data, current_assets, job_title

    def prepare_single_job(self, work_item, topnet_path, wrapper_script_source):
        """Prepare a single task job

        Args:
            work_item: The work item to process
            topnet_path: Path to the TOP network
            wrapper_script_source: Path to the wrapper script

        Returns:
            tuple: (tasks_data, upload_paths, job_title)
        """
        logger.info("╔═══════════════════════════════════════════════════════════╗")
        logger.info("║              CREATING SINGLE TASK JOB                      ║")
        logger.info("╚═══════════════════════════════════════════════════════════╝")

        # Create common directories
        scripts_dir = os.path.join(str(self.context.workingDir(False)), "scripts")
        logs_dir = os.path.join(str(self.context.workingDir(False)), "logs")
        data_dir = os.path.join(str(self.context.workingDir(False)), "data")
        wrapper_script_source_str = f'"{wrapper_script_source}"'

        # Collect initial upload paths
        initial_paths = [
            str(self.context.workingDir(False)),
            str(self.context.scriptDir(False)),
            str(self.context.tempDir(False)),
            wrapper_script_source_str,
            scripts_dir,
            logs_dir,
            data_dir,
        ]

        # Add the entire pdgtemp directory
        pdgtemp_dir = os.path.join(str(self.context.workingDir(False)), "pdgtemp")
        if os.path.exists(pdgtemp_dir):
            initial_paths.append(pdgtemp_dir)
            logger.debug(f"Added pdgtemp directory to uploads: {pdgtemp_dir}")


        # Add paths from attributes
        input_attr = work_item.stringAttribValue("conductor_upload_paths")
        if input_attr:
            logger.debug(f"Found conductor_upload_paths: {input_attr}")
            initial_paths.extend(input_attr.split(";"))

        # Filter out invalid paths (opdef:, op:, temp:, etc.)
        upload_paths = filter_upload_paths(initial_paths)
        logger.debug(f"Filtered upload paths: {len(initial_paths)} -> {len(upload_paths)}")

        # Process output files
        self.process_output_files_single(work_item, upload_paths)

        hip_file_path = hou.hipFile.path()
        if not hip_file_path:
            # Fallback if no HIP file is loaded
            hip_dir = str(self.context.workingDir(False))
            hip_file_path = os.path.join(hip_dir, f"pdg_graph_{work_item.node.name}.hip")

        script_path = re.sub("^[a-zA-Z]:", "", wrapper_script_source).replace("\\", "/")
        working_dir_path = str(self.context.workingDir(False))
        try:
            hip_file_path = util.prepare_path(hip_file_path)
            working_dir_path = util.prepare_path(working_dir_path)
        except Exception as e:
            logger.warning(f"Error setting paths: {e}")

        # Create task command
        task_command = f'hython "{script_path}" --hip_file "{hip_file_path}" --topnet_path "{topnet_path}" --item_index {work_item.index} --working_dir "{working_dir_path}" --output_dir "{self.render_dir}"'

        task = {
            "name": f"PDG_{work_item.node.name}_{work_item.name}",
            "command": task_command,
            "frames": "1"
        }

        tasks_data = [task]

        # Get versioned HIP filename for job title
        hip_filename = os.path.splitext(os.path.basename(hip_file_path))[0]
        job_title = f"PDG_Single_{work_item.node.name}_{hip_filename}"

        logger.debug(f"  Added task to batch: {task['name']}")

        return tasks_data, upload_paths, job_title

    def process_output_files(self, item, upload_paths_set):
        """Process output files for a work item and add to upload paths

        Args:
            item: The work item
            upload_paths_set: Set of upload paths to add to
        """
        # logger.debug(f"  Processing output files ({len(item.outputFiles)})...")
        for output_file in item.outputFiles:
            output_path = output_file.path
            logger.debug(f"    Output file: {output_path}")

            # Replace __PDG_DIR__ token if present
            if "__PDG_DIR__" in output_path:
                output_path = output_path.replace("__PDG_DIR__", str(self.context.workingDir(False)))
                logger.debug(f"    Replaced __PDG_DIR__ -> {output_path}")

            output_dir = os.path.dirname(output_path)
            if output_dir:
                upload_paths_set.add(output_dir)
                # Create directory if it doesn't exist
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                    logger.debug(f"    Created output directory: {output_dir}")

        # Also check for expected output paths in attributes
        output_attr = item.stringAttribValue("expected_output_path")
        if output_attr:
            logger.debug(f"  Found expected_output_path: {output_attr}")
            # Replace __PDG_DIR__ token if present
            if "__PDG_DIR__" in output_attr:
                output_attr = output_attr.replace("__PDG_DIR__", str(self.context.workingDir(False)))
                logger.debug(f"    Replaced __PDG_DIR__ -> {output_attr}")

            output_dir = os.path.dirname(output_attr)
            if output_dir:
                upload_paths_set.add(output_dir)
                # Create directory if not exist
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                    logger.debug(f"    Created expected output directory: {output_dir}")

    def process_output_files_single(self, work_item, upload_paths_list):
        """Process output files for a single work item

        Args:
            work_item: The work item
            upload_paths_list: List of upload paths to add to
        """
        logger.debug(f"Processing output files ({len(work_item.outputFiles)})...")
        for output_file in work_item.outputFiles:
            output_path = output_file.path
            # Replace __PDG_DIR__ token if present
            if "__PDG_DIR__" in output_path:
                output_path = output_path.replace("__PDG_DIR__", str(self.context.workingDir(False)))
            output_dir = os.path.dirname(output_path)
            if output_dir and os.path.exists(output_dir):
                upload_paths_list.append(output_dir)
                logger.debug(f"  Added output directory: {output_dir}")

    def build_job_environment(self, work_item, should_batch):
        """Build the environment variables for the job

        Args:
            work_item: The work item
            should_batch: Whether this is a batch job
            self.render_dir: The render directory path

        Returns:
            dict: Environment variables for the job
        """
        # Get the actual IP address from the result server address
        result_server_addr = str(self.context.workItemResultServerAddr())
        logger.debug(f"Original result server address: {result_server_addr}")

        if result_server_addr.startswith("127.0.0.1:"):
            # This is a localhost address that won't work from the farm
            port = result_server_addr.split(":")[1]
            local_ip = self.get_local_ip()
            result_server_addr = f"{local_ip}:{port}"
            logger.info(f"Replaced localhost with machine IP: {result_server_addr}")

        logger.info(f"PDG Result Server: {result_server_addr}")
        logger.warning(f"Make sure firewall allows incoming connections on port {result_server_addr.split(':')[1]}")

        pdg_dir = self.context.workingDir(False)
        pdg_dir = util.prepare_path(pdg_dir)
        pdg_temp = self.context.tempDir(False)
        pdg_temp = util.clean_path(pdg_temp)
        pdg_scriptdir = self.context.scriptDir(False)
        pdg_scriptdir = util.prepare_path(pdg_scriptdir)
        houdini_temp_dir = os.path.join(str(self.context.workingDir(False)), "render")
        houdini_temp_dir = util.prepare_path(houdini_temp_dir)

        job_env = {
            "PDG_RESULT_SERVER": result_server_addr,
            "PDG_DIR": pdg_dir,
            "PDG_TEMP": pdg_temp,
            "PDG_SCRIPTDIR": pdg_scriptdir,
            "PDG_RENDER_DIR": self.render_dir,
            "PDG_RPC_TIMEOUT": "60",
            "PDG_RPC_MAX_ERRORS": "20",
            "PDG_RPC_BATCH": "1",
            "PDG_RPC_RETRY_DELAY": "5",
            "PDG_RPC_IGNORE_WORK_ITEM_RESULTS": "0",
            "PDG_SUBMIT_AS_JOB": "0",
            "PDG_WORK_ITEM_ID": str(work_item.id) if not should_batch else "1",
            "HOUDINI_TEMP_DIR": houdini_temp_dir
        }

        # Get the multiple_machines parameter
        use_multiple_machines = rops.get_parameter_value(self.node, "multiple_machines")
        logger.debug(f"Use multiple machines: {use_multiple_machines}")

        # Apply threading configuration
        threading_env = configure_threading_environment(self.node)
        job_env.update(threading_env)

        # For single task, add task-specific environment
        if not should_batch:
            job_env["PDG_ITEM_NAME"] = str(work_item.name)
            job_env["PDG_ITEM_ID"] = str(work_item.id)
            logger.debug("Added single task environment variables")

        # Include custom environment
        env_attr = work_item.stringAttribValue("conductor_environment")
        if env_attr:
            try:
                custom_env = json.loads(env_attr)
                job_env.update(custom_env)
                logger.debug(f"Added custom environment: {custom_env}")
            except json.JSONDecodeError:
                logger.warning("Failed to parse conductor_environment JSON")

        # Add conductor environment
        if self.node:
            conductor_env = environment.resolve_payload(self.node)
            conductor_env = conductor_env.get("environment", {})
            job_env.update(conductor_env)

        for key in ["JOB", "OCIO"]:
            job_env.pop(key, None)

        # Get all Houdini paths properly - typically HFS and HB are provided
        try:
            # Get HFS and HB from job environment (typically provided by Conductor)
            hfs = job_env.get("HFS")
            hb = job_env.get("HB")

            # Get all paths (this will calculate HH and HHP from HFS/HB)
            houdini_paths = get_all_houdini_paths(hfs=hfs, hb=hb)

            # Update all Houdini environment variables
            job_env["HFS"] = houdini_paths["HFS"]
            job_env["HH"] = houdini_paths["HH"]
            job_env["HB"] = houdini_paths["HB"]
            job_env["HHP"] = houdini_paths["HHP"]

            logger.debug(f"Houdini environment paths:")
            logger.debug(f"  HFS: {houdini_paths['HFS']}")
            logger.debug(f"  HH: {houdini_paths['HH']}")
            logger.debug(f"  HB: {houdini_paths['HB']}")
            logger.debug(f"  HHP: {houdini_paths['HHP']}")

            # Get path additions
            path_additions_info = get_houdini_path_additions(houdini_paths["HH"])

            # Update PDG_SCRIPTDIR to use HHP/pdgjob
            scr_dir = os.path.join(houdini_paths["HHP"], "pdgjob").replace("\\", "/")
            job_env["PDG_SCRIPTDIR"] = scr_dir

            # Add to PATH (Linux uses : as separator)
            current_path = job_env.get("PATH", "")
            path_additions = [houdini_paths["HB"], scr_dir] + path_additions_info['path_additions']

            if current_path:
                existing_paths = current_path.split(":")
                for new_path in path_additions:
                    if new_path not in existing_paths:
                        current_path = f"{current_path}:{new_path}"
            else:
                current_path = ":".join(path_additions)

            job_env["PATH"] = current_path

            # Set HOUDINI_PATH for resource discovery
            # The & means "default Houdini path"
            houdini_path_additions = path_additions_info['houdini_path_additions']
            if houdini_path_additions:
                # Prepend custom paths before default (&)
                job_env["HOUDINI_PATH"] = ":".join(houdini_path_additions) + ":&"
            else:
                job_env["HOUDINI_PATH"] = "&"

            logger.debug(f"PATH additions: {path_additions}")
            logger.debug(f"HOUDINI_PATH: {job_env['HOUDINI_PATH']}")

        except Exception as e:
            logger.error(f"Failed to set Houdini environment paths: {e}")
            raise RuntimeError(f"Critical: Could not configure Houdini environment - {e}")

        logger.debug("Final environment variables:")
        for key, value in job_env.items():
            logger.debug(f"  {key}: {value}")

        return job_env

    def submit_job_to_conductor(self, job_spec, work_item, work_item_chain, should_batch):
        """Submit the job to Conductor

        Args:
            job_spec: The job specification dictionary
            work_item: The current work item
            work_item_chain: List of work items in the batch
            should_batch: Whether this is a batch job

        Returns:
            pdg.scheduleResult: The scheduling result
        """
        logger.info("═══════════════════════════════════════════════════════════")
        logger.info("JOB SPECIFICATION :")
        logger.info("═══════════════════════════════════════════════════════════")
        logger.debug(f"{json.dumps(job_spec, indent=2)}")
        logger.info("═══════════════════════════════════════════════════════════")

        logger.info("Submitting to Conductor...")
        submission_start = time.time()
        from ciocore import conductor_submit

        # Implement this
        use_submission_dialog = True

        if use_submission_dialog:
            logger.info(f"Showing submission dialog ...")
            def show_dialog():
                try:
                    nodes = [self.node]
                    payloads = [job_spec]
                    submission_dialog = SubmissionDialog(nodes, payloads=payloads)
                    submission_dialog.exec_()  # Use exec_() for modal dialog
                except Exception as e:
                    logger.error(f"Dialog error: {e}")

            # Execute on main thread - already imported hdefereval at top
            hdefereval.executeInMainThreadWithResult(show_dialog)
        else:
            try:
                remote_job = conductor_submit.Submit(job_spec)
                response, code = remote_job.main()
                submission_end = time.time()

                logger.info(f"Conductor response received in {submission_end - submission_start:.2f} seconds")
                logger.debug(f"Response code: {code}")
                logger.debug(f"Response: {json.dumps(response, indent=2)}")

                if code in (200, 201):
                    job_id = response.get("jobid")
                    if job_id:
                        work_item.setStringAttrib("conductor_job_id", job_id)
                        logger.debug("Set conductor_job_id attribute on work item")

                        # If batch job, update all items with the job ID
                        if should_batch:
                            logger.info(f"Updating all {len(work_item_chain)} batch items with job ID...")
                            for idx, item in enumerate(work_item_chain):
                                item.setStringAttrib("conductor_batch_job_id", job_id)
                                logger.debug(f"  Updated item {idx + 1}/{len(work_item_chain)}: {item.name}")

                        logger.info("╔══════════════════════════════════════════════════════════╗")
                        logger.info("║                    JOB SUBMITTED SUCCESSFULLY               ║")
                        logger.info(f"║  Job ID: {job_id:<50}║")
                        logger.info("╚══════════════════════════════════════════════════════════╝")

                        return pdg.scheduleResult.Succeeded
                    else:
                        logger.error(f"No job ID in response: {response}")
                        return pdg.scheduleResult.Failed
                else:
                    logger.error(f"Submission failed, code: {code}, response: {response}")
                    return pdg.scheduleResult.Failed

            except ImportError as e:
                logger.error(f"ImportError for ciocore: {traceback.format_exc()}")
                return pdg.scheduleResult.Failed
            except Exception as e:
                logger.error(f"Exception submitting job: {traceback.format_exc()}")
                return pdg.scheduleResult.Failed

    def on_schedule(self, work_item):
        """Main scheduling function for work items

        Args:
            work_item: The work item to schedule

        Returns:
            pdg.scheduleResult: The scheduling result
        """
        logger.debug("Custom onSchedule (Conductor version)")
        logger.debug(f"Script started at: {datetime.datetime.now()}")
        logger.debug(f"work_item: {work_item}")
        logger.debug(f"work_item type: {type(work_item)}")

        # Log the current work item in detail
        self.log_work_item_details(work_item)

        # Log the PDG graph state
        self.log_pdg_graph_state(work_item)

        try:
            # Ensure local staging
            logger.debug("Creating job directories and serializing work items...")
            self.context.createJobDirsAndSerializeWorkItems(work_item)
            logger.debug("Work item serialized successfully")

            # Expand the command that would have run locally - for logging purposes only
            local_command = self.context.expandCommandTokens(work_item.command, work_item)
            # logger.debug(f"Local command (for reference): {local_command}")

            # Check if this work item has already been submitted as part of a batch
            batch_job_id = work_item.stringAttribValue("conductor_batch_job_id")
            logger.debug(f"Current batch_job_id: {batch_job_id}")

            if batch_job_id and batch_job_id != "pending":
                logger.info(f"Work item already submitted in batch job: {batch_job_id}")
                return pdg.scheduleResult.Succeeded

            # Connect to Conductor and ensure connection is valid
            try:
                connect_to_conductor(self.node)
            except RuntimeError as e:
                logger.error(f"Failed to establish Conductor connection: {e}")
                return pdg.scheduleResult.Failed
            except Exception as e:
                logger.error(f"Unexpected error connecting to Conductor: {e}")
                return pdg.scheduleResult.Failed

            # Define the render directory path



            # Collect all ready work items from the current node
            work_item_chain = []
            should_batch = False

            # Check if we're the first work item to be scheduled
            first_to_schedule = self.check_first_to_schedule(work_item)

            if first_to_schedule:
                # Collect all work items from this node that are ready to be scheduled
                work_item_chain = self.collect_work_items_for_batch(work_item)
                should_batch = len(work_item_chain) > 1
                logger.info(f"First to schedule, collecting all ready items. Found {len(work_item_chain)} items")
                logger.info(f"Should batch: {should_batch}")
            else:
                # Not first, check if already part of a batch
                if batch_job_id == "pending":
                    logger.debug("Work item is pending batch submission, skipping")
                    return pdg.scheduleResult.Succeeded
                # Otherwise submit as single task
                work_item_chain = [work_item]
                should_batch = False
                logger.info("Not first to schedule, submitting as single task")

            # Get the TOP network path (uses cached value if available)
            topnet_path = self.get_topnet_path(work_item.node)
            if not topnet_path:
                logger.error("Could not determine TOP network path")
                return pdg.scheduleResult.Failed
            logger.debug(f"TOP network path: {topnet_path}")

            # Define the wrapper script path
            wrapper_script_source = rops.get_parameter_value(self.node, "render_script")

            if not wrapper_script_source:
                cio_dir = os.environ.get("CIODIR")
                if cio_dir:
                    # wrapper_script_source = os.path.join(cio_dir, "ciohoudini", "scheduler", "pdg_universal_wrapper.py")
                    wrapper_script_source = os.path.join(cio_dir, "ciohoudini", "scheduler", "simplified_pdg_wrapper.py")
                else:
                    logger.warning("CIODIR environment variable is not set. Cannot determine wrapper script path.")
                    wrapper_script_source = ""

            if wrapper_script_source and not os.path.exists(wrapper_script_source):
                logger.warning(
                    f"Wrapper script not found at {wrapper_script_source}. Falling back to default if available.")

            # Get the HIP filename for the job title
            hip_file_path = hou.hipFile.path()
            hip_filename = os.path.splitext(os.path.basename(hip_file_path))[0] if hip_file_path else "untitled"
            logger.debug(f"HIP filename: {hip_filename}")

            # Prepare job based on batch or single
            if should_batch:
                tasks_data, upload_paths, job_title = self.prepare_batch_job(
                    work_item_chain, topnet_path, wrapper_script_source
                )
            else:
                tasks_data, upload_paths, job_title = self.prepare_single_job(
                    work_item, topnet_path, wrapper_script_source
                )

            # Build job environment
            kwargs = {
                "do_asset_scan": True,
                "task_limit": -1
            }
            frame_range_to_use = self.node.parm("frame_range").evalAsString()
            job_env = self.build_job_environment(work_item, should_batch)

            project_name = project.resolve_payload(self.node)
            project_name = project_name.get("project", "default")

            instance_type = instances.resolve_payload(self.node)
            instance_type = instance_type.get("instance_type", "")

            software_package_ids = software.resolve_payload(self.node)
            software_package_ids = software_package_ids.get("software_package_ids", [])

            scout_frames = frames.resolve_payload(self.node, frame_range=frame_range_to_use)
            scout_frames = scout_frames.get("scout_frames", "1")

            # Todo: review this
            upload_paths = []

            upload_paths_conductor = pdg_assets.resolve_payload(self.node, **kwargs)
            upload_paths_conductor = upload_paths_conductor.get("upload_paths", [])
            upload_paths = list(set(upload_paths + upload_paths_conductor))

            # Filter out invalid paths (opdef:, op:, temp:, etc.)
            upload_paths = filter_upload_paths(upload_paths)
            logger.debug(f"Final filtered upload paths: {len(upload_paths_conductor)} -> {len(upload_paths)}")

            # Create job specification
            job_spec = {
                "job_title": job_title,
                "project": project_name,
                "instance_type": instance_type,
                "preemptible": False,
                "autoretry_policy": {"preempted": {"max_retries": 2}},
                "software_package_ids": software_package_ids,
                "environment": job_env,
                "output_path": self.render_dir,
                "local_upload": True,
                "scout_frames": scout_frames,
                "tasks_data": tasks_data,
                "upload_paths": upload_paths,
            }

            # Submit job to Conductor
            return self.submit_job_to_conductor(job_spec, work_item, work_item_chain, should_batch)

        except Exception as e:
            logger.error("═══════════════════════════════════════════════════════════")
            logger.error("CRITICAL ERROR IN onSchedule")
            logger.error("═══════════════════════════════════════════════════════════")
            logger.error(traceback.format_exc())
            logger.error("═══════════════════════════════════════════════════════════")
            return pdg.scheduleResult.Failed


def schedule_work_item(scheduler_self, work_item):
    """Entry point function for scheduling work items

    Args:
        scheduler_self: The scheduler context (self from PDG)
        work_item: The work item to schedule

    Returns:
        pdg.scheduleResult: The scheduling result
    """
    import logging
    from ciohoudini.scheduler.on_schedule_conductor_scheduler import PDGConductorScheduler
    import hou
    logger = logging.getLogger(__name__)

    # Get the scheduler name from the context
    scheduler_name = scheduler_self.name
    logger.debug(f"Scheduler name: {scheduler_name}")

    # Find the topnet node by traversing up the parent hierarchy
    # Start from the work item's TOP node
    current_node = work_item.node.topNode()
    topnet_hou_node = None

    logger.debug(f"Starting search for TOP network container from: {current_node.path() if current_node else 'None'}")

    # Keep going up until we find a TOP network container node or reach the root
    while current_node is not None:
        # Debug logging
        logger.debug(f"  Checking node: {current_node.path()}")
        logger.debug(f"    Type: {current_node.type().name()}")
        logger.debug(f"    Category: {current_node.type().category().name()}")

        # Check if this is a TOP network container (topnet, topnetmgr, etc.)
        # TOP network containers can contain TOP nodes (childTypeCategory is Top)
        # This distinguishes them from TOP nodes within the network
        if (hasattr(current_node, 'childTypeCategory') and
                current_node.childTypeCategory() and
                current_node.childTypeCategory().name() == "Top"):
            topnet_hou_node = current_node
            logger.debug(f"  ✓ Found TOP network container: {topnet_hou_node.path()}")
            break

        # Move up to parent
        current_node = current_node.parent()

    # Check if we found a TOP network
    if topnet_hou_node is None:
        logger.error("ERROR: Could not find TOP network container node in parent hierarchy")
        logger.error("  The node must be inside a TOP network (topnet, topnetmgr, etc.)")
        return pdg.scheduleResult.Failed

    logger.debug(f"Searching for conductorscheduler named '{scheduler_name}' in {topnet_hou_node.path()}")

    # Find our specific conductor scheduler by name within the TOP network
    scheduler_node = None
    for node in topnet_hou_node.allSubChildren():
        if (node.type().name() == "conductorscheduler" and
                node.name() == scheduler_name):
            scheduler_node = node
            logger.debug(f"  ✓ Found scheduler: {scheduler_node.path()}")
            break

    # Check if we found the scheduler
    if scheduler_node is None:
        logger.error(f"ERROR: Could not find conductorscheduler named '{scheduler_name}' in {topnet_hou_node.path()}")
        logger.error(f"  Available nodes in TOP network:")
        for node in topnet_hou_node.allSubChildren():
            logger.error(f"    - {node.name()} (type: {node.type().name()})")
        return pdg.scheduleResult.Failed

    # Create and execute the scheduler
    try:
        node_path = scheduler_node.path()
        # Pass both the scheduler node path and the TOP network path
        scheduler = PDGConductorScheduler(
            scheduler_self,
            node_path=node_path,
            topnet_path=topnet_hou_node.path()
        )
        result = scheduler.on_schedule(work_item)
        logger.debug(f"Scheduler execution completed with result: {result}")
        return result
    except Exception as e:
        logger.error(f"ERROR: Failed to execute scheduler: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return pdg.scheduleResult.Failed

# Call the function
# result = schedule_work_item(self, work_item)