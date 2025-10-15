import numpy as np
import abracatabra as tabby
import matplotlib.pyplot as plt


def test_tabbed_plot_window():
    window1 = tabby.TabbedPlotWindow(3)

    # data
    t = np.arange(0, 10, 0.1)
    ysin = np.sin(t)
    ycos = np.cos(t)
    data = np.array([t, ysin]).T


    f = window1.add_figure_tab("sin", blit=True)
    f.clear()
    ax = f.add_subplot()
    line1, = ax.plot(t, ysin, 'b+')
    line2, = ax.plot(t, ysin, 'bo', fillstyle='none', markersize=10)
    ax.set_xlabel('time')
    ax.set_ylabel('sin(t)')
    ax.set_title('Plot of sin(t)')

    window1.apply_tight_layout()

    line1.set_data([], [])
    line2.set_data([], [])
    f.canvas.draw()
    f.canvas.flush_events()

    background = f.canvas.copy_from_bbox(ax.bbox)

    # scat = ax.scatter(t, ysin, marker='.')


    # animate
    times = []
    dt = 0.1
    t_live = t.copy()
    for k in range(100):
        t_live += dt
        data[:,1] = np.sin(t_live)
        f.canvas.restore_region(background)
        line1.set_data(t, data[:, 1])
        line2.set_data(t, data[:, 1])
        ax.draw_artist(line1)
        ax.draw_artist(line2)

        # scat.set_offsets(data)
        # ax.draw_artist(scat)

        # window1.update()
        ut = tabby.TabbedPlotWindow.update_all(0.001)
        times.append(ut)

    print(f"Avg update times: {np.mean(times)}")

    tabby.abracatabra(block=not tabby.is_interactive())


if __name__ == "__main__":
    test_tabbed_plot_window()
    # test_tabbed_plot_window()
