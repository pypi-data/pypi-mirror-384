from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

import requests
from loguru import logger


class FanType(Enum):
    FAN_80MM = auto()
    FAN_240MM = auto()


@dataclass
class Indexed80mmModule:
    flat_index: int
    downstream_layer: list[int]
    upstream_layer: list[int]


class Indexed240mmModule:
    flat_index: int
    pwm: int


class FanController:
    def __init__(self, base_url: str, machine_size: tuple[int, int]) -> None:
        self.base_url = base_url.rstrip("/")
        self.machine_size = machine_size

    def stop_everything(self) -> None:
        

    def create_80mm_module_to_set(
        self,
        index_xy: tuple[int, int],
        pwms_downstream_layer: list[float] | float,
        pwms_upstream_layer: list[float] | float,
    ) -> Indexed80mmModule:
        if index_xy[0] >= self.machine_size[0] or index_xy[1] >= self.machine_size[1]:
            logger.error(f"Index {index_xy} out of range of the machine size {self.machine_size}")
            raise ValueError("Index out of range of the machine")

        flat_index = index_xy[0] * self.machine_size[1] + index_xy[1]

        if isinstance(pwms_downstream_layer, (float, int)):
            pwms_downstream_layer = [pwms_downstream_layer] * 9
        if isinstance(pwms_upstream_layer, (float, int)):
            pwms_upstream_layer = [pwms_upstream_layer] * 9

        pwms_downstream_layer_int = [round(max(0.0, min(100.0, pwm)) * 10) for pwm in pwms_downstream_layer]
        pwms_upstream_layer_int = [round(max(0.0, min(100.0, pwm)) * 10) for pwm in pwms_upstream_layer]

        return Indexed80mmModule(
            flat_index=flat_index,
            downstream_layer=pwms_downstream_layer_int,
            upstream_layer=pwms_upstream_layer_int,
        )

    def create_240mm_module_to_set(
        self,
        index_xy: tuple[int, int],
        pwm: float,
    ) -> Indexed240mmModule:
        if index_xy[0] >= self.machine_size[0] or index_xy[1] >= self.machine_size[1]:
            logger.error(f"Index {index_xy} out of range of the machine size {self.machine_size}")
            raise ValueError("Index out of range of the machine")

        if not isinstance(pwm, float):
            logger.error("For 240mm fans, pwm has to be a single float value")
            raise TypeError("For 240mm fans, pwm has to be a single float value")

        flat_index = index_xy[0] * self.machine_size[1] + index_xy[1]

        pwm_int = round(max(0.0, min(100.0, pwm)) * 10)

        return Indexed240mmModule(
            flat_index=flat_index,
            pwm=pwm_int,
        )

    def set_fans(self, list_indexed_modules: list[Indexed80mmModule | Indexed240mmModule]) -> None:
        """
        This will take a list of IndexedModule to set
        and call the REST api to set the fans accordingly
        """
        pwm_data: dict[str, dict[str, list[int]]] = {}

        for module in list_indexed_modules:
            pwm_data[str(module.flat_index)] = {}
            if isinstance(module, Indexed240mmModule):
                pwm_data[str(module.flat_index)]["0"] = [module.pwm]

            elif isinstance(module, Indexed80mmModule):  # type: ignore[unreachable], Rationale: could be reachable if type hints are ignored
                if module.downstream_layer:
                    pwm_data[str(module.flat_index)]["0"] = module.downstream_layer
                if module.upstream_layer:
                    pwm_data[str(module.flat_index)]["1"] = module.upstream_layer
            else:
                logger.error(f"Unknown module type: {type(module)}")
                raise TypeError("Unknown module type")

        payload = {"pwm_data": pwm_data}

        url = f"{self.base_url}/windcontrol/modules/pwms"
        # logger.error(f"Setting fans with payload: {payload} at {url}")
        response = requests.patch(url, json=payload, timeout=5)
        response.raise_for_status()
        if response.status_code == 200:
            pass
            # logger.info("Successfully set fans")
        else:
            logger.error(f"Set fans response: {response.status_code} - {response.text}")
