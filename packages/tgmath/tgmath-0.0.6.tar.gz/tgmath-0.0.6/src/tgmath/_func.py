import math


def _fnc(func, v, *args):
	if type(v) is list:
		return [func(vi, *args) for vi in v]
	else:
		return func(v, *args)

def floor(v, cast=int):
	'''
	Returns the largest integer smaller than 'v', cast into the provided type.
	'''
	return cast(_fnc(math.floor, v))

def ceil(v, cast=int):
	'''
	Returns the smallest integer larger than 'v', cast into the provided type.
	'''
	return cast(_fnc(math.ceil, v))


def clamp(v, _min, _max):
	'''
	Clamps 'v' to between the range of '_min' and '_max'
	'''
	return _fnc(lambda vi: min(max(vi, _min), _max), v)


def mean(v: list):
	'''
	Returns the mean of sequence 'v'
	'''
	return sum(v) / len(v)


def std_dev(v: list):
	'''
	Returns the standard deviation of sequence 'v'
	'''
	vmean = mean(v)
	return math.sqrt(sum([(vi - vmean)**2 for vi in v]) / (len(v) - 1))
standard_deviation = std_dev

def std_err(v: list):
	'''
	Returns the standard error of sequence 'v'
	'''
	return std_dev(v) / math.sqrt(len(v))
standard_error = std_err




def _round(v, places):
	'''
	Rounds v to a number of decimal places
	'''
	return _fnc(round, v, places)

def sig_figs(v, figures):
	'''
	Rounds v to a number of significant figures
	'''
	if type(v) is not list:

		sv0 = str(v) # initial string value

		## Check if value is very small or very large, and store the power
		if "e" in sv0:
			log10 = sv0[sv0.index("e")+1:]
			sv0 = sv0[:sv0.index("e")]
		else:
			log10 = "0" ## If not, power is 0
		
		in_decimal = False
		## Find the first non-0 digit
		digit = ""
		index = -1
		while digit in "-0.":
			index += 1
			digit = sv0[index]
			if digit == ".": in_decimal = True
		## Index is now the first non-0 digit

		## Advance index by {figures}
		advance = 0
		while advance < figures:
			digit = sv0[index]
			if digit != ".": advance += 1 ## Don't increment advance if character is .
			else: in_decimal = True
			index += 1

			if index == len(sv0):
				# Check if # of figures is more than the value has
				digit = 0
				break
			else: digit = sv0[index]

		if in_decimal:
			sv1 = str(round(float(sv0), index - sv0.index(".") - 1))
		else:
			sv1 = str(round(float(sv0), -(len(sv0) - index)))

		v1 = float(f"{sv1}e{log10}")
		if not in_decimal and log10 == "0": v1 = int(v1)
		return v1