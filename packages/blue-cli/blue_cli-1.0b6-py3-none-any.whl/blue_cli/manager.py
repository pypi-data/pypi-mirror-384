import curses
import os
import string
import asyncio
import subprocess
import sys
import time
import json

import configparser
import click
import pydash
from click import Context
from importlib.metadata import version

import docker

import webbrowser
import websockets
from websockets import exceptions as ws_exceptions

from blue_cli.helper import inquire_user_input, convert, print_list_curses


class Authentication:
    def __init__(self) -> None:
        self.__WEB_PORT = 25830
        self.process = None
        self.stop = None
        self.__SOCKET_PORT = 25831
        self.cookie = None
        self.uid = None
        self.__start_servers()

    def get_cookie(self):
        return self.cookie

    def get_uid(self):
        return self.uid

    def __set_cookie(self, cookie):
        if cookie == "":
            cookie = None
        self.cookie = cookie

    def __set_uid(self, uid):
        if uid == "":
            uid = None
        self.uid = uid

    def __start_servers(self):
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        try:
            self.process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "http.server",
                    str(self.__WEB_PORT),
                    "-b",
                    "localhost",
                    "-d",
                    f"{path}/blue_cli/web/auth/out",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            time.sleep(2)
            webbrowser.open(f"http://localhost:{self.__WEB_PORT}")
            self.stop = asyncio.Future()

            async def handler(websocket):
                data = None
                while True:
                    try:
                        data = await websocket.recv()
                        json_data = json.loads(data)
                        if pydash.is_equal(json_data, "REQUEST_CONNECTION_INFO"):
                            current_profile = ProfileManager().get_selected_profile()
                            current_platform = PlatformManager().get_selected_platform()
                            message = dict(current_profile) | dict(current_platform)
                            await websocket.send(json.dumps({"type": "REQUEST_CONNECTION_INFO", "message": message}))
                        else:
                            await websocket.send(json.dumps("DONE"))
                    except ws_exceptions.ConnectionClosedOK:
                        break
                    except ws_exceptions.ConnectionClosedError:
                        break
                    except Exception as ex:
                        await websocket.send(json.dumps({"error": str(ex)}))
                self.stop.set_result(json_data)

            async def main():
                async with websockets.serve(handler, "", self.__SOCKET_PORT):
                    result = await self.stop
                    self.__set_cookie(result['cookie'])
                    self.__set_uid(result['uid'])
                    if self.process is not None:
                        self.process.terminate()

            asyncio.run(main())
        except OSError as ex:
            if self.process is not None:
                self.process.terminate()
            raise Exception(ex)
        except KeyboardInterrupt as ex:
            self.stop.set_result(None)

    def __del__(self):
        if self.process is not None:
            self.process.terminate()
        if self.stop is not None and not self.stop.done():
            self.stop.set_result(None)


class ProfileManager:
    def __init__(self):
        self.__initialize()

    def __initialize(self):
        # create .blue directory, if not existing
        if not os.path.exists(os.path.expanduser("~/.blue")):
            os.makedirs(os.path.expanduser("~/.blue"))

        # set profiles path
        self.profiles_path = os.path.expanduser("~/.blue/.profiles")

        # load profile attribute config
        self.__load_profile_attributes_config()

        # read profiles
        self.__read_profiles()

        # read selected profile
        self.selected_profile = self.__get_selected_profile_name()

        # initialize default profile
        self.__initialize_default_profile()

        # activate selected profiile
        self.__activate_selected_profile()

    def __load_profile_attributes_config(self):
        self._profile_attributes_config = {}
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        with open(f"{path}/blue_cli/configs/profile.json") as cfp:
            self._profile_attributes_config = json.load(cfp)

    def inquire_profile_attributes(self, profile_name=None):
        if profile_name is None:
            profile_name = self.get_default_profile_name()

        profile = self.get_profile(profile_name)
        profile_attributes = dict(profile)

        if profile_attributes is None:
            profile_attributes = {}

        for profile_attribute in self._profile_attributes_config:
            profile_attribute_config = self._profile_attributes_config[profile_attribute]
            prompt = profile_attribute_config['prompt']
            default = profile_attribute_config['default']
            cast = profile_attribute_config['cast']
            value = default
            current = None
            if profile_attribute in profile_attributes:
                current = profile_attributes[profile_attribute]
            if current:
                value = current
            required = profile_attribute_config['required']
            if required:
                profile_attribute_value = inquire_user_input(prompt, default=value, cast=cast, required=required)
            else:
                profile_attribute_value = value

            self.set_profile_attribute(profile_name, profile_attribute, profile_attribute_value)

    def __read_profiles(self):
        # read profiles file
        self.profiles = configparser.ConfigParser()
        self.profiles.optionxform = str
        self.profiles.read(self.profiles_path)

    def __write_profiles(self):
        # write profiles file
        with open(self.profiles_path, "w") as profilesfile:
            self.profiles.write(profilesfile, space_around_delimiters=False)

    def __get_selected_profile_name(self):
        selected_profile_path = os.path.expanduser("~/.blue/.selected_profile")
        selected_profile = "default"
        try:
            with open(selected_profile_path, "r") as profilefile:
                selected_profile = profilefile.read()
        except Exception:
            pass
        return selected_profile.strip()

    def __set_selected_profile_name(self, selected_profile_name):
        selected_profile_path = os.path.expanduser("~/.blue/.selected_profile")
        with open(selected_profile_path, "w") as profilefile:
            profilefile.write(selected_profile_name)

        self.selected_profile = selected_profile_name

    def __initialize_default_profile(self):
        default_profile_name = self.get_default_profile_name()
        if not self.has_profile(default_profile_name):
            self.create_profile(default_profile_name)

    def __activate_selected_profile(self):
        for key in self.profiles[self.selected_profile]:
            value = self.profiles[self.selected_profile][key]
            os.environ[key] = value

    def get_default_profile(self):
        default_profile_name = self.get_default_profile_name()
        return self.get_profile(default_profile_name)

    def get_default_profile_name(self):
        return "default"

    def get_selected_profile_name(self):
        return self.__get_selected_profile_name()

    def set_selected_profile_name(self, selected_profile_name):
        self.__set_selected_profile_name(selected_profile_name)

    def get_selected_profile(self):
        select_profile_name = self.get_selected_profile_name()
        return self.get_profile(select_profile_name)

    def update_selected_profile(self, **profile_attributes):
        # get selected profile name
        select_profile_name = self.get_selected_profile_name()
        self.update_selected_profile(select_profile_name, **profile_attributes)

        # activate selected profiile
        self.__activate_selected_profile()

    def get_selected_profile_attribute(self, attribute_name):
        # get selected profile name
        select_profile_name = self.get_selected_profile_name()
        return self.get_profile_attribute(select_profile_name, attribute_name)

    def set_selected_profile_attribute(self, attribute_name, attribute_value):
        # get selected profile name
        select_profile_name = self.get_selected_profile_name()
        self.set_profile_attribute(select_profile_name, attribute_name, attribute_value)

    def get_profile_list(self):
        # read profiles
        self.__read_profiles()

        # list sections (i.e. profile names)
        profiles = []
        for section in self.profiles.sections():
            profiles.append(section)
        return profiles

    def has_profile(self, profile_name):
        # read profiles file
        self.__read_profiles()

        # check profile
        return profile_name in self.profiles

    def get_profile(self, profile_name):
        if self.has_profile(profile_name):
            return self.profiles[profile_name]
        else:
            return None

    def create_profile(self, profile_name, **profile_attributes):
        # read profiles file
        self.__read_profiles()

        profile = profile_attributes

        # update profiles
        self.profiles[profile_name] = profile

        # write profiles file
        self.__write_profiles()

    def update_profile(self, profile_name, **profile_attributes):
        # get profile
        profile = self.get_profile(profile_name)
        profile = profile if profile else {}

        # update profile
        profile = dict(profile) | profile_attributes
        profile = {k: v for k, v in profile.items() if v is not None}
        # update profiles
        self.profiles[profile_name] = profile
        # write profiles file
        self.__write_profiles()

        # activate selected profiile
        self.__activate_selected_profile()

    def delete_profile(self, profile_name):
        # read profiles
        self.__read_profiles()

        # delete section under profile_name
        if not self.has_profile(profile_name):
            raise Exception(f"no profile named {profile_name}")
        else:
            self.profiles.pop(profile_name)
            self.__write_profiles()

    def select_profile(self, profile_name):
        self.set_selected_profile_name(profile_name)

        # activate selected profiile
        self.__activate_selected_profile()

    def get_profile_attribute(self, profile_name, attribute_name):
        # get profile
        profile = self.get_profile(profile_name)
        if profile is None:
            return None
        if attribute_name in profile:
            return profile[attribute_name]
        else:
            return None

    def set_profile_attribute(self, profile_name, attribute_name, attribute_value):
        self.update_profile(profile_name, **{attribute_name: attribute_value})

    def get_selected_profile_cookie(self):
        return {'session': self.get_selected_profile_attribute('BLUE_COOKIE')}

    def get_selected_profile_base_api_path(self):
        api_server = self.get_selected_profile_attribute('BLUE_PUBLIC_API_SERVER')
        platform_name = self.get_selected_profile_attribute('BLUE_DEPLOY_PLATFORM')
        return f'{api_server}/blue/platform/{platform_name}'


class ProfileName(click.Group):
    def parse_args(self, ctx, args):
        if len(args) > 0 and args[0] in self.commands:
            if len(args) == 1 or args[1] not in self.commands:
                args.insert(0, "")
        super(ProfileName, self).parse_args(ctx, args)


class PlatformManager:
    def __init__(self):
        self.__initialize()

    def __initialize(self):
        # create .blue directory, if not existing
        if not os.path.exists(os.path.expanduser("~/.blue")):
            os.makedirs(os.path.expanduser("~/.blue"))

        # set platforms path
        self.platforms_path = os.path.expanduser("~/.blue/.platforms")

        # load platform attribute config
        self.__load_platform_attributes_config()

        # load platform image list
        self.__load_platform_image_config()

        # read platforms
        self.__read_platforms()

        # read selected platform
        self.selected_platform = self.__get_selected_platform_name()

        # initialize default platform
        self.__initialize_default_platform()

        # activate selected profiile
        self.__activate_selected_platform()

    def __load_platform_image_config(self):
        self._platform_images = {}
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        with open(f"{path}/blue_cli/configs/images.json") as cfp:
            self._platform_images = json.load(cfp)

    def __load_platform_attributes_config(self):
        self._platform_attributes_config = {}
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        with open(f"{path}/blue_cli/configs/platform.json") as cfp:
            self._platform_attributes_config = json.load(cfp)

    def inquire_platform_attributes(self, platform_name=None):
        if platform_name is None:
            platform_name = self.get_default_platform_name()

        platform = self.get_platform(platform_name)
        platform_attributes = dict(platform)

        if platform_attributes is None:
            platform_attributes = {}

        for platform_attribute in self._platform_attributes_config:
            platform_attribute_config = self._platform_attributes_config[platform_attribute]
            prompt = platform_attribute_config['prompt']
            default = platform_attribute_config['default']

            ### dynamic overrides
            # set default version dynamically, if not set
            if platform_attribute == "BLUE_DEPLOY_VERSION" and default == "":
                default = version('blue-platform')

            cast = platform_attribute_config['cast']
            value = default
            current = None
            if platform_attribute in platform_attributes:
                current = platform_attributes[platform_attribute]
            if current:
                value = current
            required = platform_attribute_config['required']
            if required:
                platform_attribute_value = inquire_user_input(prompt, default=value, cast=cast, required=required)
            else:
                platform_attribute_value = value

            self.set_platform_attribute(platform_name, platform_attribute, platform_attribute_value)

    def __read_platforms(self):
        # read platforms file
        self.platforms = configparser.ConfigParser()
        self.platforms.optionxform = str
        self.platforms.read(self.platforms_path)

    def __write_platforms(self):
        # write platforms file
        with open(self.platforms_path, "w") as platformsfile:
            self.platforms.write(platformsfile, space_around_delimiters=False)

    def __get_selected_platform_name(self):
        selected_platform_path = os.path.expanduser("~/.blue/.selected_platform")
        selected_platform = "default"
        try:
            with open(selected_platform_path, "r") as platformfile:
                selected_platform = platformfile.read()
        except Exception:
            pass
        return selected_platform.strip()

    def __set_selected_platform_name(self, selected_platform_name):
        selected_platform_path = os.path.expanduser("~/.blue/.selected_platform")
        with open(selected_platform_path, "w") as platformfile:
            platformfile.write(selected_platform_name)

        self.selected_platform = selected_platform_name

    def __initialize_default_platform(self):
        default_platform_name = self.get_default_platform_name()
        if not self.has_platform(default_platform_name):
            self.create_platform(default_platform_name)

    def __activate_selected_platform(self):
        for key in self.platforms[self.selected_platform]:
            value = self.platforms[self.selected_platform][key]
            os.environ[key] = value

    def get_default_platform(self):
        default_platform_name = self.get_default_platform_name()
        return self.get_platform(default_platform_name)

    def get_default_platform_name(self):
        return "default"

    def get_selected_platform_name(self):
        return self.__get_selected_platform_name()

    def set_selected_platform_name(self, selected_platform_name):
        self.__set_selected_platform_name(selected_platform_name)

    def get_selected_platform(self):
        select_platform_name = self.get_selected_platform_name()
        return self.get_platform(select_platform_name)

    def update_selected_platform(self, **platform_attributes):
        # get selected platform name
        select_platform_name = self.get_selected_platform_name()
        self.update_selected_platform(select_platform_name, **platform_attributes)

        # activate selected profiile
        self.__activate_selected_platform()

    def get_selected_platform_attribute(self, attribute_name):
        # get selected platform name
        select_platform_name = self.get_selected_platform_name()
        return self.get_platform_attribute(select_platform_name, attribute_name)

    def set_selected_platform_attribute(self, attribute_name, attribute_value):
        # get selected platform name
        select_platform_name = self.get_selected_platform_name()
        self.set_platform_attribute(select_platform_name, attribute_name, attribute_value)

    def get_platform_list(self):
        # read platforms
        self.__read_platforms()

        # list sections (i.e. platform names)
        platforms = []
        for section in self.platforms.sections():
            platforms.append(section)
        return platforms

    def has_platform(self, platform_name):
        # read platforms file
        self.__read_platforms()

        # check platform
        return platform_name in self.platforms

    def get_platform(self, platform_name):
        if self.has_platform(platform_name):
            return self.platforms[platform_name]
        else:
            return None

    def set_user_role(self, platform_name=None, cookie=None, uid=None, role=None):
        ### get profile
        # get profile
        profile = ProfileManager().get_selected_profile()
        profile = profile if profile else {}
        profile = dict(profile)

        ### get platform
        # get platform
        platform = self.get_platform(platform_name)
        platform = platform if platform else {}
        platform = dict(platform)

        config = profile | platform

        # redis container
        redis_container = None
        ### connect to docker
        client = docker.from_env()
        containers = client.containers.list()
        for container in containers:
            if 'blue.platform' in container.labels:
                if container.labels['blue.platform'].find("redis") >= 0:
                    redis_container = container

        if redis_container is None:
            print("Platform needs to be started to perform this operation.")

        BLUE_DEPLOY_PLATFORM = config["BLUE_DEPLOY_PLATFORM"]
        error = self.__container_exec_run(container, ["redis-cli", "JSON.SET", "PLATFORM:" + BLUE_DEPLOY_PLATFORM + ":METADATA", "users." + uid + ".role", '"' + role + '"'])
        if error:
            print("Error: " + str(error))

    def create_platform(self, platform_name, **platform_attributes):
        # read platforms file
        self.__read_platforms()

        platform = platform_attributes

        # deploy platform atttribute
        platform['BLUE_DEPLOY_PLATFORM'] = platform_name

        # update platforms
        self.platforms[platform_name] = platform

        # write platforms file
        self.__write_platforms()

    def update_platform(self, platform_name, **platform_attributes):
        # get platform
        platform = self.get_platform(platform_name)
        platform = platform if platform else {}

        # update platform
        platform = dict(platform) | platform_attributes
        platform = {k: v for k, v in platform.items() if v is not None}
        # update platforms
        self.platforms[platform_name] = platform
        # write platforms file
        self.__write_platforms()

        # activate selected profiile
        self.__activate_selected_platform()

    def delete_platform(self, platform_name):
        # read platforms
        self.__read_platforms()

        # delete section under platform_name
        if not self.has_platform(platform_name):
            raise Exception(f"no platform named {platform_name}")
        else:
            self.platforms.pop(platform_name)
            self.__write_platforms()

    def install_platform(self, platform_name):

        ### get profile
        # get profile
        profile = ProfileManager().get_selected_profile()
        profile = profile if profile else {}
        profile = dict(profile)

        ### get platform
        # get platform
        platform = self.get_platform(platform_name)
        platform = platform if platform else {}
        platform = dict(platform)

        config = profile | platform

        # check deployment mode
        BLUE_DEPLOY_TARGET = config['BLUE_DEPLOY_TARGET']
        if BLUE_DEPLOY_TARGET != "localhost":
            print("Only localhost mode is supported. See README for swarm mode deployment instructions...")
            return

        ### connect to docker
        client = docker.from_env()

        # create docker volume
        self._create_docker_volume(client, config)

        #### pull images
        self._pull_docker_images(client, config)

        #### copy config to docker volume
        self._copy_config_to_docker_volume(client, config)

    def uninstall_platform(self, platform_name):

        ### get profile
        # get profile
        profile = ProfileManager().get_selected_profile()
        profile = profile if profile else {}
        profile = dict(profile)

        ### get platform
        # get platform
        platform = self.get_platform(platform_name)
        platform = platform if platform else {}
        platform = dict(platform)

        config = profile | platform

        # check deployment mode
        BLUE_DEPLOY_TARGET = config['BLUE_DEPLOY_TARGET']
        if BLUE_DEPLOY_TARGET != "localhost":
            print("Only localhost mode is supported. See README for swarm mode deployment instructions...")
            return

        ### stop platform
        self.stop_platform(platform_name)

        ### connect to docker
        client = docker.from_env()

        # remove docker volume
        self._remove_docker_volume(client, config)

        #### remove images
        self._remove_docker_images(client, config)

    def _create_docker_volume(self, client, config):
        BLUE_DATA_DIR = config["BLUE_DATA_DIR"]
        BLUE_DEPLOY_PLATFORM = config["BLUE_DEPLOY_PLATFORM"]

        ### make dir if not exists
        os.makedirs(f"{BLUE_DATA_DIR}/{BLUE_DEPLOY_PLATFORM}", exist_ok=True)
        os.makedirs(f"{BLUE_DATA_DIR}/example/{BLUE_DEPLOY_PLATFORM}", exist_ok=True)

        ### create docker volume
        # docker volume create --driver local  --opt type=none --opt device=${BLUE_DATA_DIR}/${BLUE_DEPLOY_PLATFORM} --opt o=bind blue_${BLUE_DEPLOY_PLATFORM}_data
        client.volumes.create(name=f"blue_{BLUE_DEPLOY_PLATFORM}_data", driver='local', driver_opts={'type': 'none', 'o': 'bind', 'device': f"{BLUE_DATA_DIR}/{BLUE_DEPLOY_PLATFORM}"})

        # create example data volume
        client.volumes.create(
            name=f"blue_{BLUE_DEPLOY_PLATFORM}_example_data", driver='local', driver_opts={'type': 'none', 'o': 'bind', 'device': f"{BLUE_DATA_DIR}/example/{BLUE_DEPLOY_PLATFORM}"}
        )

    def _remove_docker_volume(self, client, config):
        BLUE_DATA_DIR = config["BLUE_DATA_DIR"]
        BLUE_DEPLOY_PLATFORM = config["BLUE_DEPLOY_PLATFORM"]

        ### remove docker volume
        volumes = client.volumes.list()
        for volume in volumes:
            if volume.name == "blue_" + BLUE_DEPLOY_PLATFORM + "_data" or volume.name == "blue_" + BLUE_DEPLOY_PLATFORM + "_example_data":
                print("Removing docker volume: " + volume.name)
                volume.remove()
        client.volumes.prune()

    def _pull_docker_images(self, client, config):
        BLUE_DEPLOY_VERSION = config["BLUE_DEPLOY_VERSION"]
        BLUE_CORE_DOCKER_ORG = config["BLUE_CORE_DOCKER_ORG"]
        BLUE_DEV_DOCKER_ORG = config["BLUE_DEV_DOCKER_ORG"]
        BLUE_BUILD_IMG_SUFFIX = config["BLUE_BUILD_IMG_SUFFIX"]

        for group_key in self._platform_images:
            group = self._platform_images[group_key]
            for image_key in group:
                entry = group[image_key]
                image = entry["image"]
                canonical_image = BLUE_CORE_DOCKER_ORG + "/" + image + BLUE_BUILD_IMG_SUFFIX
                self.__pull_docker_image(client, canonical_image + ":v" + BLUE_DEPLOY_VERSION)

    def __pull_docker_image(self, client, image, trials=10, sleep=5):
        if trials > 0:
            try:
                output = []
                id_to_index = {}
                response_stream = client.api.pull(image, stream=True, decode=True)
                stdscr = curses.initscr()
                curses.curs_set(0)
                curses.noecho()
                for event in response_stream:
                    if 'id' in event:
                        id = event.get('id')
                        if 'progress' in event:
                            status = event.get('status')
                            progress = event.get('progress')
                            message = f'{status} {progress}'.strip()
                            line = {'message': f'{id}: {message}', 'id': id}
                        elif 'status' in event:
                            status = event.get('status')
                            line = {'message': f'{id}: {status}', 'id': id}
                        if id not in id_to_index:
                            output.append(line)
                            id_to_index[id] = len(output) - 1
                        else:
                            output[id_to_index[id]] = line
                    if len(output) > 0:
                        print_list_curses(stdscr, output)
                curses.endwin()
                print("Pulled image: " + image)
            except Exception:
                curses.endwin()
                time.sleep(sleep)
                print("Trying again. Remaining trials: " + str(trials - 1))
                self.__pull_docker_image(client, image, trials=trials - 1)
        else:
            print("Error Pulling Image: " + image)

    def _remove_docker_images(self, client, config):
        BLUE_DEPLOY_VERSION = config["BLUE_DEPLOY_VERSION"]
        BLUE_CORE_DOCKER_ORG = config["BLUE_CORE_DOCKER_ORG"]
        BLUE_DEV_DOCKER_ORG = config["BLUE_DEV_DOCKER_ORG"]
        BLUE_BUILD_IMG_SUFFIX = config["BLUE_BUILD_IMG_SUFFIX"]

        image_list = set()
        for group_key in self._platform_images:
            group = self._platform_images[group_key]
            for image_key in group:
                entry = group[image_key]
                image = entry["image"]
                canonical_image = BLUE_CORE_DOCKER_ORG + "/" + image + BLUE_BUILD_IMG_SUFFIX
                full_image = canonical_image + ":v" + BLUE_DEPLOY_VERSION

                image_list.add(full_image)

        blue_platform_setup_image = BLUE_CORE_DOCKER_ORG + "/" + "blue-platform-setup" + BLUE_BUILD_IMG_SUFFIX
        image_list.add(blue_platform_setup_image + ":v" + BLUE_DEPLOY_VERSION)

        # remove docker images
        images = client.images.list()
        for image in images:
            image_tags = image.tags
            for image_tag in image_tags:
                if image_tag in image_list:
                    image.remove()
        client.images.prune()

    def _copy_config_to_docker_volume(self, client, config):
        BLUE_DEPLOY_VERSION = config["BLUE_DEPLOY_VERSION"]
        BLUE_CORE_DOCKER_ORG = config["BLUE_CORE_DOCKER_ORG"]
        BLUE_BUILD_IMG_SUFFIX = config["BLUE_BUILD_IMG_SUFFIX"]
        BLUE_DEPLOY_PLATFORM = config["BLUE_DEPLOY_PLATFORM"]

        blue_platform_setup_image = BLUE_CORE_DOCKER_ORG + "/" + "blue-platform-setup" + BLUE_BUILD_IMG_SUFFIX

        self.__pull_docker_image(client, blue_platform_setup_image + ":v" + BLUE_DEPLOY_VERSION)

        # Create container to copy files from to the docker volume
        # docker run -d --rm --name blue-platform-setup -v <docker_volume>:/root alpine
        print("Copying config data...")
        container = client.containers.run(
            blue_platform_setup_image + ":v" + BLUE_DEPLOY_VERSION, "tail -f /dev/null", volumes=["blue_" + BLUE_DEPLOY_PLATFORM + "_data:/blue_data"], stdout=True, stderr=True, detach=True
        )
        # rename regsitry files
        BLUE_AGENT_REGISTRY = config["BLUE_AGENT_REGISTRY"]
        BLUE_DATA_REGISTRY = config["BLUE_DATA_REGISTRY"]
        BLUE_MODEL_REGISTRY = config["BLUE_MODEL_REGISTRY"]
        BLUE_TOOL_REGISTRY = config["BLUE_TOOL_REGISTRY"]
        BLUE_OPERATOR_REGISTRY = config["BLUE_OPERATOR_REGISTRY"]

        error = self.__container_exec_run(container, "cp -r /app/. /blue_data")
        if error:
            print("Error: " + str(error))
        error = self.__container_exec_run(container, f"mv /blue_data/config/agents.json /blue_data/config/{BLUE_AGENT_REGISTRY}.agents.json")
        if error:
            print("Error: " + str(error))
        error = self.__container_exec_run(container, f"mv /blue_data/config/data.json /blue_data/config/{BLUE_DATA_REGISTRY}.data.json")
        if error:
            print("Error: " + str(error))
        error = self.__container_exec_run(container, f"mv /blue_data/config/models.json /blue_data/config/{BLUE_MODEL_REGISTRY}.models.json")
        if error:
            print("Error: " + str(error))
        error = self.__container_exec_run(container, f"mv /blue_data/config/tools.json /blue_data/config/{BLUE_TOOL_REGISTRY}.tools.json")
        if error:
            print("Error: " + str(error))
        error = self.__container_exec_run(container, f"mv /blue_data/config/operators.json /blue_data/config/{BLUE_OPERATOR_REGISTRY}.operators.json")
        if error:
            print("Error: " + str(error))

        container.stop()
        print("Done.")

    def start_platform(self, platform_name):

        ### get profile
        # get profile
        profile = ProfileManager().get_selected_profile()
        profile = profile if profile else {}
        profile = dict(profile)

        ### get platform
        # get platform
        platform = self.get_platform(platform_name)
        platform = platform if platform else {}
        platform = dict(platform)

        config = profile | platform

        BLUE_DEPLOY_PLATFORM = config["BLUE_DEPLOY_PLATFORM"]
        BLUE_CORE_DOCKER_ORG = config["BLUE_CORE_DOCKER_ORG"]
        BLUE_DEPLOY_VERSION = config["BLUE_DEPLOY_VERSION"]
        BLUE_BUILD_IMG_SUFFIX = config["BLUE_BUILD_IMG_SUFFIX"]

        # check deployment mode
        BLUE_DEPLOY_TARGET = config['BLUE_DEPLOY_TARGET']
        if BLUE_DEPLOY_TARGET != "localhost":
            print("Only localhost mode is supported. See README for swarm mode instructions...")
            return

        ### connect to docker
        client = docker.from_env()

        ### create network
        print("Creating network: " + "blue_platform_" + BLUE_DEPLOY_PLATFORM + "_network_bridge")
        try:
            client.networks.create(name="blue_platform_" + BLUE_DEPLOY_PLATFORM + "_network_bridge", driver="bridge", attachable=True, internal=False, scope="local")
        except Exception:
            print("Already running... Exiting start")
            return

        ### run redis, api, and frontend
        BLUE_PRIVATE_DB_SERVER_PORT = config["BLUE_PRIVATE_DB_SERVER_PORT"]
        # redis
        image = "redis/redis-stack:latest"
        print("Starting container: " + image)
        client.containers.run(
            image,
            network="blue_platform_" + BLUE_DEPLOY_PLATFORM + "_network_bridge",
            hostname="blue_db_redis",
            ports={str(BLUE_PRIVATE_DB_SERVER_PORT): 6379},
            volumes=["blue_" + BLUE_DEPLOY_PLATFORM + "_data:/blue_data"],
            labels={"blue.platform": BLUE_DEPLOY_PLATFORM + "." + "redis"},
            environment=config,
            restart_policy={"Name": "always"},
            detach=True,
            stdout=True,
            stderr=True,
        )

        # api
        BLUE_PRIVATE_API_SERVER_PORT = config["BLUE_PRIVATE_API_SERVER_PORT"]
        image = BLUE_CORE_DOCKER_ORG + "/" + "blue-platform-api" + BLUE_BUILD_IMG_SUFFIX + ":v" + BLUE_DEPLOY_VERSION
        print("Starting container: " + image)
        client.containers.run(
            image,
            network="blue_platform_" + BLUE_DEPLOY_PLATFORM + "_network_bridge",
            hostname="blue_platform_api",
            ports={str(BLUE_PRIVATE_API_SERVER_PORT): 5050},
            volumes=["blue_" + BLUE_DEPLOY_PLATFORM + "_data:/blue_data", "/var/run/docker.sock:/var/run/docker.sock"],
            labels={"blue.platform": BLUE_DEPLOY_PLATFORM + "." + "api"},
            environment=config,
            restart_policy={"Name": "always"},
            detach=True,
            stdout=True,
            stderr=True,
        )

        # ray
        BLUE_PRIVATE_RAY_SERVER_PORT = config["BLUE_PRIVATE_RAY_SERVER_PORT"]
        BLUE_PUBLIC_RAY_CLIENT_PORT_RANGE = config["BLUE_PUBLIC_RAY_CLIENT_PORT_RANGE"]
        image = BLUE_CORE_DOCKER_ORG + "/" + "blue-platform-ray" + BLUE_BUILD_IMG_SUFFIX + ":v" + BLUE_DEPLOY_VERSION
        ray_ports = {}
        ray_ports[str(BLUE_PRIVATE_RAY_SERVER_PORT)] = 6380
        cpa = BLUE_PUBLIC_RAY_CLIENT_PORT_RANGE.split("-")
        start = int(cpa[0])
        end = int(cpa[1])
        for port in range(start, end + 1):
            ray_ports[str(port)] = port

        print("Starting container: " + image)
        client.containers.run(
            image,
            network="blue_platform_" + BLUE_DEPLOY_PLATFORM + "_network_bridge",
            hostname="blue_server_ray",
            ports=ray_ports,
            volumes=["blue_" + BLUE_DEPLOY_PLATFORM + "_data:/blue_data", "/var/run/docker.sock:/var/run/docker.sock"],
            labels={"blue.platform": BLUE_DEPLOY_PLATFORM + "." + "ray"},
            environment=config,
            restart_policy={"Name": "always"},
            shm_size="5g",
            detach=True,
            stdout=True,
            stderr=True,
        )

        # frontend
        BLUE_PRIVATE_WEB_SERVER_PORT = config["BLUE_PRIVATE_WEB_SERVER_PORT"]
        image = BLUE_CORE_DOCKER_ORG + "/" + "blue-platform-frontend" + BLUE_BUILD_IMG_SUFFIX + ":v" + BLUE_DEPLOY_VERSION
        print("Starting container: " + image)
        client.containers.run(
            image,
            network="blue_platform_" + BLUE_DEPLOY_PLATFORM + "_network_bridge",
            hostname="blue_platform_frontend",
            ports={str(BLUE_PRIVATE_WEB_SERVER_PORT): 3000},
            volumes=["blue_" + BLUE_DEPLOY_PLATFORM + "_data:/blue_data"],
            labels={"blue.platform": BLUE_DEPLOY_PLATFORM + "." + "frontend"},
            environment=config,
            restart_policy={"Name": "always"},
            detach=True,
            stdout=True,
            stderr=True,
        )

        # example data, postgres
        image = "postgres:16.0"
        print("Starting container: " + image)
        container = client.containers.run(
            image,
            network="blue_platform_" + BLUE_DEPLOY_PLATFORM + "_network_bridge",
            hostname="blue_db_postgres_example",
            ports={"5432": 5432},
            volumes=["blue_" + BLUE_DEPLOY_PLATFORM + "_data:/blue_data", "blue_" + BLUE_DEPLOY_PLATFORM + "_example_data:/var/lib/postgresql/data"],
            labels={"blue.platform": BLUE_DEPLOY_PLATFORM + "." + "postgres"},
            environment=config,
            restart_policy={"Name": "always"},
            detach=True,
            stdout=True,
            stderr=True,
        )

        print("Ingesting example data.")

        error = self.__container_exec_run(container, ["/bin/sh", "-c", "psql -U postgres postgres < /blue_data/data/postgres.dump"])
        if error:
            print("Error: " + str(error))

        print("Launching blue web application...")

        url = "http"
        if convert(config["BLUE_DEPLOY_SECURE"], cast='bool'):
            url += "s"
        url += "://"
        url += config["BLUE_PUBLIC_WEB_SERVER"] + ":" + config["BLUE_PUBLIC_WEB_SERVER_PORT"]

        webbrowser.open(url)

        print("Done.")

    def __container_exec_run(self, container, command, trials=10, sleep=5):
        if trials > 0:
            result = container.exec_run(command)
            if result.exit_code != 0:
                time.sleep(sleep)
                print("Trying again. Remaining trials: " + str(trials - 1))
                return self.__container_exec_run(container, command, trials=trials - 1)
            else:
                return None
        else:
            return "Error Running: " + str(command)

    def stop_platform(self, platform_name):

        ### get profile
        # get profile
        profile = ProfileManager().get_selected_profile()
        profile = profile if profile else {}
        profile = dict(profile)

        ### get platform
        # get platform
        platform = self.get_platform(platform_name)
        platform = platform if platform else {}
        platform = dict(platform)

        config = profile | platform

        # check deployment mode
        BLUE_DEPLOY_PLATFORM = config['BLUE_DEPLOY_PLATFORM']
        BLUE_DEPLOY_TARGET = config['BLUE_DEPLOY_TARGET']
        if BLUE_DEPLOY_TARGET != "localhost":
            print("Only localhost mode is supported. See README for swarm mode instructions...")
            return

        ### connect to docker
        client = docker.from_env()

        # stop blue containers
        containers = client.containers.list()
        for container in containers:
            if 'blue.platform' in container.labels or 'blue.service' in container.labels or 'blue.agent' in container.labels:
                print("Stopping container: " + str(container.id)[:12] + " " + str(container.image))
                container.stop()
        print("Pruning containers...")
        client.containers.prune()

        # remove network
        networks = client.networks.list()
        for network in networks:
            if network.name == "blue_platform_" + BLUE_DEPLOY_PLATFORM + "_network_bridge":
                print("Removing network: " + network.name)
                network.remove()
        print("Pruning networks...")
        client.networks.prune()

    def select_platform(self, platform_name):
        self.set_selected_platform_name(platform_name)

        # activate selected profiile
        self.__activate_selected_platform()

    def get_platform_attribute(self, platform_name, attribute_name):
        # get platform
        platform = self.get_platform(platform_name)
        if platform is None:
            return None
        if attribute_name in platform:
            return platform[attribute_name]
        else:
            return None

    def set_platform_attribute(self, platform_name, attribute_name, attribute_value):
        self.update_platform(platform_name, **{attribute_name: attribute_value})

    def get_selected_platform_cookie(self):
        return {'session': self.get_selected_platform_attribute('BLUE_COOKIE')}

    def get_selected_platform_base_api_path(self):
        api_server = self.get_selected_platform_attribute('BLUE_PUBLIC_API_SERVER')
        platform_name = self.get_selected_platform_attribute('BLUE_DEPLOY_PLATFORM')
        return f'{api_server}/blue/platform/{platform_name}'


class PlatformName(click.Group):
    def parse_args(self, ctx, args):
        if len(args) > 0 and args[0] in self.commands:
            if len(args) == 1 or args[1] not in self.commands:
                args.insert(0, "")
        super(PlatformName, self).parse_args(ctx, args)


class ServiceManager:
    def __init__(self):
        self.__initialize()

    def __initialize(self):
        # create .blue directory, if not existing
        if not os.path.exists(os.path.expanduser("~/.blue")):
            os.makedirs(os.path.expanduser("~/.blue"))

        # set services path
        self.services_path = os.path.expanduser("~/.blue/.services")

        # load service attribute config
        self.__load_service_attributes_config()

        # read services
        self.__read_services()

        # read selected service
        self.selected_service = self.__get_selected_service_name()

        # initialize default service
        self.__initialize_default_service()

        # activate selected service
        self.__activate_selected_service()

    def __load_service_attributes_config(self):
        self._service_attributes_config = {}
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        with open(f"{path}/blue_cli/configs/service.json") as cfp:
            self._service_attributes_config = json.load(cfp)

    def inquire_service_attributes(self, service_name=None):
        if service_name is None:
            service_name = self.get_default_service_name()

        service = self.get_service(service_name)
        service_attributes = dict(service)

        if service_attributes is None:
            service_attributes = {}

        for service_attribute in self._service_attributes_config:
            service_attribute_config = self._service_attributes_config[service_attribute]
            prompt = service_attribute_config['prompt']
            default = service_attribute_config['default']
            cast = service_attribute_config['cast']
            value = default
            current = None
            if service_attribute in service_attributes:
                current = service_attributes[service_attribute]
            if current:
                value = current
            required = service_attribute_config['required']
            if required:
                service_attribute_value = inquire_user_input(prompt, default=value, cast=cast, required=required)
            else:
                service_attribute_value = value

            self.set_service_attribute(service_name, service_attribute, service_attribute_value)

    def __read_services(self):
        # read services file
        self.services = configparser.ConfigParser()
        self.services.optionxform = str
        self.services.read(self.services_path)

    def __write_services(self):
        # write services file
        with open(self.services_path, "w") as servicesfile:
            self.services.write(servicesfile, space_around_delimiters=False)

    def __get_selected_service_name(self):
        selected_service_path = os.path.expanduser("~/.blue/.selected_service")
        selected_service = "default"
        try:
            with open(selected_service_path, "r") as servicefile:
                selected_service = servicefile.read()
        except Exception:
            pass
        return selected_service.strip()

    def __set_selected_service_name(self, selected_service_name):
        selected_service_path = os.path.expanduser("~/.blue/.selected_service")
        with open(selected_service_path, "w") as servicefile:
            servicefile.write(selected_service_name)

        self.selected_service = selected_service_name

    def __initialize_default_service(self):
        default_service_name = self.get_default_service_name()
        if not self.has_service(default_service_name):
            self.create_service(default_service_name)

    def __activate_selected_service(self):
        for key in self.services[self.selected_service]:
            value = self.services[self.selected_service][key]
            os.environ[key] = value

    def get_default_service(self):
        default_service_name = self.get_default_service_name()
        return self.get_service(default_service_name)

    def get_default_service_name(self):
        return "default"

    def get_selected_service_name(self):
        return self.__get_selected_service_name()

    def set_selected_service_name(self, selected_service_name):
        self.__set_selected_service_name(selected_service_name)

    def get_selected_service(self):
        select_service_name = self.get_selected_service_name()
        return self.get_service(select_service_name)

    def update_selected_service(self, **service_attributes):
        # get selected service name
        select_service_name = self.get_selected_service_name()
        self.update_selected_service(select_service_name, **service_attributes)

        # activate selected profiile
        self.__activate_selected_service()

    def get_selected_service_attribute(self, attribute_name):
        # get selected service name
        select_service_name = self.get_selected_service_name()
        return self.get_service_attribute(select_service_name, attribute_name)

    def set_selected_service_attribute(self, attribute_name, attribute_value):
        # get selected service name
        select_service_name = self.get_selected_service_name()
        self.set_service_attribute(select_service_name, attribute_name, attribute_value)

    def get_service_list(self):
        # read services
        self.__read_services()

        # list sections (i.e. service names)
        services = []
        for section in self.services.sections():
            services.append(section)
        return services

    def has_service(self, service_name):
        # read services file
        self.__read_services()

        # check service
        return service_name in self.services

    def get_service(self, service_name):
        if self.has_service(service_name):
            return self.services[service_name]
        else:
            return None

    def create_service(self, service_name, **service_attributes):
        # read services file
        self.__read_services()

        service = service_attributes

        # update services
        self.services[service_name] = service

        # write services file
        self.__write_services()

    def update_service(self, service_name, **service_attributes):
        # get service
        service = self.get_service(service_name)
        service = service if service else {}

        # update service
        service = dict(service) | service_attributes
        service = {k: v for k, v in service.items() if v is not None}
        # update services
        self.services[service_name] = service
        # write services file
        self.__write_services()

        # activate selected profiile
        self.__activate_selected_service()

    def delete_service(self, service_name):
        # read services
        self.__read_services()

        # delete section under service_name
        if not self.has_service(service_name):
            raise Exception(f"no service named {service_name}")
        else:
            self.services.pop(service_name)
            self.__write_services()

    def install_service(self, service_name):

        ### get profile
        # get profile
        profile = ProfileManager().get_selected_profile()
        profile = profile if profile else {}
        profile = dict(profile)

        ### get platform
        # get platform
        platform = PlatformManager().get_selected_platform()
        platform = platform if platform else {}
        platform = dict(platform)

        config = profile | platform

        # check deployment mode
        BLUE_DEPLOY_TARGET = config['BLUE_DEPLOY_TARGET']
        if BLUE_DEPLOY_TARGET != "localhost":
            print("Only localhost mode is supported. See README for swarm mode deployment instructions...")
            return

        ### connect to docker
        client = docker.from_env()

        #### pull image
        self._pull_service_docker_image(client, config, service_name)

    def uninstall_service(self, service_name):

        ### get profile
        # get profile
        profile = ProfileManager().get_selected_profile()
        profile = profile if profile else {}
        profile = dict(profile)

        ### get platform
        # get platform
        platform = PlatformManager().get_selected_platform()
        platform = platform if platform else {}
        platform = dict(platform)

        config = profile | platform

        # check deployment mode
        BLUE_DEPLOY_TARGET = config['BLUE_DEPLOY_TARGET']
        if BLUE_DEPLOY_TARGET != "localhost":
            print("Only localhost mode is supported. See README for swarm mode deployment instructions...")
            return

        ### connect to docker
        client = docker.from_env()

        #### remove image
        self._remove_docker_image(client, config, service_name)

    def _pull_service_docker_image(self, client, config, service_name):
        BLUE_DEPLOY_VERSION = config["BLUE_DEPLOY_VERSION"]
        BLUE_CORE_DOCKER_ORG = config["BLUE_CORE_DOCKER_ORG"]
        BLUE_DEV_DOCKER_ORG = config["BLUE_DEV_DOCKER_ORG"]
        BLUE_BUILD_IMG_SUFFIX = config["BLUE_BUILD_IMG_SUFFIX"]

        ### get service
        # get service
        service = self.get_service(service_name)
        service = service if service else {}
        service = dict(service)

        image = service["IMAGE"]
        # pull image
        self.__pull_docker_image(client, image)

    def __pull_docker_image(self, client, image, trials=10, sleep=5):
        if trials > 0:
            print("Pulling image: " + image)
            try:
                client.images.pull(image)
            except:
                time.sleep(sleep)
                print("Trying again. Remaining trials: " + str(trials - 1))
                self.__pull_docker_image(client, image, trials=trials - 1)
        else:
            return "Error Pulling Image: " + image

    def _remove_docker_image(self, client, config, service_name):

        BLUE_DEPLOY_VERSION = config["BLUE_DEPLOY_VERSION"]
        BLUE_CORE_DOCKER_ORG = config["BLUE_CORE_DOCKER_ORG"]
        BLUE_DEV_DOCKER_ORG = config["BLUE_DEV_DOCKER_ORG"]
        BLUE_BUILD_IMG_SUFFIX = config["BLUE_BUILD_IMG_SUFFIX"]

        ### get service
        # get service
        service = self.get_service(service_name)
        service = service if service else {}
        service = dict(service)

        full_image_name = service["IMAGE"]
        # remove docker image
        images = client.images.list()
        for image in images:
            image_tags = image.tags
            for image_tag in image_tags:
                if image_tag == full_image_name:
                    print("Removing image: " + image_tag)
                    image.remove()
        print("Pruning images...")
        client.images.prune()

    def start_service(self, service_name):

        ### get profile
        # get profile
        profile = ProfileManager().get_selected_profile()
        profile = profile if profile else {}
        profile = dict(profile)

        ### get platform
        # get platform
        platform = PlatformManager().get_selected_platform()
        platform = platform if platform else {}
        platform = dict(platform)

        config = profile | platform

        BLUE_DEPLOY_PLATFORM = config["BLUE_DEPLOY_PLATFORM"]
        BLUE_CORE_DOCKER_ORG = config["BLUE_CORE_DOCKER_ORG"]
        BLUE_DEPLOY_VERSION = config["BLUE_DEPLOY_VERSION"]
        BLUE_BUILD_IMG_SUFFIX = config["BLUE_BUILD_IMG_SUFFIX"]

        ### get service
        # get service
        service = self.get_service(service_name)
        service = service if service else {}
        service = dict(service)

        image = service["IMAGE"]

        # check deployment mode
        BLUE_DEPLOY_TARGET = config['BLUE_DEPLOY_TARGET']
        if BLUE_DEPLOY_TARGET != "localhost":
            print("Only localhost mode is supported. See README for swarm mode instructions...")
            return

        ### connect to docker
        client = docker.from_env()

        # service properties
        service_properties = {"db.host": "blue_db_redis"}

        # service
        client.containers.run(
            image,
            ["--name", service_name.upper(), "--platform", BLUE_DEPLOY_PLATFORM, "--properties", json.dumps(service_properties)],
            network="blue_platform_" + BLUE_DEPLOY_PLATFORM + "_network_bridge",
            hostname="blue_service_" + service_name.lower(),
            ports={str(service["PORT_SRC"]): service["PORT_DST"]},
            volumes=["blue_" + BLUE_DEPLOY_PLATFORM + "_data:/blue_data", "/var/run/docker.sock:/var/run/docker.sock"],
            labels={"blue.service": BLUE_DEPLOY_PLATFORM + "." + service_name.lower()},
            environment=config | service,
            detach=True,
            stdout=True,
            stderr=True,
        )

    def stop_service(self, service_name):

        ### get profile
        # get profile
        profile = ProfileManager().get_selected_profile()
        profile = profile if profile else {}
        profile = dict(profile)

        ### get platform
        # get platform
        platform = PlatformManager().get_selected_platform()
        platform = platform if platform else {}
        platform = dict(platform)

        config = profile | platform

        # check deployment mode
        BLUE_DEPLOY_PLATFORM = config["BLUE_DEPLOY_PLATFORM"]
        BLUE_DEPLOY_TARGET = config['BLUE_DEPLOY_TARGET']
        if BLUE_DEPLOY_TARGET != "localhost":
            print("Only localhost mode is supported. See README for swarm mode instructions...")
            return

        ### connect to docker
        client = docker.from_env()
        containers = client.containers.list()
        for container in containers:
            if 'blue.service' in container.labels:
                if container.labels['blue.service'].find(BLUE_DEPLOY_PLATFORM + "." + service_name.lower()) >= 0:
                    print("Stopping container: " + str(container.id)[:12] + " " + str(container.image))
                    container.stop()
        client.containers.prune()

    def select_service(self, service_name):
        self.set_selected_service_name(service_name)

        # activate selected profiile
        self.__activate_selected_service()

    def get_service_attribute(self, service_name, attribute_name):
        # get service
        service = self.get_service(service_name)
        if service is None:
            return None
        if attribute_name in service:
            return service[attribute_name]
        else:
            return None

    def set_service_attribute(self, service_name, attribute_name, attribute_value):
        self.update_service(service_name, **{attribute_name: attribute_value})

    def get_selected_service_cookie(self):
        return {'session': self.get_selected_service_attribute('BLUE_COOKIE')}

    def get_selected_service_base_api_path(self):
        api_server = self.get_selected_service_attribute('BLUE_PUBLIC_API_SERVER')
        service_name = self.get_selected_service_attribute('BLUE_DEPLOY_PLATFORM')
        return f'{api_server}/blue/service/{service_name}'


class ServiceName(click.Group):
    def parse_args(self, ctx, args):
        if len(args) > 0 and args[0] in self.commands:
            if len(args) == 1 or args[1] not in self.commands:
                args.insert(0, "")
        super(ServiceName, self).parse_args(ctx, args)


class DataRegistryManager:
    """
    Data Registry Manager for handling sources in Redis.
    """

    def __init__(self, registry="default", platform="jalal-mahmud", host="localhost", port=6379, db=0):
        self.redis_client = self.__connect_redis(host, port, db)
        self.platform_prefix = "PLATFORM"
        self.registry = registry
        self.platform = platform
        # Dynamic Redis key
        self.DATA_REGISTRY_KEY = f"{self.platform_prefix}:{self.platform}:DATA_REGISTRY:{self.registry}:DATA"

    def __connect_redis(self, host, port, db):
        try:
            client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            client.ping()  # ensure connection works
            return client
        except Exception as e:
            logger.error(f"Could not connect to Redis: {e}")
            return None

    def __ensure_registry_exists(self):
        """Ensure the root JSON structure exists in RedisJSON."""
        if not self.redis_client.json().get(self.DATA_REGISTRY_KEY):
            self.redis_client.json().set(self.DATA_REGISTRY_KEY, "$", {"contents": {"source": {}}})

    def create_source(self, source_name, source_data):
        """Create a new source in the registry. Fails if the source already exists."""
        self.__ensure_registry_exists()

        # Check if the source already exists
        existing = self.get_source(source_name)
        if existing:
            raise RuntimeError(f"Source '{source_name}' already exists.")

        source_data["type"] = "source"
        source_data["scope"] = f"/"

        # Ensure the source has a contents dict for child objects
        if "contents" not in source_data:
            source_data["contents"] = {}

        path = f"$.contents.source.{source_name}"
        self.redis_client.json().set(self.DATA_REGISTRY_KEY, path, source_data)
        logger.info(f"Source '{source_name}' created successfully.")
        return True

    def create_database(self, source_name, database_name, database_data):
        """Create a new database under a source in the registry."""
        self.__ensure_registry_exists()

        # Ensure source exists
        source = self.get_source(source_name)
        if not source:
            raise RuntimeError(f"Source '{source_name}' does not exist.")

        # RedisJSON sometimes returns a list; pick the first element if needed
        if isinstance(source, list):
            source = source[0]

        # Ensure the source has a contents dict
        if "contents" not in source:
            source["contents"] = {}
            self.redis_client.json().set(self.DATA_REGISTRY_KEY, f"$.contents.source.{source_name}", source)

        # Ensure the "database" dict exists under contents
        if "database" not in source["contents"] or not isinstance(source["contents"]["database"], dict):
            source["contents"]["database"] = {}
            self.redis_client.json().set(self.DATA_REGISTRY_KEY, f"$.contents.source.{source_name}.contents.database", {})

        # Check if database already exists
        existing = self.get_database(source_name, database_name)
        if existing:
            raise RuntimeError(f"Database '{database_name}' already exists in source '{source_name}'.")

        database_data["type"] = "database"
        database_data["scope"] = f"/source/{source_name}"

        # Ensure the source has a contents dict for child objects
        if "contents" not in database_data:
            database_data["contents"] = {}

        path = f"$.contents.source.{source_name}.contents.database.{database_name}"
        self.redis_client.json().set(self.DATA_REGISTRY_KEY, path, database_data)
        logger.info(f"Database '{database_name}' created successfully in source '{source_name}'.")
        return True

    def create_collection(self, source_name, database_name, collection_name, collection_data):
        """Create a new collection under a database in the registry."""
        self.__ensure_registry_exists()

        # Ensure database exists
        database = self.get_database(source_name, database_name)
        if not database:
            raise RuntimeError(f"Database '{database_name}' does not exist in source '{source_name}'.")

        # RedisJSON sometimes returns a list; pick the first element if needed
        if isinstance(database, list):
            database = database[0]

        # Ensure the database has a contents dict
        if "contents" not in database:
            database["contents"] = {}
            self.redis_client.json().set(self.DATA_REGISTRY_KEY, f"$.contents.source.{source_name}.contents.database.{database_name}", database)

        # Ensure the "collection" dict exists under contents
        if "collection" not in database["contents"] or not isinstance(database["contents"]["collection"], dict):
            database["contents"]["collection"] = {}
            self.redis_client.json().set(self.DATA_REGISTRY_KEY, f"$.contents.source.{source_name}.contents.database.{database_name}.contents.collection", {})

        # Check if collection already exists
        existing = self.get_collection(source_name, database_name, collection_name)
        if existing:
            raise RuntimeError(f"Collection '{collection_name}' already exists in database '{database_name}'.")

        collection_data["type"] = "collection"
        collection_data["scope"] = f"/source/{source_name}/database/{database_name}"

        # Ensure collection has a contents dict for child objects
        if "contents" not in collection_data:
            collection_data["contents"] = {}

        # Write collection into the "collection" dict
        path = f"$.contents.source.{source_name}.contents.database.{database_name}.contents.collection.{collection_name}"
        self.redis_client.json().set(self.DATA_REGISTRY_KEY, path, collection_data)

        logger.info(f"Collection '{collection_name}' created successfully in database '{database_name}' of source '{source_name}'.")
        return True

    def create_entity(self, source_name, database_name, collection_name, entity_name, entity_data):
        """Create a new entity under a collection in the registry."""
        self.__ensure_registry_exists()

        # Ensure collection exists
        collection = self.get_collection(source_name, database_name, collection_name)
        if not collection:
            raise RuntimeError(f"Collection '{collection_name}' does not exist in database '{database_name}' of source '{source_name}'.")

        # RedisJSON sometimes returns a list; pick the first element if needed
        if isinstance(collection, list):
            collection = collection[0]

        # Ensure the collection has a contents dict
        if "contents" not in collection:
            collection["contents"] = {}
            self.redis_client.json().set(self.DATA_REGISTRY_KEY, f"$.contents.source.{source_name}.contents.database.{database_name}.contents.collection.{collection_name}", collection)

        # Ensure the "entity" dict exists under contents
        if "entity" not in collection["contents"] or not isinstance(collection["contents"]["entity"], dict):
            collection["contents"]["entity"] = {}
            self.redis_client.json().set(self.DATA_REGISTRY_KEY, f"$.contents.source.{source_name}.contents.database.{database_name}.contents.collection.{collection_name}.contents.entity", {})

        # Check if entity already exists
        existing = self.get_entity(source_name, database_name, collection_name, entity_name)
        if existing:
            raise RuntimeError(f"Entity '{entity_name}' already exists in collection '{collection_name}' of database '{database_name}' in source '{source_name}'.")

        entity_data["type"] = "entity"
        entity_data["scope"] = f"/source/{source_name}/database/{database_name}/collection/{collection_name}"

        # Ensure entity has a contents dict for child attributes
        if "contents" not in entity_data:
            entity_data["contents"] = {}

        # Write entity into the "entity" dict
        path = f"$.contents.source.{source_name}.contents.database.{database_name}.contents.collection.{collection_name}.contents.entity.{entity_name}"
        self.redis_client.json().set(self.DATA_REGISTRY_KEY, path, entity_data)

        logger.info(f"Entity '{entity_name}' created successfully in collection '{collection_name}' of database '{database_name}' in source '{source_name}'.")
        return True

    def create_attribute(self, source_name, database_name, collection_name, entity_name, attribute_name, attribute_data):
        """Create a new attribute under an entity."""
        self.__ensure_registry_exists()

        # Ensure entity exists
        entity = self.get_entity(source_name, database_name, collection_name, entity_name)
        if not entity:
            raise RuntimeError(f"Entity '{entity_name}' does not exist in collection '{collection_name}'.")

        # RedisJSON sometimes returns a list; pick the first element if needed
        if isinstance(entity, list):
            entity = entity[0]

        # Ensure entity has a contents dict
        if "contents" not in entity:
            entity["contents"] = {}
            self.redis_client.json().set(
                self.DATA_REGISTRY_KEY, f"$.contents.source.{source_name}.contents.database.{database_name}.contents.collection.{collection_name}.contents.entity.{entity_name}.contents", {}
            )

        # Ensure the "attribute" dict exists under contents
        if "attribute" not in entity["contents"] or not isinstance(entity["contents"]["attribute"], dict):
            entity["contents"]["attribute"] = {}
            self.redis_client.json().set(
                self.DATA_REGISTRY_KEY,
                f"$.contents.source.{source_name}.contents.database.{database_name}.contents.collection.{collection_name}.contents.entity.{entity_name}.contents.attribute",
                {},
            )

        # Check if attribute already exists
        existing = self.get_attribute(source_name, database_name, collection_name, entity_name, attribute_name)
        if existing:
            raise RuntimeError(f"Attribute '{attribute_name}' already exists in entity '{entity_name}'.")

        attribute_data["type"] = "attribute"
        attribute_data["scope"] = f"/source/{source_name}/database/{database_name}/collection/{collection_name}/entity/{entity_name}"

        # Ensure attribute has a contents dict for child objects
        if "contents" not in attribute_data:
            attribute_data["contents"] = {}

        # Write attribute into the "attribute" dict
        path = (
            f"$.contents.source.{source_name}.contents.database.{database_name}" f".contents.collection.{collection_name}.contents.entity.{entity_name}" f".contents.attribute.{attribute_name}"
        )
        self.redis_client.json().set(self.DATA_REGISTRY_KEY, path, attribute_data)

        logger.info(
            f"Attribute '{attribute_name}' created successfully in entity '{entity_name}' " f"of collection '{collection_name}' in database '{database_name}' in source '{source_name}'."
        )
        return True

    def get_source(self, source_name):
        """Fetch a single source by name."""
        logger.info(f"Source '{source_name}' need to be fetched.")

        self.__ensure_registry_exists()
        path = f"$.contents.source.{source_name}"
        return self.redis_client.json().get(self.DATA_REGISTRY_KEY, path)

    def get_database(self, source_name, database_name):
        """Fetch a single database by name under a source."""
        logger.info(f"Database '{database_name}' in source '{source_name}' needs to be fetched.")
        self.__ensure_registry_exists()
        path = f"$.contents.source.{source_name}.contents.database.{database_name}"
        return self.redis_client.json().get(self.DATA_REGISTRY_KEY, path)

    def get_collection(self, source_name, database_name, collection_name):
        """Fetch a single collection by name under a database."""
        logger.info(f"Collection '{collection_name}' in database '{database_name}' of source '{source_name}' needs to be fetched.")
        self.__ensure_registry_exists()
        path = f"$.contents.source.{source_name}.contents.database.{database_name}.contents.collection.{collection_name}"
        return self.redis_client.json().get(self.DATA_REGISTRY_KEY, path)

    def get_entity(self, source_name, database_name, collection_name, entity_name):
        """Fetch a single entity by name under a collection."""
        logger.info(f"Entity '{entity_name}' in collection '{collection_name}' of database '{database_name}' in source '{source_name}' needs to be fetched.")
        self.__ensure_registry_exists()
        path = f"$.contents.source.{source_name}.contents.database.{database_name}.contents.collection.{collection_name}.contents.entity.{entity_name}"
        return self.redis_client.json().get(self.DATA_REGISTRY_KEY, path)

    def get_attribute(self, source_name, database_name, collection_name, entity_name, attribute_name):
        """Fetch a single attribute by name under an entity."""
        logger.info(f"Attribute '{attribute_name}' in entity '{entity_name}' of collection '{collection_name}' in database '{database_name}' in source '{source_name}' needs to be fetched.")
        self.__ensure_registry_exists()
        path = f"$.contents.source.{source_name}.contents.database.{database_name}.contents.collection.{collection_name}.contents.entity.{entity_name}.contents.attribute.{attribute_name}"
        return self.redis_client.json().get(self.DATA_REGISTRY_KEY, path)

    def delete_source(self, source_name):
        """Delete a source from the registry."""
        self.__ensure_registry_exists()
        path = f"$.contents.source.{source_name}"
        deleted = self.redis_client.json().delete(self.DATA_REGISTRY_KEY, path)
        if deleted:
            logger.info(f"Source '{source_name}' deleted successfully.")
            return True
        else:
            logger.warning(f"Source '{source_name}' not found.")
            return False

    def delete_database(self, source_name, database_name):
        """Delete a database under a source."""
        self.__ensure_registry_exists()

        source = self.get_source(source_name)
        if not source:
            logger.warning(f"Source '{source_name}' not found.")
            return False
        if isinstance(source, list):
            source = source[0]

        dbs = source.get("contents", {}).get("database", {})
        if database_name not in dbs:
            logger.warning(f"Database '{database_name}' not found in source '{source_name}'.")
            return False

        del dbs[database_name]
        self.redis_client.json().set(self.DATA_REGISTRY_KEY, f"$.contents.source.{source_name}.contents.database", dbs)
        logger.info(f"Database '{database_name}' deleted successfully from source '{source_name}'.")
        return True

    def delete_collection(self, source_name, database_name, collection_name):
        """Delete a collection under a database."""
        self.__ensure_registry_exists()

        database = self.get_database(source_name, database_name)
        if not database:
            logger.warning(f"Database '{database_name}' not found in source '{source_name}'.")
            return False
        if isinstance(database, list):
            database = database[0]

        colls = database.get("contents", {}).get("collection", {})
        if collection_name not in colls:
            logger.warning(f"Collection '{collection_name}' not found in database '{database_name}'.")
            return False

        del colls[collection_name]
        self.redis_client.json().set(self.DATA_REGISTRY_KEY, f"$.contents.source.{source_name}.contents.database.{database_name}.contents.collection", colls)
        logger.info(f"Collection '{collection_name}' deleted successfully from database '{database_name}'.")
        return True

    def delete_entity(self, source_name, database_name, collection_name, entity_name):
        """Delete an entity under a collection."""
        self.__ensure_registry_exists()

        collection = self.get_collection(source_name, database_name, collection_name)
        if not collection:
            logger.warning(f"Collection '{collection_name}' not found in database '{database_name}'.")
            return False
        if isinstance(collection, list):
            collection = collection[0]

        ents = collection.get("contents", {}).get("entity", {})
        if entity_name not in ents:
            logger.warning(f"Entity '{entity_name}' not found in collection '{collection_name}'.")
            return False

        del ents[entity_name]
        self.redis_client.json().set(self.DATA_REGISTRY_KEY, f"$.contents.source.{source_name}.contents.database.{database_name}.contents.collection.{collection_name}.contents.entity", ents)
        logger.info(f"Entity '{entity_name}' deleted successfully from collection '{collection_name}'.")
        return True

    def delete_attribute(self, source_name, database_name, collection_name, entity_name, attribute_name):
        """Delete an attribute under an entity."""
        self.__ensure_registry_exists()

        entity = self.get_entity(source_name, database_name, collection_name, entity_name)
        if not entity:
            logger.warning(f"Entity '{entity_name}' not found in collection '{collection_name}'.")
            return False
        if isinstance(entity, list):
            entity = entity[0]

        attrs = entity.get("contents", {}).get("attribute", {})
        if attribute_name not in attrs:
            logger.warning(f"Attribute '{attribute_name}' not found in entity '{entity_name}'.")
            return False

        del attrs[attribute_name]
        self.redis_client.json().set(
            self.DATA_REGISTRY_KEY,
            f"$.contents.source.{source_name}.contents.database.{database_name}.contents.collection.{collection_name}.contents.entity.{entity_name}.contents.attribute",
            attrs,
        )
        logger.info(f"Attribute '{attribute_name}' deleted successfully from entity '{entity_name}'.")
        return True

    def get_all_sources(self):
        """Fetch all sources from the data registry."""
        self.__ensure_registry_exists()
        data = self.redis_client.json().get(self.DATA_REGISTRY_KEY, "$.contents.source")
        # RedisJSON returns a list for "$" queries
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return {}

    def search_sources(self, keyword):
        """Search sources by keyword in their JSON."""
        sources = self.get_all_sources()
        matches = {name: data for name, data in sources.items() if keyword.lower() in json.dumps(data).lower()}
        return matches
