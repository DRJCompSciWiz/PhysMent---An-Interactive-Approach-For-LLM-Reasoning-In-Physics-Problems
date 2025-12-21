import mujoco as mj
import mujoco.viewer
import time

for i in range(1, 151):
    model = mj.MjModel.from_xml_path(f"C:\\Users\\inbox\\OneDrive\\Desktop\\Algoverse-updated-pipeline\\Scenes\\Scene{i}\\Scene{i}.1.xml") # type: ignore #type : ignore
    data = mj.MjData(model) # type: ignore

    with mujoco.viewer.launch(model, data) as viewer: # type: ignore
        start_time = time.time()
        while viewer.is_running() and (time.time() - start_time < 20):
            time.sleep(0.05)
            mj.mj_step(model, data) # type: ignore