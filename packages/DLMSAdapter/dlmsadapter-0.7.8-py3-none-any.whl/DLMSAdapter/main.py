from typing import Protocol, Optional
from DLMS_SPODES.cosem_interface_classes.parameter import Parameter
from DLMS_SPODES.cosem_interface_classes.collection import (
    Collection, ID,
    ParameterValue,
    Template)
from semver import Version as SemVer
from StructResult import result


type_title: str = "DLMSServerType"
data_title: str = "DLMSServerData"
template_title: str = "DLMSServerTemplate"
type Manufacturer = bytes


class Adapter(Protocol):
    """universal adapter for keep/recovery DLMS data"""
    VERSION: SemVer = SemVer(0, 0)
    """reinit current adapter version"""

    @classmethod
    def set_collection(cls, col: Collection) -> None:
        """not safety of type keeping from collection(source) to destination(file(xml, json,...), sql, etc...). Save all attributes. For types only STATIC save """

    @classmethod
    def get_collection(cls, col_id: ID) -> result.Simple[Collection] | result.Error:
        """get Collection by m: manufacturer, t: type, ver: version. AdapterException if not find collection by ID """

    def get_collectionIDs(self) -> list[ID]:
        """return container used CollectionID"""

    def get_ID_tree(self) -> dict[Manufacturer, dict[ParameterValue, set[ID]]]:
        """return tree used CollectionID"""

    @classmethod
    def set_data(cls, col: Collection, ass_id: int = 3) -> result.List[Parameter] | result.Error:
        """Save attributes WRITABLE and STATIC if possible. Use LDN as ID"""

    @classmethod
    def get_data(cls, col: Collection) -> result.Ok | result.Error:
        """ set attribute values from file by. validation ID's. AdapterException if not find data by ID"""

    def set_template(self, template: Template) -> None:
        """keep used values to template by collections"""

    @classmethod
    def get_template(cls, name: str, forced_col: Optional[Collection] = None) -> Template:
        """load template by <name>"""

    @classmethod
    def get_templates(cls) -> list[str]:
        """return all templates name"""


class AdapterException(Exception):
    """"""


class __Gag(Adapter):
    @classmethod
    def set_collection(cls, col: Collection) -> None:
        raise AdapterException(F"{cls.__name__} not support <get_template>")

    @classmethod
    def get_collection(cls, col_id: ID) -> result.Simple[Collection] | result.Error:
        raise AdapterException(F"{cls.__name__} not support <get_collection>")

    @classmethod
    def set_data(cls, col: Collection, ass_id: int = 3) -> result.List[Parameter] | result.Error:
        raise AdapterException(F"{cls.__name__} not support <keep_data>")

    @classmethod
    def get_data(cls, col: Collection) -> result.Ok | result.Error:
        raise AdapterException(F"{cls.__name__} not support <get_data>")

    def set_template(self, template: Template) -> None:
        raise AdapterException(F"{self.__class__.__name__} not support <create_template>")

    @classmethod
    def get_template(cls, name: str, forced_col: Optional[Collection] = None) -> Template:
        raise AdapterException(F"{cls.__name__} not support <get_template>")

    @classmethod
    def get_templates(cls) -> list[str]:
        raise AdapterException(F"{cls.__name__} not have <templates>")

    def get_collectionIDs(self) -> list[ID]:
        raise AdapterException(F"{self.__class__.__name__} not have <manufacturers>")

    def get_ID_tree(self) -> dict[Manufacturer, dict[ParameterValue, set[ID]]]:
        raise AdapterException(F"{self.__class__.__name__} not have <manufacturers>")


gag = __Gag()
