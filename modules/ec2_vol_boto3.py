ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ec2_vol_boto3

short_description: ec2_vol, but using boto3

version_added: "2.4"

description:
    - "Attaches EBS volumes to EC2 instances, but using boto3 instead of boto. This means you can get credentials from EC2 instance roles."

options:
    instance:
        description:
            - EC2 instance to mount the volume on
        required: true
    vol:
        description:
            - EBS Volume ID
        required: true
    device:
        description:
            - Device ID, e.g. /dev/sdf
        required: true
    state:
        description:
            - attached or detached
        default: attached
        choices:
            - attached
            - detached
    exclusive:
        description:
            - No other instance can have this volume.
        default: false
        type: bool

author:
    - Chester Koh (@chesnutcase)
'''

EXAMPLES = '''
# Pass in a message
- name: Attach a volume to an instance
  ec2_vol_boto3:
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
        vol=dict(type='str', required=True),
        device=dict(type='str', required=True),
        state=dict(type='str', required=True),
        exclusive=dict(type='bool', default=True)
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
        volumes = ec2_client.describe_volumes(VolumeIds=[module.params["vol"]])["Volumes"]

        if len(volumes) == 0:
            module.fail_json(msg="No such volume found", **result)

        volume = volumes[0]
        instance_already_holds_volume = False
        for attachment in volume["Attachments"]:
            if module.params["state"] == "attached":
                if attachment["InstanceId"] != module.params["instance"]:
                    if module.params["exclusive"]:
                        module.fail_json(
                            msg="Exclusive mode requested, but this volume is already attached to another instance",
                            **result)
                else:
                    # no change
                    module.exit_json(**result)
                    return
            elif module.params["state"] == "detached":
                if attachment["InstanceId"] != module.params["instance"]:
                    if module.params["exclusive"]:
                        module.fail_json(
                            msg="Exclusive mode requested, but this volume is already attached to another instance",
                            **result)
                else:
                    instance_already_holds_volume = True

        if instance_already_holds_volume and module.params["state"] == "detached":
            # detach volume
            ec2_client.detach_volume(Device=module.params["device"], InstanceId=module.params["instance"],
                                     VolumeId=module.params["vol"])
        elif not instance_already_holds_volume and module.params["state"] == "attached":
            # attach volume
            ec2_client.attach_volume(Device=module.params["device"], InstanceId=module.params["instance"],
                                     VolumeId=module.params["vol"])
        else:
            # no change
            module.exit_json(**result)
            return

        result["changed"] = True

        def find_attachment(client, volume, instance):
            def curry():
                attachments = client.describe_volumes(VolumeIds=[volume])["Volumes"][0]["Attachments"]
                return next(filter(lambda a: a["InstanceId"] == instance, attachments))

            return curry

        while find_attachment(client=ec2_client, volume=module.params["vol"], instance=module.params["instance"])()[
            "State"] != module.params["state"]:
            time.sleep(0.25)

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
