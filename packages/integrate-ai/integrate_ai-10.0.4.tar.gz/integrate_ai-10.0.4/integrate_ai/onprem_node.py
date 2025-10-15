
# Copyright (C) Integrate.ai, Inc. All rights reserved.

import subprocess
import sys
from integrate_ai.utils.rest_client import RestClient
import typer
import os
import rich
from integrate_ai.utils.typer_utils import (
    TogglePromptOption,
)

app = typer.Typer(no_args_is_help=True)
# Default white list for AWS addr to query EC2 metadata
no_proxy_addr = "169.254.169.254,169.254.170.2,/var/run/docker.sock"


@app.command()
def install(
    token: str = TogglePromptOption(
        ...,
        help="Your generated IAI token.",
        prompt="Please provide your IAI token",
        envvar="IAI_TOKEN",
    ),
    taskrunner_name: str = TogglePromptOption(
        ...,
        help="The taskrunner name to register.",
        prompt="Please provide the taskrunner name",
        envvar="IAI_TASKRUNNER_NAME",
    ),
):
    """
    This command register this node and save the regiter information to ecsanywhere_output.txt
    """
    if os.geteuid() != 0:
        rich.print("This command must be run as root.")
        sys.exit(1)
    try:
        # clean up rm /tmp/ecs-anywhere-install.sh if there is any
        if os.path.exists("/tmp/ecs-anywhere-install.sh"):
            subprocess.run("rm /tmp/ecs-anywhere-install.sh", shell=True, check=True, text=True, capture_output=True)

        # register taskrunner id
        client = RestClient(token=token)
        response = client.register_on_prem_taskrunner(taskrunner_name)

        # install ecs anywhere
        rich.print("Installing ECS Agent..")
        install_ecs_agent(response)
        rich.print("---ECS Agent Installed---")
        taskrunners = client.get_taskrunner_info(taskrunner_name=taskrunner_name)
        prov_info = taskrunners[0].get("provisioning_info", {})
        runner_config = taskrunners[0].get("runner_config", {})
        runtime_info = prov_info.get("runtime_info")
        if runtime_info:
            proxy_addr = runtime_info.get("iai_forward_proxy_http_url")
            # configure proxy
            if proxy_addr and runner_config.get("use_global_proxy"):
                rich.print(f"Configuring ECS proxy: {proxy_addr}")
                configure_proxy(proxy_addr=proxy_addr)
        rich.print("OnPrem node installed successfully!")
    except Exception as e:
        rich.print(
            f"On-Prem register command failed with error: {e}, Logs can be found in ecsanywhere_output.txt and proxy_config.txt"
        )
        raise e


def install_ecs_agent(response):
    # install ecs anywhere
    cmd = 'sudo curl --proto "https" -o "/tmp/ecs-anywhere-install.sh" "https://amazon-ecs-agent.s3.amazonaws.com/ecs-anywhere-install-latest.sh"'
    cmd += " && sudo bash /tmp/ecs-anywhere-install.sh"
    cmd += f' --region "{response["region"]}"'
    cmd += f' --cluster "{response["cluster_name"]}"'
    cmd += f' --activation-id "{response["activation_id"]}"'
    cmd += f' --activation-code "{response["activation_code"]}"'
    cmd += "> ecsanywhere_output.txt"
    try:
        rich.print("Registering...")
        subprocess.run(cmd, shell=True, check=True, timeout=1200)
        rich.print("Agent registered successfully.")
        rich.print("Output is saved in ecsanywhere_output.txt. The file contains instance id, please do not delete.")
    except subprocess.CalledProcessError as e:
        message = f"ECS Installation command failed with error: {e.stderr}, Logs can be found in ecsanywhere_output.txt"
        rich.print(message)
        raise Exception(message) from e


# Add proxy addresses to the ecs config so traffic can go through the proxy by default
# See : https://docs.aws.amazon.com/AmazonECS/latest/developerguide/http_proxy_config.html
def configure_proxy(proxy_addr: str):
    rich.print("Configuring Proxy config in the host")
    # proxy ssm agent
    ssm_config_cmd = "sudo mkdir -p /etc/systemd/system/amazon-ssm-agent.service.d"
    ssm_config_cmd += "&& { cat > /etc/systemd/system/amazon-ssm-agent.service.d/http-proxy.conf <<-EOF \n"
    ssm_config_cmd += "[Service] \n"
    ssm_config_cmd += f"Environment=HTTPS_PROXY={proxy_addr} \n"
    ssm_config_cmd += f"Environment=NO_PROXY={no_proxy_addr} \n"
    ssm_config_cmd += "EOF\n"
    ssm_config_cmd += "}"

    # proxy docker service
    docker_svc_cmd = "sudo mkdir -p /etc/systemd/system/docker.service.d"
    docker_svc_cmd += "&& { cat > /etc/systemd/system/docker.service.d/http-proxy.conf <<-EOF \n"
    docker_svc_cmd += "[Service] \n"
    docker_svc_cmd += f"Environment=HTTPS_PROXY={proxy_addr} \n"
    docker_svc_cmd += f"Environment=NO_PROXY={no_proxy_addr} \n"
    docker_svc_cmd += "EOF\n"
    docker_svc_cmd += "}"

    # proxy ecs-init
    ecs_init_config_cmd = "sudo mkdir -p /etc/systemd/system/ecs.service.d"
    ecs_init_config_cmd += "&& { cat > /etc/systemd/system/ecs.service.d/http-proxy.conf <<-EOF \n"
    ecs_init_config_cmd += "[Service] \n"
    ecs_init_config_cmd += f"Environment=HTTPS_PROXY={proxy_addr} \n"
    ecs_init_config_cmd += f"Environment=NO_PROXY={no_proxy_addr} \n"
    ecs_init_config_cmd += "EOF\n"
    ecs_init_config_cmd += "}"

    # proxy ecs
    ecs_config_cmd = "echo patching ecs config"
    ecs_config_cmd += "&& { cat >> /etc/ecs/ecs.config <<-EOF \n"
    ecs_config_cmd += "[Service] \n"
    ecs_config_cmd += f"HTTPS_PROXY={proxy_addr} \n"
    ecs_config_cmd += f"NO_PROXY={no_proxy_addr} \n"
    ecs_config_cmd += "EOF\n"
    ecs_config_cmd += "}"

    # restart all affected services
    restart_cmd = (
        "sudo systemctl daemon-reload && sudo systemctl restart docker.service && sudo systemctl restart "
        "amazon-ssm-agent && sudo systemctl restart ecs"
    )

    # completion_command
    completion_command = "echo proxy config successfully updated"

    command_to_execute = f"{ssm_config_cmd} && {docker_svc_cmd} && {ecs_init_config_cmd} && {ecs_config_cmd} && {restart_cmd} && {completion_command}"
    try:
        # rich.print(f"Configuring Proxy command : {command_to_execute}")
        subprocess.run(command_to_execute, shell=True, check=True, timeout=1200)
        rich.print("Proxy configured successfully")
    except subprocess.CalledProcessError as e:
        message = f"Proxy configuration failed with error: {e.stderr}"
        rich.print(message)
        raise Exception(message) from e


@app.command()
def uninstall(
    token: str = TogglePromptOption(
        ...,
        help="Your generated IAI token.",
        prompt="Please provide your IAI token",
        envvar="IAI_TOKEN",
    ),
    taskrunner_name: str = TogglePromptOption(
        ...,
        help="The taskrunner id to register.",
        prompt="Please provide the taskrunner id",
        envvar="IAI_TASKRUNNER_NAME",
    ),
):
    """
    This command deregister this node and clean up the directory.
    """
    if os.geteuid() != 0:
        rich.print("This command must be run as root.")
        sys.exit(1)
    # register taskrunner id
    client = RestClient(token=token)
    instance_id = get_instance_id()
    # Deregister only if an instance state file is found
    if instance_id:
        response = client.deregister_on_prem_taskrunner(taskrunner_name=taskrunner_name, instance_id=instance_id)
        rich.print("Deregister instance ", response["containerInstance"]["ec2InstanceId"])

    # uninstall ecs anywhere
    stop_ecs = "sudo systemctl stop ecs amazon-ssm-agent"

    try:
        stop_ecs_out = subprocess.run(stop_ecs, shell=True, check=True, text=True, capture_output=True)
        rich.print(stop_ecs_out.stdout)

        # Check OS and remove packages
        os_type = None
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("ID="):
                        os_type = line.strip().split("=")[1].replace('"', "").lower()
                        break
        except FileNotFoundError:
            raise Exception("Unable to detect OS. /etc/os-release not found.")

        if "centos" in os_type or "rhel" in os_type:
            uninstall_packages_cmd = "sudo yum remove -y amazon-ecs-init amazon-ssm-agent"
        elif "debian" in os_type or "ubuntu" in os_type:
            uninstall_packages_cmd = "sudo apt remove -y amazon-ecs-init amazon-ssm-agent"
        else:
            raise Exception("Unsupported OS for package removal")

        uninstall_out = subprocess.run(uninstall_packages_cmd, shell=True, check=True, text=True, capture_output=True)
        rich.print(uninstall_out.stdout)

        # Remove leftover directories
        remove_directories_cmd = (
            "sudo rm -rf /var/lib/ecs /etc/ecs /var/lib/amazon/ssm /var/log/ecs /var/log/amazon/ssm"
        )
        remove_directories_cmd += " && sudo rm -rf /var/lib/amazon/ssm/Vault/Store/RegistrationKey"
        remove_directories_cmd += " && sudo rm -rf /etc/ecs"
        remove_directories_cmd += " && sudo rm -rf /var/lib/ecs"
        remove_directories_cmd += " && sudo rm -rf /var/log/ecs"
        remove_directories_cmd += " && sudo rm  /etc/systemd/system/ecs.service"
        remove_directories_cmd += " && sudo systemctl daemon-reexec"
        remove_directories_cmd += " && sudo rm -rf /etc/systemd/system/amazon-ssm-agent.service.d/http-proxy.conf"
        remove_directories_cmd += " && sudo rm -rf /etc/systemd/system/docker.service.d/http-proxy.conf"
        remove_directories_cmd += " && sudo rm -rf /etc/systemd/system/ecs.service.d/http-proxy.conf"
        remove_directories_cmd += " && sudo rm -rf /etc/ecs/ecs.config"

        subprocess.run(remove_directories_cmd, shell=True, check=True, text=True)
        rich.print("Leftover directories removed")

        # Remove instance id file
        remove_output_cmd = "sudo rm -f ecsanywhere_output.txt"
        subprocess.run(remove_output_cmd, shell=True, check=True, text=True)
        rich.print("ecsanywhere_output.txt removed")
        rich.print("proxy entries removed")

    except subprocess.CalledProcessError as e:
        rich.print(f"Command failed with error: {e.stderr}")


def get_instance_id():
    result = subprocess.check_output(
        "grep 'Container instance arn:' ecsanywhere_output.txt | sed 's#.*/##'", shell=True
    )
    instance_id = result.decode("utf-8").strip().strip('"')
    if not instance_id:
        rich.print(
            "[red]Error: Could not parse instance ID from ecsanywhere_output.txt. Please verify the file's contents."
        )
        rich.print("Instance ID not found.")
    rich.print("Deregister instance with instance_id ", instance_id)
    return instance_id


@app.callback()
def main():
    """
    Sub command for managing on-prem taskrunners related operations.
    """
