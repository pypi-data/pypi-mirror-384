import os
from datetime import datetime, timedelta
from ..GeneralUtilities import GeneralUtilities
from ..ScriptCollectionCore import ScriptCollectionCore
from ..SCLog import  LogLevel
from .TFCPS_CodeUnit_BuildCodeUnit import TFCPS_CodeUnit_BuildCodeUnit
from .TFCPS_Tools_General import TFCPS_Tools_General

class TFCPS_CodeUnit_BuildCodeUnits:
    repository:str=None
    tFCPS_Other:TFCPS_Tools_General=None 
    sc:ScriptCollectionCore=None
    target_environment_type:str=None
    additionalargumentsfile:str=None
    __use_cache:bool
    __is_pre_merge:bool

    def __init__(self,repository:str,loglevel:LogLevel,target_environment_type:str,additionalargumentsfile:str,use_cache:bool,is_pre_merge:bool):
        self.sc=ScriptCollectionCore()
        self.sc.log.loglevel=loglevel
        self.__use_cache=use_cache
        self.sc.assert_is_git_repository(repository)
        self.repository=repository
        self.tFCPS_Other:TFCPS_Tools_General=TFCPS_Tools_General(self.sc)
        allowed_target_environment_types=["Development","QualityCheck","Productive"]
        GeneralUtilities.assert_condition(target_environment_type in allowed_target_environment_types,"Unknown target-environment-type. Allowed values are: "+", ".join(allowed_target_environment_types))
        self.target_environment_type=target_environment_type
        self.additionalargumentsfile=additionalargumentsfile
        self.__is_pre_merge=is_pre_merge

    @GeneralUtilities.check_arguments
    def __save_lines_of_code(self, repository_folder: str, project_version: str) -> None:
        loc = self.sc.get_lines_of_code_with_default_excluded_patterns(repository_folder)
        loc_metric_folder = os.path.join(repository_folder, "Other", "Metrics")
        GeneralUtilities.ensure_directory_exists(loc_metric_folder)
        loc_metric_file = os.path.join(loc_metric_folder, "LinesOfCode.csv")
        GeneralUtilities.ensure_file_exists(loc_metric_file)
        old_lines = GeneralUtilities.read_lines_from_file(loc_metric_file)
        new_lines = []
        for line in old_lines:
            if not line.startswith(f"v{project_version};"):
                new_lines.append(line)
        new_lines.append(f"v{project_version};{loc}")
        GeneralUtilities.write_lines_to_file(loc_metric_file, new_lines)

    @GeneralUtilities.check_arguments
    def build_codeunits(self) -> None:
        self.sc.log.log(GeneralUtilities.get_line())
        self.sc.log.log(f"Start building codeunits. (Target environment-type: {self.target_environment_type})")

        #check if changelog exists
        changelog_file=os.path.join(self.repository,"Other","Resources","Changelog",f"v{self.tFCPS_Other.get_version_of_project(self.repository)}.md")
        GeneralUtilities.assert_file_exists(changelog_file,f"Changelogfile \"{changelog_file}\" does not exist. Try to create it for example using \"sccreatechangelogentry -m ...\".") 
        
        #run prepare-script
        if  os.path.isfile( os.path.join(self.repository,"Other","Scripts","PrepareBuildCodeunits.py")):
            arguments:str=f"--targetenvironmenttype {self.target_environment_type} --additionalargumentsfile {self.additionalargumentsfile} --verbosity {int(self.sc.log.loglevel)}"
            if not self.__use_cache:
                arguments=f"{arguments} --nocache"
                if self.sc.git_repository_has_uncommitted_changes(self.repository):
                    self.sc.log.log("No-cache-option can not be applied because there are uncommited changes in the repository.",LogLevel.Warning)
                else:
                    self.sc.run_program("git","clean -dfx",self.repository)

            self.sc.log.log("Prepare build codeunits...")
            self.sc.run_program("python", f"PrepareBuildCodeunits.py {arguments}", os.path.join(self.repository,"Other","Scripts"),print_live_output=True)

        #mark current version as supported
        now = GeneralUtilities.get_now()
        project_version:str=self.tFCPS_Other.get_version_of_project(self.repository)
        if not self.tFCPS_Other.suport_information_exists(self.repository, project_version):
            amount_of_years_for_support:int=1
            support_time = timedelta(days=365*amount_of_years_for_support+30*3+1) 
            until = now + support_time
            until_day = datetime(until.year, until.month, until.day, 0, 0, 0)
            from_day = datetime(now.year, now.month, now.day, 0, 0, 0)
            self.tFCPS_Other.mark_current_version_as_supported(self.repository,project_version,from_day,until_day)

        codeunits:list[str]=self.tFCPS_Other.get_codeunits(self.repository)        
        self.sc.log.log("Codeunits will be built in the following order:")
        for codeunit_name in codeunits:
            self.sc.log.log("  - "+codeunit_name)
        for codeunit_name in codeunits:
            tFCPS_CodeUnit_BuildCodeUnit:TFCPS_CodeUnit_BuildCodeUnit = TFCPS_CodeUnit_BuildCodeUnit(os.path.join(self.repository,codeunit_name),self.sc.log.loglevel,self.target_environment_type,self.additionalargumentsfile,self.use_cache(),self.is_pre_merge())
            self.sc.log.log(GeneralUtilities.get_line())
            tFCPS_CodeUnit_BuildCodeUnit.build_codeunit()

        #TODO run static code analysis tool to search for vulnerabilities
        #TODO self.__search_for_secrets()
        self.__save_lines_of_code(self.repository,self.tFCPS_Other.get_version_of_project(self.repository))

        self.sc.log.log(GeneralUtilities.get_line())
        self.sc.log.log("Finished building codeunits.")
        self.sc.log.log(GeneralUtilities.get_line())

    def __search_for_secrets(self):#pylint:disable=unused-private-member
        exe_paths=self.tFCPS_Other.ensure_trufflehog_is_available()
        exe_path:str=None
        if GeneralUtilities.current_system_is_windows():
            exe_path=exe_paths["Windows"]
        elif GeneralUtilities.current_system_is_linux():
            exe_path=exe_paths["Linux"]
        else:
            raise ValueError("unsupported")#TODO check for macos
        result=self.sc.run_program(exe_path,"filesystem . --json",self.repository)

        enabled:bool=False
        if enabled:
            self.sc.log.log("Secret-scan-result:")#TODO replace this by real analysis
            for line in GeneralUtilities.string_to_lines(result[1]):
                self.sc.log.log(line)
            for line in GeneralUtilities.string_to_lines(result[2]):
                self.sc.log.log(line,LogLevel.Error)

    @GeneralUtilities.check_arguments
    def use_cache(self) -> bool:
        return self.__use_cache


    @GeneralUtilities.check_arguments
    def is_pre_merge(self) -> bool:
        return self.__is_pre_merge

    @GeneralUtilities.check_arguments
    def update_dependencies(self) -> None:
        self.update_year_in_license_file()

        #TODO update project-wide-dependencies here
        codeunits:list[str]=self.tFCPS_Other.get_codeunits(self.repository)
        for codeunit_name in codeunits:
            tFCPS_CodeUnit_BuildCodeUnit:TFCPS_CodeUnit_BuildCodeUnit = TFCPS_CodeUnit_BuildCodeUnit(os.path.join(self.repository,codeunit_name),self.sc.log.loglevel,self.target_environment_type,self.additionalargumentsfile,self.use_cache(),self.is_pre_merge())
            tFCPS_CodeUnit_BuildCodeUnit.update_dependencies() 

    @GeneralUtilities.check_arguments
    def update_year_in_license_file(self) -> None:
        self.sc.update_year_in_first_line_of_file(os.path.join(self.repository, "License.txt"))
