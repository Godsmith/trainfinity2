from _typeshed import Incomplete

def clamp(num, min_val, max_val): ...

class Vec2(tuple):
    def __new__(cls, *args): ...
    @staticmethod
    def from_polar(mag, angle): ...
    @property
    def x(self): ...
    @property
    def y(self): ...
    @property
    def heading(self): ...
    @property
    def mag(self): ...
    def __add__(self, other): ...
    def __sub__(self, other): ...
    def __mul__(self, other): ...
    def __truediv__(self, other): ...
    def __abs__(self): ...
    def __neg__(self): ...
    def __round__(self, ndigits: Incomplete | None = ...): ...
    def __radd__(self, other): ...
    def from_magnitude(self, magnitude): ...
    def from_heading(self, heading): ...
    def limit(self, maximum): ...
    def lerp(self, other, alpha): ...
    def scale(self, value): ...
    def rotate(self, angle): ...
    def distance(self, other): ...
    def normalize(self): ...
    def clamp(self, min_val, max_val): ...
    def dot(self, other): ...
    def __getattr__(self, attrs): ...

class Vec3(tuple):
    def __new__(cls, *args): ...
    @property
    def x(self): ...
    @property
    def y(self): ...
    @property
    def z(self): ...
    @property
    def mag(self): ...
    def __add__(self, other): ...
    def __sub__(self, other): ...
    def __mul__(self, other): ...
    def __truediv__(self, other): ...
    def __abs__(self): ...
    def __neg__(self): ...
    def __round__(self, ndigits: Incomplete | None = ...): ...
    def __radd__(self, other): ...
    def from_magnitude(self, magnitude): ...
    def limit(self, maximum): ...
    def cross(self, other): ...
    def dot(self, other): ...
    def lerp(self, other, alpha): ...
    def scale(self, value): ...
    def distance(self, other): ...
    def normalize(self): ...
    def clamp(self, min_val, max_val): ...
    def __getattr__(self, attrs): ...

class Vec4(tuple):
    def __new__(cls, *args): ...
    @property
    def x(self): ...
    @property
    def y(self): ...
    @property
    def z(self): ...
    @property
    def w(self): ...
    def __add__(self, other): ...
    def __sub__(self, other): ...
    def __mul__(self, other): ...
    def __truediv__(self, other): ...
    def __abs__(self): ...
    def __neg__(self): ...
    def __round__(self, ndigits: Incomplete | None = ...): ...
    def __radd__(self, other): ...
    def lerp(self, other, alpha): ...
    def scale(self, value): ...
    def distance(self, other): ...
    def normalize(self): ...
    def clamp(self, min_val, max_val): ...
    def dot(self, other): ...
    def __getattr__(self, attrs): ...

class Mat3(tuple):
    def __new__(cls, values: Incomplete | None = ...) -> Mat3: ...
    def scale(self, sx: float, sy: float): ...
    def translate(self, tx: float, ty: float): ...
    def rotate(self, phi: float): ...
    def shear(self, sx: float, sy: float): ...
    def __add__(self, other) -> Mat3: ...
    def __sub__(self, other) -> Mat3: ...
    def __pos__(self): ...
    def __neg__(self) -> Mat3: ...
    def __round__(self, ndigits: Incomplete | None = ...) -> Mat3: ...
    def __mul__(self, other) -> Mat3: ...
    def __matmul__(self, other) -> Mat3: ...

class Mat4(tuple):
    def __new__(cls, values: Incomplete | None = ...) -> Mat4: ...
    @classmethod
    def orthogonal_projection(cls, left, right, bottom, top, z_near, z_far) -> Mat4: ...
    @classmethod
    def perspective_projection(cls, aspect, z_near, z_far, fov: int = ...) -> Mat4: ...
    @classmethod
    def from_translation(cls, vector: Vec3) -> Mat4: ...
    @classmethod
    def from_rotation(cls, angle: float, vector: Vec3) -> Mat4: ...
    @classmethod
    def look_at_direction(cls, direction: Vec3, up: Vec3) -> Mat4: ...
    @classmethod
    def look_at(cls, position: Vec3, target: Vec3, up: Vec3) -> Mat4: ...
    def row(self, index: int): ...
    def column(self, index: int): ...
    def scale(self, vector: Vec3) -> Mat4: ...
    def translate(self, vector: Vec3) -> Mat4: ...
    def rotate(self, angle: float, vector: Vec3) -> Mat4: ...
    def transpose(self) -> Mat4: ...
    def __add__(self, other) -> Mat4: ...
    def __sub__(self, other) -> Mat4: ...
    def __pos__(self): ...
    def __neg__(self) -> Mat4: ...
    def __invert__(self) -> Mat4: ...
    def __round__(self, ndigits: Incomplete | None = ...) -> Mat4: ...
    def __mul__(self, other) -> Mat4: ...
    def __matmul__(self, other) -> Mat4: ...
