import pandas as pd
import plotly.express as px

pd.set_option('mode.chained_assignment', None)


def plot_weights(ID: str, task_type: str, last=None):
    """
    plot evolution of weights throughout training
    """

    if last:
        df = pd.read_csv(f'fault_tolerant_flight_control_drl/agent/trained/tmp/monitor.csv', header=0)

    else:
        df = pd.read_csv(f'fault_tolerant_flight_control_drl/agent/trained/{task_type}_{ID}.csv', header=0)

    fig = px.line(df, x=df['l'], y=df.iloc[:, 3:].columns)

    fig.update_layout(
        showlegend=False,
        width=800, height=300,
        font=dict(size=17),
        yaxis=dict(
            tickfont=dict(size=18)
        ),
        xaxis=dict(
            tickfont=dict(size=18),
        ),
        xaxis_title='Training steps', yaxis_title=r'$w^{[2]}_{11, 1:10}$',
        template="plotly",
        margin=dict(l=50, r=5, b=50, t=10)
    )

    fig.write_image(f"figures/{task_type}_{ID}_weights.pdf")


# plot_weights('7AJEAX_ice', '3attitude_step', last=True)
# plot_weights('P7V00G','altitude_2attitude')
