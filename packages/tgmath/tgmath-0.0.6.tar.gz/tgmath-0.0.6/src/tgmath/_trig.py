import math

RADIANS = 0
DEGREES = 1

ANGLE_MODE = DEGREES
'''
Setting the angle mode will change the returned values from the functions.
'''

DEG2RAD = 3.14159 / 180
RAD2DEG = 180 / 3.14159


def _fnc(func, v, *args):
	if type(v) is list:
		return [func(vi, *args) for vi in v]
	else:
		return func(v, *args)


def degrees(r):
	'''
	Converts 'r' from radians to degrees.
	Equivilant to 'r * tmath.RAD2DEG'
	'''
	return _fnc(lambda r: r * RAD2DEG, r)
def radians(d):
	'''
	Converts 'd' from degrees to radians.
	Equivilant to 'd * tmath.DEG2RAD'
	'''
	return _fnc(lambda d: d * DEG2RAD, d)

def set_angle_mode(angle_mode):
	'''
	Sets the angle mode to dictate the return value of other trig functions.
	Options are 'tmath.RADIANS' or 'tmath.DEGREES'

	Equivilant to setting it directly: 'tmath.ANGLE_MODE = angle_mode'
	'''
	global ANGLE_MODE
	ANGLE_MODE = angle_mode


def sin(a):
	if ANGLE_MODE: a = radians(a)
	return _fnc(math.sin, a)

def cos(a):
	if ANGLE_MODE: a = radians(a)
	return _fnc(math.cos, a)

def tan(a):
	if ANGLE_MODE: a = radians(a)
	return _fnc(math.tan, a)

def asin(v):
	a = _fnc(math.asin, v)
	if ANGLE_MODE: a = degrees(a)
	return a

def acos(v):
	a = _fnc(math.acos, v)
	if ANGLE_MODE: a = degrees(a)
	return a

def atan(v):
	a = _fnc(math.atan, v)
	if ANGLE_MODE: a = degrees(a)
	return a

def atan2(y, x):
	if type(y) == type(x) == list and len(x) == len(y):
		a = [math.atan2(y[i], x[i]) for i in range(len(x))]
	else:
		a = math.atan2(y, x)
	if ANGLE_MODE: a = degrees(a)
	return a