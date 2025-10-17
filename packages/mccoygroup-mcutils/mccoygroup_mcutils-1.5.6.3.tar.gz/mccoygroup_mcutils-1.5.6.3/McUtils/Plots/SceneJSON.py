import json

__all__ = [
    "SceneJSON"
]

class SceneJSON:
    """
    JSON interchange format to use with Mathematica
    """
    class Primitive:
        def __init__(self, tag, *children, **attrs):
            self.tag = tag
            if len(children) == 1 and isinstance(children[0], (list, tuple)):
                children = children[0]
            self.children = list(children)
            self.attrs = attrs
        def to_json(self):
            return dict(
                tag=self.tag,
                children=[
                    e.to_json()
                    for e in self.children
                ],
                attrs=self.attrs
            )
        def tostring(self, **opts):
            return json.dumps(self.to_json(), **opts)
        def dump(self, file, **opts):
            if hasattr(file, 'write'):
                return json.dump(self.to_json(), file, **opts)
            else:
                with open(file, 'w+') as file:
                    return json.dump(self.to_json(), file, **opts)

    class TagElement(Primitive):
        tag = None
        def __init__(self, *children, **attrs):
            super().__init__(self.tag, *children, **attrs)

    class Graphics3D(TagElement): tag = "graphics3d"
    class Graphics(TagElement): tag = "graphics"
    class Animation(TagElement): tag = 'animation'
    class Scene(TagElement): tag = 'scene'
    class Circle(TagElement): tag = 'circle'
    class Line(TagElement): tag = 'line'
    class Rectangle(TagElement): tag = 'rectangle'
    class Polygon(TagElement): tag = 'polygon'
    class Disk(TagElement): tag = 'disk'
    class Cone(TagElement): tag = 'cone'
    class Sphere(TagElement): tag = 'sphere'
    class Cuboid(TagElement): tag = 'cuboid'
    class Cylinder(TagElement): tag = 'cylinder'
    class Text(TagElement): tag = 'text'