ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ec2_eni_boto3

short_description: ec2_eni, but using boto3

version_added: "2.4"

description:
    - "Attaches existing Elastic Network Interfaces to EC2 instances, but using boto3 instead of boto. This means you can get credentials from EC2 instance roles."

options:
    instance:
        description:
            - EC2 instance to mount the volume on
        required: true
    eni:
        description:
            - ENI id
        required: true
    index:
        description;
            - The device index for the network interface attachment
        required: true
    state:
        description:
            - attached or detached
        default: attached
        choices:
            - attached
            - detached
author:
    - Chester Koh (@chesnutcase)
'''

EXAMPLES = '''
# Pass in a message
- name: Attach an interface to an instance
  ec2_eni_boto3:
    instance: i-1234567890a
    volume: vol-987615231d
    device: /dev/sdf
    state: attached
    exclusive: true
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
import time


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        instance=dict(type='str', required=True),
        eni=dict(type='str', required=True),
        index=dict(type='int', required=True),
        state=dict(type='str', required=True),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    try:
        import boto3

        ec2_client = boto3.client("ec2")

        interfaces = ec2_client.describe_network_interfaces(
            NetworkInterfaceIds=[
                module.params["eni"]
            ]
        )

        if len(interfaces["NetworkInterfaces"]) == 0:
            module.fail_json(msg="No such interface found", **result)
            return

        interface = interfaces["NetworkInterfaces"][0]

        if module.params["state"] == "attached" and interface.get("Attachment", dict()).get("InstanceId") == \
                module.params["instance"]:
            # nothing changed
            module.exit_json(**result)
            return
        elif module.params["state"] == "detached" and interface.get("Attachment", dict()).get("InstanceId") != \
                module.params["instance"]:
            # nothing changed
            module.exit_json(**result)
            return

        if module.params["state"] == "attached":
            ec2_client.attach_network_interface(
                DeviceIndex=module.params["index"],
                InstanceId=module.params["instance"],
                NetworkInterfaceId=module.params["eni"]
            )
        elif module.params["state"] == "detached":
            attachment_id = interface["Attachment"]["AttachmentId"]
            ec2_client.detach_network_interface(
                AttachmentId=attachment_id
            )
        else:
            module.fail_json(msg="Expected 'attached' or 'detached' for state", **result)
            return

        result["changed"] = True
        module.exit_json(**result)
        return

    except ImportError as ex:
        module.fail_json(msg="This module requires boto3", **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
