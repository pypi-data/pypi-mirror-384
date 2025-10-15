import keyboard
import threading
from typing import Any, Dict

from bluer_sbc.session.functions import reply_to_bash
from bluer_algo.socket.classes import DEV_HOST

from bluer_ugv.swallow.session.classical.setpoint.classes import ClassicalSetPoint
from bluer_ugv.swallow.session.classical.mode import OperationMode
from bluer_ugv.swallow.session.classical.leds import ClassicalLeds
from bluer_ugv import env
from bluer_ugv.logger import logger

bash_keys = {
    "i": "exit",
    "o": "shutdown",
    "p": "reboot",
    "u": "update",
}


class ClassicalKeyboard:
    def __init__(
        self,
        leds: ClassicalLeds,
        setpoint: ClassicalSetPoint,
    ):
        logger.info(
            "{}: {}".format(
                self.__class__.__name__,
                ", ".join(
                    [f"{key}:{action}" for key, action in bash_keys.items()],
                ),
            )
        )

        self.leds = leds

        self.last_key: str = ""

        self.setpoint = setpoint

        self.special_key: bool = False

        self._lock = threading.Lock()
        self.config: Dict[str, Any] = {
            "debug_mode": False,
            "mode": OperationMode.NONE,
            "ultrasound_enabled": True,
        }

    def get(self, what: str, default: Any) -> Any:
        with self._lock:
            return self.config.get(what, default)

    def set(self, what: str, value: Any):
        with self._lock:
            self.config[what] = value

    def update(self) -> bool:
        self.last_key = ""

        # bash keys
        if self.special_key:
            for key, event in bash_keys.items():
                if keyboard.is_pressed(key):
                    reply_to_bash(event)
                    return False

        # other keys
        for key, func in {
            " ": self.setpoint.stop,
            "x": self.setpoint.start,
            "s": lambda: self.setpoint.put(
                what="speed",
                value=self.setpoint.get(what="speed") - 10,
            ),
            "w": lambda: self.setpoint.put(
                what="speed",
                value=self.setpoint.get(what="speed") + 10,
            ),
        }.items():
            if keyboard.is_pressed(key):
                self.special_key = False
                func()

        # steering
        if keyboard.is_pressed("a"):
            self.special_key = False
            self.last_key = "a"
            self.setpoint.put(
                what="steering",
                value=env.BLUER_UGV_SWALLOW_STEERING_SETPOINT,
            )
        elif keyboard.is_pressed("d"):
            self.special_key = False
            self.last_key = "d"
            self.setpoint.put(
                what="steering",
                value=-env.BLUER_UGV_SWALLOW_STEERING_SETPOINT,
            )
        else:
            self.setpoint.put(
                what="steering",
                value=0,
                log=False,
            )

        # debug mode
        if keyboard.is_pressed("b"):
            self.special_key = False
            self.set("debug_mode", True)
            logger.info(f'debug enabled, run "@swallow debug" on {DEV_HOST}.')

        if keyboard.is_pressed("v"):
            self.special_key = False
            self.set("debug_mode", False)
            logger.info("debug disabled.")

        # mode
        mode = self.get("mode", OperationMode.NONE)
        updated_mode = mode
        if keyboard.is_pressed("y"):
            updated_mode = OperationMode.NONE

        if keyboard.is_pressed("t"):
            updated_mode = OperationMode.TRAINING

        if keyboard.is_pressed("g"):
            updated_mode = OperationMode.ACTION

        if mode != updated_mode:
            self.set("mode", updated_mode)
            logger.info("mode: {}.".format(updated_mode.name.lower()))
            self.special_key = False

        # ultrasound
        if keyboard.is_pressed("n"):
            self.set("ultrasound_enabled", False)
            logger.info("ultrasound: disabled")
            self.special_key = False

        if keyboard.is_pressed("m"):
            self.set("ultrasound_enabled", True)
            logger.info("ultrasound: enabled")
            self.special_key = False

        # special key
        if keyboard.is_pressed("z") and not self.special_key:
            self.special_key = True
            logger.info("🪄 special key enabled.")

        if self.special_key:
            self.leds.flash_all()

        return True
