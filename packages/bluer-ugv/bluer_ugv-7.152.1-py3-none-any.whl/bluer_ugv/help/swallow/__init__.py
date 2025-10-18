from bluer_ugv.help.swallow.dataset import help_functions as help_dataset
from bluer_ugv.help.swallow.debug import help_debug
from bluer_ugv.help.swallow.env import help_functions as help_env
from bluer_ugv.help.swallow.select_target import help_select_target
from bluer_ugv.help.swallow.ultrasonic_sensor import (
    help_functions as help_ultrasonic_sensor,
)

help_functions = {
    "dataset": help_dataset,
    "debug": help_debug,
    "env": help_env,
    "select_target": help_select_target,
    "ultrasonic": help_ultrasonic_sensor,
}
