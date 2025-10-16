import argparse
import fnmatch
import glob
import lzma
import os
import sys
import tarfile
import time
from functools import partial
from pathlib import Path

from . import ArtifactMetaData

_verbose = False


def vprint(*args, **kwargs):
    """Prints the arguments if verbose is True."""
    if _verbose:
        print(*args, **kwargs, file=sys.stderr)


def fatal(*args, **kwargs):
    """Prints the arguments and raises."""
    print(*args, **kwargs, file=sys.stderr)
    raise SystemExit(1)


_MAGIC_FILE_NAME = ".artifact_store"
_ARTIFACT_DIR_NAME = "artifacts"
_TAG_DIR_NAME = "tags"
_ARCHIVE_FILE_EXTENSION = ".tar.xz"
_META_FILE_EXTENSION = ".meta.json"
_TAG_REV_SEPARATOR = "__"


def check_artifact_store(storage_path: Path):
    """Check if the given path is a valid artifact store."""
    magic_file = storage_path / _MAGIC_FILE_NAME
    if not storage_path.exists() or not storage_path.is_dir():
        fatal(f"Storage path '{storage_path}' does not exist or is not a directory.")
    if not magic_file.exists():
        fatal(f"Storage path '{storage_path}' is not a valid artifact store (missing {_MAGIC_FILE_NAME} file).")


def init(args):
    """Initialize the artifact store in the given storage path."""
    vprint(f"Initializing artifact store at '{args.storage_root}'")
    storage_path = args.storage_root
    try:
        storage_path.mkdir(parents=True, exist_ok=False)
        magic_file = storage_path / _MAGIC_FILE_NAME
        magic_file.touch()
        vprint(f"Artifact store initialized at '{storage_path}'")
    except Exception as e:
        fatal(f"Failed to initialize artifact store at '{storage_path}': {e}")
    check_artifact_store(storage_path)  # sanity check


def artifact_path(storage_root: Path, namespace: Path) -> Path:
    """Returns the path to the package directory for the current namespace."""
    return storage_root / namespace / _ARTIFACT_DIR_NAME


def tag_path(storage_root: Path, namespace: Path) -> Path:
    """Returns the path to the package directory for the current namespace."""
    return storage_root / namespace / _TAG_DIR_NAME


def tar_filter(exclude_globs, tarinfo):
    """Filter function for tarfile to exclude certain files."""
    for pattern in exclude_globs:
        if fnmatch.fnmatch(tarinfo.name, pattern):
            vprint(f"Excluding '{tarinfo.name}' from archive as per exclude pattern '{pattern}'")
            return None
    return tarinfo


def _tag(tag_link: Path, archive: Path):
    """Helper function to create a tag symlink to the given archive."""
    tag_link.parent.mkdir(parents=True, exist_ok=True)
    vprint(f"Linking tag: '{tag_link}' to '{archive}'")
    if tag_link.is_symlink() or tag_link.exists():
        tag_link.unlink()
    tag_link.symlink_to(archive)


def _get_artifact_location(args, use_tag=True) -> Path:
    """Helper function to get the artifact path based on args."""
    check_artifact_store(args.storage_root)

    path = None
    if args.revision:
        vprint(f"  using revision: {args.revision}")
        path = artifact_path(args.storage_root, args.namespace) / f"{args.name}{_TAG_REV_SEPARATOR}{args.revision}"

    if use_tag and args.tag:
        vprint(f"  using: {args.tag}")
        tag_link = tag_path(args.storage_root, args.namespace) / f"{args.name}{_TAG_REV_SEPARATOR}{args.tag}"
        if not tag_link.is_symlink():
            fatal(f"Tagged artifact '{tag_link}' is not a symlink, cannot retrieve.")
        archive = tag_link.resolve()
        path = archive.with_suffix('')  # remove the archive file extension if it was an archive

    vprint(f"  artifact location: '{path}'")

    return path


def _get_meta_data_path(args, use_tag=True) -> Path:
    """Helper function to get the metadata path based on args."""
    return _get_artifact_location(args, use_tag=use_tag).with_suffix(_META_FILE_EXTENSION)


def _get_archive_path(args, use_tag=True) -> Path:
    """Helper function to get the archive path based on args."""
    return _get_artifact_location(args, use_tag=use_tag).with_suffix(_ARCHIVE_FILE_EXTENSION)


def store(args):
    """Store a file or directory as an artifact."""
    check_artifact_store(args.storage_root)

    vprint(f"Storing artifact '{args.name}'")
    vprint(f"  with globs: '{args.glob}'")
    vprint(f"  using revision: '{args.revision}'")
    vprint(f"  linking tag: {args.tag}")
    vprint(f"  copying files: {args.copy}")

    # check revision does not violate the separator rule
    if _TAG_REV_SEPARATOR in args.revision:
        fatal(f"Revision '{args.revision}' cannot contain '{_TAG_REV_SEPARATOR}'")

    # metadata file location
    meta_filename = _get_meta_data_path(args, use_tag=False)
    if meta_filename.is_file():
        fatal(f"Metadata file '{meta_filename}' already exists, fatal - exiting.")

    # create Metadata object
    meta = ArtifactMetaData({"__API__": "1"})
    meta.add("__created_at", int(time.time()))

    if args.meta:
        for item in args.meta:
            try:
                key, value = meta.add_kv_string(item)
                vprint(f"  add: '{item}' -> '{key}' = '{value}'")
            except ValueError as e:
                fatal(e)

    # Ensure the package directory exists
    artifact_location = _get_artifact_location(args, use_tag=False)
    artifact_location.parent.mkdir(parents=True, exist_ok=True)

    # tar or copy files
    if args.copy:
        raise NotImplementedError("Copying files is not implemented yet.")
    else:
        archive = artifact_location.with_suffix(_ARCHIVE_FILE_EXTENSION)  # no check needed - checked above

        # Expand all include globs
        paths = set()
        for pattern in args.glob:
            vprint(f"  processing glob: '{pattern}'")
            paths.update(glob.glob(pattern, recursive=True))
            vprint(f"  after {paths}'")

        vprint(f"Creating tarball: {archive}, metadata: {meta_filename}")
        # Create a tarball of the specified location
        with lzma.open(archive, "wb", preset=2) as xz:  # preset = 0..9
            with tarfile.open(fileobj=xz, mode="w") as tar:
                for f in paths:
                    print(f"Adding '{f}' to archive")
                    tar.add(f,
                            filter=partial(tar_filter, args.exclude) if args.exclude else None)

        vprint(f"Tarball created: {archive}")

        # Add metadata next to the tarball
        meta.save(meta_filename)

    if args.tag:
        if _TAG_REV_SEPARATOR in args.tag:
            fatal(f"Tag name '{args.tag}' cannot contain '{_TAG_REV_SEPARATOR}'")
        _tag(tag_path(args.storage_root, args.namespace) / f"{args.name}{_TAG_REV_SEPARATOR}{args.tag}", archive)


def retrieve(args):
    """Retrieve an artifact by name and version or tag."""

    vprint(f"Retrieving artifact '{args.name}'")
    vprint(f"  to location '{args.location}'")

    archive = _get_archive_path(args)
    if not archive.is_file():
        fatal(f"Artifact archive '{archive}' does not exist, cannot retrieve.")

    # Ensure the target directory exists
    location = args.location
    location.mkdir(parents=True, exist_ok=True)
    vprint(f"  extracting to: {location}")

    # Extract the tarball to the specified location
    with tarfile.open(archive, "r:xz") as tar:
        if sys.version_info >= (3, 12):
            tar.extractall(path=location, filter='fully_trusted')
        else:  # pragma: no cover
            tar.extractall(path=location)


def tag(args):
    """Tag an existing artifact with a new tag."""

    vprint(f"Tagging artifact '{args.name}'")
    vprint(f"  with new tag: '{args.new_tag}'")

    archive = _get_archive_path(args)
    if not archive.is_file():
        fatal(f"Artifact archive '{archive}' does not exist, cannot tag.")

    # Create the new tag
    if _TAG_REV_SEPARATOR in args.new_tag:
        fatal(f"Tag name '{args.new_tag}' cannot contain '{_TAG_REV_SEPARATOR}'")
    _tag(tag_path(args.storage_root, args.namespace) / f"{args.name}{_TAG_REV_SEPARATOR}{args.new_tag}", archive)


def meta(args):
    """Get and set (optional) metadata of an artifact."""

    vprint(f"Meta-data on artifact '{args.name}'")

    meta_file = _get_meta_data_path(args)
    if not meta_file.is_file():
        fatal(f"Metadata file '{meta_file}' does not exist, cannot read or modify metadata.")

    vprint(f"  reading metadata: '{meta_file}'")

    meta = ArtifactMetaData()
    meta.load(meta_file)

    for item in args.key_value:
        try:
            key, value = meta.add_kv_string(item)
            vprint(f"  handled: '{item}' -> '{key}' = '{value}'")
        except ValueError as e:
            fatal(e)

    print(meta.dump(show_hidden=args.show_hidden))
    meta.save(meta_file)


def list_command(args):
    """List namespaces, artifacts, revisions or tags."""
    check_artifact_store(args.storage_root)

    if args.namespaces:
        # namespaces are directories containing an _ARTIFACT_DIR_NAME subdirectory
        namespaces = [str(p.relative_to(args.storage_root))
                      for p in args.storage_root.rglob('*')
                      if p.is_dir() and (p / _ARTIFACT_DIR_NAME).is_dir()]
        print('\n'.join(sorted(namespaces)))

    elif args.artifacts:
        artifact_dir = args.storage_root / args.artifacts / _ARTIFACT_DIR_NAME
        if not artifact_dir.is_dir():
            fatal(f"Namespace '{args.artifacts}' does not exist in the artifact store.")

        # artifacts are files or directories having a meta-file in the same directory with the same name
        artifacts = [str(p.relative_to(artifact_dir)).rsplit(_TAG_REV_SEPARATOR, 1)[0]
                     for p in artifact_dir.glob('*')
                     if Path(str(p).replace(_ARCHIVE_FILE_EXTENSION, "")).with_suffix(_META_FILE_EXTENSION).is_file()]
        print('\n'.join(sorted(set(artifacts))))

    elif args.revisions:
        ns, artifact = args.revisions
        artifact_dir = args.storage_root / ns / _ARTIFACT_DIR_NAME
        if not artifact_dir.is_dir():
            fatal(f"Namespace '{ns}' does not exist in the artifact store.")

        # revisions are files or directories having a meta-file in the same directory with the same name
        # the revision is the part after the separator in the name, without the archive extension
        revisions = [
            str(p.relative_to(artifact_dir)).replace(_ARCHIVE_FILE_EXTENSION, "").rsplit(_TAG_REV_SEPARATOR, 1)[1]
            for p in artifact_dir.glob(f'{artifact}{_TAG_REV_SEPARATOR}*')
            if Path(str(p).replace(_ARCHIVE_FILE_EXTENSION, "")).with_suffix(_META_FILE_EXTENSION).is_file()
               and p.is_dir() or str(p).endswith(_ARCHIVE_FILE_EXTENSION)]
        if not revisions:
            fatal(f"No revisions found for artifact '{artifact}' in namespace '{ns}'.")

        print('\n'.join(sorted(revisions)))

    elif args.tags:
        ns, artifact = args.tags
        tags_dir = args.storage_root / ns / _TAG_DIR_NAME
        if not tags_dir.is_dir():
            fatal(f"Namespace '{ns}' does not exist in the artifact store.")

        # tags are symlinks in the tag-directory of a namespace pointing to an artifact
        tags = [str(p.relative_to(tags_dir)).rsplit(_TAG_REV_SEPARATOR, 1)[1]
                for p in tags_dir.glob(f'{artifact}{_TAG_REV_SEPARATOR}*')
                if p.is_symlink()]
        print('\n'.join(sorted(tags)))
    else:  # pragma: no cover
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(description="Artifact Store interaction script")

    # Global (main) arguments
    parser.add_argument("-s", "--storage-root", type=Path, help="storage path (root of artifact store), "
                                                                "default: ARTIFACT_STORE_ROOT-environment-variable",
                        default=os.getenv("ARTIFACT_STORE_ROOT", None))
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    # Subparsers for subcommands
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: init
    parser_init = subparsers.add_parser("init", help="Initialize artifact store in the storage path")
    parser_init.set_defaults(func=init)

    # Subcommand: store
    parser_store = subparsers.add_parser("store", help="Store file/directory as artifact")
    parser_store.add_argument("-t", "--tag", type=str, help="tag artifact with a tag name (e.g. latest)")
    parser_store.add_argument("-r", "--revision", type=str, required=True, help="revision/unique-id of artifact")
    parser_store.add_argument("-c", "--copy", action="store_true", default=False,
                              help="copy files instead of creating a tar-package")
    parser_store.add_argument("-m", "--meta", action="append", help="Key-value pairs like key=value for metadata"
                                                                    "added to the artifact")
    parser_store.add_argument("-e", "--exclude", action="append", default=[],
                              help="a glob of directories or files to be excluded")

    parser_store.add_argument("namespace", type=str, help="namespace of the artifact")
    parser_store.add_argument("name", type=str, help="name of artifact")
    parser_store.add_argument("glob", type=str, nargs='+', help="globs for files and directories to store")

    parser_store.set_defaults(func=store)

    # Subcommand: retrieve
    parser_retrieve = subparsers.add_parser("retrieve", help="Retrieve a file an artifact")

    group = parser_retrieve.add_mutually_exclusive_group(required=True)
    group.add_argument("-t", "--tag", type=str, help="retrieve tag of artifact")
    group.add_argument("-r", "--revision", type=str, help="revision/unique-id of artifact to retrieve")

    parser_retrieve.add_argument("namespace", type=str, help="namespace of the artifact")
    parser_retrieve.add_argument("name", type=str, help="name of artifact")
    parser_retrieve.add_argument("location", type=Path, help="local directory location to retrieve to")

    parser_retrieve.set_defaults(func=retrieve)

    # Subcommand: tag
    parser_tag = subparsers.add_parser("tag", help="Tag an existing artifact with a new tag")
    group = parser_tag.add_mutually_exclusive_group(required=True)
    group.add_argument("-t", "--tag", type=str, help="tag artifact with a tag name (e.g. latest)")
    group.add_argument("-r", "--revision", type=str, help="revision/unique-id of artifact to tag")

    parser_tag.add_argument("namespace", type=str, help="namespace of the artifact")
    parser_tag.add_argument("name", type=str, help="name of artifact")
    parser_tag.add_argument("new_tag", type=str, help="new tag name to assign to the artifact")

    parser_tag.set_defaults(func=tag)

    parser_meta = subparsers.add_parser("meta", help="Retrieve metadata of an artifact")

    group = parser_meta.add_mutually_exclusive_group(required=True)
    group.add_argument("-t", "--tag", type=str, help="tag artifact with a tag name (e.g. latest)")
    group.add_argument("-r", "--revision", type=str, help="revision/unique-id of artifact to tag")

    parser_meta.add_argument("-H", "--show-hidden", action="store_true", help="show hidden metadata "
                                                                              "keys (starting with __)")
    parser_meta.add_argument("namespace", type=str, help="namespace of the artifact")
    parser_meta.add_argument("name", type=str, help="name of artifact")
    parser_meta.add_argument("key_value", type=str, nargs='*', help="set, replace or delete metadata key-value pairs"
                                                                    "like key=value or key= (to delete)")

    parser_meta.set_defaults(func=meta)

    parser_list = subparsers.add_parser("list", help="List all available projects, artifacts, revisions and tags")

    group = parser_list.add_mutually_exclusive_group(required=True)

    # -n: list namespaces
    group.add_argument("-n", "--namespaces", action="store_true", help="List all namespaces")

    # -a <namespace>: list artifacts in a namespace
    group.add_argument("-a", "--artifacts", metavar="NAMESPACE", help="List all artifacts in a namespace")

    # -r <namespace> <artifact-name>: list revisions of an artifact
    group.add_argument("-r", "--revisions", nargs=2, metavar=("NAMESPACE", "ARTIFACT"),
                       help="List revisions of an artifact")

    # -t <namespace> <artifact-name>: list tags of an artifact
    group.add_argument("-t", "--tags", nargs=2, metavar=("NAMESPACE", "ARTIFACT"),
                       help="List tags of an artifact")

    parser_list.set_defaults(func=list_command)

    args = parser.parse_args(argv)
    global _verbose
    _verbose = args.verbose

    # bail out if storage is not set
    if args.storage_root is None:
        fatal("Storage path is not provided. Please set the --storage-root argument or "
              "the ARTIFACT_STORE_ROOT environment variable.")

    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
