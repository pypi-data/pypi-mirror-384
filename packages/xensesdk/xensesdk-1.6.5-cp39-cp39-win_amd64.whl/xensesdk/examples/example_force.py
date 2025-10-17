import sys
from xensesdk import ExampleView
from xensesdk import Sensor


def main():
    sensor_0 = Sensor.create('OG000232')
    View = ExampleView(sensor_0)
    View2d = View.create2d(Sensor.OutputType.Rectify, Sensor.OutputType.Marker2D, Sensor.OutputType.Depth)

    def callback():
        force, res_force, mesh_init, src, diff, depth = sensor_0.selectSensorInfo(
            Sensor.OutputType.Force, 
            Sensor.OutputType.ForceResultant,
            Sensor.OutputType.Mesh3DInit,
            Sensor.OutputType.Rectify, 
            Sensor.OutputType.Difference, 
            Sensor.OutputType.Depth,
        )
        marker_img = sensor_0.drawMarkerMove(diff)
        View2d.setData(Sensor.OutputType.Rectify, src)
        View2d.setData(Sensor.OutputType.Marker2D, marker_img)
        View2d.setData(Sensor.OutputType.Depth, depth)
        View.setForceFlow(force, res_force, mesh_init)
        View.setDepth(depth)

    View.setCallback(callback)
    View.show()
    sensor_0.release()
    sys.exit()

if __name__ == '__main__':
    main()