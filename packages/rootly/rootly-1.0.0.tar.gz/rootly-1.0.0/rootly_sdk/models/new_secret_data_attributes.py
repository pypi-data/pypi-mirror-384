from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.new_secret_data_attributes_kind import NewSecretDataAttributesKind
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewSecretDataAttributes")


@_attrs_define
class NewSecretDataAttributes:
    """
    Attributes:
        name (str): The name of the secret
        secret (str): The secret
        kind (Union[Unset, NewSecretDataAttributesKind]): The kind of the secret
        hashicorp_vault_mount (Union[None, Unset, str]): The HashiCorp Vault secret mount path Default: 'secret'.
        hashicorp_vault_path (Union[None, Unset, str]): The HashiCorp Vault secret path
        hashicorp_vault_version (Union[None, Unset, str]): The HashiCorp Vault secret version Default: '0'.
    """

    name: str
    secret: str
    kind: Union[Unset, NewSecretDataAttributesKind] = UNSET
    hashicorp_vault_mount: Union[None, Unset, str] = "secret"
    hashicorp_vault_path: Union[None, Unset, str] = UNSET
    hashicorp_vault_version: Union[None, Unset, str] = "0"

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        secret = self.secret

        kind: Union[Unset, str] = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind.value

        hashicorp_vault_mount: Union[None, Unset, str]
        if isinstance(self.hashicorp_vault_mount, Unset):
            hashicorp_vault_mount = UNSET
        else:
            hashicorp_vault_mount = self.hashicorp_vault_mount

        hashicorp_vault_path: Union[None, Unset, str]
        if isinstance(self.hashicorp_vault_path, Unset):
            hashicorp_vault_path = UNSET
        else:
            hashicorp_vault_path = self.hashicorp_vault_path

        hashicorp_vault_version: Union[None, Unset, str]
        if isinstance(self.hashicorp_vault_version, Unset):
            hashicorp_vault_version = UNSET
        else:
            hashicorp_vault_version = self.hashicorp_vault_version

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "secret": secret,
            }
        )
        if kind is not UNSET:
            field_dict["kind"] = kind
        if hashicorp_vault_mount is not UNSET:
            field_dict["hashicorp_vault_mount"] = hashicorp_vault_mount
        if hashicorp_vault_path is not UNSET:
            field_dict["hashicorp_vault_path"] = hashicorp_vault_path
        if hashicorp_vault_version is not UNSET:
            field_dict["hashicorp_vault_version"] = hashicorp_vault_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        secret = d.pop("secret")

        _kind = d.pop("kind", UNSET)
        kind: Union[Unset, NewSecretDataAttributesKind]
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = NewSecretDataAttributesKind(_kind)

        def _parse_hashicorp_vault_mount(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        hashicorp_vault_mount = _parse_hashicorp_vault_mount(d.pop("hashicorp_vault_mount", UNSET))

        def _parse_hashicorp_vault_path(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        hashicorp_vault_path = _parse_hashicorp_vault_path(d.pop("hashicorp_vault_path", UNSET))

        def _parse_hashicorp_vault_version(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        hashicorp_vault_version = _parse_hashicorp_vault_version(d.pop("hashicorp_vault_version", UNSET))

        new_secret_data_attributes = cls(
            name=name,
            secret=secret,
            kind=kind,
            hashicorp_vault_mount=hashicorp_vault_mount,
            hashicorp_vault_path=hashicorp_vault_path,
            hashicorp_vault_version=hashicorp_vault_version,
        )

        return new_secret_data_attributes
