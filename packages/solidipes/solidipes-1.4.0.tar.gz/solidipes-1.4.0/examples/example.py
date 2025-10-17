import os

import solidipes as sp
from solidipes.utils import viewer_backends

os.chdir(os.path.dirname(__file__))
print(f"Using backend {viewer_backends.current_backend}")

# Text
text = sp.load_file("assets/text.md")
text.view()

# Image
image = sp.load_file("assets/solidipes.jpg")
image.view()

# Table
table = sp.load_file("assets/table.xlsx")
print(table.data_info)
table.view()

# Load mesh
mesh = sp.load_file("assets/plate_hole.vtu")
print(mesh.data_info)

# View bare mesh
mesh.view(add_kwargs={"show_edges": True})

# View warped mesh with colored data
warped_mesh = mesh.get_warped("displacement", factor=4e9)
stress_xx = mesh.get_cell_data("stress")[:, 0]
warped_mesh.set_cell_values(stress_xx)
viewer = warped_mesh.view()
viewer.save("example.png")

# Manual plotting
viewer = sp.viewers.PyvistaPlotter()
viewer.add_mesh(warped_mesh, show_edges=True)
viewer.add_points(mesh, color="red", point_size=20)
viewer.show()
