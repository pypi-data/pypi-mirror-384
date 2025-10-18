from RPi import GPIO  # type: ignore

from bluer_options import string
from bluer_options.timing.classes import Timing
from bluer_objects.env import abcli_object_name
from bluer_objects.metadata import post_to_object
from bluer_sbc.env import BLUER_SBC_ENV, BLUER_SBC_SWALLOW_HAS_STEERING

from bluer_ugv.swallow.session.classical.camera import (
    ClassicalCamera,
    ClassicalNavigationCamera,
    ClassicalTrackingCamera,
    ClassicalYoloCamera,
)
from bluer_ugv.swallow.session.classical.push_button import ClassicalPushButton
from bluer_ugv.swallow.session.classical.keyboard import ClassicalKeyboard
from bluer_ugv.swallow.session.classical.leds import ClassicalLeds
from bluer_ugv.swallow.session.classical.mousepad import ClassicalMousePad
from bluer_ugv.swallow.session.classical.motor import (
    ClassicalLeftMotor,
    ClassicalRightMotor,
    ClassicalRearMotors,
    ClassicalSteeringMotor,
)
from bluer_ugv.swallow.session.classical.setpoint.classes import ClassicalSetPoint
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.classes import (
    ClassicalUltrasonicSensor,
)
from bluer_ugv.env import BLUER_UGV_MOUSEPAD_ENABLED
from bluer_ugv.logger import logger


class ClassicalSession:
    def __init__(
        self,
        object_name: str,
    ):
        self.object_name = object_name

        GPIO.setmode(GPIO.BCM)

        self.leds = ClassicalLeds()

        self.setpoint = ClassicalSetPoint(
            leds=self.leds,
        )

        if BLUER_UGV_MOUSEPAD_ENABLED:
            self.mousepad = ClassicalMousePad(
                leds=self.leds,
                setpoint=self.setpoint,
            )

        self.keyboard = ClassicalKeyboard(
            leds=self.leds,
            setpoint=self.setpoint,
        )

        self.ultrasonic_sensor = ClassicalUltrasonicSensor(
            setpoint=self.setpoint,
            keyboard=self.keyboard,
        )

        self.push_button = ClassicalPushButton(
            leds=self.leds,
        )

        self.has_steering = BLUER_SBC_SWALLOW_HAS_STEERING == 1
        logger.info("has_steering: {}".format(self.has_steering))

        self.motor1 = (
            ClassicalSteeringMotor if self.has_steering else ClassicalRightMotor
        )(
            setpoint=self.setpoint,
            leds=self.leds,
        )

        self.motor2 = (
            ClassicalRearMotors if self.has_steering else ClassicalLeftMotor
        )(
            setpoint=self.setpoint,
            leds=self.leds,
        )

        logger.info(
            "wheel arrangement: {} + {}".format(
                self.motor1.role,
                self.motor2.role,
            )
        )

        camera_class = (
            ClassicalYoloCamera
            if BLUER_SBC_ENV == "yolo"
            else (
                ClassicalTrackingCamera
                if BLUER_SBC_ENV == "tracking"
                else (
                    ClassicalNavigationCamera
                    if BLUER_SBC_ENV == "navigation"
                    else ClassicalCamera
                )
            )
        )
        logger.info(f"camera: {camera_class.__name__}")
        self.camera = camera_class(
            keyboard=self.keyboard,
            leds=self.leds,
            setpoint=self.setpoint,
            object_name=self.object_name,
        )

        logger.info(
            "{}: created for {}".format(
                self.__class__.__name__,
                self.object_name,
            )
        )

        self.timing = Timing()

    def cleanup(self):
        self.ultrasonic_sensor.stop()
        self.camera.stop()

        for thing in [
            self.motor1,
            self.motor2,
            self.camera,
        ]:
            thing.cleanup()

        GPIO.cleanup()

        self.timing.calculate()
        loop_frequency = round(
            1 / self.timing.stats["session.update"]["average"],
            2,
        )
        self.timing.log()
        post_to_object(
            abcli_object_name,
            "timing",
            self.timing.as_dict,
        )
        logger.info(
            "loop frequency: {}".format(string.pretty_frequency(loop_frequency))
        )
        post_to_object(
            abcli_object_name,
            "loop_frequency",
            loop_frequency,
        )

        logger.info(f"{self.__class__.__name__}.cleanup")

    def initialize(self) -> bool:
        return all(
            thing.initialize()
            for thing in [
                self.push_button,
                self.leds,
                self.motor1,
                self.motor2,
                self.camera,
            ]
        )

    def update(self) -> bool:
        self.timing.start("session.update")

        for thing in [
            self.keyboard,
            self.push_button,
            self.camera,
            self.setpoint,
            self.motor1,
            self.motor2,
            self.leds,
        ]:
            self.timing.start(thing.__class__.__name__)

            if not thing.update():
                return False

            self.timing.stop(thing.__class__.__name__)

        self.timing.stop("session.update")
        return True
