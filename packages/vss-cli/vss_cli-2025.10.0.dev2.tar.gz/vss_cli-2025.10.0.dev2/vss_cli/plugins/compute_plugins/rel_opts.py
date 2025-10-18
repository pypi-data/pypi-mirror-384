"""Compute Shared Options plugin for VSS CLI (vss-cli)."""
import click

import vss_cli.autocompletion as autocompletion
from vss_cli.plugins.compute_plugins import callbacks
from vss_cli.validators import (
    retirement_value, validate_admin, validate_inform,
    validate_json_file_or_type)

source_opt = click.option(
    '--source',
    '-s',
    help='Source virtual machine or template MOREF or UUID.',
    type=click.STRING,
    required=True,
    shell_complete=autocompletion.virtual_machines,
)
source_template_opt = click.option(
    '--source',
    '-s',
    help='Source virtual machine or template MOREF or UUID.',
    type=click.STRING,
    required=True,
    shell_complete=autocompletion.vm_templates,
)
source_image_opt = click.option(
    '--source',
    '-s',
    help='Source Virtual Machine OVA/OVF id, name or path.',
    type=click.STRING,
    required=True,
    shell_complete=autocompletion.vm_images,
)
source_clib_opt = click.option(
    '--source',
    '-s',
    help='Source content library deployable item.',
    type=click.STRING,
    required=True,
    shell_complete=autocompletion.clib_deployable_items,
)
description_opt = click.option(
    '--description',
    '-d',
    help='A brief description.',
    type=click.STRING,
    required=True,
)
client_nr_opt = click.option(
    '--client',
    '-b',
    help='Client department.',
    type=click.STRING,
    required=False,
)
client_opt = click.option(
    '--client',
    '-b',
    help='Client department.',
    type=click.STRING,
    required=True,
)
admin_opt = click.option(
    '--admin',
    '-a',
    help='Admin name, phone number and email separated by '
    '`:` i.e. "John Doe:416-123-1234:john.doe@utoronto.ca"',
    type=click.STRING,
    callback=validate_admin,
    required=False,
)
inform_opt = click.option(
    '--inform',
    '-r',
    help='Informational contact emails in comma separated',
    type=click.STRING,
    callback=validate_inform,
    required=False,
)
usage_opt = click.option(
    '--usage',
    '-u',
    help='Vm usage.',
    type=click.Choice(['Test', 'Prod', 'Dev', 'QA']),
    required=False,
    default='Test',
)
os_nr_opt = click.option(
    '--os',
    '-o',
    help='Guest operating system id.',
    type=click.STRING,
    required=False,
    shell_complete=autocompletion.operating_systems,
)
os_opt = click.option(
    '--os',
    '-o',
    help='Guest operating system id.',
    type=click.STRING,
    required=True,
    shell_complete=autocompletion.operating_systems,
)
memory_opt = click.option(
    '--memory', '-m', help='Memory in GB.', type=click.INT, required=False
)
cpu_opt = click.option(
    '--cpu', '-c', help='Cpu count.', type=click.INT, required=False
)
cpu_cps_opt = click.option(
    '--cores-per-socket',
    help='Cores per socket.',
    type=click.INT,
    required=False,
    default=1,
)
folder_nr_opt = click.option(
    '--folder',
    '-f',
    help='Logical folder moref name or path.',
    type=click.STRING,
    required=False,
    shell_complete=autocompletion.folders,
)
folder_opt = click.option(
    '--folder',
    '-f',
    help='Logical folder moref name or path.',
    type=click.STRING,
    required=True,
    shell_complete=autocompletion.folders,
)
networks_nr_opt = click.option(
    '--net',
    '-n',
    help='Network adapter <moref-or-name>=<nic-type>.',
    type=click.STRING,
    multiple=True,
    required=False,
    callback=callbacks.process_networks_opt,
    shell_complete=autocompletion.networks,
)
networks_opt = click.option(
    '--net',
    '-n',
    help='Network adapter <moref-or-name>=<nic-type>.',
    type=click.STRING,
    multiple=True,
    required=True,
    callback=callbacks.process_networks_opt,
    shell_complete=autocompletion.networks,
)
scsi_ctrllr_opt = click.option(
    '--scsi',
    help='SCSI Controller Spec <type>=<sharing>.',
    type=click.STRING,
    multiple=True,
    required=True,
    callback=callbacks.process_scsi_opt,
    shell_complete=autocompletion.vm_controller_scsi_types,
)
scsi_ctrllr_nr_opt = click.option(
    '--scsi',
    help='SCSI Controller Spec <type>=<sharing>.',
    type=click.STRING,
    multiple=True,
    required=False,
    callback=callbacks.process_scsi_opt,
    shell_complete=autocompletion.vm_controller_scsi_types,
)
disks_nr_opt = click.option(
    '--disk',
    '-i',
    help='Disk spec <capacity>=<backing_mode>=<backing_sharing>. '
    'optional: backing_mode, backing_sharing',
    type=click.STRING,
    multiple=True,
    required=False,
    callback=callbacks.process_disk_opt,
)
disk_opt = click.option(
    '--disk',
    '-i',
    help='Disk spec <capacity>=<backing_mode>=<backing_sharing>=<backing_vmdk>. '  # NOQA:
    'optional: backing_mode, backing_sharing',
    type=click.STRING,
    multiple=True,
    required=True,
    callback=callbacks.process_disk_opt,
)
domain_opt = click.option(
    '--domain',
    '-t',
    help='Target fault domain name or moref.',
    type=click.STRING,
    required=False,
    shell_complete=autocompletion.domains,
)
notes_opt = click.option(
    '--notes', help='Custom notes.', type=click.STRING, required=False
)
custom_spec_opt = click.option(
    '--custom-spec',
    '-p',
    help='Guest OS custom specification in YAML or JSON format.',
    type=click.STRING,
    required=False,
    callback=validate_json_file_or_type,
)
day0_cfg_opt = click.option(
    '--day-zero',
    '-d0',
    help='Day0 config file path to pre-configure the os',
    type=click.STRING,
    callback=callbacks.process_day_zero,
    required=False,
)
day0_cfg_fname_opt = click.option(
    '--day-zero-name',
    help='Day0 config file name stored in the seed iso. '
    'Default to day0-config',
    type=click.STRING,
    required=False,
)
idtoken_cfg_opt = click.option(
    '--id-token',
    '-d0i',
    help='Day0 Identity Token to register with the Smart Licensing server.',
    type=click.STRING,
    callback=callbacks.process_day_zero,
    required=False,
)
idtoken_cfg_fname_opt = click.option(
    '--id-token-name',
    help='Day0 Identity Token config file name stored in the seed iso. '
    'Defaults to idtoken',
    type=click.STRING,
    required=False,
)
additional_parameters_opt = click.option(
    '--additional-params',
    '-ap',
    help='OVF additional parameters: PropertyParams '
    'and DeploymentOptionParams in YAML or JSON format.',
    type=click.STRING,
    required=False,
    callback=validate_json_file_or_type,
)
iso_opt = click.option(
    '--iso',
    '-s',
    help='ISO image to be mounted after creation',
    type=click.STRING,
    required=False,
    shell_complete=autocompletion.isos,
)
tpm_enable_opt = click.option(
    '--tpm',
    help='Add Trusted Platform Module device.',
    is_flag=True,
    required=False,
)
vbs_enable_opt = click.option(
    '--vbs',
    help='Enable virtualization based security.',
    is_flag=True,
    required=False,
)
power_on_opt = click.option(
    '--power-on',
    help='Power on after successful deployment.',
    is_flag=True,
    required=False,
)
template_opt = click.option(
    '--template',
    help='Mark the VM as template after deployment.',
    is_flag=True,
    required=False,
)
extra_config_opt = click.option(
    '--extra-config',
    '-e',
    help='Extra configuration key=value format.',
    type=click.STRING,
    required=False,
    multiple=True,
    callback=callbacks.process_options,
)
user_data_opt = click.option(
    '--user-data',
    help='Cloud-init user_data YAML file path to '
    'pre-configure guest os upon first boot.',
    type=click.STRING,
    callback=callbacks.process_user_data,
    required=False,
)
net_cfg_opt = click.option(
    '--network-config',
    help='Cloud-init network-config YAML file path to '
    'pre-configure guest os upon first boot.',
    type=click.STRING,
    callback=callbacks.process_user_data,
    required=False,
)
vss_service_opt = click.option(
    '--vss-service',
    help='VSS Service related to VM',
    shell_complete=autocompletion.vss_services,
    required=False,
)
instances = click.option(
    '--instances',
    help='Number of instances to deploy',
    type=click.INT,
    default=1,
    show_default=True,
)
vss_options_opt = click.option(
    '--vss-option',
    help='VSS Option to enable',
    shell_complete=autocompletion.vss_options,
    required=False,
)
gpu_profile_opt = click.option(
    '--profile',
    '-p',
    type=click.STRING,
    help='GPU Profile',
    shell_complete=autocompletion.vm_gpu_profiles,
    required=True,
)
firmware_nr_opt = click.option(
    '--firmware',
    '-w',
    help='Firmware type.',
    shell_complete=autocompletion.vm_firmware,
    required=False,
)
storage_type_nr_opt = click.option(
    '--storage-type',
    help='Storage type.',
    shell_complete=autocompletion.vm_storage_type,
    required=False,
)
snapshot = click.option(
    '--snapshot',
    help='Snapshot to clone.',
    shell_complete=autocompletion.vm_snapshots,
    required=False,
)
firmware_opt = click.option(
    '--firmware',
    '-w',
    help='Firmware type.',
    shell_complete=autocompletion.vm_firmware,
    required=True,
)
retire_type = click.option(
    '--retire-type',
    type=click.Choice(['timedelta', 'datetime']),
    help='Retirement request type.',
    required=False,
)
retire_warning = click.option(
    '--retire-warning',
    type=click.INT,
    required=False,
    help='Days before retirement date to notify',
)
retire_value = click.option(
    '--retire-value',
    help='Value for given retirement type. ' 'i.e. <hours>,<days>,<months>',
    required=False,
    callback=retirement_value,
)
