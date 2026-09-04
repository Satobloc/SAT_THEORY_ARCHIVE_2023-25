import pyvista as pv

print("Attempting to render test sphere...")
plotter = pv.Plotter()
plotter.set_background("black")
mesh = pv.Sphere(radius=10)
plotter.add_mesh(mesh, color='red')
print("Render command sent. If a window appears, the display is working.")
plotter.show()