from datetime import datetime

class Dependency:
    name:str
    current_version:str
    latest_patch_version_for_current_minor_version:str
    latest_minor_version_for_current_major_version:str
    latest_version:str
    date_of_latest_version:datetime

class TFCPS_Tools_Dependencies:
    
    def get_dependencies(self)->list[Dependency]:
        result:list[Dependency]=[]
        #TODO
        return result
