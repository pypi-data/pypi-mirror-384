from __future__ import annotations

from collections.abc import Sequence
from enum import Enum, auto
from typing import ClassVar

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class BackendApiStatus(Enum):
    OK = auto()
    INVALID_COMMAND = auto()
    NOT_IMPLEMENTED = auto()
    COMMAND_FAILED = auto()
    TIMEOUT = auto()


WallIndex = int
FlatGridIndex = int
FanLayerIndex = int
size_2d = tuple[int, int]
AcceptablePWMData = dict[FanLayerIndex, list[int]]
AcceptableRPMData = dict[FanLayerIndex, list[int]]


class ModuleType(str, Enum):
    """
    Enum representing the type of a Windshaper Module.
    """

    MODULE_0812 = "0812"
    MODULE_0816 = "0816"
    MODULE_0818 = "0818"
    MODULE_2420 = "2420"


class ModuleTypeConfig(BaseSettings):
    type: str = Field(..., alias="type")
    number_of_layers: int = Field(..., alias="number_of_layers")
    number_fans_per_layer: int = Field(..., alias="number_fans_per_layer")
    layers_rotation_directions: dict[str, str] = Field(..., alias="layers_rotation_directions")
    max_power_watt: int = Field(..., alias="max_power_watt")


class ControllableModule(BaseModel):
    MAX_LIFEPOINTS: ClassVar[int] = 50

    mac: str
    ip: str | None = None
    type: ModuleType
    # config: ModuleTypeConfig | None

    # ! States
    rpms: AcceptableRPMData
    is_connected: bool = False
    is_blinking: bool = False
    is_psu: bool = False
    lifepoints: int = MAX_LIFEPOINTS

    # ! Commands
    pwms: AcceptablePWMData
    blink_command: bool = False
    psu_command: bool = False


class WalledModules(BaseModel):
    """
    Represents walls of modules

    Each wall contains a dictionary of modules indexed in the wall (0, 0 is top-left corner)
    """

    walls: dict[WallIndex, dict[FlatGridIndex, ControllableModule]]


class WalledModulesBuilder:
    def __init__(
        self,
        walled_modules: WalledModules,
        wall_sizes: dict[WallIndex, size_2d],
        module_sizes: dict[tuple[WallIndex, FlatGridIndex], size_2d],
        module_nb_layers: dict[tuple[WallIndex, FlatGridIndex], int],
    ):
        self._walled_modules: WalledModules = walled_modules
        self.wall_sizes: dict[WallIndex, size_2d] = wall_sizes
        self.module_sizes: dict[tuple[WallIndex, FlatGridIndex], size_2d] = module_sizes
        self.module_nb_layers: dict[tuple[WallIndex, FlatGridIndex], int] = module_nb_layers

    def column(self, col: int) -> WalledModulesBuilder:
        # Select a single column for all (or selected) walls
        return self.cols([col])

    def module_flat(self, flat_index: int) -> WalledModulesBuilder._ModuleContext:
        # Only valid if a single wall is selected
        wall_idxs = list(self.wall_sizes.keys()) if len(self.wall_sizes) == 1 else None
        if wall_idxs is None:
            raise ValueError("module_flat() requires a single wall to be selected")
        wall = self._walled_modules.walls[wall_idxs[0]]
        if flat_index not in wall:
            raise ValueError(f"flat_index {flat_index} not in wall")
        return WalledModulesBuilder._ModuleContext(wall[flat_index])

    def module(self, x: int, y: int, ncols: int | None = None) -> WalledModulesBuilder._ModuleContext:
        # Only valid if a single wall is selected
        wall_idxs = list(self.wall_sizes.keys()) if len(self.wall_sizes) == 1 else None
        if wall_idxs is None:
            raise ValueError("module() requires a single wall to be selected")
        wall = self._walled_modules.walls[wall_idxs[0]]
        if ncols is None:
            ncols = self.wall_sizes[wall_idxs[0]][0] if wall_idxs[0] in self.wall_sizes else self._infer_ncols(wall)
        flat_index = y * ncols + x
        if flat_index not in wall:
            raise ValueError(f"flat_index {flat_index} (from x={x}, y={y}, ncols={ncols}) not in wall")
        return WalledModulesBuilder._ModuleContext(wall[flat_index])

    # Add column and module to wall context for chaining
    def _wall_context_column(self, col: int) -> WalledModulesBuilder:
        # Only valid if a single wall is selected
        if len(self.wall_sizes) != 1:
            raise ValueError("column() requires a single wall to be selected")
        return self.cols([col])

    def _wall_context_module(
        self, flat_index: int | None = None, x: int | None = None, y: int | None = None, ncols: int | None = None
    ) -> WalledModulesBuilder._ModuleContext:
        if flat_index is not None:
            return self.module_flat(flat_index)
        if x is not None and y is not None:
            return self.module(x, y, ncols)
        raise ValueError("Either flat_index or both x and y must be provided")

    def wall(self, wall_index: WallIndex) -> WalledModulesBuilder:
        # Create new wall_sizes, module_sizes, module_nb_layers for the selected wall
        wall_sizes = {wall_index: self.wall_sizes[wall_index]} if wall_index in self.wall_sizes else {}
        module_sizes = {k: v for k, v in self.module_sizes.items() if k[0] == wall_index}
        module_nb_layers = {k: v for k, v in self.module_nb_layers.items() if k[0] == wall_index}
        return WalledModulesBuilder(
            self._walled_modules,
            wall_sizes=wall_sizes,
            module_sizes=module_sizes,
            module_nb_layers=module_nb_layers,
        )

    def walls(self, wall_indexs: list[WallIndex]) -> WalledModulesBuilder:
        wall_sizes = {k: v for k, v in self.wall_sizes.items() if k in wall_indexs}
        module_sizes = {k: v for k, v in self.module_sizes.items() if k[0] in wall_indexs}
        module_nb_layers = {k: v for k, v in self.module_nb_layers.items() if k[0] in wall_indexs}
        return WalledModulesBuilder(
            self._walled_modules,
            wall_sizes=wall_sizes,
            module_sizes=module_sizes,
            module_nb_layers=module_nb_layers,
        )

    def rows(self, row: list[int]) -> WalledModulesBuilder:
        # Select all modules in the specified row(s) for each selected wall
        selected_walls = self.wall_sizes.keys()
        new_wall_sizes = {}
        new_module_sizes = {}
        new_module_nb_layers = {}
        new_walls = {}
        for wall_idx in selected_walls:
            ncols, nrows = self.wall_sizes[wall_idx]
            wall = self._walled_modules.walls[wall_idx]
            selected_modules = {}
            for r in row:
                if r < 0 or r >= nrows:
                    continue
                for c in range(ncols):
                    flat_idx = r * ncols + c
                    if flat_idx in wall:
                        selected_modules[flat_idx] = wall[flat_idx]
                        k = (wall_idx, flat_idx)
                        if k in self.module_sizes:
                            new_module_sizes[k] = self.module_sizes[k]
                        if k in self.module_nb_layers:
                            new_module_nb_layers[k] = self.module_nb_layers[k]
            if selected_modules:
                new_walls[wall_idx] = selected_modules
                new_wall_sizes[wall_idx] = self.wall_sizes[wall_idx]
        new_walled_modules = WalledModules(walls=new_walls)
        return WalledModulesBuilder(
            new_walled_modules,
            wall_sizes=new_wall_sizes,
            module_sizes=new_module_sizes,
            module_nb_layers=new_module_nb_layers,
        )

    def cols(self, cols: list[int]) -> WalledModulesBuilder:
        # Select all modules in the specified column(s) for each selected wall
        selected_walls = self.wall_sizes.keys()
        new_wall_sizes = {}
        new_module_sizes = {}
        new_module_nb_layers = {}
        new_walls = {}
        for wall_idx in selected_walls:
            ncols, nrows = self.wall_sizes[wall_idx]
            wall = self._walled_modules.walls[wall_idx]
            selected_modules = {}
            for c in cols:
                if c < 0 or c >= ncols:
                    continue
                for r in range(nrows):
                    flat_idx = r * ncols + c
                    if flat_idx in wall:
                        selected_modules[flat_idx] = wall[flat_idx]
                        k = (wall_idx, flat_idx)
                        if k in self.module_sizes:
                            new_module_sizes[k] = self.module_sizes[k]
                        if k in self.module_nb_layers:
                            new_module_nb_layers[k] = self.module_nb_layers[k]
            if selected_modules:
                new_walls[wall_idx] = selected_modules
                new_wall_sizes[wall_idx] = self.wall_sizes[wall_idx]
        new_walled_modules = WalledModules(walls=new_walls)
        return WalledModulesBuilder(
            new_walled_modules,
            wall_sizes=new_wall_sizes,
            module_sizes=new_module_sizes,
            module_nb_layers=new_module_nb_layers,
        )

    def set(self, pwm: int) -> WalledModulesBuilder:
        wall_indexs = self._wall_indexs if self._wall_indexs is not None else list(self._walled_modules.walls.keys())
        for wall_index in wall_indexs:
            wall = self._walled_modules.walls[wall_index]
            if self._row_idxs is not None or self._col_idxs is not None:
                # Need to know ncols for flat index math
                ncols = self._infer_ncols(wall)
                nrows = self._infer_nrows(wall, ncols)
                row_range = self._row_idxs if self._row_idxs is not None else list(range(nrows))
                col_range = self._col_idxs if self._col_idxs is not None else list(range(ncols))
                for row in row_range:
                    for col in col_range:
                        flat_idx = row * ncols + col
                        if flat_idx in wall:
                            self._apply_set(wall[flat_idx], pwm)
            else:
                for module in wall.values():
                    self._apply_set(module, pwm)
        return self

    def _infer_ncols(self, wall: dict[int, ControllableModule]) -> int:
        # Infer ncols from the max flat index (assume rectangular grid)
        if not wall:
            return 0
        max_idx = max(wall.keys())
        # Try to guess ncols by finding the smallest difference between indices
        # This assumes a row-major order
        # If user provides ncols, this can be improved
        return int(max_idx**0.5) + 1

    def _infer_nrows(self, wall: dict[int, ControllableModule], ncols: int) -> int:
        if not wall or ncols == 0:
            return 0
        return (max(wall.keys()) // ncols) + 1

    # The rest of the API (module, layer, fan, etc.) can be added as needed, following the same pattern
    # ...existing code for _ModuleContext, _LayerContext, _FanContext, etc...

    class _ModuleContext:
        def __init__(self, module: ControllableModule):
            self._module: ControllableModule = module

        def layer(self, layer_idx: int) -> WalledModulesBuilder._LayerContext:
            return WalledModulesBuilder._LayerContext(self._module, layer_idx)

        def fan_flat(self, flat_index: int) -> WalledModulesBuilder._FanContext:
            return WalledModulesBuilder._FanContext(self._module, flat_index)

        def fan(self, x: int, y: int, ncols: int) -> WalledModulesBuilder._FanContext:
            flat_index: int = y * ncols + x
            return WalledModulesBuilder._FanContext(self._module, flat_index)

        def set(self, pwm: int) -> WalledModulesBuilder._ModuleContext:
            WalledModulesBuilder._apply_set(self._module, pwm)
            return self

    class _LayerContext:
        def __init__(self, module: ControllableModule, layer_idx: int) -> None:
            self._module: ControllableModule = module
            self._layer_idx: int = layer_idx
            self._layers: Sequence[int] = [layer_idx]

        def layers(self, layers: Sequence[int]) -> WalledModulesBuilder._LayerContext:
            self._layers = layers
            return self

        def set(self, pwm: int) -> WalledModulesBuilder._LayerContext:
            for layer in self._layers:
                WalledModulesBuilder._apply_set(self._module, pwm, layer=layer)
            return self

    class _FanContext:
        def __init__(self, module: ControllableModule, flat_index: int) -> None:
            self._module: ControllableModule = module
            self._flat_index = flat_index
            self._layers: Sequence[int] | None = None

        def layers(self, layers: Sequence[int]) -> WalledModulesBuilder._FanContext:
            self._layers = layers
            return self

        def set(self, pwm: int) -> WalledModulesBuilder._FanContext:
            layers = self._layers or getattr(self._module, "pwms", {}).keys()
            for layer in layers:
                WalledModulesBuilder._apply_set(self._module, pwm, layer=layer, fan=self._flat_index)
            return self

    @staticmethod
    def _apply_set(module: ControllableModule, pwm: int, layer: int | None = None, fan: int | None = None) -> None:
        raise NotImplementedError("Implement this method to set PWM at the desired granularity.")




if __name__ == "__main__":
    # ! Example for the builder

    # 1. Set a full wall to PWM 500
    walled_modules = WalledModules(
        walls={
            0: {
                0: ControllableModule(
                    mac="00:11:22:33:44:55",
                    type=ModuleType.MODULE_0812,
                    rpms={0: [0] * 12},
                    pwms={0: [0] * 12},
                ),
                1: ControllableModule(
                    mac="66:77:88:99:AA:BB",
                    type=ModuleType.MODULE_0812,
                    rpms={0: [0] * 12},
                    pwms={0: [0] * 12},
                ),
            },
            1: {
                0: ControllableModule(
                    mac="CC:DD:EE:FF:00:11",
                    type=ModuleType.MODULE_0812,
                    rpms={0: [0] * 12},
                    pwms={0: [0] * 12},
                ),
                1: ControllableModule(
                    mac="22:33:44:55:66:77",
                    type=ModuleType.MODULE_0812,
                    rpms={0: [0] * 12},
                    pwms={0: [0] * 12},
                ),
            },
        }
    )


WallIndex = int
PWMValue = int
FlatGridIndex = int
FanLayerIndex = int
size_2d = tuple[int, int]
AcceptablePWMData = dict[FanLayerIndex, list[int]]
AcceptableRPMData = dict[FanLayerIndex, list[int]]


class WalledModules2(BaseModel):
    """
    Represents walls of modules

    Each wall contains a dictionary of Values indexed in the wall (0, 0 is top-left corner)
    """

    walls: dict[WallIndex, dict[FlatGridIndex, PWMValue]]

    wall_sizes: dict[int, tuple[int, int]] = {0: (2, 1), 1: (2, 1)}  # 2 columns, 1 row for each wall
    module_sizes: dict[tuple[int, int], tuple[int, int]] = {
        (0, 0): (1, 1),
        (0, 1): (1, 1),
        (1, 0): (1, 1),
        (1, 1): (1, 1),
    }
    module_nb_layers: dict[tuple[int, int], int] = {
        (0, 0): 1,
        (0, 1): 1,
        (1, 0): 1,
        (1, 1): 1,
    }

    builder = WalledModulesBuilder(
        walled_modules=walled_modules,
        wall_sizes=wall_sizes,
        module_sizes=module_sizes,
        module_nb_layers=module_nb_layers,
    )

    builder.set(pwm=500) # Set all walls to 500
    builder.wall(wall_index=0).set(pwm=500) # Set wall 0 to 500
    builder.wall(wall_index=1).set(pwm=500) # Set wall
    builder.wall(wall_index=1).set(pwm=500) # Set wall


    builder.wall(wall_index=0).set(pwm=500)
    builder.wall(wall_index=1).cols(col=[0, 2]).set(pwm=500) # set column 0 and 2 of wall 1 to 500
    builder.wall(wall_index=0).rows(row=[0]).set(pwm=500)
    builder.wall(wall_index=0).rows(row=[0, 1]).set(pwm=500)
    builder.wall(wall_index=0).rows(row=[0, 1]).cols(cols=[0]).set(pwm=500)  # set rows 0 and 1 of column 0 to 500
    builder.wall(wall_index=0).rows(row=[0, 1]).cols(cols=[0, 2]).set(pwm=500)  # set rows 0 and 1 of column 0 and column 2 to 500

    builder.rows(row=[0]).cols(cols=[0, 1]).set(pwm=500)  # set row 0 of column 0 and 1 of all walls, to 500
    builder.cols(cols=[0, 1]).set(pwm=500)  # set column 0 and 1 of all walls, to 500
    builder.wall(wall_index=0).cols(cols=[0]).modules([0, 1]).set(pwm=500) # set modules 0 and 1 of column 0 of wall 0 to 500 (module is flat index)
    builder.wall(wall_index=2).cols(cols=[0]).modules([0]).layers(layers=[0, 1]).set(pwm=500)
    builder.wall(wall_index=0).cols(cols=[0]).modules([0]).fans(flat_index=[0]).set(pwm=500)

    builder.wall(wall_index=0).cols(cols=[0]).modules(flat_indexes=[0]).fans(flat_indexes=[0]).set(pwm=500)
    builder.wall(wall_index=0).cols(cols=[0]).modules(flat_indexes=[0]).fans(flat_indexes=[0]).layers(layers=[0, 1]).set(pwm=500)
    builder.wall(wall_index=0).cols(cols=[0]).modules(flat_indexes=[0]).fans(flat_indexes=[0]).layers(layers=[0, 1]).set(pwm=500)

    # 2D index version
    builder.wall(wall_index=0).cols(cols=[0]).rows(rows=[1, 2]).modules_2d(indexes=[(0, 1), (0, 2)]).fans(indexes=[(0, 0), (0, 2)]).set(pwm=500)
    builder.wall(wall_index=0).cols(cols=[0]).modules_2d(indexes=[(0, 1), (0, 2)]).fans(indexes=[(0, 0), (0, 2)]).layers(layers=[0, 1]).set(pwm=500)
    builder.wall(wall_index=0).cols(cols=[0]).modules_2d(indexes=[(0, 1), (0, 2)]).fans(indexes=[(0, 0), (0, 2)]).layers(layers=[0, 1]).set(pwm=500)
