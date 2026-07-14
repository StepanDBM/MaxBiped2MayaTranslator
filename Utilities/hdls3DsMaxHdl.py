# hdls3DsMaxHdl.py
"""
Exports clean FBX files from 3ds Max files that contain animations
for Unity and from the auto-biped in 3ds Max.

Input:
    list of .max files

Output:
    list of .fbx files

This module uses ONE 3dsmaxbatch.exe session for all MAX files in a batch.
"""

import os
import time
import shutil
import subprocess
import tempfile


DEFAULT_MAXBATCH_CANDIDATES = [
    r"C:\Program Files\Autodesk\3ds Max 2026\3dsmaxbatch.exe",
    r"C:\Program Files\Autodesk\3ds Max 2025\3dsmaxbatch.exe",
    r"C:\Program Files\Autodesk\3ds Max 2024\3dsmaxbatch.exe",
    r"C:\Program Files\Autodesk\3ds Max 2023\3dsmaxbatch.exe",
    r"C:\Program Files\Autodesk\3ds Max 2022\3dsmaxbatch.exe",
]

def run_process_with_live_listener_log(
    cmd,
    log_path,
    logger=None,
    poll_interval=1.0,
    timeout=None
):
    """
    Runs a process while live-tailing the 3ds Max listener log.

    This avoids the UI looking frozen while 3ds Max Batch is exporting
    many files in one session.
    """

    start_time = time.time()
    last_log_pos = 0

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False
    )

    while True:

        # Tail listener log.
        if logger and os.path.exists(log_path):
            try:
                with open(
                    log_path,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as handle:
                    handle.seek(last_log_pos)
                    new_text = handle.read()
                    last_log_pos = handle.tell()

                if new_text:
                    for line in new_text.splitlines():
                        if line.strip():
                            logger.append(line)

            except Exception:
                pass

        # Timeout.
        if timeout is not None:
            elapsed = time.time() - start_time

            if elapsed > timeout:
                try:
                    process.kill()
                except Exception:
                    pass

                raise RuntimeError(
                    "3dsmaxbatch timed out after {} seconds.".format(
                        timeout
                    )
                )

        # Done?
        if process.poll() is not None:
            break

        time.sleep(poll_interval)

    stdout, stderr = process.communicate()

    if stdout and logger:
        try:
            stdout_text = stdout.decode("utf-8", errors="ignore")

            for line in stdout_text.splitlines():
                if line.strip():
                    logger.append(line)
        except Exception:
            logger.append(str(stdout))

    if stderr and logger:
        try:
            stderr_text = stderr.decode("utf-8", errors="ignore")
            for line in stderr_text.splitlines():
                if line.strip():
                    logger.append(line)
        except Exception:
            logger.append(str(stderr))

    # Final log tail after process ended.
    if logger and os.path.exists(log_path):
        try:
            with open(
                log_path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as handle:
                handle.seek(last_log_pos)
                new_text = handle.read()

            if new_text:
                for line in new_text.splitlines():
                    if line.strip():
                        logger.append(line)

        except Exception:
            pass

    return process

def read_text_file(path):
    """
    Safely reads a text file.
    """

    if not path:
        return ""

    if not os.path.exists(path):
        return ""

    try:
        with open(path, "r") as handle:
            return handle.read()
    except Exception:
        try:
            with open(
                path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as handle:
                return handle.read()
        except Exception:
            return ""


def is_max_file(path):
    """
    Returns True for .max files.

    Also accepts .max.txt when someone renamed a .max file for transfer/testing.
    """

    lower = path.lower()

    return (
        lower.endswith(".max") or
        lower.endswith(".max.txt")
    )


def find_3dsmaxbatch(explicit_path=None):
    """
    Finds 3dsmaxbatch.exe.

    Priority:
        1. explicit_path argument
        2. MAXMAYA_3DSMAXBATCH environment variable
        3. common Autodesk install paths
    """

    if explicit_path and os.path.exists(explicit_path):
        return explicit_path

    env_path = os.environ.get(
        "MAXMAYA_3DSMAXBATCH"
    )

    if env_path and os.path.exists(env_path):
        return env_path

    for candidate in DEFAULT_MAXBATCH_CANDIDATES:
        if os.path.exists(candidate):
            return candidate

    raise RuntimeError(
        "Could not find 3dsmaxbatch.exe. "
        "Set environment variable MAXMAYA_3DSMAXBATCH to your 3dsmaxbatch.exe path."
    )


def ensure_folder(path):
    """
    Ensures a folder exists.
    """

    if not os.path.exists(path):
        os.makedirs(path)

    return path


def clean_file_stem(path):
    """
    Makes a safe base name from a file path.
    """

    base = os.path.basename(path)

    if base.lower().endswith(".max.txt"):
        base = base[:-8]
    else:
        base = os.path.splitext(base)[0]

    bad_chars = [
        " ",
        ":",
        ";",
        ",",
        ".",
        "-",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
    ]

    for char in bad_chars:
        base = base.replace(
            char,
            "_"
        )

    while "__" in base:
        base = base.replace(
            "__",
            "_"
        )

    return base.strip("_")


def mxs_string(path):
    """
    Converts a path into a MAXScript-safe string.

    Uses forward slashes to avoid UNC/backslash escaping problems.
    """

    path = os.path.normpath(path)

    path = path.replace(
        "\\",
        "/"
    )

    path = path.replace(
        '"',
        '\\"'
    )

    return path


def make_mxs_job_array(jobs):
    """
    Builds a MAXScript array of job pairs.

    jobs:
        [
            (max_file, output_fbx),
            ...
        ]

    Result:
        #(
            #("C:/a.max", "C:/a_fromMax.fbx"),
            #("C:/b.max", "C:/b_fromMax.fbx")
        )
    """

    items = []

    for max_file, output_fbx in jobs:
        items.append(
            '#("{}", "{}")'.format(
                mxs_string(max_file),
                mxs_string(output_fbx)
            )
        )

    return "#({})".format(
        ", ".join(items)
    )


def write_batch_export_script(jobs, script_path):
    """
    Writes a MAXScript that exports many MAX files to FBX in one 3ds Max session.
    """

    jobs_mxs = make_mxs_job_array(
        jobs
    )

    script = r'''
-- Auto-generated by MaxBiped2MayaTranslator
-- Batch exports relevant Bip001 hierarchy + skinned objects to FBX.

fn logMsg msg =
(
    format "%\n" msg
)

fn collectDescendants rootNode =
(
    local result = #()
    local stack = #(rootNode)

    while stack.count > 0 do
    (
        local current = stack[stack.count]
        deleteItem stack stack.count

        appendIfUnique result current

        for c in current.children do
        (
            append stack c
        )
    )

    return result
)

fn scoreBipRoot candidate =
(
    local descendants = collectDescendants candidate
    local names = for n in descendants collect (toLower n.name)

    local score = 0

    if (findItem names "bip001 pelvis") > 0 do score += 10
    if (findItem names "bip001 spine") > 0 do score += 10
    if (findItem names "bip001 spine1") > 0 do score += 6
    if (findItem names "bip001 spine2") > 0 do score += 6
    if (findItem names "bip001 head") > 0 do score += 10
    if (findItem names "bip001 l upperarm") > 0 do score += 10
    if (findItem names "bip001 r upperarm") > 0 do score += 10
    if (findItem names "bip001 l thigh") > 0 do score += 10
    if (findItem names "bip001 r thigh") > 0 do score += 10
    if (findItem names "bip001 footsteps") > 0 do score += 3

    return score
)
fn findDescendantByLowerName descendants targetName =
(
    for n in descendants do
    (
        if (toLower n.name) == targetName do
        (
            return n
        )
    )

    return undefined
)

fn distanceToOrigin n =
(
    if n == undefined do
    (
        return 999999999.0
    )

    try
    (
        return distance n.pos [0,0,0]
    )
    catch
    (
        try
        (
            return distance n.transform.row4 [0,0,0]
        )
        catch
        (
            return 999999999.0
        )
    )
)
fn findBestBipRoot =
(
    local candidates = #()

    for o in objects do
    (
        if (toLower o.name) == "bip001" do
        (
            append candidates o
        )
    )

    if candidates.count == 0 do
    (
        throw "No object named Bip001 found."
    )

    local bestNode = undefined
    local bestScore = -1
    local bestDistance = 999999999.0
    local bestDescendantCount = -1

    for c in candidates do
    (
        local descendants = collectDescendants c
        local s = scoreBipRoot c

        local pelvisNode = findDescendantByLowerName descendants "bip001 pelvis"

        local distanceNode = pelvisNode

        if distanceNode == undefined do
        (
            distanceNode = c
        )

        local d = distanceToOrigin distanceNode
        local descendantCount = descendants.count

        logMsg (
            "Bip001 candidate: " +
            c.name +
            " handle: " +
            (c.inode.handle as string) +
            " class: " +
            ((classOf c) as string) +
            " descendants: " +
            (descendantCount as string) +
            " score: " +
            (s as string) +
            " pelvis/root distance to origin: " +
            (d as string)
        )

        if
        (
            bestNode == undefined or
            s > bestScore or
            (
                s == bestScore and
                d < bestDistance
            ) or
            (
                s == bestScore and
                d == bestDistance and
                descendantCount > bestDescendantCount
            )
        )
        do
        (
            bestScore = s
            bestDistance = d
            bestDescendantCount = descendantCount
            bestNode = c
        )
    )

    if bestNode == undefined or bestScore <= 0 do
    (
        throw "Could not identify a valid Bip001 hierarchy."
    )

    logMsg (
        "Selected Bip001 root: " +
        bestNode.name +
        " score: " +
        (bestScore as string) +
        " distance: " +
        (bestDistance as string) +
        " descendants: " +
        (bestDescendantCount as string)
    )

    return bestNode
)

fn getSkinModifier obj =
(
    for m in obj.modifiers do
    (
        if classOf m == Skin do
        (
            return m
        )
    )

    return undefined
)

fn objectUsesAnyBone obj boneNames =
(
    local sk = getSkinModifier obj

    if sk == undefined do
    (
        return false
    )

    local count = 0

    try
    (
        count = skinOps.GetNumberBones sk
    )
    catch
    (
        return false
    )

    for i = 1 to count do
    (
        local boneName = ""

        try
        (
            boneName = skinOps.GetBoneName sk i 0
        )
        catch
        (
            boneName = ""
        )

        if (findItem boneNames (toLower boneName)) > 0 do
        (
            return true
        )
    )

    return false
)

fn collectRelevantObjects bipRoot =
(
    local bipNodes = collectDescendants bipRoot
    local boneNames = for n in bipNodes collect (toLower n.name)

    local relevant = #()

    -- Always include selected biped hierarchy.
    for n in bipNodes do
    (
        appendIfUnique relevant n
    )

    -- Include skinned geometry using this biped.
    for o in geometry do
    (
        if objectUsesAnyBone o boneNames do
        (
            appendIfUnique relevant o
        )
    )

    -- Include directly parented accessories/helpers under biped nodes.
    for o in objects do
    (
        if o.parent != undefined do
        (
            if (findItem bipNodes o.parent) > 0 do
            (
                appendIfUnique relevant o
            )
        )
    )

    return relevant
)

fn configureFbxExport =
(
    try
    (
        FBXExporterSetParam "Animation" true
        FBXExporterSetParam "BakeAnimation" true
        FBXExporterSetParam "Skins" true
        FBXExporterSetParam "Shapes" true
        FBXExporterSetParam "Cameras" false
        FBXExporterSetParam "Lights" false
        FBXExporterSetParam "SmoothingGroups" true
        FBXExporterSetParam "SmoothMeshExport" true
        FBXExporterSetParam "Triangulate" false
        FBXExporterSetParam "Preserveinstances" true
        FBXExporterSetParam "UpAxis" "Y"
    )
    catch
    (
        logMsg "Warning: Some FBX exporter params could not be set."
    )
)

fn exportOne maxFile outFile =
(
    logMsg "------------------------------------------------------------"
    logMsg ("Opening MAX file: " + maxFile)

    resetMaxFile #noPrompt
    loadMaxFile maxFile quiet:true useFileUnits:true

    local bipRoot = findBestBipRoot()
    local relevant = collectRelevantObjects bipRoot

    logMsg ("Relevant object count: " + (relevant.count as string))

    if relevant.count == 0 do
    (
        throw "No relevant objects collected for export."
    )

    clearSelection()
    select relevant

    configureFbxExport()

    logMsg ("Exporting FBX: " + outFile)

    exportFile outFile #noPrompt selectedOnly:true using:FBXEXP

    logMsg "FBX export complete."
)

fn main =
(
    local jobs = __JOBS__

    logMsg ("Batch MAX export job count: " + (jobs.count as string))

    for job in jobs do
    (
        local maxFile = job[1]
        local outFile = job[2]

        try
        (
            exportOne maxFile outFile
        )
        catch
        (
            logMsg ("ERROR while exporting: " + maxFile)
            logMsg ("ERROR: " + (getCurrentException()))
        )
    )

    logMsg "Batch MAX export complete."
)

try
(
    main()
)
catch
(
    logMsg ("FATAL ERROR: " + (getCurrentException()))
    quitMAX #noPrompt exitCode:1
)

quitMAX #noPrompt exitCode:0
'''

    script = script.replace(
        "__JOBS__",
        jobs_mxs
    )

    with open(script_path, "w") as handle:
        handle.write(script)

    return script_path


def export_many_max_to_fbx(
    max_files,
    output_dir,
    maxbatch_exe=None,
    logger=None,
    timeout=7200
):
    """
    Converts many .max files to FBX using one 3dsmaxbatch.exe session.

    Returns:
        List of exported FBX paths.

    Notes:
        - Exports are created locally first.
        - Exported FBXs are copied to output_dir.
        - If copying fails, the local FBX path is returned instead.
    """

    if not max_files:
        return []

    output_dir = ensure_folder(
        output_dir
    )

    maxbatch_exe = find_3dsmaxbatch(
        maxbatch_exe
    )

    local_temp_root = ensure_folder(
        os.path.join(
            tempfile.gettempdir(),
            "MaxMayaRigTranslator_MaxBatch"
        )
    )

    batch_name = "batch_" + str(int(time.time()))

    temp_dir = ensure_folder(
        os.path.join(
            local_temp_root,
            batch_name
        )
    )

    script_path = os.path.join(
        temp_dir,
        batch_name + "_export_many_bip.ms"
    )

    log_path = os.path.join(
        temp_dir,
        batch_name + "_3dsmaxbatch.log"
    )

    local_jobs = []
    output_pairs = []

    used_output_names = {}

    for max_file in max_files:

        max_file = os.path.normpath(
            max_file
        )

        if not os.path.exists(max_file):
            raise RuntimeError(
                "MAX file does not exist: {}".format(
                    max_file
                )
            )

        base = clean_file_stem(
            max_file
        )

        # Avoid collisions if different folders have same file name.
        count = used_output_names.get(
            base,
            0
        )

        used_output_names[base] = count + 1

        if count > 0:
            base = "{}_{:02d}".format(
                base,
                count + 1
            )

        local_output_fbx = os.path.join(
            temp_dir,
            base + "_fromMax.fbx"
        )

        final_output_fbx = os.path.join(
            output_dir,
            base + "_fromMax.fbx"
        )

        local_jobs.append(
            (
                max_file,
                local_output_fbx
            )
        )

        output_pairs.append(
            (
                local_output_fbx,
                final_output_fbx
            )
        )

    write_batch_export_script(
        local_jobs,
        script_path
    )

    cmd = [
        maxbatch_exe,
        script_path,
        "-listenerlog",
        log_path,
        "-v",
        "3"
    ]

    if logger:
        logger.append("=" * 80)
        logger.append("3DS MAX MULTI-FILE BATCH EXPORT")
        logger.append("=" * 80)
        logger.append("MAX file count: {}".format(len(max_files)))
        logger.append("Temp dir:")
        logger.append(temp_dir)
        logger.append("Generated MAXScript:")
        logger.append(script_path)
        logger.append("Listener log:")
        logger.append(log_path)
        logger.append("Running 3ds Max Batch:")
        logger.append(" ".join(cmd))
        logger.append("=" * 80)

    process = run_process_with_live_listener_log(
        cmd,
        log_path,
        logger=logger,
        poll_interval=1.0,
        timeout=timeout
    )

    signed_return_code = process.returncode

    if signed_return_code > 2147483647:
        signed_return_code = signed_return_code - 4294967296

    listener_log = read_text_file(
        log_path
    )

    if logger:
        logger.append(
            "3ds Max Batch return code: {} signed: {}".format(
                process.returncode,
                signed_return_code
            )
        )

        logger.append("")
        logger.append("=" * 80)
        logger.append("3DS MAX BATCH LISTENER LOG - CURRENT RUN")
        logger.append("=" * 80)

        if listener_log:
            logger.append(listener_log)
        else:
            logger.append("No listener log content found.")

        logger.append("=" * 80)

    exported = []
    missing = []

    for local_output_fbx, final_output_fbx in output_pairs:

        if not os.path.exists(local_output_fbx):
            missing.append(local_output_fbx)
            continue

        file_size = os.path.getsize(local_output_fbx)

        if logger:
            logger.append("Exported FBX exists:")
            logger.append(local_output_fbx)
            logger.append("Size: {} bytes".format(file_size))

        if file_size < 1024:
            missing.append(local_output_fbx)

            if logger:
                logger.append("Warning: Exported FBX is suspiciously small and will be skipped.\n")

            continue

        try:
            final_folder = os.path.dirname(
                final_output_fbx
            )

            if final_folder and not os.path.exists(final_folder):
                os.makedirs(
                    final_folder
                )

            shutil.copy2(
                local_output_fbx,
                final_output_fbx
            )

            exported.append(
                final_output_fbx
            )

            if logger:
                logger.append("Copied exported FBX:")
                logger.append(final_output_fbx)

        except Exception as e:

            if logger:
                logger.append("Warning: Could not copy exported FBX to final output folder.")
                logger.append("Reason: {}".format(e))
                logger.append("Using local temporary FBX instead:")
                logger.append(local_output_fbx)

            exported.append(local_output_fbx)

    if missing:

        if logger:
            logger.append("")
            logger.append("Missing exported FBX files:")
            for path in missing:
                logger.append(path)

        if not exported:
            raise RuntimeError(
                "3ds Max batch export failed. No FBX files were created. Log: {}".format(
                    log_path
                )
            )

    if process.returncode != 0 and exported:

        if logger:
            logger.append(
                "Warning: 3ds Max Batch returned a non-zero code, "
                "but exported FBX files exist. Continuing."
            )

    return exported