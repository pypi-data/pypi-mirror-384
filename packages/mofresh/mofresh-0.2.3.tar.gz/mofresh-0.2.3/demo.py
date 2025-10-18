# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "altair==5.5.0",
#     "marimo",
#     "matplotlib==3.10.1",
#     "mofresh==0.1.0",
#     "mohtml==0.1.7",
#     "numpy==2.2.5",
#     "polars==1.29.0",
# ]
# ///

import marimo

__generated_with = "0.14.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import numpy as np
    return mo, np, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # `mofresh` demo

    The goal of this project is to offer a few tools that make it easy for you to refresh charts in marimo. This can be useful during a PyTorch training loop where you might want to update a chart on every iteration, but there are many other use-cases for this too. 

    ## How it works 

    The trick to get updating charts to work is to leverage [anywidget](https://anywidget.dev/). These widgets have a loop that is independant of the marimo cells which means that you can update a chart even if the cell hasn't completed running. The goal of this library is to make it easy to use this pattern by giving you a few utilities. 

    ## Updating `matplotlib` charts

    The easiest way to update matplotlib charts is to first write a function that can generate a chart. The most common way to use matplotlib is to use syntax like `plt.plot(...)` followed by a `plt.show(...)` and the best way to capture all of these layers is to wrap them all ina single function. Once you have such a function, you can use the `@refresh_matplotlib` decorator to turn this function into something that we can use in a refreshable-chart.
    """
    )
    return


@app.cell
def _(np):
    import matplotlib.pylab as plt
    from mofresh import refresh_matplotlib

    @refresh_matplotlib
    def cumsum_linechart(data):
        y = np.cumsum(data)
        plt.plot(np.arange(len(y)), y)
    return (cumsum_linechart,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""The decorator takes the matplotlib image and turns it into a base64 encoded string that can be plotted by `<img>` tags in html. You can see this for yourself in the example below. The `img(src=...)` function call in `mohtml` is effectively a bit of syntactic sugar around `<img src="...">`.""")
    return


@app.cell
def _(cumsum_linechart):
    from mohtml import img 

    img(src=cumsum_linechart([1, 2, 3, 2]))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Having a static image is great, but we want dynamic images! That's where our `ImageRefreshWidget` comes in. It allows you to trigger a streaming update to an image by running code from another cell. Try it out below!""")
    return


@app.cell
def _(cumsum_linechart):
    from mofresh import ImageRefreshWidget

    widget = ImageRefreshWidget(src=cumsum_linechart([1,2,3,4]))
    widget
    return (widget,)


@app.cell
def _(cumsum_linechart, random, time, widget):
    data = [random.random() - 0.5]

    for i in range(20):
        data += [random.random() - 0.5]
        # This one line over here causes the update!
        widget.src = cumsum_linechart(data)
        time.sleep(0.2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""When you re-run the cell below you should see that the widget updates. This works because the widget knows how to respond to a change to the `widget.src` property. You only need to make sure that you pass along a base64 string that html images can handle, which is covered by the decorator that we applied earlier.""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Updating `altair` charts

    This library can also deal with altair charts. This works by turning the chart into an SVG. This is a static representation that does not require any javascript to run, which means that we can apply a similar pattern as before!

    > Due to a required dependency to convert the altair chart to SVG we cannot run the altair demo in WASM. This code will run just fine locally on your machine but currently breaks on the Github pages deployment.
    """
    )
    return


@app.cell
def _():
    import altair as alt
    from mofresh import refresh_altair, HTMLRefreshWidget, altair2svg
    return HTMLRefreshWidget, alt, refresh_altair


@app.cell
def _(HTMLRefreshWidget, alt, mo, np, pl, refresh_altair):
    _out = mo.md("This demo does not work on WASM on Github pages, it should locally though!")

    if mo.app_meta().request:
        @refresh_altair
        def altair_cumsum_chart(data):
            df = pl.DataFrame({
                "x": range(len(data)), "y": np.array(data).cumsum()
            })
            return alt.Chart(df).mark_line().encode(x="x", y="y")

        svg_widget = HTMLRefreshWidget(html=altair_cumsum_chart([1, 2]))
        _out = svg_widget
    _out
    return altair_cumsum_chart, svg_widget


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Unlike matplotlib charts though, altair is actually designed to give you objects back. That means that you don't need to use a decorated function for the update, you can also just convert the altair chart to SVG directly. This library supports utilities for both patterns.""")
    return


@app.cell
def _(altair_cumsum_chart, mo, random, svg_widget, time):
    from mohtml import p

    more_data = [random.random() - 0.5 for _ in range(10)]

    if mo.app_meta().request:
        for _i in range(10):
            more_data += [random.random() - 0.5]
            svg_widget.html = altair_cumsum_chart(more_data)
            time.sleep(0.1)

        for _i in range(10):
            more_data += [random.random() - 0.5]
            svg_widget.html = altair_cumsum_chart(more_data)
            time.sleep(0.1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Oh ... one more thing about that `HTMLRefreshWidget`

    We are injecting html now into that widget to allow us to draw altair charts. But why stop there? We can put in any HTML that we like!
    """
    )
    return


@app.cell
def _(HTMLRefreshWidget, mo):
    html_widget = mo.ui.anywidget(HTMLRefreshWidget())
    html_widget
    return (html_widget,)


@app.cell
def _(html_widget, time):
    for _i in range(10):
        html_widget.html = f"<p>Counting {_i}</p>"
        time.sleep(0.1)
    return


@app.cell
def _(mo):
    mo.md(r"""## Progress bars""")
    return


@app.cell
def _():
    from mofresh import ProgressBar

    progress = ProgressBar(value=0, max_value=100)
    progress
    return (progress,)


@app.cell
def _(progress, random, time):
    from threading import Lock
    from collections import deque

    def slow_task():
        """Simulated task that takes time"""
        time.sleep(random.random())

    progress.value = 0 
    for _ in range(100):
        slow_task()
        progress.value += 1
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Enjoy!""")
    return


@app.cell
def _():
    import random 
    import time 
    return random, time


if __name__ == "__main__":
    app.run()
