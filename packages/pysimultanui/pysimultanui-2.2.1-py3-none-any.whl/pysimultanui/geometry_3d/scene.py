from nicegui.elements.scene import Scene


class ExtendedScene(Scene,
                    component='mesh_scene.js',):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
