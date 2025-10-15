import numpy as np
import abracatabra


def test_readme_example():
    window1 = abracatabra.TabbedPlotWindow(window_id="test", ncols=2)
    window2 = abracatabra.TabbedPlotWindow(size=(500, 400))

    # data
    t = np.arange(0, 10, 0.001)
    ysin = np.sin(t)
    ycos = np.cos(t)

    fig = window1.add_figure_tab("sin", col=0)
    ax = fig.add_subplot()
    (line1,) = ax.plot(t, ysin, "--")
    ax.set_xlabel("time")
    ax.set_ylabel("sin(t)")
    ax.set_title("Plot of sin(t)")

    fig = window1.add_figure_tab("time", col=1)
    ax = fig.add_subplot()
    ax.plot(t, t)
    ax.set_xlabel("time")
    ax.set_ylabel("t")
    ax.set_title("Plot of t")

    window1.apply_tight_layout()

    fig = window2.add_figure_tab("cos")
    ax = fig.add_subplot()
    (line2,) = ax.plot(t, ycos, "--")
    ax.set_xlabel("time")
    ax.set_ylabel("cos(t)")
    ax.set_title("Plot of cos(t)")

    fig = window2.add_figure_tab("sin^2")
    ax = fig.add_subplot()
    ax.plot(t, ysin**2)
    ax.set_xlabel("time")
    ax.set_ylabel("t")
    ax.set_title("Plot of t", fontsize=20)

    window2.apply_tight_layout()

    # animate
    dt = 0.1
    for k in range(100):
        t += dt
        ysin = np.sin(t)
        line1.set_ydata(ysin)
        ycos = np.cos(t)
        line2.set_ydata(ycos)
        abracatabra.update_all_windows(0.01)

    abracatabra.abracatabra(block=False)
    assert True


if __name__ == "__main__":
    test_readme_example()
