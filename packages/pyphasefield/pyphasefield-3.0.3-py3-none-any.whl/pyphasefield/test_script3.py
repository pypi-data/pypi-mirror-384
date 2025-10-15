import sys
sys.path.insert(0,"..")
import pyphasefield as ppf
import pyphasefield.Engines as engines
import time
import numpy as np

tdbc = ppf.TDBContainer("tests/Ni-Cu-Al_Ideal.tdb", ["FCC_A1", "LIQUID"], ["AL", "CU", "NI"])

sim = engines.NCGPU_new(dimensions=[400, 400])

#initialize non-array parameters
sim.set_framework("GPU_PARALLEL") #"CPU_SERIAL", "GPU_SERIAL"
sim.set_dx(0.0000046)
sim.set_time_step_counter(0)
sim.set_temperature_type("ISOTHERMAL") #None, "ISOTHERMAL", "LINEAR_GRADIENT", "XDMF_FILE"
sim.set_temperature_initial_T(1574.)
sim.set_temperature_dTdx(None)
sim.set_temperature_dTdy(None)
sim.set_temperature_dTdz(None)
sim.set_temperature_dTdt(None)
sim.set_temperature_path(None)
sim.set_temperature_units("K")
sim.set_tdb_container(tdbc)
sim.set_save_path("data/ncgpu_test2")
sim.set_autosave_flag(False)
sim.set_autosave_save_images_flag(False)
sim.set_autosave_rate(100000)
sim.set_boundary_conditions("PERIODIC")
sim._ghost_rows = 32

data = {
    "d_ratio":1.1,
    "sim_type":"seed",
    "initial_concentration_array":[0.0001, 0.3937],
    "melt_angle":0.,
    "seed_angle":np.pi/4
}
sim.set_user_data(data)

#initialize simulation arrays, all parameter changes should be BEFORE this point!
sim.initialize_fields_and_imported_data()

#change array data here, for custom simulations


#run simulation
sim.simulate(1)
t0 = time.time()
sim.simulate(19999)
t1 = time.time()
print(t1-t0)
sim.save_simulation()
sim.finish_simulation()