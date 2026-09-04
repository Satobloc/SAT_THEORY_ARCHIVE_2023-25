
def save_outputs(univ, metrics, file_id):
    unique_name = f"{univ['id']}_{uuid.uuid4().hex[:6]}"
    path_base = os.path.join(SESSION_ID, unique_name)

    # 1. Create the grid (1 row, 2 columns)
    fig, axs = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f"Manifold {univ['id']} Diagnostic", fontsize=14, fontweight='bold')
    
    # 2. Chart 1: Axis Rates - Target axs (the first box)
    # CHANGE '.var' BACK TO '.bar' HERE
    if univ['h_rates']:
        axs.bar(univ['h_rates'].keys(), univ['h_rates'].values(), color='skyblue')
    axs.set_title("Linear Strains (h*)")
    
    # 3. Chart 2: Advanced Metrics - Target axs[1] (the second box)
    # CHANGE '.var' BACK TO '.bar' HERE
    axs[1].bar(metrics.keys(), metrics.values(), color='salmon')
    axs[1].set_title("Gemini Physics Indices")
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(f"{path_base}_dashboard.png")
    plt.close()

    # 4. PyVista 3D Morphology (Remains the same)
    sphere = pv.Sphere(radius=1.0, phi_resolution=30, theta_resolution=30)
    # Defaulting missing axes to 0 to prevent deformation errors
    x_def = univ['h_rates'].get('x', 0) * 0.5
    y_def = univ['h_rates'].get('y', 0) * 0.5
    z_def = univ['h_rates'].get('z', 0) * 0.5
    
    deformed = sphere.copy()
    deformed.points[:, 0] *= (1.0 + x_def)
    deformed.points[:, 1] *= (1.0 + y_def)
    deformed.points[:, 2] *= (1.0 + z_def)
    
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(deformed, color='cyan', scalars=np.arange(deformed.n_points), cmap='magma')
    plotter.add_text(f"ID: {univ['id']}\nStress: {metrics['Stress']}", font_size=10)
    plotter.screenshot(f"{path_base}_morphology.png")

    print(f"Saved results for Universe {univ['id']} to folder: {SESSION_ID}")