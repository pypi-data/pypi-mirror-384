import numpy as np

from wnetalign.spectrum import Spectrum
from wnetalign.aligner import WNetAligner as Solver


def test_flows():
    spectrum1 = Spectrum(np.array([[1, 2, 30]]), np.array([1, 4, 3]))
    spectrum2 = Spectrum(np.array([[1, 4, 30, 31]]), np.array([5, 1, 1, 1]))

    def dist_fun(x, y):
        return np.linalg.norm(x - y, axis=0)
    trash_cost = 10
    max_distance = 100
    solver = Solver(
        empirical_spectrum=spectrum1,
        theoretical_spectra=[spectrum2],
        distance_function=dist_fun,
        max_distance=max_distance,
        trash_cost=trash_cost,
        scale_factor=None,
    )

    solver.set_point([1])

    solver.print_diagnostics()

    print("Flows:")
    for flow in solver.flows():
        print(flow)

    # DGW = DecompositableGraphWrapper(solver.graph)
    # SG = list(DGW.get_subgraphs())[0]
    # print(SG.as_nx_graph())
    # SG.show()


if __name__ == "__main__":
    test_flows()
    print("Everything passed")
