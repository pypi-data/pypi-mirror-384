import math
import tgmath._trig as trig
import typing


def flatten(iterable:list|tuple|set|range, level=0) -> list|tuple|set|range:
    if isinstance(iterable, (list, tuple, set, range)):
        for sub in iterable:
            yield from flatten(sub, level+1)
    else:
        yield iterable


class vec: ...
class mat: ...



class vec:
	'''
	Vector class with varying size to fit use cases and custom variable type.
	Max size 4 (xyzw), min size 1 (x)

	Various functions are included for your benefit (and my requirements)
	'''

	def __init__(self, x=None, y=None, z=None, w=None, size=None, _type=float):
		'''
		Creates a new vector.
		If 'size' is undefined, it will be inferred from the values of 'x', 'y', 'z' and 'w'.
		If 'size' is defined, the values of 'x', 'y' and 'z' will default to 0 and 'w' will default to 1 (for easier matrix multiplication).
		
		All values are cast to '_type' where applicable and they are expected to stay this type but that is up to you to enforce ig.
		Use it how you like lmao.
		'''

		self._type = _type
		
		if size is None:
			if None not in (x,) and (y, z, w) == (None, None, None): size = 1
			elif None not in (x, y) and (z, w) == (None, None): size = 2
			elif None not in (x, y, z) and w == None: size = 3
			elif None not in (x, y, z, w): size = 4
			else: size = 0
		self.size = size

		self.x = self._type(x) if x is not None else 0
		self.y = self._type(y) if y is not None else 0
		self.z = self._type(z) if z is not None else 0
		self.w = self._type(w) if w is not None else 1


	def _length(v) -> float:
		return (v.x**2 + v.y**2 + v.z**2) ** 0.5
	length = property(
		fget=_length
	)

	def _length_sqr(v) -> float:
		return (v.x**2 + v.y**2 + v.z**2)
	length_sqr = property(
		fget=_length_sqr
	)

	def normalise(v) -> vec:
		l = v.length
		if l != 0:
			return vec(*(i/l for i in v.vec))
		else:
			return vec(size=v.size)

	def _get_vec(v) -> list:
		match v.size:
			case 1:
				return (v.x,)
			case 2:
				return (v.x, v.y)
			case 3:
				return (v.x, v.y, v.z)
			case _:
				return (v.x, v.y, v.z, v.w)
	def _set_vec(v, val) -> None:
		self.x = val[0] if len(val) >= 1 else self.x
		self.y = val[1] if len(val) >= 1 else self.y
		self.z = val[2] if len(val) >= 1 else self.z
		self.w = val[3] if len(val) >= 1 else self.w
	vec = property(
		fget=_get_vec,
		fset=_set_vec
	) # This property returns the values of the vec in tuple form

	def to_matrix(v, size=None):
		'''
		Converts this vector (or a provided one if treated as static ig) into a mat1x{v.size}
		'''
		if size is None:
			return mat([list(v.vec)])
		else:
			t = None
			match size:
				case 1:
					t = [v.x,]
				case 2:
					t = [v.x, v.y]
				case 3:
					t = [v.x, v.y, v.z]
				case _:
					t = [v.x, v.y, v.z, v.w]
			return mat([t])


	@staticmethod
	def dot(a:vec, b:vec) -> float:
		return a.x * b.x + a.y * b.y + a.z * b.z

	@staticmethod
	def cross(a:vec, b:vec) -> vec:
		if (a.size, b.size) == (3, 3):
			return vec(
				a.y*b.z - a.z*b.y,
				a.z*b.x - a.x*b.z,
				a.x*b.y - a.y*b.x,
				a.w,
				3, float
			)
		return None

	@staticmethod
	def dist(a:vec, b:vec) -> float:
		return (a - b).length

	@staticmethod
	def dist_sqr(a:vec, b:vec) -> float:
		return (a - b).length_sqr

	@staticmethod
	def up():
		return vec(0, 1, 0)
	@staticmethod
	def down():
		return vec(0, -1, 0)
	@staticmethod
	def left():
		return vec(-1, 0, 0)
	@staticmethod
	def right():
		return vec(1, 0, 0)
	@staticmethod
	def forward():
		return vec(0, 0, 1)
	@staticmethod
	def backward():
		return vec(0, 0, -1)

	def __trunc__(v) -> vec:
		return vec(math.trunc(v.x), math.trunc(v.y), math.trunc(v.z), math.trunc(v.w), v.size, int)

	def __ceil__(v) -> vec:
		return vec(math.ceil(v.x), math.ceil(v.y), math.ceil(v.z), math.ceil(v.w), v.size, int)

	def __floor__(v) -> vec:
		return vec(math.floor(v.x), math.floor(v.y), math.floor(v.z), math.floor(v.w), v.size, int)

	def __round__(v, n) -> vec:
		return vec(math.round(v.x, n), math.round(v.y, n), math.round(v.z, n), math.round(v.w, n), v.size, float if n != 0 else int)

	def __abs__(v) -> vec:
		return vec(abs(v.x), abs(v.y), abs(v.z), abs(v.w), v.size, v._type)

	def __neg__(v) -> vec:
		return vec(-v.x, -v.y, -v.z, -v.w, v.size, v._type)

	def __add__(a, b:vec) -> vec:
		return vec(a.x + b.x, a.y + b.y, a.z + b.z, a.w + b.w, max(a.size, b.size))

	def __sub__(a, b:vec) -> vec:
		return vec(a.x - b.x, a.y - b.y, a.z - b.z, a.w - b.w, max(a.size, b.size))

	def __mul__(a, b:float) -> vec:
		return vec(a.x * b, a.y * b, a.z * b, a.w * b, a.size)

	def __floordiv__(a, b:float) -> vec:
		return vec(a.x // b, a.y // b, a.z // b, a.w // b, a.size, int)

	def __truediv__(a, b:float) -> vec:
		return vec(a.x / b, a.y / b, a.z / b, a.w / b, a.size)

	def __mod__(a, b:float) -> vec:
		return vec(a.x % b, a.y % b, a.z % b, a.w % b, a.size)

	def __divmod__(a, b:float) -> tuple[vec, vec]:
		return (a // b, a % b)
	
	def __pow__(a, b:float) -> vec:
		return vec(a.x ** b, a.y ** b, a.z ** b, a.w ** b, a.size)

	def __str__(v) -> str:
		match v.size:
			case 2:
				return f"vec2> x: {v.x}, y: {v.y}"
			case 3:
				return f"vec3> x: {v.x}, y: {v.y}, z: {v.z}"
			case _:
				return f"vec4> x: {v.x}, y: {v.y}, z: {v.z}, w: {v.w}"

	def __repr__(v) -> str:
		return f"vec({v.x}, {v.y}, {v.z}, {v.w}, {v._type})"

	def __eq__(a, b: vec) -> bool:
		return a.x == b.x and a.y == b.y and a.z == b.z and a.w == b.y

	def __ne__(a, b: vec) -> bool:
		return not (a == b)


class mat:
	'''
	Matrix class with varying sizes.

	Contains all the math for matrix multiplication and interaction with vectors. 
	'''

	def __init__(self, data=None, w=None, h=None):
		'''
		Creates a new matrix
		If 'w' or 'h' are undefined, the matrix will be sized in that respective dimension based
		on the values in 'data'.
		If 'data' is not provided, then a blank 'w'x'h' matrix will be created.

		A value for 'data' must be provided if either 'w' or 'h' are left undefined.
		The matrix will be padded with zeros if 'data' is incomplete based on 'w' or 'h' values.

		'data' is a two-dimensional list, horizontal then vertical.

		Individual matrix values can be retrieved using 'mat[x][y]'.
		'''

		self.matrix = None
		self.w = w
		self.h = h

		if data is None and None not in (w, h):
			## Generate empty matrix
			self.w = int(w)
			self.h = int(h)
			self.matrix = [[0 for i in range(h)] for j in range(w)]

		elif data is not None:
			
			self.matrix = []
			self.w = len(data) if w is None else int(w)
			self.h = max([len(data[x]) for x in range(self.w)]) if h is None else int(h)

			for x in range(self.w):
				column = []
				for y in range(self.h):
					if x < len(data) and y < len(data[x]):
						column.append(data[x][y])
					else:
						column.append(0)
				self.matrix.append(column)

		else:
			raise AttributeError("Either the size or the data of the matrix must be provided.")

		self.size = (self.w, self.h)


	def to_vec(m):
		'''
		Converts a mat1x4 into a vec4.
		'''
		if m.h <= 4 and m.w == 1:
			return vec(*tuple(m[0]), size=m.h)


	@staticmethod
	def identity(d:int) -> mat:
		return mat([[1 if x==y else 0 for y in range(d)] for x in range(d)])

	@staticmethod
	def scale(s:float|int|vec) -> mat:

		match s:
			case float() | int():
				mscale = mat.identity(4) * s
				mscale[3][3] = 1
				return mscale
			case vec():
				mscale = mat.identity(4)
				mscale[0][0] = s.x
				mscale[1][1] = s.y
				mscale[2][2] = s.z
				return mscale

	@staticmethod
	def translate(t:vec) -> mat:
		if t.size == 3:
			mtrans = mat.identity(4)
			mtrans.matrix[3] = list(t.vec) + [1]
			return mtrans
		else:
			raise AttributeError("Vector to translate by must have 3 dimensions.")

	@staticmethod
	def rotate_x(theta:float) -> mat:
		mrot = mat.identity(4)
		mrot[1][1] = trig.cos(theta)
		mrot[2][1] = -trig.sin(theta)
		mrot[1][2] = trig.sin(theta)
		mrot[2][2] = trig.cos(theta)
		return mrot

	@staticmethod
	def rotate_y(theta:float) -> mat:
		mrot = mat.identity(4)
		mrot[0][0] = trig.cos(theta)
		mrot[2][0] = trig.sin(theta)
		mrot[0][2] = -trig.sin(theta)
		mrot[2][2] = trig.cos(theta)
		return mrot

	@staticmethod
	def rotate_z(theta:float) -> mat:
		mrot = mat.identity(4)
		mrot[0][0] = trig.cos(theta)
		mrot[1][0] = -trig.sin(theta)
		mrot[0][1] = trig.sin(theta)
		mrot[1][1] = trig.cos(theta)
		return mrot
	
	@staticmethod
	def rotate_axis(theta:float, axis:vec) -> vec:
		cos0 = trig.cos(theta)
		sin0 = trig.sin(theta)

		mrot = mat([
			[cos0 + axis.x*axis.x*(1-cos0), axis.y*axis.x*(1-cos0) + axis.z*sin0, axis.z*axis.x*(1-cos0) - axis.y*sin0, 0],
			[axis.x*axis.y*(1-cos0) - axis.z*sin0, cos0 + axis.y*axis.y*(1-cos0), axis.z*axis.y*(1-cos0) - axis.x*sin0, 0],
			[axis.x*axis.z*(1-cos0) + axis.y*sin0, axis.y*axis.z*(1-cos0) - axis.x*sin0, cos0 + axis.z*axis.z*(1-cos0), 0],
			[0, 0, 0, 1]
		])
		return mrot

	@staticmethod
	def perspective_projection(fov, aspect, z_near, z_far):

		f = trig.tan(fov / 2)

		proj = mat(None, 4, 4)
		proj[0][0] = 1 / (f * aspect)
		proj[1][1] = 1 / f
		proj[2][2] = z_far / (z_far - z_near)
		proj[3][2] = (-z_near * z_far) / (z_far - z_near)
		proj[2][3] = 1

		return proj

	@staticmethod
	def look_at(position, target, up):

		forward = (position - target).normalise()
		right = vec.cross(up, forward).normalise()
		up = vec.cross(forward, right)

		p_m = mat.identity(4)
		p_m.matrix[3] = list(position.vec) + [1]

		return mat([
			[right.x, up.x, forward.x, 0],
			[right.y, up.y, forward.y, 0],
			[right.z, up.z, forward.z, 0],
			[0, 0, 0, 1]]) * p_m

	def __getitem__(self, index):
		return self.matrix[index]

	def __add__(a, b:mat) -> mat:

		if a.size == b.size:
			return mat([[a[x][y] + b[x][y] for y in range(a.h)] for x in range(a.w)], *a.size)
		return None

	def __sub__(a, b:mat) -> mat:

		if a.size == b.size:
			return mat([[a[x][y] - b[x][y] for y in range(a.h)] for x in range(a.w)], *a.size)
		return None

	def __mul__(a, b:float|int|mat|vec) -> mat:

		match b:
			case float() | int():
				return mat([[a[x][y] * b for y in range(a.h)] for x in range(a.w)], *a.size)

			case mat():
				if a.w == b.h:
					#return mat([[sum([a[i][y] * b[x][i] for i in range(a.w)]) for y in range(a.h)] for x in range(b.w)], b.w, a.h)

					new = mat(None, b.w, a.h)
					for x in range(b.w):
						for y in range(b.h):
							t = 0
							for i in range(a.w):
								t += a[i][y] * b[x][i]
							new[x][y] = t
					return new

				else:
					raise ValueError("a * b> # of columns of 'a' must equal # of rows of 'b'.")

			case vec():
				return (a * b.to_matrix(a.w)).to_vec()

	def __str__(m) -> str:
		title = f"mat{m.w}x{m.h}> "
		longest = max([len(str(v)) for v in flatten(m.matrix)])
		text = "\n".join([f"{' '*len(title) if y != 0 else title}[{' '.join([str(m.matrix[x][y]).ljust(longest) for x in range(m.w)])}]" for y in range(m.h)])
		return text

	def __repr__(m) -> str:
		return f"mat({m.matrix}, {m.w}, {m.h})"


