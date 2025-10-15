import argparse
import os
from .TFCPS.TFCPS_CodeUnit_BuildCodeUnit import TFCPS_CodeUnit_BuildCodeUnit
from .TFCPS.TFCPS_CodeUnit_BuildCodeUnits import TFCPS_CodeUnit_BuildCodeUnits
from .TFCPS.TFCPS_Tools_General import TFCPS_Tools_General
from .SCLog import LogLevel
from .GeneralUtilities import GeneralUtilities
from .ScriptCollectionCore import ScriptCollectionCore

class AnionBuildPlatformConfiguration:
    build_repositories_folder:str
    additional_arguments_file:str
    verbosity:LogLevel
    source_branch:str
    common_remote_name:str
    update_dependencies:bool

    def __init__(self,
                 build_repositories_folder:str,
                 additional_arguments_file:str,
                 verbosity:LogLevel,
                 source_branch:str,
                 common_remote_name:str,
                 update_dependencies:bool):
        self.build_repositories_folder=build_repositories_folder
        self.additional_arguments_file=additional_arguments_file
        self.verbosity=verbosity
        self.source_branch=source_branch
        self.common_remote_name=common_remote_name
        self.update_dependencies=update_dependencies

class AnionBuildPlatform:

    __configuration: AnionBuildPlatformConfiguration
    __sc:ScriptCollectionCore
    __tFCPS_Tools_General:TFCPS_Tools_General

    def __init__(self, configuration: AnionBuildPlatformConfiguration):
        self.__configuration = configuration
        self.__sc = ScriptCollectionCore()
        self.__sc.log.loglevel=configuration.verbosity
        self._tFCPS_Tools_General=TFCPS_Tools_General(self.__sc)

    def run(self) -> None:
        # Checkout source branch
        build_repo_folder:str=self.__configuration.build_repositories_folder
        GeneralUtilities.assert_condition(build_repo_folder.endswith("Build"),f"buildrepositoriesfolder {build_repo_folder} must end with 'Build'")
        self.__sc.assert_is_git_repository(build_repo_folder)
        product_name=os.path.basename(build_repo_folder)[:-len("Build")]
        repository:str=os.path.join(build_repo_folder,"Submodules",product_name)
        self.__sc.assert_is_git_repository(repository)
        self.__sc.git_commit(build_repo_folder,"Updated changes")
        self.__sc.git_checkout(repository,self.__configuration.source_branch)

        # Pull changes from remote
        self.__sc.git_fetch(repository)
        self.__sc.git_merge(repository,self.__configuration.common_remote_name+"/"+self.__configuration.source_branch,self.__configuration.source_branch,fastforward=True)#TODO check if is anchestor and throw exception if nor
        self.__sc.git_commit(build_repo_folder,"Updated changes")

        #Update dependencies
        if self.__configuration.update_dependencies:
            self.__update_dependencies(product_name)
        
        #Do release
        scripts_folder:str=os.path.join(build_repo_folder,"Scripts","CreateRelease")

        merge_to_main_arguments=""
        #if self.__configuration.project_to_build is not None:
        #    merge_to_main_arguments+=f" --productname {self.__configuration.project_to_build}"
        if self.__configuration.source_branch is not None:
            merge_to_main_arguments+=f" --mergesourcebranch {self.__configuration.source_branch}"
        #if self.__configuration.additional_arguments_file is not None:
        #    merge_to_main_arguments+=f" --additionalargumentsfile {self.__configuration.additional_arguments_file}"
        #if self.__configuration.main_branch is not None:
        #    merge_to_main_arguments+=f" --mainbranch {self.__configuration.main_branch}"
        #if self.__configuration.common_remote_name is not None:
        #    merge_to_main_arguments+=f" --commonremotename {self.__configuration.common_remote_name}"
        if self.__configuration.verbosity is not None:
            merge_to_main_arguments+=f" --verbosity {self.__configuration.verbosity.value}"
        self.__sc.run_program("python",f"MergeToMain.py{merge_to_main_arguments}",scripts_folder,print_live_output=True)

        merge_to_stable_arguments=""
        #if self.__configuration.project_to_build is not None:
        #    merge_to_stable_arguments+=f" --productname {self.__configuration.project_to_build}"
        #if self.__configuration.additional_arguments_file is not None:
        #    merge_to_stable_arguments+=f" --additionalargumentsfile {self.__configuration.additional_arguments_file}"
        #if self.__configuration.source_branch is not None:
        #    merge_to_stable_arguments+=f" --sourcebranch {self.__configuration.source_branch}"
        #if self.__configuration.main_branch is not None:
        #    merge_to_stable_arguments+=f" --targetbranch {self.__configuration.main_branch}"
        #if self.__configuration.reference_repo is not None:
        #    merge_to_stable_arguments+=f" --referencerepo {self.__configuration.referencerepo}"
        #if self.__configuration.common_remote_name is not None:
        #    merge_to_stable_arguments+=f" --commonremotename {self.__configuration.common_remote_name}"
        #if self.__configuration.build_repo_main_branch_name is not None:
        #    merge_to_stable_arguments+=f" --buildrepomainbranchname {self.__configuration.build_repo_main_branch_name}"
        #if self.__configuration.reference_repo_main_branch_name is not None:
        #    merge_to_stable_arguments+=f" --referencerepomainbranchname {self.__configuration.reference_repo_main_branch_name}"
        #if self.__configuration.reference_remote_name is not None:
        #    merge_to_stable_arguments+=f" --referenceremotename {self.__configuration.reference_remote_name}"
        #if self.__configuration.build_repo_remote_name is not None:
        #    merge_to_stable_arguments+=f" --buildreporemotename {self.__configuration.build_repo_remote_name}"
        #if self.__configuration.artifacts_target_folder is not None:
        #    merge_to_stable_arguments+=f" --artifactstargetfolder {self.__configuration.artifacts_target_folder}"
        #if self.__configuration.common_remote_url is not None:
        #    merge_to_stable_arguments+=f" --commonremoteurl {self.__configuration.common_remote_url}"
        if self.__configuration.verbosity is not None:
            merge_to_stable_arguments+=f" --verbosity {self.__configuration.verbosity.value}"
        self.__sc.run_program("python",f"MergeToStable.py{merge_to_stable_arguments}",scripts_folder,print_live_output=True)

        #prepare for next-release
        self.__sc.git_checkout(repository,self.__configuration.source_branch)

    def __update_dependencies(self,product_name:str) -> None:
        self.__sc.log.log("Update dependencies...")
        repository:str=os.path.join(self.__configuration.build_repositories_folder,product_name+"Build","Submodules",product_name)
        self.__sc.assert_no_uncommitted_changes(repository)
        self.__sc.run_program("python","UpdateDependencies.py",os.path.join(repository,"Other","Scripts"))
        codeunits:list[str]=self._tFCPS_Tools_General.get_codeunits(repository)   
        for codeunit_name in codeunits:
            self.__sc.log.log(f"Update dependencies of codeunit {codeunit_name}...")
            codeunit_folder=os.path.join(repository,codeunit_name)
            tFCPS_CodeUnit_BuildCodeUnit:TFCPS_CodeUnit_BuildCodeUnit = TFCPS_CodeUnit_BuildCodeUnit(codeunit_folder,self.__sc.log.loglevel,"QualityCheck",None,True,False)
            tFCPS_CodeUnit_BuildCodeUnit.build_codeunit()#ensure requirements for updating are there (some programming types needs this)
            if self.__tFCPS_Tools_General.codeunit_has_updatable_dependencies(os.path.join(codeunit_folder,f"{codeunit_name}.codeunit.xml")):
                self.__sc.run_program("python","UpdateDependencies.py",os.path.join(codeunit_folder,"Other"))
            tFCPS_CodeUnit_BuildCodeUnit.build_codeunit()#check if codeunit is still buildable

        if self.__sc.git_repository_has_uncommitted_changes(repository):
            changelog_folder = os.path.join(repository, "Other", "Resources", "Changelog")
            project_version:str=self._tFCPS_Tools_General.get_version_of_project(repository)
            changelog_file = os.path.join(changelog_folder, f"v{project_version}.md")
            if not os.path.isfile(changelog_file):
                self.__ensure_changelog_file_is_added(repository, project_version)
            t=TFCPS_CodeUnit_BuildCodeUnits(repository,self.__sc.log.loglevel,"QualityCheck",None,True,False)
            t.build_codeunits()#check codeunits are buildable at all
            self.__sc.git_commit(repository, "Updated dependencies", stage_all_changes=True) 


    def __ensure_changelog_file_is_added(self, repository_folder: str, version_of_project: str):
        changelog_file = os.path.join(repository_folder, "Other", "Resources", "Changelog", f"v{version_of_project}.md")
        if not os.path.isfile(changelog_file):
            GeneralUtilities.ensure_file_exists(changelog_file)
            GeneralUtilities.write_text_to_file(changelog_file, """# Release notes

## Changes

- Updated dependencies.
""")

class TFCPS_AnionBuildPlatform_CLI:

    @staticmethod
    def get_with_overwritable_defaults(default_project_to_build:str=None,default_loglevel:LogLevel=None,default_additionalargumentsfile:str=None,default_build_repositories_folder:str=None,default_source_branch:str=None,default_main_branch:str=None,default_remote_name:str=None)->AnionBuildPlatform:
        parser = argparse.ArgumentParser()
        verbosity_values = ", ".join(f"{lvl.value}={lvl.name}" for lvl in LogLevel)
        parser.add_argument('-b', '--buildrepositoriesfolder', required=False,default=None)
        parser.add_argument('-p', '--projecttobuild', required=False, default=None)
        parser.add_argument('-a', '--additionalargumentsfile', required=False, default=None)
        parser.add_argument('-v', '--verbosity', required=False,  help=f"Sets the loglevel. Possible values: {verbosity_values}")
        parser.add_argument('-s', '--sourcebranch', required=False)#other/next-release
        parser.add_argument('-m', '--mainbranch', required=False)#main
        parser.add_argument('-r', '--defaultremotename', required=False)#origin
        parser.add_argument('-u', '--updatedependencies', required=False, action='store_true', default=False)
        args=parser.parse_args()

        if args.projecttobuild is not None: 
            default_project_to_build=args.projecttobuild

        if args.buildrepositoriesfolder is not None:
            default_build_repositories_folder=args.buildrepositoriesfolder

        scripts_folder=os.getcwd()
        
        if default_build_repositories_folder is None:
            parent_parent_folder=GeneralUtilities.resolve_relative_path("../..",scripts_folder)
            if os.path.basename(parent_parent_folder).endswith("Build"):
                default_build_repositories_folder=os.path.dirname(parent_parent_folder)
        GeneralUtilities.assert_not_null(default_build_repositories_folder,"buildrepositoriesfolder is not set")
        
        if default_project_to_build is None:
            parent_parent_folder=GeneralUtilities.resolve_relative_path("../..",scripts_folder)
            if os.path.basename(parent_parent_folder).endswith("Build"):
                default_project_to_build=os.path.basename(parent_parent_folder)[:-len("Build")]
        GeneralUtilities.assert_not_null(default_project_to_build,"projecttobuild is not set")

        if args.verbosity is not None:
            default_loglevel=LogLevel(int( args.verbosity))
        GeneralUtilities.assert_not_null(default_loglevel,"verbosity is not set")

        if args.additionalargumentsfile is not None:
            default_additionalargumentsfile=args.additionalargumentsfile

        if args.sourcebranch is not None:
            default_source_branch=args.sourcebranch
        GeneralUtilities.assert_not_null(default_source_branch,"sourcebranch is not set")

        if args.defaultremotename is not None:
            default_remote_name=args.defaultremotename
        GeneralUtilities.assert_not_null(default_remote_name,"defaultremotename is not set")

        config:AnionBuildPlatformConfiguration=AnionBuildPlatformConfiguration(default_build_repositories_folder,default_additionalargumentsfile,default_loglevel,default_source_branch,default_remote_name,args.updatedependencies)
        tFCPS_MergeToMain:AnionBuildPlatform=AnionBuildPlatform(config)
        return tFCPS_MergeToMain
