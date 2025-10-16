import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import colorsys

def get_text_color(rgb):
    r, g, b = rgb
    def adjust(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    
    L = 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)

    return "black" if L > 0.179  else "white"

# Helper function to darken a color by a given factor.

# Load the DataFrame.
df = pd.read_pickle("experiment_database.pkl")

#metric_checked = "RMSE_acceleration"
#metric_checked = "RMSE_validation"
#metric_checked = "RMSE_trajectory"
metric_checked = "RMSE_model"

# Group the DataFrame by the unique condition tuple.
unique_groups = df[['algoritm', 'optimization_function', 'noise_level']].drop_duplicates()




grouped = df.groupby(['algoritm', 'optimization_function', 'noise_level'])[['filename', metric_checked]]
# Convert to a list of tuples

group_list = [x for x,_ in grouped]

group_list = sorted(group_list)



# Create an empty 2D grid (DataFrame) with groups as row and column labels
double_entry_table_result = pd.DataFrame(index=group_list, columns=group_list, dtype=float)
double_entry_table_count = pd.DataFrame(index=group_list, columns=group_list, dtype=float)


group_num = len(grouped)



# Example: Iterate over all groups
for group_key1, group_df1 in grouped:

    for group_key2, group_df2 in grouped:  

        merged_df = pd.merge(group_df1, group_df2, on="filename", suffixes=('_df1', '_df2')).dropna()
        merged_df["evolution"] = (merged_df[metric_checked+'_df1']-merged_df[metric_checked+'_df2'])/(merged_df[metric_checked+'_df1']+merged_df[metric_checked+'_df2'])

        double_entry_table_result.at[group_key2,group_key1] = merged_df["evolution"].mean()*100
        double_entry_table_count.at[group_key2,group_key1] = len(merged_df)




# Assuming double_entry_table_result is a DataFrame
fig, ax = plt.subplots(figsize=(6.4, 5.2))  # Increased size for better readability

colormap=cm.RdYlGn

cax = ax.matshow(double_entry_table_result, cmap=colormap, vmin=-100, vmax=100)

# Add color bar
plt.colorbar(cax)

# Extract noise levels (assuming they are stored as third elements in tuples)
noise_levels = [str(item[2]) for item in group_list]


ax.set_xticks(np.arange(len(noise_levels)))
ax.tick_params(bottom=True, labelbottom=True,top=False, labeltop=False)
ax.set_xticklabels(noise_levels, rotation=0, fontsize=8)  # Rotated for readability

#Extract main categories (first two elements)

master_labels = [(item[0], item[1]) for item in group_list[::4]]

# label the classes X axis:
sec = ax.secondary_xaxis(location=0)
position_label_tick = (np.arange(len(noise_levels)/4)+.5)*len(noise_levels)/4 -0.5
sec.set_xticks(position_label_tick, labels=[f"\n \n {x[0]} \n {"".join(x[1].split("_")[0])}" for x in master_labels[:4]],fontsize=10)
sec.tick_params('x', length=0)

sec2 = ax.secondary_xaxis(location=0)
position_label_tick = (np.arange(len(noise_levels)/4+1))*len(noise_levels)/4 -0.5
sec2.set_xticks(position_label_tick, labels=[])
sec2.tick_params('x', length=40, width=1.5)

# label the classes Y axis:
sec3 = ax.secondary_yaxis(location=0)
position_label_tick = (np.arange(len(noise_levels)/4)+.5)*len(noise_levels)/4 -0.5
sec3.set_yticks(position_label_tick, labels=[f"{x[0]} \n {"".join(x[1].split("_")[0])}" for x in master_labels[:4]],fontsize=10)
sec3.tick_params('y', length=0,pad=30)

sec4 = ax.secondary_yaxis(location=0)
position_label_tick = (np.arange(len(noise_levels)/4+1))*len(noise_levels)/4 -0.5
sec4.set_yticks(position_label_tick, labels=[])
sec4.tick_params('y', length=40, width=1.5)


# Set y-ticks
ax.set_yticks(np.arange(len(noise_levels)))
ax.set_yticklabels(noise_levels, fontsize=8)

# Show values in the cells

max_result = np.nanmax(double_entry_table_result.to_numpy())

min_result = np.nanmin(double_entry_table_result.to_numpy())

def normalise(point):
    return (point+100)/200

for i in range(len(group_list)):
    for j in range(len(group_list)):
        if np.isfinite(double_entry_table_result.iloc[i, j]):

            text_color=get_text_color(colormap(normalise(double_entry_table_result.iloc[i, j]))[:3])

            #ax.text(j, i, f'{double_entry_table_result.iloc[i, j]:.0f}', ha='center', va='center', color=text_color,fontsize=6)
            #ax.text(j, i+0.05, f'{double_entry_table_count.iloc[i, j]:.0f}', ha='center', va='top', color=text_color,fontsize=8)

plt.title(f"Cross comparison {" ".join(metric_checked.split("_"))}")
plt.tight_layout()

fig.savefig(f"poster_figure/method_comparison_{metric_checked}_tiny.svg", format="svg")
#plt.show()