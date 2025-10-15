import numpy as np
import abracatabra


def test_readme_blit_example():
    blit = True
    window = abracatabra.TabbedPlotWindow(autohide_tabs=True)
    fig = window.add_figure_tab("robot arm animation", include_toolbar=False, blit=blit)
    ax = fig.add_subplot()

    # background elements
    fig.tight_layout()
    ax.set_aspect("equal", "box")
    length = 1.0
    lim = 1.25 * length
    ax.axis((-lim, lim, -lim, lim))
    (baseline,) = ax.plot([0, length], [0, 0], "k--")

    # draw and save background for fast rendering
    fig.canvas.draw()
    background = fig.canvas.copy_from_bbox(ax.bbox)  # type: ignore

    # moving elements
    def get_arm_endpoints(theta):
        x = np.array([0, length * np.cos(theta)])
        y = np.array([0, length * np.sin(theta)])
        return x, y

    theta_hist = np.sin(np.linspace(0, 10, 501))
    x, y = get_arm_endpoints(theta_hist[0])
    (arm_line,) = ax.plot(x, y, linewidth=5, color="blue")

    # animate
    for theta in theta_hist:
        x, y = get_arm_endpoints(theta)
        arm_line.set_xdata(x)
        arm_line.set_ydata(y)

        if blit:
            fig.canvas.restore_region(background)  # type: ignore
            ax.draw_artist(arm_line)

        abracatabra.update_all_windows(0.01)

    # keep window open
    abracatabra.abracatabra(block=False)
    assert True


if __name__ == "__main__":
    test_readme_blit_example()
