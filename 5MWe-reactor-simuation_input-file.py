import onix
import openmc
from onix import utils
from onix.couple import Couple_openmc
from onix.sequence import Sequence
from onix.system import System
from onix.salameche import burn
import onix.data as d


natU_mat = openmc.Material()
natU_mat.temperature = 800
natU_mat.set_density('g/cc', density = 17.98)
natU_mat.add_nuclide('U234', d.NATURAL_ABUNDANCE['U234'])
natU_mat.add_nuclide('U235', d.NATURAL_ABUNDANCE['U235'])
natU_mat.add_nuclide('U238', d.NATURAL_ABUNDANCE['U238'])

clad_mat = openmc.Material()
clad_mat.temperature = 700
Mg_frac = 98.95
Al_frac = 1
Be_frac = 0.05
clad_mat.add_nuclide('Mg24',0.79*Mg_frac)
clad_mat.add_nuclide('Mg25',0.10*Mg_frac)
clad_mat.add_nuclide('Mg26',0.11*Mg_frac)
clad_mat.add_nuclide('Al27',1*Al_frac)
clad_mat.add_nuclide('Be9',1*Be_frac)
clad_mat.set_density('g/cc', density = 1.65)

mod_mat = openmc.Material()
mod_mat.temperature = 650
mod_mat.set_density('g/cc', density = 1.628)
mod_mat.add_nuclide('C12',0.989)
mod_mat.add_nuclide('C13',0.011)
mod_mat.add_s_alpha_beta('c_Graphite')

sample_mat = openmc.Material()
sample_mat.temperature = 650
sample_mat.set_density('g/cc', density = 1.628)
sample_mat.add_nuclide('C12',0.989)
sample_mat.add_nuclide('C13',0.011)
sample_mat.add_s_alpha_beta('c_Graphite')

cool_mat = openmc.Material()
cool_mat.temperature = 650
cool_mat.set_density('g/cc', density = 1.628)
C_frac = 33.33
O_frac = 66.66
cool_mat.add_nuclide('C12',C_frac*0.989)
cool_mat.add_nuclide('C13',C_frac*0.011)
cool_mat.add_nuclide('O16',O_frac*0.9976)
# Instantiate a Materials collection
materials_file = openmc.Materials([natU_mat, clad_mat, cool_mat, mod_mat, sample_mat])
#materials_file.cross_sections = '/tigress/jdtdl/openmc/mcnp_endfb70/cross_sections.xml'
materials_file.cross_sections = '/home/julien/cross-sections/lib80x_hdf5/cross_sections.xml'

# Export to "materials.xml"
materials_file.export_to_xml()


# Create cylinders for the fuel and clad
fuel_outer_radius = openmc.ZCylinder(x0=0.0, y0=0.0, R=1.45)
clad_outer_radius = openmc.ZCylinder(x0=0.0, y0=0.0, R=1.50)
coolant_outer_radius = openmc.ZCylinder(x0=0.0, y0=0.0, R=3.25)

#Create cylinder of the sample
sample_cylinder = openmc.ZCylinder(x0=0.0, y0=1.55, R=0.05)

# Create boundary planes to surround the geometry
min_x = openmc.XPlane(x0=-10, boundary_type='reflective')
max_x = openmc.XPlane(x0=+10, boundary_type='reflective')
min_y = openmc.YPlane(y0=-10, boundary_type='reflective')
max_y = openmc.YPlane(y0=+10, boundary_type='reflective')
min_z = openmc.ZPlane(z0=-0.5, boundary_type='reflective')
max_z = openmc.ZPlane(z0=+0.5, boundary_type='reflective')

# Create a Universe to encapsulate the fuel pin
pin_cell_universe = openmc.Universe(name='Fuel Pin')

# Create fuel1 Cell
fuel_cell = openmc.Cell(name='fuel')
fuel_cell.fill = natU_mat
fuel_cell.region = -fuel_outer_radius
pin_cell_universe.add_cell(fuel_cell)

# Create a clad Cell for 1
clad_cell = openmc.Cell(name='Clad')
clad_cell.fill = clad_mat
clad_cell.region = +fuel_outer_radius & -clad_outer_radius
pin_cell_universe.add_cell(clad_cell)

# Create a coolant Cell for 1
cool_cell = openmc.Cell(name='Cool')
cool_cell.fill = cool_mat
cool_cell.region = +clad_outer_radius & +sample_cylinder & - coolant_outer_radius
pin_cell_universe.add_cell(cool_cell)

# Create a moderator Cell for 1
mod_cell = openmc.Cell(name='Mod')
mod_cell.fill = mod_mat
mod_cell.region = +coolant_outer_radius
pin_cell_universe.add_cell(mod_cell)

# Create sample cell
sample_cell = openmc.Cell(name='Sample')
sample_cell.fill = clad_mat
sample_cell.region = -sample_cylinder
pin_cell_universe.add_cell(sample_cell)

# Create root Cell
root_cell = openmc.Cell(name='root cell')
root_cell.fill = pin_cell_universe
root_cell.region = +min_x & -max_x & +min_y & -max_y & +min_z & -max_z

# Create root Universe
root_universe = openmc.Universe(universe_id=0, name='root universe')
root_universe.add_cell(root_cell)

# Create Geometry and set root Universe
openmc_geometry = openmc.Geometry(root_universe)

# Export to "materials.xml"
materials_file.export_to_xml()
# Export to "geometry.xml"
openmc_geometry.export_to_xml()

# OpenMC simulation parameters
batches = 100
inactive = 10
particles = 10000

# Instantiate a Settings object
settings_file = openmc.Settings()
settings_file.batches = batches
settings_file.inactive = inactive
settings_file.particles = particles

# Create an initial uniform spatial source distribution over fissionable zones
#bounds = [-0.65635, -0.65635, -0.65635, 0.65635, 0.65635, 0.65635]
#uniform_dist = openmc.stats.Box(bounds[:3], bounds[3:], only_fissionable=True)
point_dist = openmc.stats.Point(xyz=(0.0, 0.0, 0.0))
settings_file.source = openmc.source.Source(space=point_dist)

# Export to "settings.xml"
settings_file.export_to_xml()


macrostep_vector = [0.0087, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
macrostep_unit = 'MWd/kg' # This indicates the unit of the sequence vector steps (can be in seconds, days, month, years or MWd/kg)
norma_vector = [0.15]*len(macrostep_vector)
norma_unit = 'power' # This indicates the unit of the normalization factor
microstep_vector = [3]*len(macrostep_vector) # This is a vector of the number of substep for each sequence step

sequence1 = Sequence(1) # Instantation of a sequence object with id number = 1
sequence1.set_macrostep(macrostep_vector, macrostep_unit)# We set the sequence_vector and sequence unit for this sequence object
sequence1.set_norma(norma_vector, norma_unit) # We set the normalization vector and normalization unit for this sequence object
sequence1.microstep_vector = microstep_vector # We set the substep vector for this sequence object
sequence1.flux_approximation = 'iv'

couple = Couple_openmc()

couple.set_bounding_box([-10.16, -10.16, -0.5], [10.16, 10.16, 0.5])

couple.openmc_bin_path = '/home/julien/anaconda3/envs/sphinx_test3/bin/openmc'
couple.select_bucells([fuel_cell, sample_cell])

couple.import_openmc(root_cell)

vol_dict = {'fuel': 6.6051, 'Sample':0.007853 ,'total volume':400}
couple.set_vol(vol_dict)

couple.set_sequence(sequence1)

couple.burn()