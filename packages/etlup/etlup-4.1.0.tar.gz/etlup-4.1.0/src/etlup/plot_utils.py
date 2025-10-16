
from io import BytesIO
import base64
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
from collections import namedtuple
import numpy as np

def convert_fig_to_html_img(fig) -> str:
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    # style = "width: 80%; height: auto; @media only screen and (max-width: 390px) { img {width: 100px;} }"
    # return f"<img src='data:image/png;base64,{data}' style={style}>"
    img = f'<img src="data:image/png;base64,{data}" style="width: clamp(300px, 75vw, 1000px); height: auto;">'
    return img

def module_plot(bl_nw, vmin:int=None, vmax:int=None, title:str=None) -> Figure:
    fig, axs = plt.subplots(2, 4, figsize=(32*1.25, 16*1.25), 
                           gridspec_kw={'width_ratios': [1.2, 1.2, 0.8, 0.8]})

    Position = namedtuple("Position", ["pos", "matrix", "invert_x", "invert_y", "heatmap_ax", "hist_ax"])
    positions = [
        Position(pos='3', matrix=bl_nw.pos_3, invert_x=False,  invert_y=False,  heatmap_ax=axs[0, 0], hist_ax=axs[0, 2]),
        Position(pos='1', matrix=bl_nw.pos_1, invert_x=False,  invert_y=False,  heatmap_ax=axs[0, 1], hist_ax=axs[0, 3]),
        Position(pos='2', matrix=bl_nw.pos_2, invert_x=True, invert_y=True, heatmap_ax=axs[1, 0], hist_ax=axs[1, 2]),
        Position(pos='0', matrix=bl_nw.pos_0, invert_x=True, invert_y=True, heatmap_ax=axs[1, 1], hist_ax=axs[1, 3]),
    ]
    images = []
    for pos, matrix, invert_x, invert_y, heatmap_ax, hist_ax in positions:
        if matrix is not None:
            matrix = np.array(matrix)
            
            # Create heatmap
            im = heatmap_ax.matshow(matrix, vmin=vmin, vmax=vmax)
            images.append(im)
            for row in range(16):
                for col in range(16):
                    #       x,   y
                    heatmap_ax.text(col, row, int(matrix[row,col]), ha="center", va="center", color="w", fontsize=12)
            
            heatmap_ax.set_xlabel('Column', fontsize=16)
            heatmap_ax.set_ylabel('Row', fontsize=16)
            if invert_x:
                heatmap_ax.invert_xaxis()
            if invert_y:
                heatmap_ax.invert_yaxis()

            heatmap_ax.minorticks_off()
            heatmap_ax.xaxis.set_ticks_position('bottom')
            heatmap_ax.xaxis.set_label_position('bottom')
            heatmap_ax.set_aspect('equal')  # Make heatmap square
            heatmap_ax.tick_params(axis='both', which='major', labelsize=14)  # Set tick font size
            
            # Get ETROC vtemp value for this position if available
            etroc_Vtemp = getattr(bl_nw, f'etroc_{pos}_Vtemp', None)
            
            # Create combined label with position, ADC, mean, and std dev
            pos_label = pos
            if etroc_Vtemp is not None:
                pos_label = f"{pos} (Temp (volts): {etroc_Vtemp})"
            
            # Add mean and std dev to the same line
            mean_val = np.round(np.mean(matrix), 2)
            std_val = np.round(np.std(matrix), 2)
            combined_label = f"{pos_label} | μ={mean_val}, σ={std_val}"
            
            heatmap_ax.text(0.0, 1.01, combined_label, 
                    ha="left", 
                    va="bottom", 
                    transform=heatmap_ax.transAxes, 
                    fontsize=18, 
                    fontweight = "bold")
            
            # Create histogram
            flat_data = matrix.flatten()
            
            # Set bins to align with integer values
            data_min = int(np.floor(flat_data.min()))
            data_max = int(np.ceil(flat_data.max()))
            bins = np.arange(data_min, data_max + 2) - 0.5  # Bin edges at x.5 to center bars on integers
            
            hist_ax.hist(flat_data, bins=bins if bl_nw.name.lower()=='noisewidth' else None, alpha=0.7, edgecolor='black')
            hist_ax.axvline(np.mean(flat_data), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(flat_data):.2f}')
            hist_ax.axvline(np.mean(flat_data) + np.std(flat_data), color='orange', linestyle='--', linewidth=1, label=f'+1σ: {np.mean(flat_data) + np.std(flat_data):.2f}')
            hist_ax.axvline(np.mean(flat_data) - np.std(flat_data), color='orange', linestyle='--', linewidth=1, label=f'-1σ: {np.mean(flat_data) - np.std(flat_data):.2f}')
            hist_ax.set_xlabel("DAC", fontsize=16)
            hist_ax.set_ylabel('Number of Pixels', fontsize=16)
            
            # Set x-axis limits based on test name
            if bl_nw.name.lower() == 'noisewidth':
                hist_ax.set_xlim(0, 12)
                hist_ax.set_xticks(range(0, 13))  # Show integer ticks from 0 to 12
            # For baseline, leave axis limits automatic (no xlim set)
            
            hist_ax.tick_params(axis='both', which='major', labelsize=14)  # Set tick font size
            
            # Don't set aspect equal for histograms - let them fill the space
            hist_ax.legend(fontsize=16)
            hist_ax.grid(True, alpha=0.3)
            
            # Use same position label with ADC if available
            etroc_Vtemp = getattr(bl_nw, f'etroc_{pos}_ADC', None)
            pos_label = f'Pos {pos}'
            if etroc_Vtemp is not None:
                pos_label = f'Pos {pos} (ADC: {etroc_Vtemp})'
            
            hist_ax.text(0.0, 1.01, pos_label, 
                    ha="left", 
                    va="bottom", 
                    transform=hist_ax.transAxes, 
                    fontsize=24, 
                    fontweight = "bold")

        else:
            # Handle the case where matrix is None
            heatmap_ax.set_title(f'{pos} (No Data)', fontsize=24, fontweight='bold')
            heatmap_ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center', 
                    transform=heatmap_ax.transAxes, fontsize=20, color='gray')
            heatmap_ax.set_xlim(0, 15)
            heatmap_ax.set_ylim(0, 15)
            heatmap_ax.set_aspect('equal')  # Make empty heatmap square
            heatmap_ax.set_xticks([])
            heatmap_ax.set_yticks([])
            
            hist_ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center', 
                    transform=hist_ax.transAxes, fontsize=20, color='gray')
            # Don't set aspect equal for empty histograms either
            hist_ax.set_xticks([])
            hist_ax.set_yticks([])
    
    # Place colorbar for the heatmaps only (first two columns)
    cbar = fig.colorbar(images[0], ax=axs[:, :2]) # first two columns
    cbar.set_label(bl_nw.name.capitalize(), fontsize = 40)

    fig.text(0.08, 0.92, "CMS", fontsize=50, ha="left", va="bottom", fontweight='bold')
    fig.text(0.155, 0.924, "ETL Preliminary", fontsize=40, ha="left", va="bottom", style='italic')
    
    # Add module information (serial number, ambient temp, bias voltage)
    info_text = f"{bl_nw.module}"
    if hasattr(bl_nw, 'ambient_celcius') and bl_nw.ambient_celcius is not None:
        info_text += f" | Ambient: {bl_nw.ambient_celcius}°C"
    if hasattr(bl_nw, 'bias_volts') and bl_nw.bias_volts is not None:
        info_text += f" | Bias: {bl_nw.bias_volts}V"
    
    fig.text(0.5, 0.96, info_text, fontsize=24, ha="center", va="bottom", fontweight='bold')
    
    # Add black triangles to top right corners of both sections
    offset = 0
    size = 0.05
    
    # Triangle for heatmap section (left side)
    triangle_x_left = [0.48 - offset, 0.48 - offset, 0.48 - offset - size]
    triangle_y_left = [0.95, 0.95 - size, 0.95]
    
    triangle_left = Polygon(list(zip(triangle_x_left, triangle_y_left)), 
                           closed=True, 
                           transform=fig.transFigure, 
                           facecolor='black', 
                           edgecolor='black',
                           zorder=1000,
                           clip_on=False)
    fig.add_artist(triangle_left)
    
    # Triangle for histogram section (right side)
    triangle_x_right = [0.95 - offset, 0.95 - offset, 0.95 - offset - size]
    triangle_y_right = [0.95, 0.95 - size, 0.95]
    
    triangle_right = Polygon(list(zip(triangle_x_right, triangle_y_right)), 
                            closed=True, 
                            transform=fig.transFigure, 
                            facecolor='black', 
                            edgecolor='black',
                            zorder=1000,
                            clip_on=False)
    fig.add_artist(triangle_right)
    fig.suptitle(f"Orientation: sensor side up, you are looking on the sensors", 
                    fontsize=22, fontweight='bold', y=0.04)
    return fig