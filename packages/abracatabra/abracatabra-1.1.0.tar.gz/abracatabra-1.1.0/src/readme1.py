import numpy as np
import abracatabra as tabby


window1 = tabby.TabbedPlotWindow(window_id="README example", ncols=2)
window2 = tabby.TabbedPlotWindow(size=(500, 400))

# data
t = np.arange(0, 10, 0.001)
ysin = np.sin(t)
ycos = np.cos(t)


f = window1.add_figure_tab("sin", col=0)
ax = f.add_subplot()
(line1,) = ax.plot(t, ysin, "--")
ax.set_xlabel("time")
ax.set_ylabel("sin(t)")
ax.set_title("Plot of sin(t)")

f = window1.add_figure_tab("time", col=1)
ax = f.add_subplot()
ax.plot(t, t)
ax.set_xlabel("time")
ax.set_ylabel("t")
ax.set_title("Plot of t")

window1.apply_tight_layout()

f = window2.add_figure_tab("cos")
ax = f.add_subplot()
(line2,) = ax.plot(t, ycos, "--")
ax.set_xlabel("time")
ax.set_ylabel("cos(t)")
ax.set_title("Plot of cos(t)")

f = window2.add_figure_tab("time")
ax = f.add_subplot()
ax.plot(t, t)
ax.set_xlabel("time")
ax.set_ylabel("t")
ax.set_title("Plot of t", fontsize=20)

window2.apply_tight_layout()


### animate

## option 1
dt = 0.1
for k in range(100):
    t += dt
    ysin = np.sin(t)
    line1.set_ydata(ysin)
    ycos = np.cos(t)
    line2.set_ydata(ycos)

    # For timing to be accurate, you would have to calculate how long it took to
    # run the previous 5 lines and subtract that from dt
    tabby.update_all_windows(dt)

# You would need this to keep windows open if not in an interactive environment
# tabby.show_all_windows(block=True)


## option 2: use animation callbacks
print("Same thing, but using animation callbacks now")


def update_sin(frame: int):
    time = t + frame * dt
    line1.set_ydata(np.sin(time))


def update_cos(frame: int):
    time = t + frame * dt
    line2.set_ydata(np.cos(time))


window1.tab_groups[0, 0].get_tab("sin").register_animation_callback(update_sin)
window2.tab_groups[0, 0].get_tab("cos").register_animation_callback(update_cos)

# This method accounts for how long it takes to call the animation callbacks
# so that the time between frames is closer to the specified time step. Also,
# if a tab is not active (visible), it will not call the animation callback
# for that tab, which can save a lot of time if you have many tabs.
tabby.animate_all_windows(frames=100, ts=dt, print_timing=True, hold=False)

tabby.abracatabra()  # keep windows open if not in an interactive environment
