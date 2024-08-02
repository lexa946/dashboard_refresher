import json
import os

import requests
from requests_toolbelt import MultipartEncoder

from .helpers import Process, User, Schedule, Release, Machine, Asset


class ManagerAPI:
    def __init__(self, user_key, org_id, tenant, client_id, org_unit_id):
        self.__user_key = user_key
        self.__org_id = org_id
        self.__tenant = tenant
        self.__client_id = client_id
        self.__org_unit_id = org_unit_id
        self.__base_url = f"https://cloud.uipath.com/{org_id}/{tenant}/orchestrator_"
        self.__token = self.__get_token()
        self.__base_headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.__token}",
            "Content-Type": "application/json",
            "X-UIPATH-Localization": "en",
            "X-UIPATH-Orchestrator": "true",
            "X-UIPATH-OrganizationUnitId": self.__org_unit_id,
            # "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }


    def __get_token(self):
        url = "https://account.uipath.com/oauth/token"

        headers = {
            "X-UIPATH-TenantName": self.__tenant,
            "Content-Type": "application/json",
        }
        body = {
            "grant_type": "refresh_token",
            "client_id": self.__client_id,
            "refresh_token": self.__user_key,
        }

        response = requests.post(url, json=body, headers=headers, verify=False)
        return response.json()["access_token"]

    def __get_base(self, method_url):
        response = requests.get(self.__base_url+method_url, headers=self.__base_headers, verify=False)
        json_ = response.json()
        return json_

    def get_processes(self):
        json_ = self.__get_base("/odata/Processes")
        return [Process(item) for item in json_['value']]

    def get_package_main_entry_point(self, package_key):
        json_ = self.__get_base(f"/odata/Processes/UiPath.Server.Configuration.OData.GetPackageMainEntryPoint(key='{package_key}')")
        return json_

    def create_release(self, process: Process):
        entry_point = self.get_package_main_entry_point(process.key)
        body = {
            "Name": process.id,
            "Description": process.description,
            "ProcessKey": process.id,
            "ProcessVersion": process.version,
        }
        if entry_point:
            body["EntryPointId"] =  entry_point['Id']


        response = requests.post(self.__base_url + "/odata/Releases", json=body, headers=self.__base_headers, verify=False)
        return Release(response.json())

    def get_process_versions(self, process: Process):
        json_ = self.__get_base(f"/odata/Processes/UiPath.Server.Configuration.OData.GetProcessVersions(processId='{process.id}')")
        return json_['value']

    def download_process(self, process: Process, save_path):
        url = f"{self.__base_url}/odata/Processes/UiPath.Server.Configuration.OData.DownloadPackage(key='{process.key}')"
        response = requests.get(url, headers=self.__base_headers, verify=False)
        with open(os.path.join(save_path, process.key), "wb") as file_out:
            file_out.write(response.content)

    def upload_process(self, path_folder, filename):
        url = f"{self.__base_url}/odata/Processes/UiPath.Server.Configuration.OData.UploadPackage()"
        headers = self.__base_headers.copy()

        fields = {}
        io_file = open(os.path.join(path_folder, filename), 'rb')
        fields[os.path.splitext(filename)[0]] = (filename, io_file, 'multipart/form-data')

        m = MultipartEncoder(fields=fields)

        headers["Content-Type"] = m.content_type
        response = requests.post(url, data=m, headers=headers, verify=False)
        io_file.close()
        json_ = response.json()


        body = json.loads(json_['value'][0]['Body'])
        return body


    def get_schedules(self):
        json_ = self.__get_base("/odata/ProcessSchedules")
        return [Schedule.from_json(item) for item in json_['value']]


    def create_schedule(self, schedule: Schedule):
        body = {
            "Name": schedule.name,
            "ReleaseId": schedule.release_id,
            "ReleaseKey": schedule.release_key,
            "ReleaseName": schedule.release_name,
            "PackageName": schedule.package_name,
            "ExecutorRobots": schedule.executor_robots,
            "StartProcessCron": schedule.start_process_cron,
            "StartProcessCronDetails": schedule.start_process_cron_detail,
            "TimeZoneId": schedule.time_zone_id,
            "MachineRobots": schedule.machine_robots,
            "Enabled": schedule.enabled,
            "RuntimeType": schedule.runtime_type,
            "InputArguments": schedule.input_arguments,
            "StartStrategy": schedule.start_strategy,

        }

        response = requests.post(self.__base_url+"/odata/ProcessSchedules", json=body, headers=self.__base_headers, verify=False)
        return response.json()


    def get_users(self):
        json_ = self.__get_base("/odata/Users")
        return [User.from_json(user) for user in json_['value']]

    def create_user(self, user: User):
        body = {

            "RolesList": list(user.roles),
            "UnattendedRobot": {
                "UserName": user.robot_username,
                "Password": user.robot_password,
                "ExecutionSettings": user.robot_execution_settings,
            },
            "Type": "DirectoryRobot",
            "Domain": "autogen",

        }
        response = requests.post(self.__base_url+"/odata/Users", json=body, headers=self.__base_headers, verify=False)
        print()
        return response.json()


    def get_machines(self):
        json_ = self.__get_base("/odata/Machines")
        return [Machine(machine) for machine in json_['value']]

    def get_releases(self):
        json_ = self.__get_base("/odata/Releases")
        return [Release(release) for release in json_['value']]

    def get_assets(self):
        json_ = self.__get_base("/odata/Assets")
        assets = []
        for asset in json_['value']:
            tmp = Asset.from_json(asset)
            if tmp.value_type == "Text":
                assets.append(tmp)
        return assets

    def create_asset(self, asset: Asset):
        body = {
            "Name": asset.name,
            "ValueScope": asset.value_scope,
            "ValueType": asset.value_type,
            "Value": asset.value,
            "StringValue": asset.value,
        }
        response = requests.post(self.__base_url+"/odata/Assets", json=body, headers=self.__base_headers, verify=False)
        return response.json()

    def download_report_queue(self, queue_id: int, filename: str ="report.csv"):
        url = f"{self.__base_url}/odata/QueueDefinitions({queue_id})/UiPathODataSvc.Reports?$filter=((QueueDefinitionId%20eq%20{queue_id}))&$top=10&$expand=Robot,ReviewerUser&$orderby=Id%20desc"
        response = requests.get(url, headers=self.__base_headers, verify=False)
        if response.status_code not in (200, 201):
            raise ConnectionError("Not Connect to orchestrator!")
        with open(filename, "wb") as file:
            file.write(response.content)

# https://cloud.uipath.com/exfat/DefaultTenant/orchestrator_/odata/QueueDefinitions(635201)/UiPathODataSvc.Export?$filter=((QueueDefinitionId%20eq%20635201))&$top=10&$expand=Robot,ReviewerUser&$orderby=Id%20desc

class Orchestrator:
    def __init__(self, user_key, org_id, tenant, client_id, org_unit_id):
        self.__manager = ManagerAPI(user_key, org_id, tenant, client_id, org_unit_id)
        self.users = None
        self.processes = None
        self.schedules = None
        self.releases = None
        self.machines = None
        self.assets = None
        self.refresh()


    def refresh(self):
        self.users = self.__manager.get_users()
        self.processes = self.__manager.get_processes()
        self.schedules = self.__manager.get_schedules()
        self.releases = self.__manager.get_releases()
        self.machines = self.__manager.get_machines()
        self.assets = self.__manager.get_assets()



    def get_user_by_robot_id(self, robot_id):
        for user in self.users:
            if user.robot_id == robot_id: return user

    def get_user_by_robot_username(self, robot_username):
        for user in self.users:
            if user.robot_username == robot_username: return user

    def get_release_by_name(self, release_name):
        for release in self.releases:
            if release.name == release_name: return release

    def get_machine_by_name(self, machine_name):
        for machine in self.machines:
            if machine.name == machine_name: return machine

    def get_process_by_id(self, process_id):
        for process in self.processes:
            if process.id == process_id: return process

    def create_schedule(self, schedule: Schedule):
        return self.__manager.create_schedule(schedule)

    def create_release(self, process: Process):
        return self.__manager.create_release(process)

    def create_asset(self, asset: Asset):
        return self.__manager.create_asset(asset)

    def create_user(self, user: User):
        return self.__manager.create_user(user)

    def download_report_queue(self, queue_id, filename="report.csv"):
        self.__manager.download_report_queue(queue_id, filename)