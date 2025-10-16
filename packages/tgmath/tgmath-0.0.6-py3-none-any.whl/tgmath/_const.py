
from tgmath._func import *

## Mathematical constants
pi = 3.141592653589793
tau = pi * 2
e = 2.718281828459045


## Physical constants
class PHYSICAL_CONSTANTS:

	CONSTANTS = [
		(299792458, "c", "speed_of_light", 3),
		(6.62607015e-34, "h", "plank_constant", 4),
		(1.054571817e-34, "hbar", "reduced_plank_constant", 4),
		(1.380649e-23, "k_B", "boltzmann_constant", 4),
		(6.6743015e-11, "G", "gravitational_constant", 4),
		(5.670374419e-8, "sigma", "stefan_boltzmann_constant", 4),
		(5.878925757e10, "b", "wien_displacement_law_constant", 4),
		(3.002916077e-3, "b_entropy", "wien_entropy_displacement_law_constant", 4),
		(1.602176634e-19, "e", "elementary_charge", 3),
		(7.748091729e-5, "G_0", "conductance_quantum", 4),
		(2.067833848e-15, "Phi_0", "magnetic_flux_quantum", 4),
		(0.007297352564311, "alpha", "fine_structure_constant", 4),
		(1.2566370612720e-6, "mu_0", "vacuum_magnetic_permeability", 4),
		(8.854187818814e-12, "epsilon_0", "vacuum_electric_permittivity", 4),
		(9.109383713928e-31, "m_e", "electron_mass", 3),
		(1.88353162742e-28, "m_mu", "muon_mass", 3),
		(3.1675421e-27, "m_tau", "tau_mass", 3),
		(1.6726219259552e-27, "m_p", "proton_mass", 3),
		(1.6749275005685e-27, "m_n", "neutron_mass", 3),
		(2.0023193043609236, "g_e", "electron_g_factor", 6),
		(2.0023318412382, "g_mu", "muon_g_factor", 6),
		(5.585694689316, "g_p", "proton_g_factor", 6),
		(10973731.56815712, "R_inf", "rydberg_constant", 4),
		(6.02214076e23, "N_A", "avogadro_constant", 4),
		(8.31446261815324, "R", "molar_gas_constant", 4),
		(1.6605390689252e-27, "m_u", " atomic_mas_constant", 4)
	]

	def __init__(self):
		...


	def __getattr__(self, value):
		constant_details = self.get_constant_details(value)
		if constant_details is not None:
			return sig_figs(constant_details[0], constant_details[3])
		else: return self.__dict__[value]
	
	def get_constant_value(self, symbol_or_name):
		for (value, _symbol, _name, sig_figs) in self.CONSTANTS:
			if symbol_or_name == _name or symbol_or_name == _symbol:
				return value

	def get_constant_details(self, symbol_or_name):
		for (value, _symbol, _name, sig_figs) in self.CONSTANTS:
			if symbol_or_name == _name or symbol_or_name == _symbol:
				return (value, _symbol, _name, sig_figs)



	def get_constant_names(self):
		return [constant[2] for constant in self.CONSTANTS]
	def get_constant_symbols(self):
		return [constant[1] for constant in self.CONSTANTS]



physical_constants = phys = PHYSICAL_CONSTANTS()