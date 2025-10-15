Plotnine (:mod:`.compat.plotnine`)
**********************************

`Package documentation <https://plotnine.org>`_

.. currentmodule:: genno.compat.plotnine

To use :class:`.Plot`:

.. ipython:: python
   :suppress:

   import matplotlib
   matplotlib.use("svg")

.. ipython::

   In [1]:    from pathlib import Path
      ...:
      ...:    import xarray as xr
      ...:    import plotnine as p9
      ...:
      ...:    from genno import Computer, Quantity
      ...:    from genno.compat.plotnine import Plot


1. Create a subclass that overrides :meth:`Plot.generate`, :attr:`Plot.basename`, and optionally :attr:`Plot.inputs`.

   .. ipython::

      In [1]: class DemoPlot(Plot):
         ...:     basename = "plotnine-demo"
         ...:     suffix = ".svg"
         ...:
         ...:     def generate(self, x, y):
         ...:         data = x.merge(y, on="t")
         ...:         return (
         ...:             p9.ggplot(data, p9.aes(x="x", y="y"))
         ...:             + p9.geom_line(color="red")
         ...:             + p9.geom_point(color="blue")
         ...:         )

2. :meth:`~.Computer.add` the class to a :class:`.Computer` directly.
   The :meth:`.Plot.add_tasks` method handles connecting the :attr:`.Plot.inputs` to :meth:`.Plot.save`:

   .. ipython:: python

      # Set up a Computer, including the output path and some data
      c = Computer(output_dir=Path("."))
      t = {"t": [-1, 0, 1]}
      c.add("x:t", Quantity([1.0, 2, 3], coords=t, name="x"))
      c.add("y:t", Quantity([1.0, 4, 9], coords=t, name="y"))

      # Add the plot to the Computer
      c.add("plot", DemoPlot, "x:t", "y:t")

      # Show the task that was added
      c.graph["plot"]

3. :meth:`.get` the node. The result is the path the the saved plot(s).

   .. ipython::

      In [1]: c.get("plot")
      Out[1]: PosixPath("plotnine-demo.svg")

   .. image:: ./plotnine-demo.svg
      :alt: Demonstration output from genno.compat.plotnine.

.. automodule:: genno.compat.plotnine
   :members:
