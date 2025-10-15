"""Core processing functions for nemorosa."""

import traceback
from enum import Enum
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

import msgspec
import torf
from pydantic import BaseModel, Field

from . import client_instance, config, db, filecompare, filelinking, logger
from .api import get_target_apis
from .clients import ClientTorrentInfo, TorrentConflictError

if TYPE_CHECKING:
    from .api import GazelleJSONAPI, GazelleParser


class ProcessStatus(Enum):
    """Status enumeration for process operations."""

    SUCCESS = "success"
    NOT_FOUND = "not_found"
    ERROR = "error"
    SKIPPED = "skipped"
    SKIPPED_POTENTIAL_TRUMP = "skipped_potential_trump"


class ProcessorStats(msgspec.Struct):
    """Statistics for torrent processing session."""

    found: int = 0
    downloaded: int = 0
    scanned: int = 0
    cnt_dl_fail: int = 0
    attempted: int = 0
    successful: int = 0
    failed: int = 0
    removed: int = 0


class PostProcessStats(msgspec.Struct):
    """Statistics for post-processing injected torrents."""

    matches_checked: int = 0
    matches_completed: int = 0
    matches_started_downloading: int = 0
    matches_already_downloading: int = 0
    matches_failed: int = 0


class ProcessResponse(BaseModel):
    """Response model for process operations."""

    status: ProcessStatus = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "success",
                    "message": "Successfully processed torrent: name (infohash)",
                },
                {
                    "status": "skipped",
                    "message": "Torrent already exists on all target trackers: [tracker1, tracker2]",
                },
            ]
        }
    }


class NemorosaCore:
    """Main class for processing torrents and cross-seeding operations."""

    stats: ProcessorStats

    def __init__(self):
        """Initialize the torrent processor."""
        self.torrent_client = client_instance.get_torrent_client()
        self.database = db.get_database()
        self.stats = ProcessorStats()
        self.logger = logger.get_logger()

    async def hash_based_search(
        self,
        *,
        torrent_object: torf.Torrent,
        api: "GazelleJSONAPI | GazelleParser",
    ) -> int | None:
        """Search for torrent using hash-based search.

        Args:
            torrent_object (torf.Torrent): Torrent object for hash calculation.
            api: API instance for the target site.

        Returns:
            int | None: Torrent ID if found, None otherwise.
        """
        self.logger.debug("Trying hash-based search first")

        # Get target source flag from API
        target_source_flag = api.source_flag

        source_flags = [target_source_flag, ""]

        # Define possible source flags for the target tracker
        # This should match the logic in fertilizer
        if target_source_flag == "RED":
            source_flags.append("PTH")
        elif target_source_flag == "OPS":
            source_flags.append("APL")

        # Create a copy of the torrent and try different source flags
        for flag in source_flags:
            try:
                torrent_object.source = flag

                # Calculate hash
                torrent_hash = torrent_object.infohash

                # Search torrent by hash
                search_result = await api.search_torrent_by_hash(torrent_hash)
                if search_result:
                    self.logger.success(f"Found torrent by hash! Hash: {torrent_hash}")

                    # Get torrent ID from search result
                    torrent_id = search_result["response"]["torrent"]["id"]
                    if torrent_id:
                        tid = int(torrent_id)
                        self.logger.success(f"Found match! Torrent ID: {tid}")
                        return tid
            except Exception as e:
                self.logger.debug(f"Hash search failed for source '{flag}': {e}")
                raise

        return None

    async def filename_search(
        self,
        *,
        fdict: dict[str, int],
        tsize: int,
        api: "GazelleJSONAPI | GazelleParser",
    ) -> int | None:
        """Search for torrent using filename-based search.

        Args:
            fdict (dict): File dictionary mapping filename to size.
            tsize (int): Total size of the torrent.
            api: API instance for the target site.

        Returns:
            int | None: Torrent ID if found, None otherwise.
        """
        self.logger.debug("No torrent found by hash, falling back to filename search")
        # search for the files with top 5 longest name
        tid = None
        scan_querys = []
        max_fnames = sorted(fdict.keys(), key=len, reverse=True)
        for index, fname in enumerate(max_fnames):
            if index == 0 or filecompare.is_music_file(fname):
                scan_querys.append(fname)
            if len(scan_querys) >= 5:
                break

        for fname in scan_querys:
            self.logger.debug(f"Searching for file: {fname}")
            fname_query = fname
            try:
                torrents = await api.search_torrent_by_filename(fname_query)
            except Exception as e:
                self.logger.error(f"Error searching for file '{fname_query}': {e}")
                raise

            # Record the number of results found
            self.logger.debug(f"Found {len(torrents)} potential matches for file '{fname_query}'")

            # If no results found and it's a music file, try make filename query and search again
            if len(torrents) == 0 and filecompare.is_music_file(fname):
                fname_query = filecompare.make_filename_query(fname)
                if fname_query != fname:
                    self.logger.debug(
                        f"No results found for '{fname}', trying fallback search with basename: '{fname_query}'"
                    )
                    try:
                        fallback_torrents = await api.search_torrent_by_filename(fname_query)
                        if fallback_torrents:
                            torrents = fallback_torrents
                            self.logger.debug(
                                f"Fallback search found {len(torrents)} potential matches for '{fname_query}'"
                            )
                        else:
                            self.logger.debug(f"Fallback search also found no results for '{fname_query}'")
                    except Exception as e:
                        self.logger.error(f"Error in fallback search for file basename '{fname_query}': {e}")
                        raise

            # Match by total size
            size_match_found = False
            for t in torrents:
                if tsize == t["size"]:
                    tid = t["torrentId"]
                    size_match_found = True
                    self.logger.success(f"Size match found! Torrent ID: {tid} (Size: {tsize})")
                    break

            if size_match_found:
                break

            # Handle cases with too many results
            if len(torrents) > 20:
                self.logger.warning(f"Too many results found for file '{fname_query}' ({len(torrents)}). Skipping.")
                continue

            # Match by file content
            if tid is None:
                self.logger.debug(f"No size match found. Checking file contents for '{fname_query}'")
                tid = await self.match_by_file_content(
                    torrents=torrents,
                    fname=fname,
                    fdict=fdict,
                    scan_querys=scan_querys,
                    api=api,
                )

            # If match found, exit early
            if tid is not None:
                self.logger.debug(f"Match found with file '{fname}'. Stopping search.")
                break

            self.logger.debug(f"No more results for file '{fname}'")
            if filecompare.is_music_file(fname):
                self.logger.debug("Stopping search as music file match is not found")
                break

        return tid

    async def _search_torrent_by_filename_in_client(self, torrent_fdict: dict[str, int]) -> list[ClientTorrentInfo]:
        """Search for matching torrents in client by filename using database.

        Args:
            torrent_fdict (dict): File dictionary of the incoming torrent.

        Returns:
            list: List of matching ClientTorrentInfo objects.
        """
        try:
            matched_torrents = []

            # Get incoming torrent file list, sorted by filename length (longest first)
            torrent_files = sorted(torrent_fdict.keys(), key=len, reverse=True)

            # Select top 5 longest filenames for search
            scan_queries = []
            for index, fname in enumerate(torrent_files):
                if index == 0 or filecompare.is_music_file(fname):
                    scan_queries.append(fname)
                if len(scan_queries) >= 5:
                    break

            self.logger.debug(f"Searching with {len(scan_queries)} file queries: {scan_queries}")

            for fname in scan_queries:
                self.logger.debug(f"Searching for file: {fname}")

                # Get the file size to match
                target_file_size = torrent_fdict[fname]

                # Use make_filename_query to process filename
                fname_query = filecompare.make_filename_query(fname)
                if not fname_query:
                    continue

                fname_query_words = fname_query.split()

                # Get matching torrents from client's database cache
                candidate_torrents = await self.torrent_client.get_file_matched_torrents(
                    target_file_size=target_file_size, fname_keywords=fname_query_words
                )

                self.logger.debug(f"Found {len(candidate_torrents)} candidate torrents")

                # Verify each candidate for conflicts
                for candidate in candidate_torrents:
                    self.logger.debug(f"Verifying candidate torrent: {candidate.name}")

                    # Database query already ensured size and name match, only check conflicts
                    if config.cfg.linking.enable_linking or not filecompare.check_conflicts(
                        candidate.fdict, torrent_fdict
                    ):
                        self.logger.success(f"Complete torrent match found: {candidate.name}")
                        matched_torrents.append(candidate)
                    else:
                        self.logger.debug(f"Match found but has conflicts: {candidate.name}")

                # If matching torrent found, can return early
                if matched_torrents:
                    break

                # If music file and no match found, stop searching
                if filecompare.is_music_file(fname):
                    self.logger.debug("Stopping search as music file match is not found")
                    break

            return matched_torrents

        except Exception as e:
            self.logger.error(f"Error searching torrent by filename in client: {e}")
            return []

    async def match_by_file_content(
        self,
        *,
        torrents: list[dict],
        fname: str,
        fdict: dict,
        scan_querys: list[str],
        api: "GazelleJSONAPI | GazelleParser",
    ) -> int | None:
        """Match torrents by file content.

        Args:
            torrents (list[dict]): List of torrents to check.
            fname (str): Original filename.
            fdict (dict): File dictionary mapping filename to size.
            scan_querys (list[str]): List of scan queries.
            api: API instance for the target site.

        Returns:
            int | None: Torrent ID if found, None otherwise.
        """
        for t_index, t in enumerate(torrents, 1):
            self.logger.debug(f"Checking torrent #{t_index}/{len(torrents)}: ID {t['torrentId']}")

            resp = await api.torrent(t["torrentId"])
            resp_files = resp.get("fileList", {})

            check_music_file = fname if filecompare.is_music_file(fname) else scan_querys[-1]

            # For music files, byte-level size comparison is sufficient for identical matching
            # as it provides reliable file identification without requiring full content comparison
            if fdict[check_music_file] in resp_files.values():
                # Check file conflicts
                if config.cfg.linking.enable_linking or not filecompare.check_conflicts(fdict, resp_files):
                    self.logger.success(f"File match found! Torrent ID: {t['torrentId']} (File: {check_music_file})")
                    return t["torrentId"]
                else:
                    self.logger.debug("Conflict detected. Skipping this torrent.")
                    return None

        return None

    async def process_torrent_search(
        self,
        *,
        torrent_details: ClientTorrentInfo,
        api: "GazelleJSONAPI | GazelleParser",
        torrent_object: torf.Torrent | None = None,
    ):
        """Process torrent search and injection.

        Args:
            torrent_details (ClientTorrentInfo): Torrent details from client.
            api: API instance for the target site.
            torrent_object (torf.Torrent, optional): Original torrent object for hash search.

        Returns:
            tuple[int | None, bool]: (torrent_id, downloaded) - torrent ID and download success status.
        """
        self.stats.scanned += 1

        tid = None
        hash_match = True

        # Track if any search method failed with an error
        search_error_occurred = False

        # Try hash-based search first if torrent object is available
        if torrent_object:
            try:
                tid = await self.hash_based_search(torrent_object=torrent_object, api=api)
            except Exception as e:
                self.logger.error(f"Hash-based search failed: {e}")
                search_error_occurred = True

        # If hash search didn't find anything, try filename search
        if tid is None:
            try:
                tid = await self.filename_search(fdict=torrent_details.fdict, tsize=torrent_details.total_size, api=api)
                hash_match = False
            except Exception as e:
                self.logger.error(f"Filename search failed: {e}")
                search_error_occurred = True

        # Handle no match found case
        if tid is None:
            self.logger.header("No matching torrent found")

            # Record scan result: no matching torrent found
            if not search_error_occurred:
                await self.database.add_scan_result(
                    local_torrent_hash=torrent_details.hash,
                    local_torrent_name=torrent_details.name,
                    matched_torrent_id=None,
                    site_host=api.site_host,
                    matched_torrent_hash=None,
                )
            return None, False

        # Found a match
        self.stats.found += 1
        self.logger.success(f"Found match! Torrent ID: {tid}")

        # If found via hash search, modify the existing torrent for the new tracker
        # Otherwise, download the torrent data
        if hash_match:
            assert torrent_object is not None
            torrent_object.comment = api.get_torrent_url(tid)
            torrent_object.trackers = [api.announce]
            torrent_data = torrent_object.dump()
        else:
            torrent_data = await api.download_torrent(tid)
            if torrent_data is None:
                raise ValueError("Failed to download torrent data")
            torrent_object = torf.Torrent.read_stream(torrent_data)

        # Generate file dictionary and rename map
        fdict_torrent = {"/".join(f.parts[1:]): f.size for f in torrent_object.files}

        rename_map = filecompare.generate_rename_map(torrent_details.fdict, fdict_torrent)

        # Handle file linking and rename map based on configuration
        if config.cfg.linking.enable_linking:
            # Generate link map for file linking
            file_mapping = filecompare.generate_link_map(torrent_details.fdict, fdict_torrent)
            # File linking mode: create links first, then add torrent with linked directory
            final_download_dir = filelinking.create_file_links_for_torrent(
                torrent_object, torrent_details.download_dir, torrent_details.name, file_mapping
            )
            if final_download_dir is None:
                self.logger.error("Failed to create file links, falling back to original directory")
                final_download_dir = torrent_details.download_dir
        else:
            # Normal mode: generate rename map for file renaming
            final_download_dir = torrent_details.download_dir

        # Inject torrent and handle renaming
        downloaded = False
        if not config.cfg.global_config.no_download:
            try:
                success, _ = self.torrent_client.inject_torrent(
                    torrent_data, final_download_dir, torrent_details.name, rename_map, hash_match
                )
                if success:
                    downloaded = True
                    self.stats.downloaded += 1
                    self.logger.success("Torrent injected successfully")
                else:
                    self.logger.error(f"Failed to inject torrent: {tid}")
                    self.stats.cnt_dl_fail += 1
                    if self.stats.cnt_dl_fail <= 10:
                        self.logger.error(traceback.format_exc())
                        self.logger.error(
                            f"It might because the torrent id {tid} has reached the "
                            f"limitation of non-browser downloading of {api.server}. "
                            f"The failed download info will be saved to database. "
                            "You can download it from your own browser."
                        )
                        if self.stats.cnt_dl_fail == 10:
                            self.logger.debug("Suppressing further hinting for .torrent file downloading failures")
            except TorrentConflictError as e:
                # Torrent conflict - treat as no match found
                self.logger.debug(f"Torrent conflict detected: {e}")
                # Record scan result: no matching torrent found
                await self.database.add_scan_result(
                    local_torrent_hash=torrent_details.hash,
                    local_torrent_name=torrent_details.name,
                    matched_torrent_id=None,
                    site_host=api.site_host,
                    matched_torrent_hash=None,
                )
                return None, False

        # Record scan result: matching torrent found
        await self.database.add_scan_result(
            local_torrent_hash=torrent_details.hash,
            local_torrent_name=torrent_details.name,
            matched_torrent_id=str(tid),
            site_host=api.site_host,
            matched_torrent_hash=torrent_object.infohash,
        )
        if not downloaded:
            torrent_info = {
                "download_dir": final_download_dir,
                "local_torrent_name": torrent_details.name,
                "rename_map": rename_map,
            }
            await self.database.add_undownloaded_torrent(str(tid), torrent_info, api.site_host)

        # Start tracking verification after database operations are complete
        if downloaded:
            await self.torrent_client.track_verification(torrent_object.infohash)

        return tid, downloaded

    async def process_single_torrent_from_client(
        self,
        torrent_details: ClientTorrentInfo,
    ) -> bool:
        """Process a single torrent from client torrent list.

        Args:
            torrent_details (ClientTorrentInfo): Torrent details from client.

        Returns:
            bool: True if any target site was successful, False otherwise.
        """

        # Try to get torrent data from torrent client for hash search
        torrent_object = self.torrent_client.get_torrent_object(torrent_details.hash)

        # Scan and match for each target site
        any_success = False
        existing_target_trackers = set(torrent_details.existing_target_trackers)

        for api_instance in get_target_apis():
            # Check if torrent has been scanned on this specific site
            if await self.database.is_hash_scanned(
                local_torrent_hash=torrent_details.hash, site_host=api_instance.site_host
            ):
                self.logger.debug(
                    "Skipping already scanned torrent on %s: %s (%s)",
                    api_instance.site_host,
                    torrent_details.name,
                    torrent_details.hash,
                )
                continue
            self.logger.debug(f"Trying target site: {api_instance.server} (tracker: {api_instance.tracker_query})")

            # Check if this content already exists on current target tracker
            if api_instance.tracker_query in existing_target_trackers:
                self.logger.debug(f"Content already exists on {api_instance.tracker_query}, skipping")
                continue

            try:
                # Scan and match
                tid, _ = await self.process_torrent_search(
                    torrent_details=torrent_details,
                    api=api_instance,
                    torrent_object=torrent_object,  # Pass torrent object for hash search
                )

                if tid is not None:
                    any_success = True
                    self.logger.success(f"Successfully processed on {api_instance.server}")

            except Exception as e:
                self.logger.error(f"Error processing torrent on {api_instance.server}: {e}")
                continue

        return any_success

    async def process_torrents(self):
        """Process torrents in client, supporting multiple target sites."""
        self.logger.section("===== Processing Torrents =====")

        # Extract target_trackers from target_apis
        target_trackers = [api_instance.tracker_query for api_instance in get_target_apis()]

        # Reset stats for this processing session
        self.stats = ProcessorStats()

        try:
            # Get filtered torrent list
            torrents = await self.torrent_client.get_filtered_torrents(target_trackers)
            self.logger.debug("Found %d torrents in client matching the criteria", len(torrents))

            for i, (torrent_name, torrent_details) in enumerate(torrents.items()):
                self.logger.header(
                    "Processing %d/%d: %s (%s)",
                    i + 1,
                    len(torrents),
                    torrent_name,
                    torrent_details.hash,
                )

                # Process single torrent
                any_success = await self.process_single_torrent_from_client(
                    torrent_details=torrent_details,
                )

                # Record processed torrents (scan history handled inside scan function)
                if any_success:
                    self.logger.success("Torrent processed successfully")

        except Exception as e:
            self.logger.error("Error processing torrents: %s", e)
            self.logger.error(traceback.format_exc())
        finally:
            self.logger.success("Torrent processing summary:")
            self.logger.success("Torrents scanned: %d", self.stats.scanned)
            self.logger.success("Matches found: %d", self.stats.found)
            self.logger.success(".torrent files downloaded: %d", self.stats.downloaded)
            self.logger.section("===== Torrent Processing Complete =====")

    async def retry_undownloaded_torrents(self):
        """Re-download undownloaded torrents."""
        self.logger.section("===== Retrying Undownloaded Torrents =====")

        # Reset retry stats
        retry_stats = ProcessorStats()

        try:
            # Process undownloaded torrents for each target site
            for api_instance in get_target_apis():
                self.logger.debug(f"Processing undownloaded torrents for site: {api_instance.server}")

                # Get undownloaded torrents for this site
                undownloaded_torrents = await self.database.load_undownloaded_torrents(api_instance.site_host)

                if not undownloaded_torrents:
                    self.logger.debug(f"No undownloaded torrents found for site: {api_instance.server}")
                    continue

                self.logger.debug(
                    f"Found {len(undownloaded_torrents)} undownloaded torrents for site: {api_instance.server}"
                )

                for torrent_id, torrent_info in undownloaded_torrents.items():
                    retry_stats.attempted += 1
                    self.logger.header(
                        f"Retrying torrent ID: {torrent_id} ({retry_stats.attempted}/{len(undownloaded_torrents)})"
                    )

                    try:
                        # Download torrent data
                        torrent_data = await api_instance.download_torrent(torrent_id)

                        # Get torrent information
                        download_dir = torrent_info.get("download_dir", "")
                        local_torrent_name = torrent_info.get("local_torrent_name", "")
                        rename_map = torrent_info.get("rename_map", {})

                        self.logger.debug(f"Attempting to inject torrent: {local_torrent_name}")
                        self.logger.debug(f"Download directory: {download_dir}")
                        self.logger.debug(f"Rename map: {rename_map}")

                        # Try to inject torrent into client
                        success, _ = self.torrent_client.inject_torrent(
                            torrent_data, download_dir, local_torrent_name, rename_map, False
                        )
                        if success:
                            retry_stats.successful += 1
                            retry_stats.removed += 1

                            # Injection successful, remove from undownloaded table
                            await self.database.remove_undownloaded_torrent(torrent_id, api_instance.site_host)
                            self.logger.success(f"Successfully downloaded and injected torrent {torrent_id}")
                            self.logger.success(f"Removed torrent {torrent_id} from undownloaded list")
                        else:
                            retry_stats.failed += 1
                            self.logger.error(f"Failed to inject torrent {torrent_id}")

                    except Exception as e:
                        retry_stats.failed += 1
                        self.logger.error(f"Error processing torrent {torrent_id}: {e}")
                        continue

        except Exception as e:
            self.logger.error("Error retrying undownloaded torrents: %s", e)
            self.logger.error(traceback.format_exc())
        finally:
            self.logger.success("Retry undownloaded torrents summary:")
            self.logger.success("Torrents attempted: %d", retry_stats.attempted)
            self.logger.success("Successfully downloaded: %d", retry_stats.successful)
            self.logger.success("Failed downloads: %d", retry_stats.failed)
            self.logger.success("Removed from undownloaded list: %d", retry_stats.removed)
            self.logger.section("===== Retry Undownloaded Torrents Complete =====")

    async def post_process_injected_torrents(self):
        """Post-process previously injected torrents to start downloading completed torrents.

        This function checks previously found cross-seed matches in scan_results,
        verifies if local torrents are 100% complete, and starts downloading the matched
        torrents for cross-seeding. The matched torrents are already added to the client,
        we just need to start downloading them when the local torrents reach 100% completion.
        """
        self.logger.section("===== Post-Processing Injected Torrents =====")

        # Reset stats for injected torrents processing
        stats = PostProcessStats()

        try:
            # Get all matched scan results
            matched_results = await self.database.get_matched_scan_results()
            if not matched_results:
                self.logger.debug("No matched torrents found")
                return

            self.logger.info(f"Found {len(matched_results)} matched torrents")

            # Process all matched results
            for matched_torrent_hash in matched_results:
                stats.matches_checked += 1

                # Process single torrent
                result = await self.torrent_client.post_process_single_injected_torrent(matched_torrent_hash)

                # Update stats based on result
                if result.status == "completed":
                    stats.matches_completed += 1
                    if result.started_downloading:
                        stats.matches_started_downloading += 1
                elif result.status == "partial_kept":
                    # Partial torrent kept, no action needed
                    pass
                elif result.status in ("partial_removed", "error"):
                    stats.matches_failed += 1
                # For "not_found" and "checking" status, no stats update needed

        except Exception as e:
            self.logger.error("Error processing injected torrents: %s", e)
            self.logger.error(traceback.format_exc())
        finally:
            self.logger.success("Injected torrents post-processing summary:")
            self.logger.success("Matches checked: %d", stats.matches_checked)
            self.logger.success("Matches completed: %d", stats.matches_completed)
            self.logger.success("Matches started downloading: %d", stats.matches_started_downloading)
            self.logger.success("Matches already downloading: %d", stats.matches_already_downloading)
            self.logger.success("Matches failed: %d", stats.matches_failed)
            self.logger.section("===== Injected Torrents Post-Processing Complete =====")

    async def process_single_torrent(
        self,
        infohash: str,
    ) -> ProcessResponse:
        """Process a single torrent by infohash from torrent client.

        Args:
            infohash (str): Infohash of the torrent to process.

        Returns:
            ProcessResponse: Processing result with status and details.
        """

        try:
            # Extract target_trackers from target_apis
            target_trackers = [api_instance.tracker_query for api_instance in get_target_apis()]

            # Get torrent details from torrent client with existing trackers info
            torrent_info = self.torrent_client.get_single_torrent(infohash, target_trackers)

            if not torrent_info:
                return ProcessResponse(
                    status=ProcessStatus.ERROR,
                    message=f"Torrent with infohash {infohash} not found in client or was filtered out",
                )

            # Check if torrent already exists on all target trackers
            existing_trackers = set(torrent_info.existing_target_trackers)
            target_tracker_set = set(target_trackers)

            if target_tracker_set.issubset(existing_trackers):
                return ProcessResponse(
                    status=ProcessStatus.SKIPPED,
                    message=f"Torrent already exists on all target trackers: {list(existing_trackers)}",
                )

            # Process the torrent using the same logic as process_single_torrent_from_client
            any_success = await self.process_single_torrent_from_client(
                torrent_details=torrent_info,
            )

            if any_success:
                return ProcessResponse(
                    status=ProcessStatus.SUCCESS,
                    message=f"Successfully processed torrent: {torrent_info.name} ({infohash})",
                )
            else:
                return ProcessResponse(
                    status=ProcessStatus.NOT_FOUND,
                    message=f"No matching torrents found for: {torrent_info.name} ({infohash})",
                )

        except Exception as e:
            self.logger.error(f"Error processing single torrent {infohash}: {str(e)}")
            return ProcessResponse(status=ProcessStatus.ERROR, message=f"Error processing torrent: {str(e)}")

    async def process_reverse_announce_torrent(
        self,
        torrent_name: str,
        torrent_link: str,
        torrent_data: bytes,
    ) -> ProcessResponse:
        """Process a single announce torrent for cross-seeding.

        Args:
            torrent_name (str): Name of the torrent.
            torrent_link (str): Torrent link containing the torrent ID.
            torrent_data (bytes): Torrent file data.

        Returns:
            ProcessResponse: Processing result with status and details.
        """
        try:
            # Extract torrent ID from torrent_link
            parsed_link = urlparse(torrent_link)
            query_params = parse_qs(parsed_link.query)
            tid = query_params["id"][0]

            self.logger.debug(f"Extracted torrent ID: {tid} from link: {torrent_link}")

            # Refresh client torrent cache
            await self.torrent_client.refresh_client_torrents_cache()

            # Parse incoming torrent data
            torrent_object = torf.Torrent.read_stream(torrent_data)
            fdict_torrent = {"/".join(f.parts[1:]): f.size for f in torrent_object.files}

            # Search for matching torrents using database (no need to load all torrents)
            matched_torrents = await self._search_torrent_by_filename_in_client(fdict_torrent)

            if not matched_torrents:
                return ProcessResponse(
                    status=ProcessStatus.NOT_FOUND,
                    message=f"No matching torrent found in client for: {torrent_name}",
                )

            # Check if incoming torrent may trump local torrent
            for matched_torrent in matched_torrents:
                for api_instance in get_target_apis():
                    # Check if local matched torrent contains tracker consistent with incoming torrent
                    local_hostname = urlparse(matched_torrent.trackers[0]).hostname
                    incoming_hostname = urlparse(torrent_object.trackers.flat[0]).hostname
                    if (
                        local_hostname is not None
                        and incoming_hostname is not None
                        and api_instance.tracker_query in local_hostname
                        and api_instance.tracker_query in incoming_hostname
                    ):
                        self.logger.warning(
                            f"Incoming torrent {tid} may trump local torrent {matched_torrent.hash}, "
                            "skipping processing"
                        )
                        return ProcessResponse(
                            status=ProcessStatus.SKIPPED_POTENTIAL_TRUMP,
                            message=f"Local torrent {matched_torrent.hash} may be trumped, skipping processing",
                        )

            # Use the first matching torrent
            matched_torrent = max(matched_torrents, key=lambda x: len(x.files))
            self.logger.success(f"Found matching torrent in client: {matched_torrent.name}")

            # Use client's file dictionary
            rename_map = filecompare.generate_rename_map(matched_torrent.fdict, fdict_torrent)

            # Handle file linking and rename map based on configuration
            if config.cfg.linking.enable_linking:
                # Generate link map for file linking
                file_mapping = filecompare.generate_link_map(matched_torrent.fdict, fdict_torrent)
                # File linking mode: create links first, then add torrent with linked directory
                final_download_dir = filelinking.create_file_links_for_torrent(
                    torrent_object, matched_torrent.download_dir, matched_torrent.name, file_mapping
                )
                if final_download_dir is None:
                    self.logger.error("Failed to create file links, falling back to original directory")
                    final_download_dir = matched_torrent.download_dir
            else:
                # Normal mode: use original download directory
                final_download_dir = matched_torrent.download_dir

            # Inject torrent and handle renaming
            downloaded = False
            if not config.cfg.global_config.no_download:
                success, _ = self.torrent_client.inject_torrent(
                    torrent_data, final_download_dir, matched_torrent.name, rename_map, False
                )
                if success:
                    downloaded = True
                    self.stats.downloaded += 1
                    self.logger.success("Torrent injected successfully")
                else:
                    self.logger.error(f"Failed to inject torrent: {tid}")

            if downloaded:
                await self.torrent_client.track_verification(torrent_object.infohash)
            else:
                torrent_info = {
                    "download_dir": final_download_dir,
                    "local_torrent_name": matched_torrent.name,
                    "rename_map": rename_map,
                }
                await self.database.add_undownloaded_torrent(str(tid), torrent_info, str(parsed_link.hostname))

            return ProcessResponse(
                status=ProcessStatus.SUCCESS,
                message=f"Successfully processed reverse announce torrent: {torrent_name}",
            )

        except Exception as e:
            self.logger.error(f"Error processing reverse announce torrent {torrent_name}: {str(e)}")
            return ProcessResponse(status=ProcessStatus.ERROR, message=f"Error processing torrent: {str(e)}")
