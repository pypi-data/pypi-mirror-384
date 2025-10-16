import os
import re
from ..GeneralUtilities import GeneralUtilities
from ..ScriptCollectionCore import ScriptCollectionCore
from ..SCLog import LogLevel
from .TFCPS_Tools_General import TFCPS_Tools_General


class TFCPS_CodeUnit_BuildCodeUnit:

    codeunit_folder: str
    repository_folder: str
    sc: ScriptCollectionCore = ScriptCollectionCore()
    codeunit_name: str
    tFCPS_Tools: TFCPS_Tools_General
    target_environment_type: str
    additionalargumentsfile: str
    use_cache: bool
    is_pre_merge: bool

    def __init__(self, codeunit_folder: str, verbosity: LogLevel, target_environment_type: str, additionalargumentsfile: str, use_cache: bool,is_pre_merge:bool):
        self.sc = ScriptCollectionCore()
        self.sc.log.loglevel = verbosity
        self.tFCPS_Tools = TFCPS_Tools_General(self.sc)
        self.tFCPS_Tools.assert_is_codeunit_folder(codeunit_folder)
        self.codeunit_folder = codeunit_folder
        self.codeunit_name = os.path.basename(self.codeunit_folder)
        self.target_environment_type = target_environment_type
        self.additionalargumentsfile = additionalargumentsfile
        self.use_cache = use_cache
        self.is_pre_merge=is_pre_merge

    @GeneralUtilities.check_arguments
    def build_codeunit(self) -> None:
        codeunit_file: str = str(os.path.join(self.codeunit_folder, f"{self.codeunit_name}.codeunit.xml"))

        if not self.tFCPS_Tools.codeunit_is_enabled(codeunit_file):
            self.sc.log.log(f"Codeunit {self.codeunit_name} is disabled.", LogLevel.Warning)
            return

        self.sc.log.log(f"Build codeunit {self.codeunit_name}...")

        GeneralUtilities.ensure_folder_exists_and_is_empty(self.codeunit_folder+"/Other/Artifacts")

        arguments: str = f"--targetenvironmenttype {self.target_environment_type} --additionalargumentsfile {self.additionalargumentsfile} --verbosity {int(self.sc.log.loglevel)}"
        if not self.use_cache:
            arguments = f"{arguments} --nocache"

        if self.is_pre_merge:
            arguments = f"{arguments} --ispremerge"

        self.sc.log.log("Do common tasks...")
        self.sc.run_program("python", f"CommonTasks.py {arguments}", os.path.join(self.codeunit_folder, "Other"), print_live_output=True)
        self.verify_artifact_exists(self.codeunit_folder, dict[str, bool]({"License": True, "DiffReport": True}))

        self.sc.log.log("Build...")
        self.sc.run_program("python", f"Build.py {arguments}", os.path.join(self.codeunit_folder, "Other", "Build"), print_live_output=True)
        artifacts = {"BuildResult_.+": True, "BOM": False, "SourceCode":  self.tFCPS_Tools.codeunit_has_testable_sourcecode(codeunit_file)}
        self.verify_artifact_exists(self.codeunit_folder, dict[str, bool](artifacts))

        if self.tFCPS_Tools.codeunit_has_testable_sourcecode(codeunit_file):
            self.sc.log.log("Run testcases...")
            self.sc.run_program("python", f"RunTestcases.py {arguments}", os.path.join(self.codeunit_folder, "Other", "QualityCheck"), print_live_output=True)
            self.verify_artifact_exists(self.codeunit_folder, dict[str, bool]({"TestCoverage": True, "TestCoverageReport": False}))

        self.sc.log.log("Check for linting-issues...")
        linting_result = self.sc.run_program("python", f"Linting.py {arguments}", os.path.join(self.codeunit_folder, "Other", "QualityCheck"), print_live_output=True, throw_exception_if_exitcode_is_not_zero=False)
        if linting_result[0] != 0:
            self.sc.log.log("Linting-issues were found.", LogLevel.Warning)

        self.sc.log.log("Generate reference...")
        self.sc.run_program("python", "GenerateReference.py", os.path.join(self.codeunit_folder, "Other", "Reference"), print_live_output=True)
        self.verify_artifact_exists(self.codeunit_folder, dict[str, bool]({"Reference": True}))

        if os.path.isfile(os.path.join(self.codeunit_folder, "Other", "OnBuildingFinished.py")):
            self.sc.log.log('Run "OnBuildingFinished.py"...')
            self.sc.run_program("python", f"OnBuildingFinished.py {arguments}", os.path.join(self.codeunit_folder, "Other"), print_live_output=True)

        artifacts_folder = os.path.join(self.codeunit_folder, "Other", "Artifacts")
        artifactsinformation_file = os.path.join(artifacts_folder, f"{self.codeunit_name}.artifactsinformation.xml")
        codeunit_version = self.tFCPS_Tools.get_version_of_codeunit(codeunit_file)
        GeneralUtilities.ensure_file_exists(artifactsinformation_file)
        artifacts_list = []
        for artifact_folder in GeneralUtilities.get_direct_folders_of_folder(artifacts_folder):
            artifact_name = os.path.basename(artifact_folder)
            artifacts_list.append(f"        <cps:artifact>{artifact_name}<cps:artifact>")
        artifacts = '\n'.join(artifacts_list)
        moment = GeneralUtilities.datetime_to_string(GeneralUtilities.get_now())
        # TODO implement usage of reference_latest_version_of_xsd_when_generating_xml
        GeneralUtilities.write_text_to_file(artifactsinformation_file, f"""<?xml version="1.0" encoding="UTF-8" ?>
<cps:artifactsinformation xmlns:cps="https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure" artifactsinformationspecificationversion="1.0.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="https://raw.githubusercontent.com/anionDev/ProjectTemplates/main/Templates/Conventions/RepositoryStructure/CommonProjectStructure/artifactsinformation.xsd">
    <cps:name>{self.codeunit_name}</cps:name>
    <cps:version>{codeunit_version}</cps:version>
    <cps:timestamp>{moment}</cps:timestamp>
    <cps:targetenvironmenttype>{self.target_environment_type}</cps:targetenvironmenttype>
    <cps:artifacts>
{artifacts}
    </cps:artifacts>
</cps:artifactsinformation>""")
        # TODO validate artifactsinformation_file against xsd
        self.sc.log.log(f"Finished building codeunit {self.codeunit_name} without errors.")


    @GeneralUtilities.check_arguments
    def verify_artifact_exists(self, codeunit_folder: str, artifact_name_regexes: dict[str, bool]) -> None:
        codeunit_name: str = os.path.basename(codeunit_folder)
        artifacts_folder = os.path.join(codeunit_folder, "Other/Artifacts")
        existing_artifacts = [os.path.basename(x) for x in GeneralUtilities.get_direct_folders_of_folder(artifacts_folder)]
        for artifact_name_regex, required in artifact_name_regexes.items():
            artifact_exists = False
            for existing_artifact in existing_artifacts:
                pattern = re.compile(artifact_name_regex)
                if pattern.match(existing_artifact):
                    artifact_exists = True
            if not artifact_exists:
                message = f"Codeunit {codeunit_name} does not contain an artifact which matches the name '{artifact_name_regex}'."
                if required:
                    raise ValueError(message)
                else:
                    self.sc.log.log(message, LogLevel.Warning)

    @GeneralUtilities.check_arguments
    def update_dependencies(self) -> None:
        self.sc.log.log("Update dependencies...")
        self.sc.run_program("python", "UpdateDependencies.py", os.path.join(self.codeunit_folder, "Other"))
