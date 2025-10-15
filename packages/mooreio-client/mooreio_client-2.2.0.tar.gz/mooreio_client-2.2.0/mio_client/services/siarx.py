# Copyright 2020-2025 Datum Technology Corporation
# All rights reserved.
#######################################################################################################################
import base64
import os.path
import re
import tarfile
from abc import ABC
from enum import Enum, auto
from http import HTTPMethod
from io import BytesIO
from pathlib import Path
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from semantic_version import Version

from mio_client.core.scheduler import JobScheduler, Job, JobSchedulerConfiguration
from mio_client.core.service import Service, ServiceType
from mio_client.core.ip import Ip
from mio_client.core.model import Model


#######################################################################################################################
# API Entry Point
#######################################################################################################################
def get_services():
    return [SiArxService]


#######################################################################################################################
# Support Classes
#######################################################################################################################
class SiArxMode(Enum):
    NEW_PROJECT = "Initialize new Project"
    UPDATE_PROJECT = "Update existing Project"


class SiArxRequest(Model):
    input_path: Path = Path()
    mode: SiArxMode
    force_update: bool
    project_id: str
    quiet: Optional[bool] = True


class SiArxReport(Model):
    success: Optional[bool] = False
    infos: Optional[List[str]] = []
    warnings: Optional[List[str]] = []
    errors: Optional[List[str]] = []
    output_path: Optional[Path] = Path()

    def infos_report(self) -> List[str]:
        return {}

    def warnings_report(self) -> List[str]:
        return {}

    def error_report(self) -> List[str]:
        return {}


class SiArxResponseFile(Model):
    name: str
    path: str
    replace_user_file: bool


class SiArxResponsePackage(Model):
    name: str
    infos: Optional[List[str]] = []
    warnings: Optional[List[str]] = []
    errors: Optional[List[str]] = []
    payload: Optional[str] = ""
    path: Optional[Path] = Path()
    files: Optional[List[SiArxResponseFile]] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._extract_path: Path = Path()

    @property
    def extract_path(self) -> Path:
        return self._extract_path
    @extract_path.setter
    def extract_path(self, value: Path):
        self._extract_path = value


class SiArxResponseIp(Model):
    sync_id: str
    name: str
    infos: Optional[List[str]] = []
    warnings: Optional[List[str]] = []
    errors: Optional[List[str]] = []
    packages: Optional[List[SiArxResponsePackage]] = []

    def info_report(self) -> List[str]:
        all_infos: List[str] = []
        for package in self.packages:
            all_infos += package.infos
        return all_infos

    def warning_report(self) -> List[str]:
        all_warnings: List[str] = []
        for package in self.packages:
            all_warnings += package.warnings
        return all_warnings

    def error_report(self) -> List[str]:
        all_errors: List[str] = []
        for package in self.packages:
            all_errors += package.errors
        return all_errors


class SiArxResponse(Model):
    success: bool
    job_id: Optional[str] = ""
    project_id: Optional[str] = ""
    project_name: Optional[str] = ""
    project_full_name: Optional[str] = ""
    infos: Optional[List[str]] = []
    warnings: Optional[List[str]] = []
    errors: Optional[List[str]] = []
    ips: Optional[List[SiArxResponseIp]] = []
    project_files_payload: Optional[str] = ""
    files: Optional[List[SiArxResponseFile]] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._extract_path: Path = Path()

    @property
    def extract_path(self) -> Path:
        return self._extract_path
    @extract_path.setter
    def extract_path(self, value: Path):
        self._extract_path = value

    def info_report(self) -> List[str]:
        all_infos: List[str] = []
        for ip in self.ips:
            all_infos += ip.info_report()
        return all_infos

    def warning_report(self) -> List[str]:
        all_warnings: List[str] = []
        for ip in self.ips:
            all_warnings += ip.warning_report()
        return all_warnings

    def error_report(self) -> List[str]:
        all_errors: List[str] = []
        for ip in self.ips:
            all_errors += ip.error_report()
        return all_errors


#######################################################################################################################
# Service
#######################################################################################################################
class SiArxService(Service):
    def __init__(self, rmh: 'RootManager'):
        super().__init__(rmh, 'datum', 'siarx', 'SiArx')
        self._type = ServiceType.CODE_GENERATION
        self._work_path = self.rmh.md / "siarx"

    def is_available(self) -> bool:
        return True

    def create_directory_structure(self):
        self.rmh.create_directory(self._work_path)

    def create_files(self):
        pass

    def get_version(self) -> Version:
        return Version('1.0.0')

    def gen_project(self, request: SiArxRequest) -> SiArxReport:
        report = SiArxReport()
        report.output_path = request.input_path
        response: SiArxResponse
        try:
            data = {
                'project_id': request.project_id,
            }
            raw_response = self.rmh.web_api_call(HTTPMethod.POST, 'siarx/gen', data)
            response = SiArxResponse.model_validate(raw_response.json())
        except Exception as e:
            report.success = False
            report.errors.append(f"SiArx failed to generate response for Project '{request.project_id}': {e}")
            return report
        else:
            report.infos = response.info_report()
            report.warnings = response.warning_report()
            report.errors = response.error_report()
            report.success = response.success
            if response.success:
                self.extract_response(request, response, report)
                if request.mode == SiArxMode.UPDATE_PROJECT:
                    self.update_codebase(request, response, report)
            return report

    def extract_response(self, request: SiArxRequest, response: SiArxResponse, report: SiArxReport):
        if request.mode == SiArxMode.NEW_PROJECT:
            response.extract_path = request.input_path
        else:
            response.extract_path = self._work_path / response.project_name
            self.rmh.create_directory(response.extract_path)
        try:
            tgz_data = base64.b64decode(response.project_files_payload)
            with tarfile.open(fileobj=BytesIO(tgz_data), mode='r:gz') as tar:
                tar.extractall(path=response.extract_path, filter='data')
        except Exception as e:
            report.success = False
            report.errors.append(f"Failed to unpack Project files at path '{request.input_path}': {e}")
        else:
            for ip in response.ips:
                for package in ip.packages:
                    if not request.quiet:
                        self.rmh.info(f"Processing IP {ip.name}/{package.name} ...")
                    if request.mode == SiArxMode.NEW_PROJECT:
                        package.extract_path = request.input_path / package.path
                    else:
                        package.extract_path = self._work_path / package.name
                        self.rmh.create_directory(response.extract_path)
                    try:
                        tgz_data = base64.b64decode(package.payload)
                        with tarfile.open(fileobj=BytesIO(tgz_data), mode='r:gz') as tar:
                            tar.extractall(path=package.extract_path, filter='data')
                    except Exception as e:
                        report.success = False
                        report.errors.append(f"Failed to unpack IP {ip.name}/{package.name} at path '{package.extract_path}': {e}")

    def update_codebase(self, request: SiArxRequest, response: SiArxResponse, report: SiArxReport):
        """
        Parallelized file update:
          - Project-level files first
          - Then per-IP package files
          - For each file: merge pragma sections if the destination exists and replace_user_file is True
        """

        # Build a list of work items to process in parallel.
        # Each item is a tuple describing the source and destination plus flags.
        work_items = []

        # 1) Project-level files
        for file in response.files:
            extracted_file_path: Path = response.extract_path / file.path
            current_file_path: Path = self.rmh.project_root_path / file.path
            work_items.append((
                extracted_file_path,
                current_file_path,
                file.replace_user_file,   # may be True/False
                True                      # is_project_level
            ))

        # 2) Package-level files
        for ip in response.ips or []:
            for package in ip.packages or []:
                for file in package.files or []:
                    extracted_file_path: Path = package.extract_path / file.path
                    # TODO Replace with IP location obtained from DB (if IP exists)
                    current_file_path: Path = (self.rmh.project_root_path / package.path / file.path)
                    work_items.append((
                        extracted_file_path,
                        current_file_path,
                        file.replace_user_file,
                        False                     # is_project_level
                    ))

        # De-duplicate by destination path (last wins). Also avoids two threads writing same file.
        dedup = {}
        for src, dst, replace_user_file, is_project in work_items:
            dedup[str(dst)] = (src, dst, replace_user_file, is_project)
        work_items = list(dedup.values())

        # Worker to process a single file update.
        def _process_one(item):
            src, dst, replace_user_file, is_project = item
            local_warnings = []
            local_errors = []

            try:
                # Skip if source doesn't exist (nothing was generated for it).
                if not self.rmh.file_exists(src):
                    return (local_warnings, [f"Generated file missing: '{src}'"])

                dst_parent = dst.parent
                dst_parent.mkdir(parents=True, exist_ok=True)  # safe even if exists

                if self.rmh.file_exists(dst):
                    # Destination exists
                    if is_project:
                        # Project-level rule: only replace when replace_user_file and force_update are both True
                        if replace_user_file and request.force_update:
                            self.rmh.warning(f"Replacing '{dst}'")
                            self.rmh.move_file(src, dst)
                        else:
                            # Keep user file
                            pass
                    else:
                        # Package-level rule: merge pragma blocks if replace_user_file
                        if replace_user_file:
                            try:
                                user_sections = self.find_user_file_sections(dst)
                            except Exception as e:
                                # If merge failed and --force: replace; else bubble the error
                                if request.force_update:
                                    self.rmh.warning(f"Replacing '{dst}' (merge failed: {e})")
                                    self.rmh.move_file(src, dst)
                                else:
                                    return (local_warnings, [f"Failed reading user sections in '{dst}': {e}"])
                            else:
                                try:
                                    self.replace_generated_file_sections_with_user_contents(src, user_sections)
                                    self.rmh.move_file(src, dst)
                                except Exception as e:
                                    if request.force_update:
                                        self.rmh.warning(f"Replacing '{dst}' (section merge failed: {e})")
                                        self.rmh.move_file(src, dst)
                                    else:
                                        return (local_warnings, [f"Failed merging sections for '{dst}': {e}"])
                        else:
                            # Not allowed to replace user file; leave as-is
                            pass
                else:
                    # Destination does not exist → just move generated file
                    self.rmh.move_file(src, dst)

            except Exception as e:
                local_errors.append(f"Failed to update '{dst}': {e}")

            return (local_warnings, local_errors)

        # Run the workers in parallel and fold results
        max_workers = min(32, (os.cpu_count() or 1) * 5)
        warnings_accum, errors_accum = [], []

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(_process_one, item) for item in work_items]
            for fut in as_completed(futures):
                w, e = fut.result()
                if w:
                    warnings_accum.extend(w)
                if e:
                    errors_accum.extend(e)

        # Aggregate into the report
        report.warnings.extend(warnings_accum)
        report.errors.extend(errors_accum)
        if errors_accum:
            report.success = False

    def find_user_file_sections(self, file: Path) -> Dict:
        file_content: str = ""
        with open(file, 'r') as original_file:
            file_content = original_file.read()
        section_pattern = r"// pragma siarx (\w+) begin(.*?)// pragma siarx \1 end"
        return {match[0]: match[1] for match in re.findall(section_pattern, file_content, re.DOTALL)}

    def replace_generated_file_sections_with_user_contents(self, file: Path, sections: Dict):
        with open(file, 'r') as generated_file:
            generated_file_contents = generated_file.read()
        def replace_section(match):
            section_name = match.group(1)
            original_section_content = sections.get(section_name, match.group(2))
            return f"// pragma siarx {section_name} begin{original_section_content}// pragma siarx {section_name} end"
        updated_content = re.sub(
            r"// pragma siarx (\w+) begin(.*?)// pragma siarx \1 end",
            replace_section,
            generated_file_contents,
            flags=re.DOTALL
        )
        with open(file, 'w') as output_file:
            output_file.write(updated_content)


