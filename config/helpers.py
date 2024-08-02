class Process:
    def __init__(self, process_json):
        self.id = process_json['Id']
        self.title = process_json['Title']
        self.key = process_json['Key']
        self.version = process_json['Version']
        self.description = process_json['Description']


    def __repr__(self):
        return self.key

class Machine:
    def __init__(self, machine_json):
        self.id = machine_json['Id']
        self.name = machine_json['Name']

    def __repr__(self):
        return self.name


class Release:
    def __init__(self, release_json):
        self.id = release_json['Id']
        self.name = release_json['Name']
        self.description = release_json['Description']
        self.key = release_json['Key']
        self.process_version = release_json['ProcessVersion']

    def __repr__(self):
        return self.name

class User:
    def __init__(self, name, robot_username, robot_password=None, robot_execution_settings={}, roles=("Robot",)):
        self.id = None
        self.name = name
        self.key = None
        self.robot_username = robot_username
        self.robot_id = None
        self.robot_execution_settings = robot_execution_settings
        self.roles = roles
        self.robot_password = robot_password


    def __repr__(self):
        return self.name

    @classmethod
    def from_json(cls, user_json):
        if user_json['UnattendedRobot']:
            user = cls(user_json['Name'], user_json['UnattendedRobot']['UserName'],
                       robot_execution_settings=user_json['UnattendedRobot']['ExecutionSettings'])
            user.robot_id = user_json['UnattendedRobot']['RobotId']
        else:
            user = cls(user_json['Name'], None, robot_execution_settings=None)
        user.id = user_json['Id']
        user.key = user_json['Key']
        user.roles = user_json['RolesList']
        return user


class Schedule:
    def __init__(self, name, release_id, release_key, release_name, package_name, executor_robots,
                 start_process_cron, start_process_cron_detail,
                 machine_robots, start_strategy=1, enabled=False, runtime_type="Unattended", input_arguments="",
                 time_zone_id="Russian Standard Time"):

        self.name = name
        self.release_id = release_id
        self.release_key = release_key
        self.release_name = release_name
        self.package_name = package_name
        self.executor_robots = executor_robots
        self.start_process_cron = start_process_cron
        self.start_process_cron_detail = start_process_cron_detail
        self.start_strategy = start_strategy
        self.time_zone_id = time_zone_id
        self.machine_robots = machine_robots
        self.enabled = enabled
        self.runtime_type = runtime_type
        self.input_arguments = input_arguments


    @classmethod
    def from_json(cls, json_):
        executor_robots = [{"Id": item['RobotId']} for item in json_['MachineRobots']]

        return cls(json_['Name'], json_['ReleaseId'], json_['ReleaseKey'], json_['ReleaseName'], json_['PackageName'],
                   executor_robots,
                   json_['StartProcessCron'], json_['StartProcessCronDetails'],
                   json_['MachineRobots'],json_['StartStrategy'],
                   json_['Enabled'], json_['RuntimeType'], json_['InputArguments'], json_['TimeZoneId'])


    def __repr__(self):
        return self.name



class Asset:
    def __init__(self, name, value, value_type, value_scope):
        self.name = name
        self.value = value
        self.value_type = value_type
        self.value_scope = value_scope

    def __repr__(self):
        return self.name

    @classmethod
    def from_json(cls, asset_json):
        return cls(asset_json['Name'], asset_json['Value'], asset_json['ValueType'], asset_json['ValueScope'])


class QueueItem:
    __status_switch = {
        "New": 0,
        "In Progress": 1,
        "Failed": 2,
        "Successful": 3,
        "Invalid": 4,
        "Retried": 5,
        "Abandoned": 6,
        "Deleted": 7,
    }

    def __init__(self, csv_row):
        self.status_id = self.__status_switch[csv_row[0]]
        self.revision = csv_row[1]
        self.reference = csv_row[2].replace('\n', '').replace("'", '"')
        self.exception = csv_row[3]
        self.deadline = csv_row[4]
        self.deadline_absolute = csv_row[5]
        self.priority = csv_row[6]
        self.robot = csv_row[7]
        self.postpone = csv_row[8]
        self.postpone_absolute = csv_row[9]
        self.started = csv_row[10]
        self.started_absolute = csv_row[11]
        self.ended = csv_row[12]
        self.ended_absolute = csv_row[13]
        self.transaction_execution_time = csv_row[14]
        self.retry_count = csv_row[15]
        self.specific_data = csv_row[16].replace('\n', '').replace("'", '"')
        self.key = csv_row[17]
        self.reviewer_name = csv_row[18]
        self.exception_reason = csv_row[19].replace('\n', '').replace("'", '"')
        self.output = csv_row[20]


