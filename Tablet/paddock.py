import pyray as pr
import os
import shutil

from ast import literal_eval
from pathlib import Path
from shapely import Polygon

from UI import InfoBox

class Paddock:
    def __init__(self, name: str, file_path: str, infoboxes: list, remove_infobox: object) -> None:
        self.name = name
        self.file_path = file_path

        self.infoboxes = infoboxes
        self.remove_infobox = remove_infobox

        self.paint_tex_grid = {}
        self.runlines = {}
        self.boundaries = {}
        self.obstacles = {}

        self.marking_boundary = False
        self.marking_obstacle = False

    def load(self) -> None:
        self.paint_tex_grid = {}
        paint_path = Path(self.file_path, ".paint-data")

        if paint_path.exists():
            for filename in os.listdir(paint_path):
                image = pr.load_image(str(Path(self.file_path, ".paint-data", filename)))
                texture = pr.load_texture_from_image(image)
                pr.unload_image(image)

                x, y = filename.replace(".png", "").split("_")

                self.paint_tex_grid[(int(x), int(y))] = pr.load_render_texture(self.CHUNK_SIZE, self.CHUNK_SIZE)

                pr.begin_texture_mode(self.paint_tex_grid[(int(x), int(y))])
                pr.rl_set_blend_mode(3)
                pr.draw_texture_rec(texture, pr.Rectangle(0, 0, texture.width, -texture.height), (0, 0), pr.WHITE)
                pr.rl_set_blend_mode(0)
                pr.end_texture_mode()
        else:
            print(f"Paint data doesn't exist! Previous paint data cleared.")
            self.infoboxes.append(InfoBox("Paint data doesn't exist!", 'warning', self.remove_infobox))

        # AB data could also be changed or corrupted. More robust error handling should be implemented here too.
        self.runlines = {}
        run_path = Path(self.file_path, ".run-data")

        if run_path.exists():
            for file in os.listdir(run_path):
                with open(file, "r") as f:
                    ab_dir, ab_offset = f.read().split(",")
                    self.runlines[file] = (float(ab_dir), float(ab_offset))
        else:
            print(f"AB data doesn't exist! AB data reset.")
            self.infoboxes.append(InfoBox("AB data doesn't exist!", 'warning', self.remove_infobox))
            
        self.boundaries = {}
        self.obstacles = {}

        root_path = Path(self.file_path, ".boundary-data")
        boundaries_path = os.path.join(root_path, "boundaries")
        obstacles_path = os.path.join(root_path, "obstacles")

        if root_path.exists():
            if boundaries_path.exists():
                for file in os.listdir(boundaries_path):
                    with open(os.path.join(boundaries_path, file), 'r') as f:
                        self.boundaries[file] = Polygon(literal_eval(f.read()))
            else:
                text = "Boundary data doesn't exist!"
                print(text)
                self.infoboxes.append(InfoBox(text, 'warning', self.remove_infobox))

                os.mkdir(boundaries_path)

            if obstacles_path.exists():
                for file in os.listdir(obstacles_path):
                    with open(os.path.join(obstacles_path, file), 'r') as f:
                        self.obstacles[file] = Polygon(literal_eval(f.read()))
            else:
                text = "Obstacle data doesn't exist!"
                print(text)
                self.infoboxes.append(InfoBox(text, 'warning', self.remove_infobox))

                os.mkdir(obstacles_path)
        else:
            text = "Boundary & obstacle data doesn't exist!"
            print(text)
            self.infoboxes.append(InfoBox(text, 'warning', self.remove_infobox))

            os.mkdir(root_path)
            os.mkdir(boundaries_path)
            os.mkdir(obstacles_path)

    def save(self) -> None:
        # This should never be called without the `load` method being called, that is why directories are assumed to be created here

        paint_path = Path(self.file_path, ".paint-data")
        run_path = Path(self.file_path, ".run-data")

        root_path = Path(self.file_path, ".boundary-data")
        boundaries_path = os.path.join(root_path, "boundaries")
        obstacles_path = os.path.join(root_path, "obstacles")

        shutil.rmtree(paint_path, True)
        os.mkdir(paint_path)

        for (x, y) in self.paint_tex_grid.keys():
            image = pr.load_image_from_texture(self.paint_tex_grid[(x, y)].texture)
            pr.export_image(image, os.path.join(paint_path, f"{x}_{y}.png"))

        for name, (run_dir, run_offset) in self.runlines:
            with open(os.path.join(run_path, name), "w") as f:
                f.write(f"{run_dir},{run_offset}")

        for name, boundary in self.boundaries:
            with open(os.path.join(boundaries_path, name), 'w') as f:
                f.write(str(boundary.boundary))

        for name, obstacle in self.obstacles:
            with open(os.path.join(obstacles_path, name), 'w') as f:
                f.write(str(obstacle.boundary))

class OutlineSide:
    LEFT = False
    RIGHT = True

class PaddockManager:
    def __init__(self, infoboxes: list[InfoBox], remove_infobox: object) -> None:
        self.infoboxes = infoboxes
        self.remove_infobox = remove_infobox

        self.paddocks = []
        self.active_paddock = None

        self.outline_side = OutlineSide.LEFT

        self._load_saved_data()

    def _load_saved_data(self) -> None:
        self.paddocks = []

        if not os.path.exists(".paddock-data"):
            text = "Paddock data doesn't exist!"
            print(text)
            self.infoboxes.append(InfoBox(text, 'warning', self.remove_infobox))

            os.mkdir(".paddock-data")

        for pdk_dir in os.listdir(".paddock-data"):
            self.paddocks.append(Paddock(pdk_dir, os.path.join(".paddock-data", pdk_dir), self.infoboxes, self.remove_infobox))

    def get_paddock_names(self) -> list[str]:
        return [paddock.name for paddock in self.paddocks]

    def load_paddock(self, paddock_name: str) -> None:
        paddock_names = self.get_paddock_names()

        if paddock_name not in paddock_names:
            raise Exception(f"Paddock name ({paddock_name}) not in paddocks!")

        self.save_active_paddock()

        self.active_paddock = self.paddocks[paddock_names.index(paddock_name)]
        self.active_paddock.load()

    def save_active_paddock(self) -> None:
        if self.active_paddock is not None:
            self.active_paddock.save()

    def reset_paint(self) -> None:
        if self.active_paddock is None: return

        self.active_paddock.reset_paint()

    def create_paddock(self, name: str) -> None:
        # PaddockManager is strict and expects the caller to check for this already
        if name in self.get_paddock_names():
            raise Exception(f"Paddock name ({name}) already exists!")

        new_paddock_path = Path(".paddock-data", name)
        new_paddock = Paddock(name, new_paddock_path, self.infoboxes, self.remove_infobox)

        self.paddocks.append(new_paddock)

    def delete_paddock(self, name: str) -> None:
        paddock_names = self.get_paddock_names()

        if name not in paddock_names:
            raise Exception(f"Paddock name ({name}) does not exist!")

        self.paddocks.pop(paddock_names.index(name))

    def is_marking_boundary_outline(self) -> bool:
        """Returns: `True` if it is marking a boundary, `False` if not."""
        if self.active_paddock is None: return False

        return self.active_paddock.marking_boundary

    def toggle_marking_boundary_outline(self) -> None:
        if self.active_paddock is None: return

    def is_marking_obstacle_outline(self) -> bool:
        """Returns: `True` if it is marking an obstacle, `False` if not."""
        if self.active_paddock is None: return False

        return self.active_paddock.marking_obstacle

    def toggle_marking_obstacle_outline(self) -> None:
        if self.active_paddock is None: return

    def get_outline_side(self) -> bool:
        """Returns: `OutlineSide.LEFT` if the outline side is to the left, `OutlineSide.RIGHT` if it is to the right"""

        return self.outline_side

    def toggle_outline_side(self) -> None:
        self.outline_side = not self.outline_side