import json
import random

from openmodule.utils.package_reader import ServiceSetting, PackageReader, PackageData


class FakeServiceRepo(dict):
    def remove(self, package: str):
        self.pop(package, None)
        self._resolve_parents()

    def _resolve_parents(self):
        for service in self.values():
            service.parent = None
        for service in self.values():
            parent = service.env.get("PARENT")
            if parent and parent in self:
                service.parent = self.get(parent)

    def add_package(self, settings: ServiceSetting):
        settings.hardware_type = json.loads(settings.env.get("HARDWARE_TYPE")) \
            if settings.env.get("HARDWARE_TYPE") else None
        settings.parent_type = json.loads(settings.env.get("PARENT_TYPE")) \
            if settings.env.get("PARENT_TYPE") else None
        settings.software_type = json.loads(settings.env.get("SOFTWARE_TYPE")) \
            if settings.env.get("SOFTWARE_TYPE") else None
        self[settings.name] = settings
        self._resolve_parents()

    def add_hardware_package(self, name, env: dict | None = None, yml: dict | None = None,
                             hardware_type: list[str] | None = None, ip: str | None = None,
                             revision: int | None = None, package_data: PackageData | None = None):
        revision = revision or random.randint(0, 1000000000)
        merged_yml = {}
        if ip:
            merged_yml.update(dict(
                ip=ip,
                network=dict(
                    addresses=[f"{ip}/24"], dhcp=False,
                    gateway=".".join([ip.rsplit(".", 1)[0], "1"]),
                    nameservers=["8.8.8.8", "1.1.1.1"],
                    ntp_servers=["0.pool.ntp.org", "1.pool.ntp.org", "2.pool.ntp.org", "3.pool.ntp.org"])
            ))
        merged_yml.update(yml or {})
        merged_env = {
            "NAME": name,
            "HARDWARE_TYPE": json.dumps(hardware_type or []),
            **(env or {})
        }
        self.add_package(ServiceSetting(env=merged_env, yml=merged_yml, name=name,
                                        revision=revision, package_data=package_data))

    def add_software_package(self, name, env: dict | None = None, yml: dict | None = None,
                             parent_type: list[str] | None = None, revision: int | None = None,
                             parent: str | None = None, package_data: PackageData | None = None,
                             software_type: list[str] | None = None):
        revision = revision or random.randint(0, 1000000000)
        merged_env = {
            "NAME": name,
            "PARENT_TYPE": json.dumps(parent_type or []),
            "SOFTWARE_TYPE": json.dumps(software_type or []),
            **(env or {})
        }
        if parent:
            merged_env["PARENT"] = parent
        self.add_package(ServiceSetting(env=merged_env, yml=yml or {}, name=name,
                                        revision=revision, package_data=package_data))


class MockPackageReader(PackageReader):
    _services: FakeServiceRepo

    @property
    def services(self) -> FakeServiceRepo:
        return self._services

    def __init__(self, *args, **kwargs):
        # noinspection PyTypeChecker
        super().__init__(rpc_client=1)
        # note we need to overwrite the rpc client with something not-null, otherwise it tries to fetch the rpc client
        # from the openmodule core which may not be initialized in testcases

        self._services = FakeServiceRepo()

    def get_service_by_name(self, service: str) -> ServiceSetting | None:
        return self._services.get(service)

    def list_all_services(self, prefix: str | None = None, compute_id: int | None = None) -> list[ServiceSetting]:
        """
        :param compute_id: compute unit id, if None packages from all units are returned
        :param prefix: prefix of the package id, if none is passed all are returned
        """
        compute_id_str = str(compute_id) if compute_id else None
        return [
            x for x in self._services.values()
            if (not prefix or x.name.startswith(prefix)) and
               (compute_id is None or (x.env.get("COMPUTE_ID") or '1') == compute_id_str)
        ]

    def list_by_hardware_type(self, prefix: str, compute_id: int | None = None):
        """
        lists all packages with a certain hardware type (prefix). Note that these can only be hardware packages
        i.e. their name starts with "hw_"

        :param compute_id: compute unit id, if None packages from all units are returned
        :param prefix: prefix of the hardware type
        """
        compute_id_str = str(compute_id) if compute_id else None
        return [
            x for x in self._services.values()
            if x.name.startswith("hw_") and
               x.hardware_type and
               any(y.startswith(prefix) for y in x.hardware_type) and
               (compute_id is None or (x.env.get("COMPUTE_ID") or '1') == compute_id_str)
        ]

    def list_by_parent_type(self, prefix: str, compute_id: int | None = None):
        """
        lists all packages with a certain parent type (prefix). Note that these can only be software packages
        i.e. their name starts with "om_"

        :param compute_id: compute unit id, if None packages from all units are returned
        :param prefix: prefix of the parent type
        """
        compute_id_str = str(compute_id) if compute_id else None
        return [
            x for x in self._services.values()
            if x.name.startswith("om_") and
               x.parent_type and
               any(y.startswith(prefix) for y in x.parent_type) and
               (compute_id is None or (x.env.get("COMPUTE_ID") or '1') == compute_id_str)
        ]

    def list_by_software_type(self, prefix: str, compute_id: int | None = None):
        """
        lists all packages with a certain software type (prefix). Note that these can only be software packages
        i.e. their name starts with "om_"

        :param compute_id: compute unit id, if None packages from all units are returned
        :param prefix: prefix of the software type
        """
        compute_id_str = str(compute_id) if compute_id else None
        return [
            x for x in self._services.values()
            if x.name.startswith("om_") and
               x.software_type and
               any(y.startswith(prefix) for y in x.software_type) and
               (compute_id is None or (x.env.get("COMPUTE_ID") or '1') == compute_id_str)
        ]
