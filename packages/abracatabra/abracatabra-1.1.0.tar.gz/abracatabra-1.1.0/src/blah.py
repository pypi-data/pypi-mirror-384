# %%
import numpy as np
import abracatabra as tabby
from scat import test_tabbed_plot_window as scat_test


def test_tabbed_plot_window():
    window1 = tabby.TabbedPlotWindow('1', nrows=[1,2])
    window2 = tabby.TabbedPlotWindow(2, size=(500,400), ncols=2)

    # data
    t = np.arange(0, 10, 0.001)
    ysin = np.sin(t)
    ycos = np.cos(t)

    f = window1.add_figure_tab("sin")
    ax = f.add_subplot()
    line1, = ax.plot(t, ysin, '--')
    ax.set_xlabel('time')
    ax.set_ylabel('sin(t)')
    ax.set_title('Plot of sin(t)')
    # f = plt.figure(figsize=(12.76, 8.66))
    # f.show()
    # ax = f.add_subplot()
    # line1, = ax.plot(t, ysin, '--')
    # ax.set_xlabel('time')
    # ax.set_ylabel('sin(t)')
    # ax.set_title('Plot of sin(t)')

    window1 = tabby.TabbedPlotWindow(window_id='1')
    window1.apply_tight_layout()

    f = window1.add_figure_tab("time", col=1)
    ax = f.add_subplot()
    ax.plot(t, t)
    ax.set_xlabel('time')
    ax.set_ylabel('t')
    ax.set_title('Plot of t')
    # f = plt.figure(figsize=(12.76, 8.66))
    # f.show()
    # ax = f.add_subplot()
    # ax.plot(t, t)
    # ax.set_xlabel('time')
    # ax.set_ylabel('t')
    # ax.set_title('Plot of t')

    window1.apply_tight_layout()
    window1.enable_tab_autohide()
    window1.set_tab_position('left')

    f = window2.add_figure_tab("cos")
    ax = f.add_subplot()
    line2, = ax.plot(t, ycos, '--')
    ax.set_xlabel('time')
    ax.set_ylabel('cos(t)')
    ax.set_title('Plot of cos(t)')
    # f = plt.figure(figsize=(4.96, 3.66))
    # f.show()
    # ax = f.add_subplot()
    # line2, = ax.plot(t, ycos, '--')
    # ax.set_xlabel('time')
    # ax.set_ylabel('cos(t)')
    # ax.set_title('Plot of cos(t)')

    f = window2.add_figure_tab("time")
    ax = f.add_subplot()
    ax.plot(t, t)
    ax.set_xlabel('time')
    ax.set_ylabel('t')
    ax.set_title('Plot of t', fontsize=20)
    # f = plt.figure(figsize=(4.96, 3.66))
    # f.show()
    # ax = f.add_subplot()
    # ax.plot(t, t)
    # ax.set_xlabel('time')
    # ax.set_ylabel('t')
    # ax.set_title('Plot of t', fontsize=20)

    window1.apply_tight_layout()
    window2.apply_tight_layout()

    # animate
    times = []
    dt = 0.1
    for k in range(100):
        t += dt
        ysin = np.sin(t)
        line1.set_ydata(ysin)
        ycos = np.cos(t)
        line2.set_ydata(ycos)
        # window1.update()
        ut = tabby.update_all_windows(0.001)
        times.append(ut)

    print(f"Avg update times: {np.mean(times)}")

    tabby.abracatabra()


if __name__ == "__main__":
    test_tabbed_plot_window()
    scat_test()
    # test_tabbed_plot_window()
