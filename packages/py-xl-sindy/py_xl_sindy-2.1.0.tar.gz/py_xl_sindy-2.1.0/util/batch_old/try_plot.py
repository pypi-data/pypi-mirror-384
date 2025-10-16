import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec

# Generate sample data
x = np.linspace(0, 10, 100)
y1, y2, y3 = np.sin(x), np.cos(x), np.tan(x) * 0.1  # Scaled tan to avoid extreme values
y4, y5, y6 = np.exp(-x), np.log1p(x), np.sqrt(x)

# Create figure with specific size (landscape 2:1 ratio)
fig = plt.figure(figsize=(12, 6))
gs = gridspec.GridSpec(4, 4, height_ratios=[1, 1, 1, 1], width_ratios=[1, 1, 1, 1])

# Top three plots (sharing x and y labels but not axes)
ax1 = plt.subplot(gs[0, :])
ax2 = plt.subplot(gs[1, :], sharex=ax1, sharey=ax1)
ax3 = plt.subplot(gs[2, :], sharex=ax1, sharey=ax1)

# Bottom six plots (2 sets of 3 stacked)
ax4 = plt.subplot(gs[3, 0], sharex=ax1, sharey=ax1)
ax5 = plt.subplot(gs[3, 1], sharex=ax1, sharey=ax1)
ax6 = plt.subplot(gs[3, 2], sharex=ax1, sharey=ax1)
ax7 = plt.subplot(gs[3, 3], sharex=ax1, sharey=ax1)

# Plot data for top three plots
ax1.plot(x, y1, label="sin(x)", color="b")
ax2.plot(x, y2, label="cos(x)", color="r")
ax3.plot(x, y3, label="tan(x)", color="g")

# Plot data for bottom six plots
ax4.plot(x, y4, label="exp(-x)", color="m")
ax5.plot(x, y5, label="log1p(x)", color="c")
ax6.plot(x, y6, label="sqrt(x)", color="y")
ax7.plot(x, y1 * y2, label="sin(x) * cos(x)", color="k")

# Set labels and legends
for ax in [ax1, ax2, ax3, ax4, ax5, ax6, ax7]:
    ax.legend()
    ax.grid(True)

ax1.set_ylabel("Top Y Label")
ax4.set_ylabel("Bottom Y Label")
ax4.set_xlabel("X Axis Label")
ax5.set_xlabel("X Axis Label")
ax6.set_xlabel("X Axis Label")
ax7.set_xlabel("X Axis Label")

# Adjust layout
plt.tight_layout()
plt.show()
