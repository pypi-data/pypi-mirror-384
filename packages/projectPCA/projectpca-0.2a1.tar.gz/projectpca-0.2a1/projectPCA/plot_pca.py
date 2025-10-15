### Code to plot PC coordinates
### @Harald Ringbauer, October 2025

import matplotlib.pyplot as plt

### Optional Import of plotly for HTML plotting
try:
    import plotly.graph_objects as go
except:
    go = False

def plot_df_pc(df_pcs=[], df_bgrd_pcs=[], plot_cols=["pc1", "pc2"],
               figsize=(6,6), s=30, lw=0.5, leg_loc="upper right",
               savepath="", show=True):
    """Plot a simple PCA:
    df_pcs: Value of the PCA to plot
    df_bgrd_pcs: Pandas dataframe with columns pc1 and pc2.
    plot_cols: List of which two columns to plot (and order)
    Usually pre-computed. If given, plot the values of this background."""
    assert(len(plot_cols)==2)
    col1, col2 = plot_cols # Extract the two plot columns

    fig = plt.figure(figsize=figsize)
    ax=plt.gca()

    if len(df_bgrd_pcs)>0:
        ax.scatter(df_bgrd_pcs[col1], df_bgrd_pcs[col2], c="silver", s=15, alpha=0.5)
    
    for _, row in df_pcs.iterrows():
        ax.scatter(row[col1], row[col2], lw=lw, 
                   s=s, edgecolor="k", label = row["iid"])
    
    ### Formatting Plot
    ax.set_xlabel(col1)
    ax.set_ylabel(col2)
    ax.legend(loc=leg_loc)

    ### Save Figure
    if len(savepath)>0:
        plt.savefig(savepath, bbox_inches ='tight', pad_inches = 0, dpi=600)

    if show:
        plt.show()
    return fig



def plot_df_pc_plotly(
    df_pcs, df_bgrd_pcs=None, plot_cols=("pc1", "pc2"),
    s=8, lw=0.5, leg_loc="top right",
    savepath="", show=True, title="PCA Plot (Interactive)"):

    if not go:
        print("You need to install Plotly to plot .html. Aborting figure...")
        return None
    
    col1, col2 = plot_cols
    fig = go.Figure()

    # Background points with hover
    if df_bgrd_pcs is not None and len(df_bgrd_pcs) > 0:
        hover_bg = [
            f"<b>{iid}</b><br>pop: {pop}" 
            for iid, pop in zip(df_bgrd_pcs["iid"], df_bgrd_pcs["pop"])
        ]
        hovertemplate_bg = "<b>%{text}</b><br>" + col1 + ": %{x}<br>" + col2 + ": %{y}<extra></extra>"

        fig.add_trace(go.Scattergl(
            x=df_bgrd_pcs[col1],
            y=df_bgrd_pcs[col2],
            mode="markers",
            marker=dict(size=5, color="lightgray", opacity=0.6),
            text=hover_bg,
            hovertemplate=hovertemplate_bg,
            name="Background"
        ))

    # Foreground points
    hovertemplate_fg = "<b>%{text}</b><br>" + col1 + ": %{x}<br>" + col2 + ": %{y}<extra></extra>"
    fig.add_trace(go.Scattergl(
        x=df_pcs[col1],
        y=df_pcs[col2],
        mode="markers",
        marker=dict(size=s, color="steelblue", line=dict(width=lw, color="black")),
        text=df_pcs["iid"],
        hovertemplate=hovertemplate_fg,
        name="Samples"
    ))

    # Layout
    fig.update_layout(
        title=title,
        xaxis_title=col1,
        yaxis_title=col2,
        template="plotly_white",
        width=600,
        height=600,
        legend=dict(
            y=0.99 if "top" in leg_loc else 0.01,
            x=0.99 if "right" in leg_loc else 0.01,
            yanchor="top" if "top" in leg_loc else "bottom",
            xanchor="right" if "right" in leg_loc else "left"
        )
    )

    if savepath:
        fig.write_html(savepath, include_plotlyjs="cdn")
        print(f"✅ Saved interactive plot to: {savepath}")

    if show:
        fig.show()

    return fig