import sys
sys.path.insert(0,"..")
import pyphasefield.Engines as engines
import time
from numba import cuda

print(cuda.current_context().get_memory_info())

dim = [16000, 16000]
steps = 200

for i in [1, 2, 4, 8, 16, 32, 64, 128]:
    sim = engines.Diffusion(dimensions=dim)

    #initialize non-array parameters
    sim.set_framework("GPU_PARALLEL") #"CPU_SERIAL", "GPU_SERIAL" (GPU_SERIAL requires numba)
    sim.set_dx(1.)
    sim.set_dt(0.1)
    sim.set_save_path("data/diffusion_test")
    sim.set_autosave_flag(False)
    sim.set_autosave_save_images_flag(False)
    sim.set_autosave_rate(20000)
    sim.set_boundary_conditions("PERIODIC")
    sim._ghost_rows = i

    data = {
        "D":1.
    }
    sim.set_user_data(data)

    #initialize simulation arrays, all parameter changes should be BEFORE this point!
    sim.initialize_fields_and_imported_data()

    #change array data here, for custom simulations
    """
    sim.fields[0].data[:] = 1.
    length = sim.dimensions[0]
    width = sim.dimensions[1]
    sim.fields[0].data[length // 4:3 * length // 4, width // 4:3 * width // 4] = 0.
    """


    #initial conditions
    sim.save_simulation()

    #run simulation
    sim.simulate(1)
    t0 = time.time()
    sim.simulate(steps-1)
    t1 = time.time()
    print(str(t1-t0)+", ")

    #final conditions
    sim.save_simulation()
    sim.finish_simulation()

if(sim._MPI_rank == 0):
    sim = engines.Diffusion(dimensions=dim)

    #initialize non-array parameters
    sim.set_framework("GPU_SERIAL") #"CPU_SERIAL", "GPU_SERIAL" (GPU_SERIAL requires numba)
    sim.set_dx(1.)
    sim.set_dt(0.1)
    sim.set_save_path("data/diffusion_test")
    sim.set_autosave_flag(False)
    sim.set_autosave_save_images_flag(False)
    sim.set_autosave_rate(20000)
    sim.set_boundary_conditions("PERIODIC")
    sim._ghost_rows = i

    data = {
        "D":1.
    }
    sim.set_user_data(data)

    #initialize simulation arrays, all parameter changes should be BEFORE this point!
    sim.initialize_fields_and_imported_data()

    #change array data here, for custom simulations
    """
    sim.fields[0].data[:] = 1.
    length = sim.dimensions[0]
    width = sim.dimensions[1]
    sim.fields[0].data[length // 4:3 * length // 4, width // 4:3 * width // 4] = 0.
    """


    #initial conditions
    sim.save_simulation()

    #run simulation
    sim.simulate(1)
    t0 = time.time()
    sim.simulate(steps-1)
    t1 = time.time()
    print("serial: "+str(t1-t0))

    #final conditions
    sim.save_simulation()
    sim.finish_simulation()