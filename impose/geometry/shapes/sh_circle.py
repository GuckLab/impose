from .sh_ellipse import Ellipse


class Circle(Ellipse):
    def __init__(self, x=33., y=10., r=23., phi=0, point_um=1):
        """Circle

        Parameters
        ----------
        x, y: float
            center coordinates [pt]
        r: float
            radius of the sphere [pt]
        phi: float
            rotation angle [rad]; this is required when you have
            to compare point clouds (via :func:`Ellipse.to_points`).

        point_um: float
            point size in microns
        """
        super(Circle, self).__init__(x=x, y=y, a=r, b=r, phi=phi,
                                     point_um=point_um)

    def __getstate__(self):
        return dict(x=self.x,
                    y=self.y,
                    r=self.r,
                    phi=self.phi,
                    point_um=self.point_um)

    def __setstate__(self, state):
        self.x = state["x"]
        self.y = state["y"]
        self.r = state["r"]
        self.phi = state["phi"]
        self.point_um = state["point_um"]

    def __repr__(self):
        fmtstr = "<Circle(x={:.5g}, y={:.5g}, r={:.3g}, point_um={:.3g}) " \
                 + "at {}>"
        return fmtstr.format(self.x, self.y, self.r, self.point_um,
                             hex(id(self)))

    def __str__(self):
        fmtstr = "Circle x={:.3g}µm, y={:.3g}µm, r={:.3g}µm"
        pum = self.point_um
        return fmtstr.format(self.x*pum, self.y*pum, self.r*pum)

    @property
    def r(self):
        return self.a

    @r.setter
    def r(self, r):
        self.a = r
        self.b = r

    @staticmethod
    def from_pg_roi(roi, tr, point_um):
        """Instantiate from a pyqtgraph ROI object"""
        ell = Ellipse.from_pg_roi(roi, tr, point_um)
        state = ell.__getstate__()
        # also remember "phi", so we can compare point clouds
        cir = Circle(x=state["x"], y=state["y"], r=state["a"],
                     phi=state["phi"], point_um=state["point_um"])
        return cir
