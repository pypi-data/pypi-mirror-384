from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.setup_ducklake_catalog_db_response_200_logs import SetupDucklakeCatalogDbResponse200Logs


T = TypeVar("T", bound="SetupDucklakeCatalogDbResponse200")


@_attrs_define
class SetupDucklakeCatalogDbResponse200:
    """
    Attributes:
        logs (SetupDucklakeCatalogDbResponse200Logs):
        success (bool): Whether the operation completed successfully Example: True.
        error (Union[Unset, None, str]): Error message if the operation failed Example: Connection timeout.
    """

    logs: "SetupDucklakeCatalogDbResponse200Logs"
    success: bool
    error: Union[Unset, None, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        logs = self.logs.to_dict()

        success = self.success
        error = self.error

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "logs": logs,
                "success": success,
            }
        )
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.setup_ducklake_catalog_db_response_200_logs import SetupDucklakeCatalogDbResponse200Logs

        d = src_dict.copy()
        logs = SetupDucklakeCatalogDbResponse200Logs.from_dict(d.pop("logs"))

        success = d.pop("success")

        error = d.pop("error", UNSET)

        setup_ducklake_catalog_db_response_200 = cls(
            logs=logs,
            success=success,
            error=error,
        )

        setup_ducklake_catalog_db_response_200.additional_properties = d
        return setup_ducklake_catalog_db_response_200

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
